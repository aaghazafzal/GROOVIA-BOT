"""
🎵 Groovia Music Bot — Config
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot ──────────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "8334511601:AAGpaDzTXbZrGKSlWWNBbg7q3Iq1-xfJ_yU")
ADMIN_IDS   = [int(x) for x in os.getenv("ADMIN_IDS", "7097905601").split(",") if x.strip().isdigit()]

# 🎶 Channel (existing Groovia channel with 1 lakh+ songs cached)
CHANNEL_ID  = os.getenv("CHANNEL_ID", "-1004422628064")

# 💾 MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://grooviabot1:aaghaz9431@groovia-bot1.9zgtyxp.mongodb.net/?appName=groovia-bot1")
DB_NAME     = os.getenv("DB_NAME", "groovia_db")

# ── Download ──────────────────────────────────────────────────────────────────
COOKIES_FILE   = os.path.join(os.path.dirname(__file__), "www.youtube.com_cookies.txt")
DOWNLOAD_DIR   = os.path.join(os.path.dirname(__file__), "tmp_downloads")
MAX_FILE_MB    = 48          # Telegram bot limit is 50 MB; keep some headroom
AUDIO_FORMAT   = "mp3"
AUDIO_QUALITY  = "128"       # kbps  (medium — fast + good enough)

# Piped API instances (public, no auth needed)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://piped-api.garudalinux.org",
    "https://api.piped.yt",
    "https://pipedapi.in",
]

# ── Misc ──────────────────────────────────────────────────────────────────────
PORT           = int(os.getenv("PORT", 8080))
RESULTS_PER_PAGE = 8
