"""
Proper test: ytmusicapi se SAHI video ID dhundo, phir download + upload
Songs: Kesariya, Srivalli, Faded, Tum Hi Ho, Senorita, Shape of You,
       Blinding Lights, Tera Yaar Hoon Main, Apna Bana Le, Butter (BTS)
"""
import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'mass_indexer')

import logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors
    format='%(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from ytmusicapi import YTMusic
from db import Database
from downloader import download_song, delete_song
from uploader import upload_song

# Songs to test — we'll search for each one via ytmusicapi
TEST_SONGS = [
    {"search": "Kesariya Arijit Singh Brahmastra", "expected_lang": "Hindi"},
    {"search": "Srivalli Sid Sriram Pushpa",       "expected_lang": "Telugu"},
    {"search": "Faded Alan Walker",                 "expected_lang": "English"},
    {"search": "Tum Hi Ho Arijit Singh",            "expected_lang": "Hindi"},
    {"search": "Senorita Shawn Mendes Camila",      "expected_lang": "English"},
    {"search": "Shape of You Ed Sheeran",           "expected_lang": "English"},
    {"search": "Blinding Lights The Weeknd",        "expected_lang": "English"},
    {"search": "Tera Yaar Hoon Main Arijit Singh",  "expected_lang": "Hindi"},
    {"search": "Apna Bana Le Arijit Bhediya",       "expected_lang": "Hindi"},
    {"search": "Butter BTS",                        "expected_lang": "English"},
]


def search_song(ytm: YTMusic, query: str) -> dict:
    """Search ytmusicapi and return top result with correct yt_id"""
    results = ytm.search(query, filter='songs', limit=3)
    if not results:
        return None

    top = results[0]
    yt_id = top.get('videoId')
    if not yt_id:
        return None

    title = (top.get('title') or '').strip()
    artists = top.get('artists') or []
    artist = artists[0].get('name', '').strip() if artists else 'Unknown'
    duration_str = top.get('duration', '0:00')

    # Parse duration
    try:
        parts = [int(x) for x in str(duration_str).split(':')]
        duration = parts[0] * 60 + parts[1] if len(parts) == 2 else 0
    except Exception:
        duration = 0

    return {
        'yt_id':    yt_id,
        'title':    title,
        'artist':   artist,
        'duration': duration,
    }


def main():
    print("\n" + "=" * 60)
    print("  GROOVIA PROPER PIPELINE TEST - 10 Songs")
    print("  (ytmusicapi se sahi ID, phir download + upload)")
    print("=" * 60 + "\n")

    ytm = YTMusic()
    db  = Database()

    results_summary = []

    for i, song_req in enumerate(TEST_SONGS, 1):
        query        = song_req['search']
        expected_lang = song_req['expected_lang']

        print(f"\n[{i}/10] Searching: '{query}'")

        # Step 1: Get correct yt_id from ytmusicapi
        song = search_song(ytm, query)
        if not song:
            print(f"  SEARCH FAILED - no result")
            results_summary.append({'query': query, 'status': 'search_failed'})
            continue

        yt_id  = song['yt_id']
        title  = song['title']
        artist = song['artist']
        print(f"  Found:  '{title}' by {artist}")
        print(f"  YT ID:  {yt_id}")
        print(f"  Expected language: {expected_lang}")

        # Step 2: Skip if already uploaded
        if db.is_processed(yt_id):
            print(f"  Already in DB - skipping")
            results_summary.append({'query': query, 'title': title, 'artist': artist,
                                     'status': 'skipped (already uploaded)'})
            continue

        db.add_to_queue(yt_id, {**song, 'language': expected_lang.lower(), 'priority': 1})
        db.mark_downloading(yt_id)

        # Step 3: Download
        print(f"  Downloading 128kbps MP3...")
        file_path, dl_info = download_song(yt_id)

        if not file_path:
            print(f"  DOWNLOAD FAILED!")
            db.mark_failed(yt_id, "Download failed")
            results_summary.append({'query': query, 'title': title, 'status': 'download_failed'})
            continue

        size_mb = os.path.getsize(file_path) / 1024 / 1024
        print(f"  Downloaded: {size_mb:.2f} MB")

        # Step 4: Upload to Telegram
        print(f"  Uploading to Telegram channel...")
        tg_file_id, tg_msg_id = upload_song(
            file_path=file_path,
            title=title,
            artist=artist,
            duration=song['duration'],
            yt_id=yt_id,
        )

        if not tg_file_id:
            print(f"  UPLOAD FAILED!")
            db.mark_failed(yt_id, "Upload failed")
            delete_song(file_path)
            results_summary.append({'query': query, 'title': title, 'status': 'upload_failed'})
            continue

        # Step 5: Save to DB and cleanup
        db.mark_uploaded(yt_id, tg_file_id, tg_msg_id, int(size_mb * 1024 * 1024))
        delete_song(file_path)

        print(f"  SUCCESS! Message #{tg_msg_id} in channel")
        results_summary.append({
            'query':    query,
            'title':    title,
            'artist':   artist,
            'size_mb':  round(size_mb, 2),
            'msg_id':   tg_msg_id,
            'status':   'uploaded'
        })

    # Final summary
    print("\n" + "=" * 60)
    print("  FINAL RESULTS")
    print("=" * 60)
    uploaded = [r for r in results_summary if r.get('status') == 'uploaded']
    failed   = [r for r in results_summary if 'failed' in r.get('status', '')]

    print(f"\n  Uploaded: {len(uploaded)}/10")
    for r in uploaded:
        print(f"  OK  [{r.get('size_mb', 0):.1f}MB] {r['title']} - {r['artist']} (msg #{r['msg_id']})")

    if failed:
        print(f"\n  Failed: {len(failed)}")
        for r in failed:
            print(f"  FAIL  {r.get('title', r['query'])} - {r['status']}")

    print(f"\n  Check 'song database' channel for {len(uploaded)} new songs!")
    print("  Verify: sahi song play ho raha hai ki nahi?\n")

    stats = db.get_stats()
    print(f"  MongoDB: {stats.get('uploaded', 0)} total songs stored")
    print("=" * 60 + "\n")
    db.close()


if __name__ == '__main__':
    main()
