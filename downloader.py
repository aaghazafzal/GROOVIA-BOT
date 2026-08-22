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
            logger.warning(f"  yt-dlp attempt 2 failed [{yt_id}]: {res2.stderr.strip()[-100:]}")

        # Try 3: iOS and TV clients (bypasses some strict datacenter blocks)
        logger.info(f"  🔄 Retrying with iOS/TV clients for [{yt_id}]...")
        cmd3 = YTDLP_BIN + [
            "--no-playlist", "--extract-audio", "--audio-format", "mp3", "--audio-quality", "5",
            f"--max-filesize={MAX_FILE_MB}m", "--socket-timeout", "30", "--retries", "3",
            "--output", out_tmpl, "--no-warnings", "--quiet",
            "--extractor-args", "youtube:player_client=ios,tv,web_embedded",
            "-f", "18/93/92/91/bestaudio", url
        ]
        res3 = await loop.run_in_executor(None, lambda: run_cmd(cmd3))
        if res3.returncode == 0 and os.path.exists(out_path):
            logger.info(f"  ✅ yt-dlp done [{yt_id}] (Attempt 3)")
            return out_path
        logger.warning(f"  yt-dlp attempt 3 failed [{yt_id}]: {res3.stderr.strip()[-100:]}")
        
        # Try 4: MWEB client
        logger.info(f"  🔄 Retrying with mweb client for [{yt_id}]...")
        cmd4 = YTDLP_BIN + [
            "--no-playlist", "--extract-audio", "--audio-format", "mp3", "--audio-quality", "5",
            f"--max-filesize={MAX_FILE_MB}m", "--socket-timeout", "30", "--retries", "3",
            "--output", out_tmpl, "--no-warnings", "--quiet",
            "--extractor-args", "youtube:player_client=mweb,default",
            "-f", "18/93/92/91/bestaudio", url
        ]
        res4 = await loop.run_in_executor(None, lambda: run_cmd(cmd4))
        if res4.returncode == 0 and os.path.exists(out_path):
            logger.info(f"  ✅ yt-dlp done [{yt_id}] (Attempt 4)")
            return out_path
        logger.warning(f"  yt-dlp attempt 4 failed [{yt_id}]: {res4.stderr.strip()[-100:]}")
        
        # Try 5 (Ultimate Failsafe): Silent Piped Stream + FFmpeg conversion
        logger.info(f"  🔥 Retrying with Silent Ultimate Bypass (Stream+FFmpeg) for [{yt_id}]...")
        try:
            import aiohttp
            from config import PIPED_INSTANCES
            
            stream_url = None
            async with aiohttp.ClientSession() as session:
                for inst in PIPED_INSTANCES:
                    try:
                        async with session.get(f"{inst}/streams/{yt_id}", timeout=10) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                streams = data.get("audioStreams", [])
                                if streams:
                                    streams.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
                                    stream_url = streams[0]["url"]
                                    break
                    except Exception:
                        continue
            
            if stream_url:
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-i", stream_url, 
                    "-vn", "-ar", "44100", "-ac", "2", "-b:a", "128k", "-f", "mp3", 
                    out_path
                ]
                res5 = await loop.run_in_executor(None, lambda: subprocess.run(ffmpeg_cmd, capture_output=True, timeout=120))
                if res5.returncode == 0 and os.path.exists(out_path):
                    logger.info(f"  ✅ Ultimate Bypass done [{yt_id}]")
                    return out_path
                else:
                    logger.warning(f"  Ultimate Bypass ffmpeg failed: {res5.stderr.decode(errors='ignore')[-100:]}")
        except Exception as e:
            logger.error(f"  Ultimate Bypass failed [{yt_id}]: {e}")

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
