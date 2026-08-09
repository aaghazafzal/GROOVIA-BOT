"""
🎵 Groovia Mass Indexer — yt-dlp Downloader
Downloads songs as 128kbps MP3 to a temp directory.
Handles retries, timeouts, and cleanup automatically.
"""

import os
import logging
import time
import random
from typing import Optional, Tuple

import yt_dlp
from config import DOWNLOAD_QUALITY, TEMP_DIR, MAX_RETRIES, DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX

logger = logging.getLogger(__name__)

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)


# ─── YT-DLP OPTIONS ──────────────────────────────────────────────────────────

def _get_ydl_opts(yt_id: str) -> dict:
    """Build yt-dlp options for a single song download"""
    return {
        # Audio quality: let yt-dlp pick best audio, ffmpeg converts to 128kbps mp3
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': DOWNLOAD_QUALITY,
        }],
        # Save to temp dir with yt_id as filename
        'outtmpl': os.path.join(TEMP_DIR, f'{yt_id}.%(ext)s'),

        # Silent operation
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,

        # Network settings
        'socket_timeout': 60,
        'retries': 2,
        'fragment_retries': 3,
        'file_access_retries': 3,

        # Anti-ban: random user agent + delays
        'http_headers': {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            ]),
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
        },

        # Geo bypass
        'geo_bypass': True,
        'geo_bypass_country': 'IN',

        # Don't re-download if file exists
        'overwrites': False,
        'nopart': True,  # Don't leave .part files on failure

        # Extractor args
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android'],
            }
        },
    }


# ─── MAIN DOWNLOAD FUNCTION ──────────────────────────────────────────────────

def download_song(yt_id: str) -> Tuple[Optional[str], Optional[dict]]:
    """
    Download a song by YouTube video ID.

    Returns:
        (file_path, info_dict) on success
        (None, None) on failure after all retries
    """
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')

    # Already downloaded? Skip re-download
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
        logger.info(f"♻️  [{yt_id}] Already downloaded, using cached file")
        return mp3_path, {"title": "Unknown", "uploader": "Unknown", "duration": 0}

    url = f"https://music.youtube.com/watch?v={yt_id}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"⬇️  [{yt_id}] Download attempt {attempt}/{MAX_RETRIES}")
            opts = _get_ydl_opts(yt_id)

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Verify file exists and is non-empty
            if not os.path.exists(mp3_path):
                raise FileNotFoundError(f"MP3 not found after download: {mp3_path}")

            size = os.path.getsize(mp3_path)
            if size < 50_000:  # Less than 50KB → probably corrupt
                raise ValueError(f"File too small ({size} bytes) — likely corrupt")

            logger.info(f"✅ [{yt_id}] Downloaded: {size/1024/1024:.1f} MB")

            # Random delay between downloads (anti-ban)
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

            return mp3_path, {
                'title':      info.get('title', 'Unknown'),
                'artist':     info.get('uploader', info.get('channel', 'Unknown')),
                'duration':   int(info.get('duration', 0) or 0),
                'view_count': int(info.get('view_count', 0) or 0),
            }

        except yt_dlp.utils.DownloadError as e:
            err = str(e).lower()
            # Permanent errors — don't retry
            if any(x in err for x in ['video unavailable', 'private video',
                                       'age-restricted', 'not available',
                                       'removed by', 'copyright']):
                logger.warning(f"⛔ [{yt_id}] Permanent error: {e}")
                _cleanup(mp3_path)
                return None, None

            logger.warning(f"⚠️  [{yt_id}] Download error (attempt {attempt}): {e}")
            _cleanup(mp3_path)
            if attempt < MAX_RETRIES:
                backoff = 10 * attempt + random.uniform(0, 5)
                logger.info(f"⏳ [{yt_id}] Waiting {backoff:.0f}s before retry...")
                time.sleep(backoff)

        except Exception as e:
            logger.warning(f"⚠️  [{yt_id}] Unexpected error (attempt {attempt}): {e}")
            _cleanup(mp3_path)
            if attempt < MAX_RETRIES:
                time.sleep(5 * attempt)

    logger.error(f"❌ [{yt_id}] All {MAX_RETRIES} attempts failed")
    return None, None


def _cleanup(file_path: str):
    """Remove a file if it exists"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def delete_song(file_path: str):
    """Delete temp file after successful upload"""
    _cleanup(file_path)
    logger.debug(f"🗑️  Deleted temp file: {file_path}")
