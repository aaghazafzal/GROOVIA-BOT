"""
🎵 Groovia Mass Indexer — MongoDB Database Layer
Handles all DB operations: save, check, update, stats
"""

import logging
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from config import MONGODB_URI, DB_NAME, COLLECTION

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database handler with connection pooling"""

    def __init__(self):
        self.client = None
        self.db     = None
        self.col    = None
        self.connect()

    # ─── CONNECTION ──────────────────────────────────────────────────────────

    def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            self.client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=10_000,
                connectTimeoutMS=10_000,
                socketTimeoutMS=60_000,
                maxPoolSize=10,
                retryWrites=True,
            )
            # Verify connection
            self.client.admin.command('ping')
            self.db  = self.client[DB_NAME]
            self.col = self.db[COLLECTION]
            self._ensure_indexes()
            logger.info("✅ MongoDB connected successfully")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise

    def _ensure_indexes(self):
        """Create necessary indexes (runs only if not already exist)"""
        existing = [idx['name'] for idx in self.col.list_indexes()]

        # 1. Unique index on yt_id — prevents duplicates
        if 'yt_id_unique' not in existing:
            self.col.create_index(
                [("yt_id", ASCENDING)],
                unique=True,
                name='yt_id_unique'
            )

        # 2. Text index for bot search (title + artist + album)
        # NOTE: language_override='_lang' prevents MongoDB from treating our
        # 'language' field as a language specifier (which caused WriteError).
        if 'search_text' not in existing:
            self.col.create_index(
                [("title", TEXT), ("artist", TEXT), ("album", TEXT)],
                name='search_text',
                default_language='english',
                language_override='_lang'  # Use non-existent field → avoids conflict
            )

        # 3. Status index — for pipeline resume
        if 'status_idx' not in existing:
            self.col.create_index([("status", ASCENDING)], name='status_idx')

        # 4. Language index — for bot filtering
        if 'language_idx' not in existing:
            self.col.create_index([("language", ASCENDING)], name='language_idx')

        # 5. Popularity index — for sorting search results
        if 'popularity_idx' not in existing:
            self.col.create_index(
                [("view_count", DESCENDING)],
                name='popularity_idx'
            )

        logger.info("✅ MongoDB indexes verified")

    # ─── WRITE OPERATIONS ────────────────────────────────────────────────────

    def add_to_queue(self, yt_id: str, metadata: dict) -> bool:
        """
        Add a song to the queue (status=pending).
        Returns True if added, False if already exists.
        """
        doc = {
            "yt_id":        yt_id,
            "title":        metadata.get("title", "Unknown"),
            "artist":       metadata.get("artist", "Unknown"),
            "artists":      metadata.get("artists", []),
            "album":        metadata.get("album", ""),
            "duration":     metadata.get("duration", 0),
            "language":     metadata.get("language", "unknown"),
            "genre":        metadata.get("genre", ""),
            "view_count":   metadata.get("view_count", 0),
            "priority":     metadata.get("priority", 4),  # 1=charts,2=artist,3=playlist,4=search
            "tg_file_id":   None,
            "tg_message_id":None,
            "file_size":    0,
            "quality":      "128kbps",
            "status":       "pending",       # pending → downloading → uploaded / failed
            "retry_count":  0,
            "error":        None,
            "indexed_at":   datetime.utcnow(),
            "uploaded_at":  None,
        }
        try:
            self.col.insert_one(doc)
            return True
        except DuplicateKeyError:
            return False  # Already in DB — skip silently

    def mark_downloading(self, yt_id: str):
        """Lock song as 'in progress' to prevent double processing"""
        self.col.update_one(
            {"yt_id": yt_id},
            {"$set": {"status": "downloading"}}
        )

    def mark_uploaded(self, yt_id: str, tg_file_id: str,
                      tg_message_id: int, file_size: int):
        """Mark song as successfully uploaded to Telegram"""
        self.col.update_one(
            {"yt_id": yt_id},
            {"$set": {
                "tg_file_id":    tg_file_id,
                "tg_message_id": tg_message_id,
                "file_size":     file_size,
                "status":        "uploaded",
                "error":         None,
                "uploaded_at":   datetime.utcnow(),
            }}
        )

    def mark_failed(self, yt_id: str, error: str):
        """Mark song as failed, increment retry counter"""
        self.col.update_one(
            {"yt_id": yt_id},
            {
                "$set": {"status": "failed", "error": str(error)[:500]},
                "$inc": {"retry_count": 1}
            }
        )

    def reset_stuck(self):
        """Reset songs stuck in 'downloading' state (from crashed workers)"""
        result = self.col.update_many(
            {"status": "downloading"},
            {"$set": {"status": "pending", "error": "reset_after_crash"}}
        )
        if result.modified_count:
            logger.info(f"🔄 Reset {result.modified_count} stuck songs → pending")

    def reset_failed(self, max_retries: int = 3):
        """Re-queue failed songs that haven't exceeded max retries"""
        result = self.col.update_many(
            {"status": "failed", "retry_count": {"$lt": max_retries}},
            {"$set": {"status": "pending"}}
        )
        logger.info(f"🔄 Re-queued {result.modified_count} failed songs")
        return result.modified_count

    # ─── READ OPERATIONS ─────────────────────────────────────────────────────

    def is_processed(self, yt_id: str) -> bool:
        """Check if song is already uploaded (fast indexed lookup)"""
        doc = self.col.find_one(
            {"yt_id": yt_id, "status": "uploaded"},
            {"_id": 1}
        )
        return doc is not None

    def exists(self, yt_id: str) -> bool:
        """Check if yt_id is in DB at all (any status)"""
        return self.col.count_documents({"yt_id": yt_id}, limit=1) > 0

    def get_pending_batch(self, batch_size: int = 200) -> list:
        """Get a batch of pending songs, highest priority first"""
        return list(self.col.find(
            {"status": "pending"},
            {"yt_id": 1, "title": 1, "artist": 1, "duration": 1,
             "priority": 1, "_id": 0}
        ).sort([("priority", 1), ("view_count", -1)]).limit(batch_size))

    def search_songs(self, query: str, language: str = None,
                     limit: int = 10) -> list:
        """
        Full-text search for the Groovia bot.
        Returns uploaded songs matching the query.
        """
        filt = {"status": "uploaded", "$text": {"$search": query}}
        if language:
            filt["language"] = language

        return list(self.col.find(
            filt,
            {"tg_file_id": 1, "title": 1, "artist": 1, "duration": 1,
             "language": 1, "file_size": 1, "_id": 0},
            sort=[("view_count", -1)]
        ).limit(limit))

    # ─── STATS ───────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get pipeline progress statistics"""
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        result   = {doc["_id"]: doc["count"] for doc in self.col.aggregate(pipeline)}
        total    = self.col.count_documents({})
        uploaded = result.get("uploaded", 0)

        return {
            "total":       total,
            "uploaded":    uploaded,
            "pending":     result.get("pending", 0),
            "downloading": result.get("downloading", 0),
            "failed":      result.get("failed", 0),
            "progress_pct": round((uploaded / max(total, 1)) * 100, 2),
        }

    def close(self):
        if self.client:
            self.client.close()
