from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram.constants import ChatMemberStatus

FSUB_CHANNEL_ID = -1002657096509
FSUB_CHANNEL_URL = "https://t.me/Univora88"

async def is_user_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=FSUB_CHANNEL_ID, user_id=user_id)
        if member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.RESTRICTED
        ]:
            return True
        return False
    except BadRequest as e:
        if "not found" in str(e).lower() or "invalid" in str(e).lower():
            return False
        # If bot is not admin in the fsub channel or some other error, log it and fail-open
        print(f"FSub Error: {e}")
        return True
    except Exception as e:
        print(f"FSub Error: {e}")
        return True

async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if the user is a member, False otherwise. Replies with the force-join message if False."""
    user = update.effective_user
    if not user:
        return True
    
    is_member = await is_user_member(context, user.id)
    if is_member:
        return True
        
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=FSUB_CHANNEL_URL)],
        [InlineKeyboardButton("🔄 Refresh", callback_data="fsub_refresh")]
    ])
    
    fsub_text = (
        "<b>🔒 Access Denied!</b>\n\n"
        "To use this bot, you must join our main channel to get the latest updates and stay connected.\n\n"
        "Please join the channel below, then click <b>Refresh</b> to continue."
    )
    
    if update.callback_query:
        if update.callback_query.data != "fsub_refresh":
            try:
                await update.callback_query.answer("⚠️ You must join our channel first!", show_alert=True)
            except:
                pass
            try:
                await update.callback_query.message.reply_html(fsub_text, reply_markup=kb)
            except:
                pass
    elif update.message:
        await update.message.reply_html(fsub_text, reply_markup=kb)
        
    return False
