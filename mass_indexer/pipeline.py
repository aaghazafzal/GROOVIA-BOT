"""
🎵 Groovia Mass Indexer — Main Pipeline
Producer-Consumer architecture:
  - 1 Producer thread: Discovers songs, adds to queue
  - N Worker threads: Download → Upload → Save → Repeat

Features:
  ✅ Threaded workers (configurable count)
  ✅ Resume support (crash-safe via MongoDB status)
  ✅ Auto-retry failed songs
  ✅ Real-time progress display
  ✅ Clean temp file management
  ✅ Graceful shutdown on Ctrl+C
"""

import os
import time
import logging
import threading
import queue
import signal
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import NUM_WORKERS, TARGET_SONGS, TEMP_DIR
from db import Database
from discovery import SongDiscovery
from downloader import download_song, delete_song
from uploader import upload_song, test_bot_connection

logger  = logging.getLogger(__name__)
console = Console()

# ─── GLOBAL SHUTDOWN FLAG ─────────────────────────────────────────────────────
_shutdown = threading.Event()


def _handle_shutdown(signum, frame):
    console.print("\n[yellow]⚠️  Shutdown signal received — finishing current songs...[/yellow]")
    _shutdown.set()


signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)


# ─── PIPELINE STATE ───────────────────────────────────────────────────────────

class PipelineState:
    """Thread-safe counters for progress tracking"""
    def __init__(self):
        self._lock          = threading.Lock()
        self.downloaded     = 0
        self.uploaded       = 0
        self.failed         = 0
        self.skipped        = 0
        self.start_time     = time.time()
        self.worker_status  = {}  # worker_id → current action

    def inc(self, field: str, worker_id: int = None, status: str = None):
        with self._lock:
            setattr(self, field, getattr(self, field) + 1)
            if worker_id is not None and status:
                self.worker_status[worker_id] = status

    def set_worker(self, worker_id: int, status: str):
        with self._lock:
            self.worker_status[worker_id] = status

    def rate_per_hour(self) -> float:
        elapsed = (time.time() - self.start_time) / 3600
        return self.uploaded / max(elapsed, 0.001)

    def eta(self, target: int) -> str:
        remaining = target - self.uploaded
        rph = self.rate_per_hour()
        if rph <= 0:
            return "Calculating..."
        hours_left = remaining / rph
        eta_dt = datetime.now() + timedelta(hours=hours_left)
        if hours_left < 24:
            return f"{hours_left:.1f}h"
        days = hours_left / 24
        return f"{days:.1f} days"


# ─── WORKER FUNCTION ──────────────────────────────────────────────────────────

def worker(worker_id: int, song_queue: queue.Queue,
           db: Database, state: PipelineState):
    """
    Worker thread: pulls songs from queue and processes them.
    Download → Upload → Save to MongoDB → Delete temp file
    """
    logger.info(f"🔧 Worker {worker_id} started")
    state.set_worker(worker_id, "🟢 Ready")

    while not _shutdown.is_set():
        try:
            # Get next song (block up to 30 seconds for new items)
            try:
                song = song_queue.get(timeout=30)
            except queue.Empty:
                if _shutdown.is_set():
                    break
                continue

            yt_id  = song['yt_id']
            title  = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown')

            # ── STEP 1: Final duplicate check ────────────────────────────────
            if db.is_processed(yt_id):
                state.inc('skipped')
                state.set_worker(worker_id, f"⏭️  Skip: {title[:25]}")
                song_queue.task_done()
                continue

            # ── STEP 2: Mark as downloading (lock in DB) ──────────────────────
            db.mark_downloading(yt_id)
            state.set_worker(worker_id, f"⬇️  DL: {title[:25]}")

            # ── STEP 3: Download ──────────────────────────────────────────────
            file_path, dl_info = download_song(yt_id)

            if file_path is None:
                db.mark_failed(yt_id, "Download failed after all retries")
                state.inc('failed')
                state.set_worker(worker_id, f"❌ Failed: {title[:25]}")
                song_queue.task_done()
                continue

            state.inc('downloaded')

            # Update metadata from actual download (more accurate)
            if dl_info:
                title  = dl_info.get('title', title) or title
                artist = dl_info.get('artist', artist) or artist
                song['duration']   = dl_info.get('duration', song.get('duration', 0))
                song['view_count'] = dl_info.get('view_count', song.get('view_count', 0))

            # ── STEP 4: Upload to Telegram ────────────────────────────────────
            state.set_worker(worker_id, f"📤 Upload: {title[:25]}")

            tg_file_id, tg_msg_id = upload_song(
                file_path    = file_path,
                title        = title,
                artist       = artist,
                duration     = song.get('duration', 0),
                yt_id        = yt_id,
            )

            if tg_file_id is None:
                db.mark_failed(yt_id, "Telegram upload failed after all retries")
                state.inc('failed')
                state.set_worker(worker_id, f"❌ Upload failed: {title[:25]}")
                delete_song(file_path)
                song_queue.task_done()
                continue

            # ── STEP 5: Save to MongoDB ───────────────────────────────────────
            file_size = os.path.getsize(file_path)
            db.mark_uploaded(
                yt_id       = yt_id,
                tg_file_id  = tg_file_id,
                tg_message_id = tg_msg_id,
                file_size   = file_size,
            )

            # ── STEP 6: Delete temp file ──────────────────────────────────────
            delete_song(file_path)

            state.inc('uploaded')
            state.set_worker(worker_id, f"✅ Done: {title[:25]}")
            logger.info(f"✅ Worker {worker_id} | {title} — {artist}")

            song_queue.task_done()

        except Exception as e:
            logger.error(f"❌ Worker {worker_id} unhandled exception: {e}", exc_info=True)
            state.set_worker(worker_id, f"💥 Error: {str(e)[:30]}")
            try:
                song_queue.task_done()
            except Exception:
                pass

    logger.info(f"🔧 Worker {worker_id} stopped")
    state.set_worker(worker_id, "🔴 Stopped")


# ─── PRODUCER FUNCTION ────────────────────────────────────────────────────────

def producer(song_queue: queue.Queue, db: Database, state: PipelineState):
    """
    Producer thread: discovers songs and adds them to the queue.
    First processes existing pending songs from DB, then discovers new ones.
    """
    logger.info("🔍 Producer started")
    seen_ids = set()

    # ── Phase A: Resume pending songs from DB ────────────────────────────────
    state.set_worker(-1, "📂 Loading pending from DB...")
    db.reset_stuck()  # Reset any songs stuck in 'downloading' from a crash

    pending = db.get_pending_batch(batch_size=10_000)
    logger.info(f"📂 Found {len(pending)} pending songs in DB to process first")
    for song in pending:
        if _shutdown.is_set():
            return
        seen_ids.add(song['yt_id'])
        song_queue.put(song, timeout=60)

    # ── Phase B: Discover new songs ───────────────────────────────────────────
    if _shutdown.is_set():
        return

    db_stats = db.get_stats()
    already_uploaded = db_stats.get('uploaded', 0)
    logger.info(f"🎯 Already uploaded: {already_uploaded}. Target: {TARGET_SONGS}")

    if already_uploaded >= TARGET_SONGS:
        logger.info(f"🎉 Target of {TARGET_SONGS:,} songs already reached!")
        _shutdown.set()
        return

    state.set_worker(-1, "🔍 Discovering new songs...")
    discovery = SongDiscovery()
    new_songs_queued = 0

    for song_meta in discovery.discover(seen_ids=seen_ids):
        if _shutdown.is_set():
            break

        yt_id = song_meta['yt_id']

        # Skip if already in DB
        if db.exists(yt_id):
            seen_ids.add(yt_id)
            continue

        # Add to DB as pending
        added = db.add_to_queue(yt_id, song_meta)
        if added:
            seen_ids.add(yt_id)
            # Add to processing queue (block if queue is full — back-pressure)
            try:
                song_queue.put(song_meta, timeout=60)
                new_songs_queued += 1

                if new_songs_queued % 1000 == 0:
                    logger.info(f"📥 Producer: Queued {new_songs_queued} new songs")
            except queue.Full:
                logger.warning("⚠️  Song queue full — producer slowing down")
                time.sleep(10)

        # Check if target reached
        current_stats = db.get_stats()
        if current_stats.get('uploaded', 0) >= TARGET_SONGS:
            logger.info(f"🎉 Target {TARGET_SONGS:,} reached!")
            _shutdown.set()
            break

    logger.info(f"✅ Producer done — queued {new_songs_queued} new songs for processing")


# ─── PROGRESS DISPLAY ─────────────────────────────────────────────────────────

def _build_progress_table(state: PipelineState, db_stats: dict) -> Panel:
    """Build a Rich table showing current progress"""
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", width=22)
    table.add_column("Value", style="white", width=20)

    table.add_row("🎵 Uploaded (Total)",   f"{db_stats.get('uploaded', 0):,}")
    table.add_row("⬇️  Downloaded (Session)", f"{state.downloaded:,}")
    table.add_row("📤 Uploaded (Session)",  f"{state.uploaded:,}")
    table.add_row("❌ Failed (Session)",    f"{state.failed:,}")
    table.add_row("⏭️  Skipped (Session)",   f"{state.skipped:,}")
    table.add_row("📋 Pending in DB",       f"{db_stats.get('pending', 0):,}")
    table.add_row("🚀 Speed",               f"{state.rate_per_hour():.0f} songs/hr")
    table.add_row("⏱️  ETA to 1 Lakh",       state.eta(TARGET_SONGS))
    table.add_row("─────────────────────",  "────────────────────")

    for wid, status in sorted(state.worker_status.items()):
        name = f"Producer" if wid == -1 else f"Worker {wid}"
        table.add_row(f"  {name}", status)

    runtime = timedelta(seconds=int(time.time() - state.start_time))
    table.add_row("⏳ Runtime", str(runtime))

    return Panel(
        table,
        title="[bold green]🎵 GROOVIA MASS INDEXER[/bold green]",
        subtitle=f"[dim]Target: {TARGET_SONGS:,} songs | Press Ctrl+C to stop safely[/dim]",
        border_style="green",
    )


# ─── MAIN ENTRY POINT ─────────────────────────────────────────────────────────

def run_pipeline(num_workers: int = NUM_WORKERS, resume: bool = True):
    """Start the mass indexer pipeline"""

    console.print("[bold green]🎵 GROOVIA MASS INDEXER STARTING...[/bold green]")

    # ── Pre-flight checks ────────────────────────────────────────────────────
    console.print("🔌 Testing Telegram connection...")
    if not test_bot_connection():
        console.print("[red]❌ Telegram connection failed! Check BOT_TOKEN and CHANNEL_ID.[/red]")
        return

    console.print("🗄️  Connecting to MongoDB...")
    try:
        db = Database()
    except Exception as e:
        console.print(f"[red]❌ MongoDB connection failed: {e}[/red]")
        return

    # Show current stats
    stats = db.get_stats()
    console.print(f"[cyan]📊 Current DB: {stats.get('uploaded', 0):,} uploaded | "
                  f"{stats.get('pending', 0):,} pending | "
                  f"{stats.get('failed', 0):,} failed[/cyan]")

    # Reset failed songs for retry
    if resume:
        retried = db.reset_failed()
        if retried:
            console.print(f"[yellow]🔄 Re-queued {retried} previously failed songs[/yellow]")

    # Ensure temp dir
    os.makedirs(TEMP_DIR, exist_ok=True)

    # ── Setup queue and state ─────────────────────────────────────────────────
    state      = PipelineState()
    song_queue = queue.Queue(maxsize=1000)  # Max 1000 songs buffered in memory

    # ── Start producer thread ─────────────────────────────────────────────────
    prod_thread = threading.Thread(
        target  = producer,
        args    = (song_queue, db, state),
        daemon  = True,
        name    = "Producer"
    )
    prod_thread.start()
    state.set_worker(-1, "🔍 Starting...")

    # ── Start worker threads ──────────────────────────────────────────────────
    console.print(f"[green]🚀 Starting {num_workers} worker threads...[/green]")
    workers = []
    with ThreadPoolExecutor(max_workers=num_workers,
                            thread_name_prefix="Worker") as executor:
        for i in range(1, num_workers + 1):
            state.set_worker(i, "🟡 Starting...")
            future = executor.submit(worker, i, song_queue, db, state)
            workers.append(future)

        # ── Progress display loop ─────────────────────────────────────────────
        with Live(console=console, refresh_per_second=0.5) as live:
            while not _shutdown.is_set():
                try:
                    db_stats = db.get_stats()
                    live.update(_build_progress_table(state, db_stats))

                    # Check if all songs processed and queue empty
                    if (not prod_thread.is_alive() and
                            song_queue.empty() and
                            db_stats.get('pending', 0) == 0):
                        console.print("\n[bold green]🎉 All songs processed![/bold green]")
                        _shutdown.set()
                        break

                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Display error: {e}")
                    time.sleep(5)

    # ── Shutdown ──────────────────────────────────────────────────────────────
    console.print("\n[yellow]⏹️  Shutting down...[/yellow]")
    _shutdown.set()

    final_stats = db.get_stats()
    console.print(f"\n[bold green]📊 FINAL STATS:[/bold green]")
    console.print(f"  ✅ Total uploaded: {final_stats.get('uploaded', 0):,}")
    console.print(f"  ❌ Total failed:   {final_stats.get('failed', 0):,}")
    console.print(f"  📋 Still pending:  {final_stats.get('pending', 0):,}")
    console.print(f"  ⚡ Session rate:   {state.rate_per_hour():.0f} songs/hr")
    console.print(f"  ⏳ Runtime:        {timedelta(seconds=int(time.time() - state.start_time))}")

    db.close()
    console.print("[bold green]✅ Pipeline stopped cleanly.[/bold green]")
