"""
🎵 Groovia Bot — /start, /help, /stats commands
"""
from datetime import datetime, timedelta
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from cache import db_stats
from handlers.fsub import check_fsub

logger = logging.getLogger(__name__)

HELP_TEXT = """
💡 <b>Help</b>

<b>Search:</b> Just type any song name.
<b>Example:</b> <code>Tere Bin</code> or <code>Arijit Singh best songs</code>

<b>Inline mode:</b> Type <code>@Groovia_bot &lt;song&gt;</code> in any chat.

<b>Tips:</b>
• Be specific → better results
• Include artist name for exact match
• Supports Hindi, Punjabi, English, Urdu songs

<i>Built with ❤️ — Powered by YouTube Music</i>
"""

def get_greeting():
    # Calculate IST time (UTC + 5:30)
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    hour = ist_time.hour
    if hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 20:
        return "Good Evening"
    else:
        return "Good Night"

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FSub check
    if not await check_fsub(update, context):
        return

    user = update.effective_user
    greeting = get_greeting()
    # Create HTML link for the user's name
    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    start_text = f"""
🌅 <b>{greeting}, {mention}!</b>

🎵 <b>Welcome to Groovia Music Bot!</b>

The fastest music bot — powered by YouTube Music.

<b>How to use:</b>
▸ Just type any song name, artist, or album
▸ Pick from the results
▸ Get the audio instantly!

If the song is already in our cache of <b>1 lakh+ songs</b> you'll get it in seconds.
Otherwise it will be downloaded fresh just for you.

<i>Start searching ↓</i>
"""
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔎 Search a Song", switch_inline_query_current_chat=""),
    ]])
    await update.message.reply_html(
        start_text,
        reply_markup=kb,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_fsub(update, context):
        return
    await update.message.reply_html(HELP_TEXT)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = await db_stats()
        text = (
            f"📊 *Groovia Stats*\n\n"
            f"🎵 Total in DB: `{stats['total']:,}`\n"
            f"⚡ Cached \\(file\\_id\\): `{stats['cached']:,}`\n\n"
            f"_Every cached song = instant delivery, no download needed\\!_"
        )
    except Exception as e:
        text = f"📊 Stats unavailable: {e}"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
