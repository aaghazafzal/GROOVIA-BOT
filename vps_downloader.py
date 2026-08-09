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
# FALLBACK: yt-dlp with Proxies & Cookies
# =============================================================================

import concurrent.futures

PROXIES_CACHE = []

def get_free_proxies():
    global PROXIES_CACHE
    if not PROXIES_CACHE:
        try:
            logger.info("  [Proxy] Fetching fresh proxies from ProxyScrape...")
            r = requests.get('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=all', timeout=10)
            raw = [p for p in r.text.strip().split('\r\n') if p]
            logger.info(f"  [Proxy] Found {len(raw)} proxies. Testing them concurrently...")
            
            working = []
            def check(p):
                try:
                    r2 = requests.get('https://www.youtube.com', proxies={'http': f"http://{p}", 'https': f"http://{p}"}, timeout=4)
                    if r2.status_code == 200:
                        return p
                except:
                    pass
                return None
                
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                futures = [executor.submit(check, p) for p in raw[:100]]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res:
                        working.append(res)
                        if len(working) >= 3: # Keep 3 working ones to save time
                            break
                            
            # Cancel remaining futures if any
            executor.shutdown(wait=False, cancel_futures=True)
                            
            PROXIES_CACHE = working
            logger.info(f"  [Proxy] Cached {len(PROXIES_CACHE)} VERIFIED working proxies!")
        except Exception as e:
            logger.warning(f"  [Proxy Error] {e}")
            
    # Return a random working proxy
    if PROXIES_CACHE:
        return [random.choice(PROXIES_CACHE)]
    return []

def _get_ydl_opts(yt_id: str, proxy: str = None) -> dict:
    """yt-dlp options — fallback when Piped fails"""
    opts = {
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
        'retries': 2,
        'cookiefile': '/root/groovia/cookies.txt', # Use uploaded cookies
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb', 'ios', 'web_music'],
                'player_skip': ['webpage', 'configs'],
            }
        },
    }
    if proxy:
        opts['proxy'] = f"http://{proxy}"
    return opts


def _download_via_ytdlp(yt_id: str) -> Optional[str]:
    """Fallback: yt-dlp download with proxy rotation"""
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')
    url = f"https://www.youtube.com/watch?v={yt_id}"
    
    # 1. Try without proxy (using cookies)
    try:
        with yt_dlp.YoutubeDL(_get_ydl_opts(yt_id)) as ydl:
            ydl.extract_info(url, download=True)
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
            return mp3_path
    except Exception as e:
        logger.warning(f"  yt-dlp (no proxy) failed: {str(e)[:100]}")
        _cleanup(mp3_path)

    # 2. Try with Proxies
    proxies = get_free_proxies()
    if not proxies:
        return None
        
    random.shuffle(proxies)
    for i in range(min(5, len(proxies))):
        proxy = proxies[i]
        logger.info(f"  yt-dlp trying Proxy ({i+1}/5): {proxy}")
        try:
            with yt_dlp.YoutubeDL(_get_ydl_opts(yt_id, proxy)) as ydl:
                ydl.extract_info(url, download=True)
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
                logger.info(f"  ✅ yt-dlp success with proxy: {proxy}")
                return mp3_path
        except Exception as e:
            logger.debug(f"  yt-dlp proxy {proxy} failed: {str(e)[:100]}")
            _cleanup(mp3_path)
            
    return None


import base64
from pyDes import des, ECB, PAD_PKCS5

def decrypt_url(url):
    des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    enc_url = base64.b64decode(url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
    return dec_url.replace("_96.mp4", "_160.mp4")

def _download_via_jiosaavn(yt_id: str) -> Optional[str]:
    """Fallback: JioSaavn direct download using song title from MongoDB"""
    from db import Database
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')
    
    # Get title from DB
    db = Database()
    song = db.col.find_one({'yt_id': yt_id})
    db.close()
    
    if not song:
        logger.warning(f"  JioSaavn: Song {yt_id} not in DB")
        return None
        
    query = f"{song.get('title', '')} {song.get('artist', '')}".strip()
    if not query:
        return None
        
    logger.info(f"  JioSaavn searching for: {query}")
    try:
        import urllib.parse
        q = urllib.parse.quote(query)
        url = f"https://www.jiosaavn.com/api.php?_format=json&_marker=0&api_version=4&ctx=web6dot0&n=1&p=1&q={q}&__call=search.getResults"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        results = data.get('results', [])
        if not results:
            logger.info("  JioSaavn: No results found")
            return None
            
        song_id = results[0].get('id')
        detail_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids={song_id}"
        r2 = requests.get(detail_url, headers=headers, timeout=10)
        d2 = r2.json()
        
        if song_id in d2:
            enc_url = d2[song_id].get('encrypted_media_url')
            if not enc_url:
                enc_url = d2[song_id].get('more_info', {}).get('encrypted_media_url')
                
            if enc_url:
                dec_url = decrypt_url(enc_url)
                logger.info(f"  JioSaavn downloading direct URL...")
                # Download using requests
                r3 = requests.get(dec_url, timeout=60, stream=True)
                with open(mp3_path, 'wb') as f:
                    for chunk in r3.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
                    logger.info("  ✅ JioSaavn download success!")
                    return mp3_path, {
                        'title': results[0].get('title', song.get('title')),
                        'artist': results[0].get('subtitle', song.get('artist')),
                        'duration': 0,
                        'view_count': 0
                    }
    except Exception as e:
        logger.warning(f"  JioSaavn failed: {e}")
        
    _cleanup(mp3_path)
    return None, None

# =============================================================================
# MAIN DOWNLOAD FUNCTION
# =============================================================================

def download_song(yt_id: str) -> Tuple[Optional[str], Optional[dict]]:
    """
    Download song by YouTube video ID.
    Tries Piped API first, then yt-dlp, then JioSaavn fallback.
    """
    mp3_path = os.path.join(TEMP_DIR, f'{yt_id}.mp3')

    # Already cached?
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 50_000:
        logger.info(f"♻️  [{yt_id}] Using cached file")
        return mp3_path, {'title': None, 'artist': None, 'duration': 0}

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"⬇️  [{yt_id}] Download attempt {attempt}/{MAX_RETRIES}")

        # ── Attempt 1: JioSaavn ───────────────────────────────────────────────
        if attempt == 1:
            logger.info(f"  Trying JioSaavn first...")
            res_jio = _download_via_jiosaavn(yt_id)
            if res_jio and res_jio[0]:
                result, info_dict = res_jio
        
        # ── Attempt 2: Piped API ──────────────────────────────────────────────
        if not result and attempt == 2:
            logger.info(f"  Trying Piped API...")
            result = _download_via_piped(yt_id)
            if isinstance(result, tuple):
                result, info_dict = result
            elif result:
                info_dict = {'title': None, 'artist': None, 'duration': 0, 'view_count': 0}

        # ── Attempt 3: yt-dlp fallback ────────────────────────────────────────
        if not result and attempt == 3:
            logger.info(f"  Trying yt-dlp fallback...")
            result = _download_via_ytdlp(yt_id)
            if result:
                info_dict = {'title': None, 'artist': None, 'duration': 0, 'view_count': 0}

        if result:
            size = os.path.getsize(result)
            logger.info(f"✅ [{yt_id}] Downloaded: {size/1024/1024:.1f} MB")
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))
            return result, info_dict

        if attempt < MAX_RETRIES:
            wait = 5 * attempt + random.uniform(0, 3)
            logger.info(f"⏳ [{yt_id}] Retrying in {wait:.0f}s...")
            time.sleep(wait)

    logger.error(f"❌ [{yt_id}] All {MAX_RETRIES} attempts failed (Piped + JioSaavn + yt-dlp)")
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
