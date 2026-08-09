"""
🎵 Groovia Mass Indexer — Configuration
All settings in one place
"""

# ─── TELEGRAM ────────────────────────────────────────────────────────────────
BOT_TOKEN   = "8334511601:AAGpaDzTXbZrGKSlWWNBbg7q3Iq1-xfJ_yU"
CHANNEL_ID  = -1004422628064   # Private channel where songs are uploaded

# ─── MONGODB ──────────────────────────────────────────────────────────────────
MONGODB_URI    = "mongodb+srv://grooviabot1:aaghaz9431@groovia-bot1.9zgtyxp.mongodb.net/?appName=groovia-bot1"
DB_NAME        = "groovia_db"
COLLECTION     = "songs"

# ─── PIPELINE SETTINGS ────────────────────────────────────────────────────────
NUM_WORKERS        = 5          # Concurrent workers on server (2vCPU = 5 safe)
MAX_RETRIES        = 3          # Max retry attempts per song
DOWNLOAD_QUALITY   = "128"      # kbps — ~4-5MB per song
TEMP_DIR           = "/tmp/groovia_dl" if __import__('os').name != 'nt' else "C:/temp/groovia_dl"

# ─── DELAY SETTINGS (Anti-ban) ────────────────────────────────────────────────
DOWNLOAD_DELAY_MIN  = 2.0   # Min seconds between downloads per worker
DOWNLOAD_DELAY_MAX  = 5.0   # Max seconds between downloads per worker
TELEGRAM_DELAY      = 4.0   # Seconds between Telegram uploads (rate limit safe)
DISCOVERY_DELAY     = 1.0   # Seconds between ytmusicapi calls

# ─── DISCOVERY TARGETS ────────────────────────────────────────────────────────
TARGET_SONGS        = 100_000   # Phase 1: 1 lakh songs
RESULTS_PER_QUERY   = 50        # Results to fetch per search query

# ─── LOGGING ──────────────────────────────────────────────────────────────────
LOG_FILE    = "groovia_indexer.log"
LOG_LEVEL   = "INFO"
