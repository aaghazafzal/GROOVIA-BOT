"""
🎵 Groovia Bot - Configuration
All settings and constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============= BOT SETTINGS =============
BOT_TOKEN = os.getenv("BOT_TOKEN", "8081495139:AAE6egoJ-19wHIlDjwBSw87djH4TSphhwuQ")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "7097905601").split(",") if x.strip().isdigit()]

# ============= API SETTINGS =============
# New Vercel API - Faster and more reliable
API_BASE_URL = "https://jiosavan-sigma.vercel.app"

# API Endpoints
API_ENDPOINTS = {
    'global_search': '/api/search',
    'song_search': '/api/search/songs',
    'album_search': '/api/search/albums',
    'artist_search': '/api/search/artists',
    'playlist_search': '/api/search/playlists',
    'song_details': '/api/songs',
    'album_details': '/api/albums',
    'artist_details': '/api/artists',
    'playlist_details': '/api/playlists',
    'lyrics': '/api/songs/{id}/lyrics',
}

# ============= APP SETTINGS =============
PORT = int(os.getenv("PORT", 8080))
SONGS_PER_PAGE = 10
MAX_RETRIES = 5
REQUEST_TIMEOUT = 300

# ============= QUALITY SETTINGS =============
QUALITY_OPTIONS = {
    '12kbps': {'name': '12kbps (Preview)', 'emoji': '🔉'},
    '48kbps': {'name': '48kbps (Low)', 'emoji': '🔊'},
    '96kbps': {'name': '96kbps (Medium)', 'emoji': '📶'},
    '160kbps': {'name': '160kbps (Good)', 'emoji': '🎵'},
    '320kbps': {'name': '320kbps (Best)', 'emoji': '💎'},
}

DEFAULT_QUALITY = '160kbps'

# ============= UI MESSAGES =============
LOADING_MSGS = [
    "⏳ Loading your music…",
    "🎵 Fetching the beats…",
    "🔄 Almost there…",
    "🎧 Preparing your track…",
    "✨ Magic happening…"
]

SEARCH_MSGS = [
    "🔍 Searching the universe…",
    "🎵 Finding your vibe…",
    "🔎 Hunting for tracks…"
]

LYRICS_MSGS = [
    "🎼 Detecting song from lyrics…",
    "🔍 Analyzing your lyrics…",
    "🎵 Finding the perfect match…"
]

# ============= EMOJIS =============
EMOJI = {
    'song': '🎵',
    'album': '💿',
    'artist': '🎤',
    'playlist': '📋',
    'favorite': '💖',
    'history': '📜',
    'download': '⬇️',
    'search': '🔍',
    'settings': '⚙️',
    'home': '🏠',
    'close': '❌',
    'prev': '◀️',
    'next': '▶️',
    'play': '▶️',
    'pause': '⏸️',
    'trending': '🔥',
    'new': '🆕',
}

# ============= DATABASE =============
# For now using in-memory storage
# Can be upgraded to SQLite/MongoDB later
USE_DATABASE = False
DATABASE_PATH = "groovia_bot.db"
