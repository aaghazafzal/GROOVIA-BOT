"""
🎵 Groovia Bot — Inline Query Handler
Allows: @Groovia_bot <song name> in any chat
"""
import logging
import uuid
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes

from ytmusic_search import search_songs, format_duration
from handlers.fsub import is_user_member

logger = logging.getLogger(__name__)


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.inline_query.query.strip()
    
    # FSub check
    is_member = await is_user_member(context, update.inline_query.from_user.id)
    if not is_member:
        await update.inline_query.answer(
            [],
            switch_pm_text="🔒 Join channel to search!",
            switch_pm_parameter="fsub",
            cache_time=0,
        )
        return

    if len(query_text) < 2:
        await update.inline_query.answer(
            [],
            switch_pm_text="Type a song name to search…",
            switch_pm_parameter="inline_help",
            cache_time=0,
        )
        return

    songs = search_songs(query_text, limit=10)

    results = []
    for song in songs:
        dur = format_duration(song.get("duration", 0))
        description = f"{song['artist']}"
        if song.get("album"):
            description += f" • {song['album']}"
        if dur:
            description += f" • {dur}"

        text = (
            f"🎵 {song['title']}\n"
            f"👤 {song['artist']}\n\n"
            f"Open @Groovia_bot and search: {song['title']}"
        )

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"🎵 {song['title']}",
                description=description,
                thumbnail_url=song.get("thumbnail") or None,
                input_message_content=InputTextMessageContent(text),
            )
        )

    await update.inline_query.answer(results, cache_time=30)
