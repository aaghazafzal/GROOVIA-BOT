"""
🎵 Groovia Music Bot — Main Entry Point
"""
import logging
import asyncio
import os
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, InlineQueryHandler, filters,
)
from config import BOT_TOKEN, DOWNLOAD_DIR
from handlers.commands import cmd_start, cmd_help, cmd_stats
from handlers.search import handle_text_message
from handlers.callbacks import handle_callback
from handlers.inline import handle_inline_query

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def post_init(app: Application):
    from keep_alive import start_webserver
    await start_webserver()
    
    await app.bot.set_my_commands([
        BotCommand("start",  "🎵 Start Groovia"),
        BotCommand("help",   "❓ How to use"),
        BotCommand("stats",  "📊 Bot stats"),
    ])
    logger.info("🎵 Groovia Bot ready!")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(60)
        .write_timeout(120)
        .connect_timeout(30)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("stats",  cmd_stats))

    # Text messages → search
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Inline button callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Inline mode (@botname <query>)
    app.add_handler(InlineQueryHandler(handle_inline_query))

    app.post_init = post_init

    logger.info("🚀 Starting bot (polling)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
