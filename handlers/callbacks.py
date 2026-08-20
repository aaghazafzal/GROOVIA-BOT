"""
🎵 Groovia Bot — Callback query handler
Handles button clicks: play:<idx>, page:<n>, noop
"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from cache import get_cached, save_cache
from downloader import download_audio, cleanup
from ytmusic_search import format_duration
from config import CHANNEL_ID, RESULTS_PER_PAGE
from handlers.fsub import check_fsub

logger = logging.getLogger(__name__)

def _escape(text: str) -> str:
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def _song_caption(song: dict) -> str:
    title   = _escape(song.get("title", "Unknown"))
    artist  = _escape(song.get("artist", "Unknown Artist"))
    album   = _escape(song.get("album", ""))
    dur     = _escape(format_duration(song.get("duration", 0)))
    yt_id   = song.get("yt_id", "")
    yt_link = f"https://youtu.be/{yt_id}"

    lines = [f"🎵 *{title}*", f"👤  {artist}"]
    if album:
        lines.append(f"💿 {album}")
    lines.append(f"⏱ {dur}")
    lines.append(f"\n[▶️ YouTube]({yt_link})  •  @Groovia\\_bot")
    return "\n".join(lines)

def _build_results_keyboard(songs: list, page: int) -> InlineKeyboardMarkup:
    start = page * RESULTS_PER_PAGE
    end   = start + RESULTS_PER_PAGE
    page_songs = songs[start:end]

    rows = []
    for i, song in enumerate(page_songs):
        idx   = start + i
        label = f"🎵 {song['title']} — {song['artist']}"
        if len(label) > 60:
            label = label[:57] + "..."
        rows.append([InlineKeyboardButton(label, callback_data=f"play:{idx}")])

    nav = []
    total_pages = max(1, (len(songs) - 1) // RESULTS_PER_PAGE + 1)
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if end < len(songs):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(rows)

STICKER_DL = "CAACAgIAAxkBAAERvzFqhx2vLqdIm-Di4Pz-xFlw4GZMBAAClw0AAoOQeUqKysE-Ow0_uT0E"
STICKER_UP = "CAACAgQAAxkBAAERoDRqaY03Btc6IPb6K0izcgy6u0hK-QACZAADjRtGJ_-6BsP_SXPxPQQ"

async def process_play_song(message, song: dict, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Core logic to download, upload and send the song with stickers."""
    yt_id = song["yt_id"]

    # Delete the triggering message
    try:
        await message.delete()
    except Exception:
        pass

    # 1. Check MongoDB cache
    cached = await get_cached(yt_id)
    file_id_from_cache = None
    if cached:
        file_id_from_cache = cached.get("tg_file_id") or cached.get("file_id")

    if file_id_from_cache:
        logger.info(f"⚡ Cache HIT [{yt_id}]")
        try:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=file_id_from_cache,
                caption=_song_caption(song),
                parse_mode=ParseMode.MARKDOWN_V2,
                title=song.get("title", ""),
                performer=song.get("artist", ""),
            )
            return
        except Exception as e:
            logger.warning(f"Cache forward failed: {e} — downloading fresh")

    # 2. Download fresh
    logger.info(f"⬇️  Cache MISS [{yt_id}] — downloading...")
    sticker_msg = None
    try:
        sticker_msg = await context.bot.send_sticker(chat_id, STICKER_DL)
    except Exception as e:
        logger.error(f"Failed to send DL sticker: {e}")

    file_path = await download_audio(yt_id, title=song.get("title",""), artist=song.get("artist",""))
    if not file_path:
        if sticker_msg:
            try:
                await sticker_msg.delete()
            except:
                pass
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ *Could not download this song\\.*\n\nPossible reasons:\n• YouTube is blocking the request\n• Song not available",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        except Exception:
            pass
        return

    # 3. Upload to channel, then forward to user
    if sticker_msg:
        try:
            await sticker_msg.delete()
        except:
            pass

    try:
        sticker_msg = await context.bot.send_sticker(chat_id, STICKER_UP)
    except Exception:
        sticker_msg = None

    caption = _song_caption(song)
    file_id = None

    try:
        with open(file_path, "rb") as audio_f:
            channel_msg = await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=audio_f,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN_V2,
                title=song.get("title", ""),
                performer=song.get("artist", ""),
                read_timeout=180,
                write_timeout=180,
            )
        file_id = channel_msg.audio.file_id
    except Exception as e:
        logger.error(f"Channel upload failed [{yt_id}]: {e}")

    try:
        # Send to user
        if file_id:
            await save_cache(yt_id, file_id, {
                "title":     song.get("title", ""),
                "artist":    song.get("artist", ""),
                "album":     song.get("album", ""),
                "duration":  song.get("duration", 0),
                "thumbnail": song.get("thumbnail", ""),
            })
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=file_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN_V2,
                title=song.get("title", ""),
                performer=song.get("artist", ""),
            )
        else:
            with open(file_path, "rb") as audio_f:
                sent = await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_f,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    title=song.get("title", ""),
                    performer=song.get("artist", ""),
                    read_timeout=180,
                    write_timeout=180,
                )
            await save_cache(yt_id, sent.audio.file_id, {
                "title":    song.get("title", ""),
                "artist":   song.get("artist", ""),
                "album":    song.get("album", ""),
                "duration": song.get("duration", 0),
                "thumbnail":song.get("thumbnail", ""),
            })

        if sticker_msg:
            try:
                await sticker_msg.delete()
            except:
                pass

        logger.info(f"✅ Sent [{yt_id}] to user {chat_id}")

    except Exception as e:
        logger.error(f"Send to user failed [{yt_id}]: {e}")
        if sticker_msg:
            try:
                await sticker_msg.delete()
            except:
                pass
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ *Failed to send song\\!*\n\n`{_escape(str(e)[:120])}`",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        except Exception:
            pass
    finally:
        cleanup(file_path)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "fsub_refresh":
        # Force a fresh check (pass query so check_fsub knows it's a callback)
        is_member = await check_fsub(update, context)
        if is_member:
            await query.answer("✅ Verified! You can now use the bot.", show_alert=True)
            await query.message.delete()
        return

    # Check FSub for other callbacks before answering
    if not await check_fsub(update, context):
        return

    await query.answer()

    if data == "noop":
        return

    if data.startswith("page:"):
        page  = int(data.split(":")[1])
        songs = context.user_data.get("songs", [])
        if not songs:
            await query.answer("❌ Search again please.", show_alert=True)
            return
        await query.message.edit_reply_markup(reply_markup=_build_results_keyboard(songs, page))
        return

    if data.startswith("play:"):
        idx   = int(data.split(":")[1])
        songs = context.user_data.get("songs", [])
        if not songs or idx >= len(songs):
            await query.answer("❌ Search again please.", show_alert=True)
            return

        song    = songs[idx]
        chat_id = query.message.chat_id
        
        await process_play_song(query.message, song, context, chat_id)
