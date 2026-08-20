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

# yt-dlp binary path (use venv's copy)
_VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
if sys.platform == "win32":
    YTDLP_BIN = os.path.join(_VENV_DIR, "Scripts", "yt-dlp.exe")
    if not os.path.exists(YTDLP_BIN):
        YTDLP_BIN = os.path.join(_VENV_DIR, "Scripts", "yt-dlp")
else:
    YTDLP_BIN = os.path.join(_VENV_DIR, "bin", "yt-dlp")

if not os.path.exists(YTDLP_BIN):
    YTDLP_BIN = "yt-dlp"

async def _download_ytdlp(yt_id: str) -> str | None:
    """yt-dlp with cookies, runs in executor."""
    url = f"https://www.youtube.com/watch?v={yt_id}"
    out_tmpl = os.path.join(DOWNLOAD_DIR, f"{yt_id}.%(ext)s")
    out_path  = os.path.join(DOWNLOAD_DIR, f"{yt_id}.mp3")

    cmd = [
        YTDLP_BIN,
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
        # Format 18 is https-only (no bot check), m3u8 formats as fallback
        "-f", "18/93/92/91/bestaudio",
    ]

    if os.path.exists(COOKIES_FILE):
        cmd += ["--cookies", COOKIES_FILE]

    cmd.append(url)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        )
        if result.returncode == 0 and os.path.exists(out_path):
            logger.info(f"  ✅ yt-dlp done [{yt_id}]")
            return out_path
        else:
            stderr = result.stderr.strip()[-300:] if result.stderr else "(no error)"
            logger.warning(f"  yt-dlp failed [{yt_id}]: {stderr}")
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
