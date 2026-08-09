"""
🎵 Groovia Mass Indexer — Telegram Uploader
Uploads MP3 files to the Groovia Telegram channel.
Uses raw Telegram Bot API (requests) — simpler and thread-safe.
Returns file_id for storage in MongoDB.
"""

import os
import time
import logging
import random
from typing import Optional, Tuple

import requests

from config import BOT_TOKEN, CHANNEL_ID, TELEGRAM_DELAY, MAX_RETRIES

logger = logging.getLogger(__name__)

# Telegram Bot API base URL
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Thread-level rate limiter (simple time-based)
_last_upload_time = 0.0


def upload_song(
    file_path: str,
    title: str,
    artist: str,
    duration: int,
    yt_id: str,
) -> Tuple[Optional[str], Optional[int]]:
    """
    Upload an MP3 file to the Telegram channel.

    Args:
        file_path:  Local path to the MP3 file
        title:      Song title (shown in Telegram)
        artist:     Artist name
        duration:   Duration in seconds
        yt_id:      YouTube video ID (for reference in caption)

    Returns:
        (file_id, message_id) on success
        (None, None) on failure
    """
    global _last_upload_time

    if not os.path.exists(file_path):
        logger.error(f"❌ File not found for upload: {file_path}")
        return None, None

    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:  # 50 MB Telegram limit
        logger.warning(f"⚠️  File too large ({file_size/1024/1024:.1f} MB): {yt_id}")
        return None, None

    # Rate limiting — enforce gap between uploads
    _enforce_rate_limit()

    caption = (
        f"🎵 <b>{_escape_html(title)}</b>\n"
        f"👤 {_escape_html(artist)}\n"
        f"🆔 <code>{yt_id}</code>"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"📤 [{yt_id}] Uploading to Telegram (attempt {attempt})...")

            with open(file_path, 'rb') as audio_file:
                response = requests.post(
                    f"{API_BASE}/sendAudio",
                    data={
                        'chat_id':   CHANNEL_ID,
                        'title':     title[:64],         # Telegram limit
                        'performer': artist[:64],
                        'duration':  duration,
                        'caption':   caption,
                        'parse_mode': 'HTML',
                    },
                    files={
                        'audio': (f"{yt_id}.mp3", audio_file, 'audio/mpeg')
                    },
                    timeout=180  # 3 minutes for large files
                )

            _last_upload_time = time.time()

            if response.status_code == 200:
                data       = response.json()
                message    = data['result']
                audio_info = message['audio']
                file_id    = audio_info['file_id']
                message_id = message['message_id']

                logger.info(
                    f"✅ [{yt_id}] Uploaded: {file_size/1024/1024:.1f} MB | "
                    f"file_id: {file_id[:20]}..."
                )
                return file_id, message_id

            elif response.status_code == 429:
                # Rate limited by Telegram
                retry_after = int(response.json().get('parameters', {}).get('retry_after', 30))
                logger.warning(f"⏳ [{yt_id}] Telegram rate limit — waiting {retry_after}s")
                time.sleep(retry_after + random.uniform(1, 5))

            elif response.status_code in (400, 403):
                # Permanent error — bad file or bot not in channel
                logger.error(f"❌ [{yt_id}] Telegram permanent error: {response.text}")
                return None, None

            else:
                logger.warning(
                    f"⚠️  [{yt_id}] Telegram error {response.status_code} "
                    f"(attempt {attempt}): {response.text[:200]}"
                )

        except requests.exceptions.Timeout:
            logger.warning(f"⏰ [{yt_id}] Upload timeout (attempt {attempt})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"🔌 [{yt_id}] Connection error (attempt {attempt})")
        except Exception as e:
            logger.error(f"❌ [{yt_id}] Upload exception (attempt {attempt}): {e}")

        if attempt < MAX_RETRIES:
            backoff = 15 * attempt + random.uniform(0, 10)
            logger.info(f"⏳ [{yt_id}] Retrying in {backoff:.0f}s...")
            time.sleep(backoff)

    logger.error(f"❌ [{yt_id}] All upload attempts failed")
    return None, None


def _enforce_rate_limit():
    """Ensure minimum gap between uploads (thread-safe via GIL)"""
    global _last_upload_time
    elapsed = time.time() - _last_upload_time
    if elapsed < TELEGRAM_DELAY:
        wait = TELEGRAM_DELAY - elapsed + random.uniform(0.5, 1.5)
        time.sleep(wait)


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram"""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def test_bot_connection() -> bool:
    """Test if bot token is valid and can post to the channel"""
    try:
        r = requests.get(f"{API_BASE}/getMe", timeout=10)
        if r.status_code != 200:
            logger.error(f"❌ Bot token invalid: {r.text}")
            return False
        bot_name = r.json()['result']['username']
        logger.info(f"✅ Bot connected: @{bot_name}")

        # Test channel access
        r2 = requests.get(f"{API_BASE}/getChat",
                          params={"chat_id": CHANNEL_ID}, timeout=10)
        if r2.status_code != 200:
            logger.error(f"❌ Cannot access channel {CHANNEL_ID}: {r2.text}")
            return False
        chat_title = r2.json()['result'].get('title', 'Unknown')
        logger.info(f"✅ Channel access OK: {chat_title}")
        return True

    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False
