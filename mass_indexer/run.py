"""
Groovia Mass Indexer - CLI Entry Point
Usage:
  python run.py run              - Start the indexer (full pipeline)
  python run.py run --workers 5  - Run with 5 workers
  python run.py stats            - Show database stats
  python run.py retry            - Reset failed songs and run
  python run.py test             - Test connections only
  python run.py reset-stuck      - Reset stuck 'downloading' songs
"""

import sys
import os
import argparse
import logging
import io
import sys
from datetime import datetime

# Force UTF-8 output on Windows to support unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ─── LOGGING SETUP ───────────────────────────────────────────────────────────
from config import LOG_FILE, LOG_LEVEL, NUM_WORKERS

logging.basicConfig(
    level   = getattr(logging, LOG_LEVEL, logging.INFO),
    format  = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    handlers = [
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)

# Suppress noisy third-party loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('yt_dlp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ─── COMMANDS ────────────────────────────────────────────────────────────────

def cmd_run(args):
    """Start the full pipeline"""
    from pipeline import run_pipeline
    workers = args.workers if hasattr(args, 'workers') and args.workers else NUM_WORKERS
    print(f"\n{'='*60}")
    print(f"  🎵 GROOVIA MASS INDEXER")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Workers: {workers}")
    print(f"{'='*60}\n")
    run_pipeline(num_workers=workers, resume=True)


def cmd_stats(args):
    """Show database statistics"""
    from db import Database
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    try:
        db    = Database()
        stats = db.get_stats()
        db.close()
    except Exception as e:
        console.print(f"[red]❌ DB Error: {e}[/red]")
        return

    table = Table(title="🎵 Groovia DB Statistics",
                  box=box.DOUBLE_EDGE,
                  title_style="bold cyan")
    table.add_column("Status",   style="cyan",   width=18)
    table.add_column("Count",    style="white",  width=12, justify="right")
    table.add_column("Details",  style="dim",    width=30)

    table.add_row("✅ Uploaded",    f"{stats.get('uploaded', 0):,}",    "In Telegram channel")
    table.add_row("📋 Pending",     f"{stats.get('pending', 0):,}",     "Waiting to process")
    table.add_row("⬇️  Downloading", f"{stats.get('downloading', 0):,}", "Currently in progress")
    table.add_row("❌ Failed",      f"{stats.get('failed', 0):,}",      "Failed (will retry)")
    table.add_row("─────────────", "──────────",                        "──────────────────────")
    table.add_row("📊 TOTAL",       f"{stats.get('total', 0):,}",       f"Progress: {stats.get('progress_pct', 0)}%")

    console.print(table)
    console.print(f"\n[dim]Target: 1,00,000 songs | "
                  f"Remaining: {max(0, 100_000 - stats.get('uploaded', 0)):,}[/dim]")


def cmd_retry(args):
    """Reset failed songs and restart"""
    from db import Database
    db = Database()
    count = db.reset_failed(max_retries=10)  # Allow more retries
    print(f"🔄 Reset {count} failed songs → pending")
    db.close()
    # Now run
    cmd_run(args)


def cmd_test(args):
    """Test all connections without starting the pipeline"""
    from db import Database
    from uploader import test_bot_connection
    from rich.console import Console

    console = Console(force_terminal=True, highlight=False)

    print("\n=== Testing Groovia Connections ===")

    # Test Telegram
    print("\n[1] Telegram Bot...")
    tg_ok = test_bot_connection()
    print("    " + ("OK" if tg_ok else "FAILED"))

    # Test MongoDB
    print("\n[2] MongoDB Atlas...")
    try:
        db    = Database()
        stats = db.get_stats()
        db.close()
        print(f"    OK -- {stats.get('total', 0):,} songs in DB")
    except Exception as e:
        print(f"    FAILED: {e}")

    # Test ytmusicapi
    print("\n[3] ytmusicapi...")
    try:
        from ytmusicapi import YTMusic
        ytm = YTMusic()
        results = ytm.search("Arijit Singh", filter='songs', limit=1)
        print(f"    OK -- Test search returned {len(results)} result(s)")
        if results:
            print(f"    Sample: {results[0].get('title', '?')} by {results[0].get('artists', [{}])[0].get('name', '?')}")
    except Exception as e:
        print(f"    FAILED: {e}")

    # Test yt-dlp
    print("\n[4] yt-dlp...")
    try:
        import yt_dlp
        print(f"    OK -- yt-dlp version: {yt_dlp.version.__version__}")
    except Exception as e:
        print(f"    FAILED: {e}")

    # Test ffmpeg
    print("\n[5] ffmpeg...")
    import subprocess
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"    OK -- {version}")
        else:
            print("    FAILED -- ffmpeg not found! Run: choco install ffmpeg  (Windows)")
    except FileNotFoundError:
        print("    FAILED -- ffmpeg not installed. Download from: https://ffmpeg.org/download.html")

    print("\n=== Test Complete ===")


def cmd_reset_stuck(args):
    """Reset songs stuck in 'downloading' status"""
    from db import Database
    db = Database()
    db.reset_stuck()
    print("✅ Reset stuck songs → pending")
    db.close()


# ─── CLI SETUP ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🎵 Groovia Mass Music Indexer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  run            Start the indexer pipeline
  stats          Show database statistics  
  retry          Reset failed songs and run
  test           Test all connections
  reset-stuck    Reset stuck 'downloading' songs

Examples:
  python run.py run
  python run.py run --workers 5
  python run.py stats
  python run.py test
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # run command
    run_parser = subparsers.add_parser('run', help='Start the indexer')
    run_parser.add_argument('--workers', type=int, default=NUM_WORKERS,
                            help=f'Number of worker threads (default: {NUM_WORKERS})')

    # stats command
    subparsers.add_parser('stats', help='Show database statistics')

    # retry command
    retry_parser = subparsers.add_parser('retry', help='Reset failed songs and run')
    retry_parser.add_argument('--workers', type=int, default=NUM_WORKERS)

    # test command
    subparsers.add_parser('test', help='Test connections')

    # reset-stuck command
    subparsers.add_parser('reset-stuck', help='Reset stuck songs')

    args = parser.parse_args()

    if args.command == 'run':
        cmd_run(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'retry':
        cmd_retry(args)
    elif args.command == 'test':
        cmd_test(args)
    elif args.command == 'reset-stuck':
        cmd_reset_stuck(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
