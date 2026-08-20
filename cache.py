"""
🎵 Groovia Bot — MongoDB Cache Layer (Fault-Tolerant)
- Connects to VPS MongoDB (SSH tunnel) OR MongoDB Atlas
- If MongoDB is unavailable, bot still works — just no caching
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_col = None          # motor collection
_available = False   # True once connected successfully


async def _init():
    """Lazy init — connect once, silently fail if unavailable."""
    global _col, _available
    if _col is not None:
        return

    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from config import MONGODB_URI, DB_NAME

        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        # Ping to verify connection
        await client.admin.command("ping")
        db   = client[DB_NAME]
        _col = db["songs"]
        try:
            await _col.create_index("yt_id", unique=True, name="yt_id_unique")
            await _col.create_index("tg_file_id")
        except Exception as e:
            logger.debug(f"Index creation skipped/failed: {e}")
        _available = True
        logger.info("✅ MongoDB connected for caching")
    except Exception as e:
        _available = False
        logger.warning(f"⚠️  MongoDB unavailable — running without cache: {e}")


async def get_cached(yt_id: str) -> dict | None:
    """Return cached doc if exists, else None. Never crashes."""
    await _init()
    if not _available or _col is None:
        return None
    try:
        doc = await _col.find_one(
            {"yt_id": yt_id, "tg_file_id": {"$exists": True, "$ne": None}},
            {"tg_file_id": 1, "title": 1, "artist": 1, "album": 1, "duration": 1}
        )
        if not doc:
            doc = await _col.find_one(
                {"yt_id": yt_id, "file_id": {"$exists": True, "$ne": None}},
                {"file_id": 1, "tg_file_id": 1, "title": 1, "artist": 1, "album": 1, "duration": 1}
            )
        return doc
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None


async def save_cache(yt_id: str, file_id: str, meta: dict):
    """Upsert cache entry. Never crashes."""
    await _init()
    if not _available or _col is None:
        return
    try:
        now = datetime.utcnow()
        await _col.update_one(
            {"yt_id": yt_id},
            {
                "$set": {
                    "tg_file_id": file_id,
                    "title":     meta.get("title", ""),
                    "artist":    meta.get("artist", ""),
                    "album":     meta.get("album", ""),
                    "duration":  meta.get("duration", 0),
                    "thumbnail": meta.get("thumbnail", ""),
                    "cached_at": now,
                },
                "$setOnInsert": {
                    "yt_id":      yt_id,
                    "status":     "uploaded",
                    "created_at": now,
                }
            },
            upsert=True
        )
        logger.info(f"💾 Cached [{yt_id}]")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


async def db_stats() -> dict:
    """Return stats dict. Never crashes."""
    await _init()
    if not _available or _col is None:
        return {"total": 0, "cached": 0, "status": "MongoDB not connected"}
    try:
        total  = await _col.count_documents({})
        cached = await _col.count_documents({"tg_file_id": {"$exists": True, "$ne": None}})
        cached += await _col.count_documents({"file_id": {"$exists": True, "$ne": None}})
        return {"total": total, "cached": cached, "status": "connected"}
    except Exception as e:
        return {"total": 0, "cached": 0, "status": str(e)}
