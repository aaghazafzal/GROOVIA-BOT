"""
🎵 Groovia Bot - Main Entry Point
Professional Music Bot with Advanced Features
"""

import logging
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN, PORT
from handlers.commands import (
    cmd_start, cmd_help, cmd_menu, cmd_settings,
    cmd_favorites, cmd_history, cmd_stats
)
from handlers.search import handle_text_message
from handlers.callbacks import handle_callback_query

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def setup_bot_commands(app: Application):
    """Set bot commands for menu"""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Main menu"),
        BotCommand("help", "Show help"),
        BotCommand("settings", "Bot settings"),
        BotCommand("favorites", "Your favorites"),
        BotCommand("history", "Listening history"),
        BotCommand("stats", "Your statistics"),
    ]
    
    await app.bot.set_my_commands(commands)
    logger.info("✅ Bot commands registered")


async def post_init(app: Application):
    """Post-initialization setup"""
    await setup_bot_commands(app)
    logger.info("🎵 Groovia Bot initialized successfully!")


def main():
    """Start the bot"""
    logger.info("🚀 Starting Groovia Bot...")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ============= COMMAND HANDLERS =============
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("favorites", cmd_favorites))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("stats", cmd_stats))
    
    # ============= MESSAGE HANDLERS =============
    # Text messages -> Search
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # ============= CALLBACK HANDLERS =============
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # ============= POST-INIT =============
    app.post_init = post_init
    
    # ============= RUN BOT =============
    logger.info("✅ All handlers registered")
    logger.info("🎵 Bot is now running! Press Ctrl+C to stop.")
    
    # Start polling
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
