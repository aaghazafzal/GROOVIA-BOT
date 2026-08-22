"""
🎵 Groovia Bot — Downloader
"""

import os
import sys
import logging
import asyncio
import subprocess

from config import COOKIES_FILE, DOWNLOAD_DIR, MAX_FILE_MB

logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

import sys
YTDLP_BIN = [sys.executable, "-m", "yt_dlp"]

async def _download_ytdlp(yt_id: str) -> str | None:
    """yt-dlp with cookies, runs in executor."""
    url = f"https://www.youtube.com/watch?v={yt_id}"
    out_tmpl = os.path.join(DOWNLOAD_DIR, f"{yt_id}.%(ext)s")
    out_path  = os.path.join(DOWNLOAD_DIR, f"{yt_id}.mp3")

    cmd_base = YTDLP_BIN + [
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        f"--max-filesize={MAX_FILE_MB}m",
        "--socket-timeout", "30",
        "--retries", "3",
        "--output", out_tmpl,
        "--no-warnings",
        "--quiet",
        "--extractor-args", "youtube:player_client=android",
        "-f", "18/93/92/91/bestaudio",
    ]

    # Try 1: With cookies (if available)
    cmd1 = cmd_base.copy()
    if os.path.exists(COOKIES_FILE):
        cmd1 += ["--cookies", COOKIES_FILE]
    cmd1.append(url)

    loop = asyncio.get_event_loop()
    
    def run_cmd(c):
        return subprocess.run(c, capture_output=True, text=True, timeout=120)

    try:
        res1 = await loop.run_in_executor(None, lambda: run_cmd(cmd1))
        if res1.returncode == 0 and os.path.exists(out_path):
            logger.info(f"  ✅ yt-dlp done [{yt_id}] (Attempt 1)")
            return out_path
        
        logger.warning(f"  yt-dlp attempt 1 failed [{yt_id}]: {res1.stderr.strip()[-200:]}")
        
        # Try 2: Without cookies (sometimes datacenter IPs fail with residential cookies)
        if os.path.exists(COOKIES_FILE):
            logger.info(f"  🔄 Retrying without cookies for [{yt_id}]...")
            cmd2 = cmd_base.copy()
            cmd2.append(url)
            res2 = await loop.run_in_executor(None, lambda: run_cmd(cmd2))
            if res2.returncode == 0 and os.path.exists(out_path):
                logger.info(f"  ✅ yt-dlp done [{yt_id}] (Attempt 2)")
                return out_path
            logger.warning(f"  yt-dlp attempt 2 failed [{yt_id}]: {res2.stderr.strip()[-200:]}")

        return None
    except subprocess.TimeoutExpired:
        logger.error(f"  yt-dlp timeout [{yt_id}]")
        return None
    except Exception as e:
        logger.error(f"  yt-dlp error [{yt_id}]: {e}")
        return None

async def download_audio(yt_id: str, title: str = "", artist: str = "") -> str | None:
    """
    Download audio for given YouTube ID directly from YouTube using yt-dlp.
    Returns local .mp3 path or None.
    """
    out_path = os.path.join(DOWNLOAD_DIR, f"{yt_id}.mp3")
    cleanup(out_path)

    logger.info(f"⬇️  [{yt_id}] Downloading via YouTube (yt-dlp)…")
    return await _download_ytdlp(yt_id)

def cleanup(path: str):
    """Delete temp file silently."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
