"""
🎵 Groovia Bot - Command Handlers
/start, /help, /menu, /settings etc.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.keyboards import kb
from utils.formatters import escape_markdown
from services.database import db

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command
    Displays professional welcome message with Univora branding
    """
    user = update.effective_user
    user_id = user.id
    first_name = escape_markdown(user.first_name)
    
    # Initialize user in database (non-blocking if DB is efficient)
    db.user_stats[user_id] 
    
    # Professional, User-Friendly Welcome Message
    # Note: Escaped characters for MarkdownV2: _ * [ ] ( ) ~ > # + - = | { } . !
    # Using wide characters to force message width
    welcome_text = f"""
╔══════════════════════════╗
       🎵 *Groovia Music Bot*    
╚══════════════════════════╝

*Hey {first_name}* 👋

*Welcome to the Ultimate Music Experience* 🎧
_Powered by Univora Platform_

Experience high\\-quality music instantly\\! ⚡️

🔥 *Want 10x More Features?*
Try our new Web App for:
✅ Smooth Lag\\-free Playback
✅ Visualizer & Equalizer
✅ 10x Faster Experience

[👉 Click to Open Groovia Web App](https://grooviamodern.vercel.app)

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎵 *Bot Features:*
• 🔍 *Smart Search* \\- Songs, Albums, Artists
• 📥 *Fast Download* \\- Multiple qualities
• 📜 *Lyrics* \\- Sing along

👤 *Owner:* [Rolex Sir](tg://user?id={user_id})
🏢 *Platform:* [Univora](https://univora.site)
━━━━━━━━━━━━━━━━━━━━━━━━━━

👇 *Start exploring below:*
"""
    
    # Send message with new keyboard
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.start_keyboard(),
        disable_web_page_preview=True 
    )
    
    logger.info(f"✅ /start: User {user_id}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 *Help Guide*

*🔍 Search:*
Send any song name to search instantly\\!
Example: `Tum Hi Ho`

*📋 Menu Options:*
• *Songs* \\- Search only songs
• *Albums* \\- Browse albums
• *Artists* \\- Find artists
• *Playlists* \\- Discover playlists
• *Favorites* \\- Your saved songs
• *History* \\- Recently played

*⬇️ Download:*
Tap any song to see options\\. Choose your preferred quality\\!

*💡 Quality Options:*
• 12kbps \\- Preview
• 48kbps \\- Low \\(fast\\)
• 96kbps \\- Medium
• 160kbps \\- Good ⭐ \\(recommended\\)
• 320kbps \\- Best \\(high quality\\)

*📝 Commands:*
/start \\- Start the bot
/menu \\- Open main menu
/help \\- Show this help
/settings \\- Bot settings

*❓ Need more help?*
Contact: @YourSupportBot

━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.main_menu()
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command"""
    menu_text = """
╔═══════════════════╗
   🎵 *Main Menu*
╚═══════════════════╝

Choose an option below:
"""
    
    await update.message.reply_text(
        menu_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.main_menu()
    )


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    user_id = update.effective_user.id
    settings = db.get_all_settings(user_id)
    quality = settings.get('quality', '160kbps')
    
    settings_text = f"""
⚙️ *Settings*

*Current Configuration:*
📶 Quality: `{escape_markdown(quality)}`
🌐 Language: `{escape_markdown(settings.get('language', 'hindi'))}`
🔔 Notifications: `{escape_markdown('On' if settings.get('notifications') else 'Off')}`

Tap a button below to change settings\\.

━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(
        settings_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.settings(quality)
    )


async def cmd_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /favorites command"""
    user_id = update.effective_user.id
    favorites = db.get_favorites(user_id)
    
    if not favorites:
        text = """
💔 *No favorites yet\\!*

Search for songs and tap 💖 to add them to your favorites\\.

*Quick tip:* Your favorites are saved and you can access them anytime\\!

━━━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.main_menu()
        )
        return
    
    # Store favorites in search data so we can display them
    db.set_search_data(user_id, {
        'type': 'favorites',
        'results': favorites,
        'total': len(favorites)
    })
    
    text = f"""
💖 *Your Favorites*

📊 {len(favorites)} songs saved

Choose a song to play or download:

━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.song_list(favorites, page=0, total=len(favorites))
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    user_id = update.effective_user.id
    history = db.get_history(user_id)
    
    if not history:
        text = """
📜 *No history yet\\!*

Start exploring music and your listening history will appear here\\.

*Quick tip:* History helps you rediscover songs you loved\\!

━━━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.main_menu()
        )
        return
    
    # Store history in search data
    db.set_search_data(user_id, {
        'type': 'history',
        'results': history,
        'total': len(history)
    })
    
    text = f"""
📜 *Your History*

📊 {len(history)} songs

Recently played songs:

━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.song_list(history, page=0, total=len(history))
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    user_stats = db.get_user_stats(user_id)
    global_stats = db.get_global_stats()
    
    stats_text = f"""
╔══════════════════════════╗
       📊 *Your Statistics*       
╚══════════════════════════╝

🔍 *Searches:* {user_stats['searches']}
⬇️ *Downloads:* {user_stats['downloads']}
💖 *Favorites:* {user_stats['favorites_count']}
📜 *History:* {user_stats['history_count']}

📅 *Member since:* {escape_markdown(user_stats['first_seen'][:10])}
⏰ *Last active:* {escape_markdown(user_stats['last_active'][:10])}

━━━━━━━━━━━━━━━━━━━━━
🌍 *Global Stats*
👥 Total Users: {global_stats['total_users']}
📥 Downloads: {global_stats['total_downloads']}
🔍 Searches: {global_stats['total_searches']}

━━━━━━━━━━━━━━━━━━━━━
"""
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.main_menu()
    )
