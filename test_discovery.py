"""
Quick test: Discovery engine se 50 songs fetch karo and check karo
"""
import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'mass_indexer')

from discovery import SongDiscovery, ARTISTS, SEARCH_QUERIES

def main():
    print("\n=== Discovery Engine Test ===\n")
    
    # Stats about our DB
    total_artists = sum(len(v) for v in ARTISTS.values())
    print(f"Total artists in DB:    {total_artists}")
    print(f"Total search queries:   {len(SEARCH_QUERIES)}")
    print(f"Potential songs (est):  {total_artists * 30 + len(SEARCH_QUERIES) * 20:,}")
    print()

    # Test discovery - get first 50 songs
    discovery = SongDiscovery()
    songs = []
    lang_count = {}

    print("Fetching first 50 unique songs from Charts + Artists...")
    print("-" * 50)

    for song in discovery.discover():
        songs.append(song)
        lang = song.get('language', 'unknown')
        lang_count[lang] = lang_count.get(lang, 0) + 1
        priority = song.get('priority', 4)
        print(f"[P{priority}] [{lang[:4]}] {song['title'][:35]} — {song['artist'][:25]}")
        if len(songs) >= 50:
            break

    print("\n" + "=" * 50)
    print(f"Fetched: {len(songs)} unique songs")
    print("\nLanguage breakdown:")
    for lang, count in sorted(lang_count.items(), key=lambda x: -x[1]):
        bar = "#" * count
        print(f"  {lang:<12}: {count:>3} {bar}")
    print("=" * 50)

if __name__ == '__main__':
    main()
