"""
🎵 Groovia Mass Indexer — Downloader v2.0
PRIMARY:  Piped API (bypasses YouTube datacenter IP blocks, zero auth)
FALLBACK: yt-dlp with mweb client (for non-blocked IPs / future use)

Why Piped?
  - DigitalOcean IPs are blocked by YouTube ("Sign in to confirm bot")
  - Piped is a YouTube proxy with residential IPs — not blocked
  - Multiple public instances for redundancy
  - No authentication or cookies needed
"""

import os
import logging
import time
import random
import subprocess
import requests
from typing import Optional, Tuple

import yt_dlp
from config import DOWNLOAD_QUALITY, TEMP_DIR, MAX_RETRIES, DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX

logger = logging.getLogger(__name__)

os.makedirs(TEMP_DIR, exist_ok=True)

# ── Piped API Instances (public, free, no auth) ───────────────────────────────
PIPED_INSTANCES = [
    'https://pipedapi.kavin.rocks',
    'https://api.piped.yt',
    'https://pipedapi.moomoo.me',
    'https://piped-api.privacy.com.de',
    'https://watchapi.whatever.social',
]


# =============================================================================
# PRIMARY: Piped API Downloader
# =============================================================================

def _download_via_piped(yt_id: str) -> Optional[str]:
    """
    Download audio via Piped API proxy.
    Piped fetches from YouTube using its own residential IPs,
    so datacenter bot-blocks are completely bypassed.
    """
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')

    for instance in PIPED_INSTANCES:
        try:
            # 1. Get stream info from Piped
            url = f"{instance}/streams/{yt_id}"
            resp = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Groovia/1.0)'
            })

            if resp.status_code != 200:
                logger.debug(f"  Piped {instance}: HTTP {resp.status_code}")
                continue

            data = resp.json()

            # 2. Extract best audio stream
            audio_streams = [
                s for s in data.get('audioStreams', [])
                if s.get('url') and (
                    'audio' in s.get('mimeType', '').lower() or
                    'opus' in s.get('mimeType', '').lower() or
                    'webm' in s.get('mimeType', '').lower()
                )
            ]

            if not audio_streams:
                logger.debug(f"  Piped {instance}: No audio streams")
                continue

            # Sort by bitrate (highest first)
            audio_streams.sort(key=lambda x: int(x.get('bitrate', 0)), reverse=True)
            best = audio_streams[0]
            stream_url = best['url']
            mime = best.get('mimeType', 'audio/webm')
            bitrate = best.get('bitrate', 0)

            logger.info(f"  Piped stream: {mime} @ {bitrate//1000}kbps from {instance}")

            # 3. Download + convert to MP3 via ffmpeg
            result = subprocess.run(
                [
                    'ffmpeg', '-y',
                    '-i', stream_url,
                    '-vn',
                    '-ar', '44100',
                    '-ac', '2',
                    '-b:a', f'{DOWNLOAD_QUALITY}k',
                    mp3_path
                ],
                capture_output=True,
                timeout=180,
                text=True
            )

            if result.returncode == 0 and os.path.exists(mp3_path):
                size = os.path.getsize(mp3_path)
                if size > 50_000:
                    logger.info(f"  ✅ Piped download OK: {size/1024/1024:.1f} MB")
                    return mp3_path
                else:
                    logger.warning(f"  Piped: file too small ({size} bytes)")
                    _cleanup(mp3_path)
                    continue
            else:
                err = result.stderr[-300:] if result.stderr else ''
                logger.warning(f"  ffmpeg failed (Piped {instance}): {err}")
                _cleanup(mp3_path)
                continue

        except requests.exceptions.Timeout:
            logger.debug(f"  Piped {instance}: timeout")
            continue
        except Exception as e:
            logger.debug(f"  Piped {instance}: {e}")
            continue

    return None


# =============================================================================
# FALLBACK: yt-dlp
# =============================================================================

def _get_ydl_opts(yt_id: str) -> dict:
    """yt-dlp options — fallback when Piped fails"""
    return {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': DOWNLOAD_QUALITY,
        }],
        'outtmpl': os.path.join(TEMP_DIR, f'{yt_id}.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'socket_timeout': 60,
        'retries': 1,
        'fragment_retries': 3,
        'geo_bypass': True,
        'geo_bypass_country': 'IN',
        'overwrites': False,
        'nopart': True,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Linux; Android 13; Pixel 7) '
                'AppleWebKit/537.36 Chrome/124.0.6367.82 Mobile Safari/537.36'
            ),
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'ios', 'web_music'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }


def _download_via_ytdlp(yt_id: str) -> Optional[str]:
    """Fallback: yt-dlp download"""
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')
    url = f"https://music.youtube.com/watch?v={yt_id}"
    try:
        with yt_dlp.YoutubeDL(_get_ydl_opts(yt_id)) as ydl:
            ydl.extract_info(url, download=True)
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
            return mp3_path
    except Exception as e:
        err = str(e).lower()
        if 'sign in' not in err and 'bot' not in err:
            logger.warning(f"  yt-dlp: {str(e)[:100]}")
    _cleanup(mp3_path)
    return None


# =============================================================================
# MAIN DOWNLOAD FUNCTION
# =============================================================================

def download_song(yt_id: str) -> Tuple[Optional[str], Optional[dict]]:
    """
    Download song by YouTube video ID.
    Tries Piped API first (bypasses datacenter blocks), then yt-dlp.

    Returns:
        (file_path, info_dict) on success
        (None, None) on failure
    """
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')

    # Already cached?
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
        logger.info(f"♻️  [{yt_id}] Using cached file")
        return mp3_path, {'title': 'Unknown', 'artist': 'Unknown', 'duration': 0}

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"⬇️  [{yt_id}] Download attempt {attempt}/{MAX_RETRIES}")

        # ── Attempt 1 & 2: Piped API ─────────────────────────────────────────
        result = _download_via_piped(yt_id)

        # ── Attempt 3: yt-dlp fallback ────────────────────────────────────────
        if not result and attempt == MAX_RETRIES:
            logger.info(f"  Trying yt-dlp fallback...")
            result = _download_via_ytdlp(yt_id)

        if result:
            size = os.path.getsize(result)
            logger.info(f"✅ [{yt_id}] Downloaded: {size/1024/1024:.1f} MB")
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))
            return result, {
                'title':      'Unknown',
                'artist':     'Unknown',
                'duration':   0,
                'view_count': 0,
            }

        if attempt < MAX_RETRIES:
            wait = 5 * attempt + random.uniform(0, 3)
            logger.info(f"⏳ [{yt_id}] Retrying in {wait:.0f}s...")
            time.sleep(wait)

    logger.error(f"❌ [{yt_id}] All {MAX_RETRIES} attempts failed (Piped + yt-dlp)")
    return None, None


def _cleanup(file_path: str):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def delete_song(file_path: str):
    _cleanup(file_path)
    logger.debug(f"🗑️  Deleted: {file_path}")
