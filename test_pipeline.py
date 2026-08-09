"""
Quick test: Download 2 songs and upload to Telegram channel.
Verifies the full pipeline works end-to-end.
"""
import sys
import os
import io
import logging

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add mass_indexer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mass_indexer'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from db import Database
from downloader import download_song, delete_song
from uploader import upload_song

# 2 popular songs to test with
TEST_SONGS = [
    {
        'yt_id':    'gdZLi9oWNZg',  # Kesariya - Arijit Singh
        'title':    'Kesariya',
        'artist':   'Arijit Singh',
        'duration': 270,
    },
    {
        'yt_id':    'tgbNymZ7vqY',  # Gangnam Style (universal test)
        'title':    'Gangnam Style',
        'artist':   'PSY',
        'duration': 252,
    },
]

def main():
    print("\n" + "="*50)
    print("  GROOVIA PIPELINE TEST — 2 Songs")
    print("="*50 + "\n")

    db = Database()

    for i, song in enumerate(TEST_SONGS, 1):
        yt_id  = song['yt_id']
        title  = song['title']
        artist = song['artist']

        print(f"\n[Song {i}/2] {title} by {artist}")
        print(f"  YouTube ID: {yt_id}")

        # Skip if already uploaded
        if db.is_processed(yt_id):
            print(f"  Already in DB -- skipping")
            continue

        # Add to DB
        db.add_to_queue(yt_id, song)
        db.mark_downloading(yt_id)

        # Download
        print(f"  Downloading...")
        file_path, dl_info = download_song(yt_id)

        if not file_path:
            print(f"  DOWNLOAD FAILED!")
            db.mark_failed(yt_id, "Download failed in test")
            continue

        size_mb = os.path.getsize(file_path) / 1024 / 1024
        print(f"  Downloaded: {size_mb:.2f} MB")

        # Upload
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
            db.mark_failed(yt_id, "Upload failed in test")
            delete_song(file_path)
            continue

        # Save to DB
        db.mark_uploaded(yt_id, tg_file_id, tg_msg_id, int(size_mb * 1024 * 1024))
        delete_song(file_path)

        print(f"  SUCCESS!")
        print(f"  file_id: {tg_file_id[:40]}...")
        print(f"  message_id: {tg_msg_id}")

    # Final stats
    stats = db.get_stats()
    print("\n" + "="*50)
    print(f"  RESULT: {stats.get('uploaded',0)} songs uploaded to channel!")
    print(f"  Check your 'song database' Telegram channel!")
    print("="*50 + "\n")
    db.close()

if __name__ == '__main__':
    main()
