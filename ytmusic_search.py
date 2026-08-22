"""
🎵 Groovia Bot — YouTube Music Search
Uses ytmusicapi (unofficial, no API key needed).
"""
import logging
from ytmusicapi import YTMusic

logger = logging.getLogger(__name__)

_ytm: YTMusic = None


def _get_ytm() -> YTMusic:
    global _ytm
    if _ytm is None:
        _ytm = YTMusic()
        logger.info("✅ YTMusic initialized")
    return _ytm


def search_songs(query: str, limit: int = 20) -> list[dict]:
    """
    Search YouTube Music and return cleaned song list.
    Each dict: {yt_id, title, artist, album, duration, thumbnail}
    """
    ytm = _get_ytm()
    try:
        results = ytm.search(query, filter="songs", limit=limit)
        songs = []
        for r in results:
            yt_id = r.get("videoId")
            if not yt_id:
                continue

            # Artists
            artists = r.get("artists", [])
            artist_str = ", ".join(a.get("name", "") for a in artists if a.get("name"))

            # Album
            album = r.get("album", {})
            album_name = album.get("name", "") if album else ""

            # Duration seconds
            dur = r.get("duration_seconds") or 0

            # Thumbnail — pick largest
            thumbs = r.get("thumbnails", [])
            thumbnail = thumbs[-1]["url"] if thumbs else ""

            songs.append({
                "yt_id":     yt_id,
                "title":     r.get("title", "Unknown"),
                "artist":    artist_str or "Unknown Artist",
                "album":     album_name,
                "duration":  dur,
                "thumbnail": thumbnail,
            })
        return songs
    except Exception as e:
        logger.error(f"YTMusic search error: {e}")
        return []


def get_song_info(yt_id: str) -> dict | None:
    """Fetch specific song info by yt_id with yt-dlp fallback."""
    ytm = _get_ytm()
    try:
        data = ytm.get_song(yt_id)
        if data and "videoDetails" in data:
            details = data["videoDetails"]
            title = details.get("title", "Unknown")
            artist = details.get("author", "Unknown Artist")
            dur = int(details.get("lengthSeconds", 0))
            
            thumbnail = ""
            thumbs = details.get("thumbnail", {}).get("thumbnails", [])
            if thumbs:
                thumbnail = thumbs[-1]["url"]
                
            return {
                "yt_id": yt_id,
                "title": title,
                "artist": artist,
                "album": "",
                "duration": dur,
                "thumbnail": thumbnail,
            }
    except Exception as e:
        logger.warning(f"YTMusic get_song_info error, falling back to yt-dlp: {e}")

    # Fallback to YouTube oEmbed API (Fastest, zero-auth required)
    import requests
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={yt_id}&format=json"
        res = requests.get(oembed_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "yt_id": yt_id,
                "title": data.get("title", "Unknown"),
                "artist": data.get("author_name", "Unknown Artist"),
                "album": "",
                "duration": 0, # oEmbed doesn't provide duration, default to 0
                "thumbnail": data.get("thumbnail_url", ""),
            }
    except Exception as e:
        logger.error(f"oEmbed fallback exception: {e}")

    # Final Fallback to yt-dlp (without cookies to bypass residential cookie blocks on datacenters)
    import sys
    import subprocess
    import json
    
    YTDLP_BIN = [sys.executable, "-m", "yt_dlp"]
    cmd = YTDLP_BIN + [
        "--dump-json", 
        "--no-warnings", 
        "--extractor-args", "youtube:player_client=android",
        f"https://youtu.be/{yt_id}"
    ]
        
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            return {
                "yt_id": yt_id,
                "title": data.get("title", "Unknown"),
                "artist": data.get("uploader", "Unknown Artist"),
                "album": "",
                "duration": data.get("duration", 0),
                "thumbnail": data.get("thumbnail", ""),
            }
        else:
            logger.error(f"yt-dlp final fallback failed: {res.stderr[-200:]}")
    except Exception as e:
        logger.error(f"yt-dlp final fallback exception: {e}")

    return None

def format_duration(seconds: int) -> str:
    if not seconds:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
