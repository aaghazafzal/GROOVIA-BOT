"""
🎵 Groovia Bot - Database Service
In-memory data storage (can be upgraded to SQLite/MongoDB)
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataStore:
    """In-memory data storage for bot"""
    
    def __init__(self):
        # User data
        self.user_searches: Dict[int, Dict] = {}  # user_id -> current search data
        self.user_favorites: Dict[int, List] = defaultdict(list)
        self.user_history: Dict[int, List] = defaultdict(list)
        self.user_settings: Dict[int, Dict] = defaultdict(lambda: {
            'quality': '160kbps',
            'language': 'hindi',
            'notifications': True
        })
        
        # Global stats
        self.global_downloads = 0
        self.global_searches = 0
        
        # User stats
        self.user_stats: Dict[int, Dict] = defaultdict(lambda: {
            'searches': 0,
            'downloads': 0,
            'first_seen': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        })
    
    # ============= SEARCH DATA =============
    
    def set_search_data(self, user_id: int, data: dict):
        """Store current search results for user"""
        self.user_searches[user_id] = data
        self.user_stats[user_id]['searches'] += 1
        self.user_stats[user_id]['last_active'] = datetime.now().isoformat()
        self.global_searches += 1
    
    def get_search_data(self, user_id: int) -> Optional[dict]:
        """Get user's current search data"""
        return self.user_searches.get(user_id)
    
    def clear_search_data(self, user_id: int):
        """Clear user's search data"""
        if user_id in self.user_searches:
            del self.user_searches[user_id]
    
    # ============= FAVORITES =============
    
    def add_to_favorites(self, user_id: int, song: dict) -> bool:
        """
        Add song to user's favorites
        
        Returns:
            True if added, False if already exists
        """
        song_id = song.get('id')
        
        # Check if already in favorites
        if any(s.get('id') == song_id for s in self.user_favorites[user_id]):
            return False
        
        self.user_favorites[user_id].append(song)
        logger.info(f"✅ Added to favorites: User {user_id}, Song {song_id}")
        return True
    
    def remove_from_favorites(self, user_id: int, song_id: str) -> bool:
        """
        Remove song from favorites
        
        Returns:
            True if removed, False if not found
        """
        original_len = len(self.user_favorites[user_id])
        self.user_favorites[user_id] = [
            s for s in self.user_favorites[user_id] 
            if s.get('id') != song_id
        ]
        
        removed = len(self.user_favorites[user_id]) < original_len
        if removed:
            logger.info(f"❌ Removed from favorites: User {user_id}, Song {song_id}")
        
        return removed
    
    def get_favorites(self, user_id: int) -> List[dict]:
        """Get user's favorite songs"""
        return self.user_favorites[user_id]
    
    def is_favorite(self, user_id: int, song_id: str) -> bool:
        """Check if song is in favorites"""
        return any(s.get('id') == song_id for s in self.user_favorites[user_id])
    
    def clear_favorites(self, user_id: int):
        """Clear all favorites"""
        self.user_favorites[user_id] = []
        logger.info(f"🗑️ Cleared favorites: User {user_id}")
    
    # ============= HISTORY =============
    
    def add_to_history(self, user_id: int, song: dict):
        """Add song to listening history"""
        song_id = song.get('id')
        
        # Remove if already in history
        self.user_history[user_id] = [
            s for s in self.user_history[user_id] 
            if s.get('id') != song_id
        ]
        
        # Add to beginning
        self.user_history[user_id].insert(0, song)
        
        # Keep only last 100 songs
        self.user_history[user_id] = self.user_history[user_id][:100]
        
        # Update stats
        self.user_stats[user_id]['last_active'] = datetime.now().isoformat()
    
    def get_history(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get user's listening history"""
        return self.user_history[user_id][:limit]
    
    def clear_history(self, user_id: int):
        """Clear user's history"""
        self.user_history[user_id] = []
        logger.info(f"🗑️ Cleared history: User {user_id}")
    
    # ============= SETTINGS =============
    
    def get_user_setting(self, user_id: int, key: str, default=None):
        """Get specific user setting"""
        return self.user_settings[user_id].get(key, default)
    
    def set_user_setting(self, user_id: int, key: str, value):
        """Set user setting"""
        self.user_settings[user_id][key] = value
        logger.info(f"⚙️ Setting updated: User {user_id}, {key}={value}")
    
    def get_all_settings(self, user_id: int) -> dict:
        """Get all user settings"""
        return self.user_settings[user_id]
    
    # ============= STATS =============
    
    def increment_downloads(self, user_id: int):
        """Increment download count"""
        self.user_stats[user_id]['downloads'] += 1
        self.global_downloads += 1
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        stats = self.user_stats[user_id].copy()
        stats['favorites_count'] = len(self.user_favorites[user_id])
        stats['history_count'] = len(self.user_history[user_id])
        return stats
    
    def get_global_stats(self) -> dict:
        """Get global statistics"""
        return {
            'total_users': len(self.user_stats),
            'total_downloads': self.global_downloads,
            'total_searches': self.global_searches,
            'total_favorites': sum(len(favs) for favs in self.user_favorites.values())
        }


# Global database instance
db = DataStore()
