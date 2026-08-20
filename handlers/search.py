"""
🎵 Groovia Bot — Text message handler (search)
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import re
from ytmusic_search import search_songs, format_duration, get_song_info
from config import RESULTS_PER_PAGE
from handlers.fsub import check_fsub

logger = logging.getLogger(__name__)

def _escape(text: str) -> str:
    """Escape MarkdownV2 special chars."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def _build_results_keyboard(songs: list, page: int) -> InlineKeyboardMarkup:
    """Build paginated inline keyboard of song buttons."""
    start = page * RESULTS_PER_PAGE
    end   = start + RESULTS_PER_PAGE
    page_songs = songs[start:end]

    rows = []
    for i, song in enumerate(page_songs):
        idx = start + i
        label = f"🎵 {song['title']} — {song['artist']}"
        if len(label) > 60:
            label = label[:57] + "…"
        rows.append([InlineKeyboardButton(label, callback_data=f"play:{idx}")])

    # Pagination row
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"page:{page-1}"))
    total_pages = max(1, (len(songs) - 1) // RESULTS_PER_PAGE + 1)
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if end < len(songs):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"page:{page+1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(rows)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_fsub(update, context):
        return

    query = update.message.text.strip()
    if len(query) < 2:
        await update.message.reply_text("❌ Too short — please type at least 2 characters.")
        return

    # Check if query is a YouTube link
    if "youtu" in query.lower():
        yt_regex = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
        m = re.search(yt_regex, query)
        if m:
            yt_id = m.group(1)
            status = await update.message.reply_text("🔗 YouTube link detected. Fetching details...")
            song = get_song_info(yt_id)
            if song:
                from handlers.callbacks import process_play_song
                await process_play_song(status, song, context, update.message.chat_id)
                return
            else:
                await status.edit_text("❌ Could not get details for this YouTube link.")
                return

    # Show searching…
    status = await update.message.reply_text(f"🔍 Searching for *{_escape(query)}*…", parse_mode=ParseMode.MARKDOWN_V2)

    songs = search_songs(query, limit=40)

    if not songs:
        await status.edit_text(
            f"❌ No results found for *{_escape(query)}*\\.\n\nTry different keywords\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    # Store results in user context
    context.user_data["songs"]   = songs
    context.user_data["query"]   = query

    kb = _build_results_keyboard(songs, page=0)
    await status.edit_text(
        f"🔍 *Results for:* {_escape(query)}\n\n"
        f"Found *{_escape(str(len(songs)))}* songs\\. Tap one to get it\\:",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb,
    )
