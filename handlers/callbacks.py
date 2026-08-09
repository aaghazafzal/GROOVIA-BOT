"""
🎵 Groovia Bot - Callback Query Handlers
Handle all button clicks
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.api_client import api
from services.database import db
from utils.keyboards import kb
from config import EMOJI
from utils.formatters import (
    escape_markdown, format_song_info, format_album_info,
    format_artist_info, format_playlist_info, get_image_url
)
from handlers.downloads import download_song, download_multiple_songs

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query handler - routes to specific handlers"""
    
    query = update.callback_query
    
    data = query.data
    user_id = update.effective_user.id
    
    logger.info(f"🔘 Callback received: User {user_id}, Data: '{data}'")
    
    # Answer callback immediately
    try:
        await query.answer()
        logger.info(f"✅ Callback answered: {data}")
    except Exception as e:
        logger.error(f"❌ Error answering callback: {e}")
    
    try:
        # Menu navigation
        if data == "menu":
            await show_main_menu(query)
        
        elif data.startswith("menu_"):
            await handle_menu_selection(query, data, context)
            
        elif data.startswith("search_"):
            await handle_search_type_selection(query, data, context)
        
        # Song actions
        elif data.startswith("song_"):
            await show_song_detail(query, data, user_id)
        
        elif data.startswith("dl_"):
            await handle_download_request(update, context, query, data, user_id)
        
        elif data.startswith("q_"):
            await handle_quality_selection(update, context, query, data, user_id)
        
        elif data.startswith("fav_"):
            await handle_add_favorite(query, data, user_id)
        
        elif data.startswith("unfav_"):
            await handle_remove_favorite(query, data, user_id)
        
        elif data.startswith("lyrics_"):
            await show_lyrics(query, data, user_id)
        
        elif data.startswith("similar_"):
            await show_similar_songs(query, data, user_id)
        
        elif data.startswith("share_"):
            await handle_share(query, data, user_id)
        
        # Album/Artist/Playlist actions
        elif data.startswith("album_"):
            await show_album_detail(query, data, user_id)
        
        elif data.startswith("artist_"):
            await show_artist_detail(query, data, user_id)
        
        elif data.startswith("playlist_"):
            await show_playlist_detail(query, data, user_id)
        
        # Pagination
        elif data.startswith("page_"):
            await handle_pagination(query, data, user_id)
        
        elif data.startswith("albumpage_"):
            await handle_album_pagination(query, data, user_id)
        
        elif data.startswith("artistpage_"):
            await handle_artist_pagination(query, data, user_id)
        
        elif data.startswith("playlistpage_"):
            await handle_playlist_pagination(query, data, user_id)
        
        elif data.startswith("back_"):
            await handle_back_navigation(query, data, user_id)
        
        # Bulk actions
        elif data == "download_all":
            await handle_download_all(update, context, query, user_id)
        
        elif data == "shuffle":
            await handle_shuffle(query, user_id)
        
        # Search type selection
        elif data.startswith("search_"):
            await handle_search_type_selection(query, data)
        
        # Settings
        elif data.startswith("setting_"):
            await handle_settings(query, data, user_id)
        
        # Close
        elif data == "close":
            await query.message.delete()
        
        # Info buttons (do nothing)
        elif data in ["page_info", "x"]:
            await query.answer("ℹ️ Page info", show_alert=False)
        
        else:
            await query.answer("⚠️ Unknown action!", show_alert=True)
            logger.warning(f"Unknown callback data: {data}")
    
    except Exception as e:
        logger.error(f"❌ Callback error: {e}")
        await query.answer("❌ Error occurred!", show_alert=True)


# ============= MENU HANDLERS =============

async def show_main_menu(query):
    """Show main menu"""
    menu_text = """
╔═══════════════════╗
   🎵 *Main Menu*
╚═══════════════════╝

Choose an option below:
"""
    
    await query.message.edit_text(
        menu_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.main_menu()
    )


async def handle_menu_selection(query, data, context=None):
    """Handle menu button clicks"""
    user_id = query.from_user.id
    
    # Extract action from data (menu_search -> search)
    action = data.replace("menu_", "")
    
    if action == "search":
        # Search Menu
        text = f"""
╔═══════════════════╗
   {EMOJI['search']} *Search Music*
╚═══════════════════╝

Choose what you want to search for:

• {EMOJI['song']} *Songs* \\- Search for specific songs
• {EMOJI['album']} *Albums* \\- Find full albums
• {EMOJI['artist']} *Artists* \\- Discover artist profiles
• {EMOJI['playlist']} *Playlists* \\- Browse playlists

Or just send me any song name\\!
━━━━━━━━━━━━━━━━━━━━━
"""
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.search_type()
        )
        
    elif action == "trending":
        await query.answer("🔥 Trending feature coming soon!", show_alert=True)
        
    elif action == "songs":
        await handle_search_type_selection(query, "search_songs")
        
    elif action == "albums":
        await handle_search_type_selection(query, "search_albums")
        
    elif action == "artists":
        await handle_search_type_selection(query, "search_artists")
        
    elif action == "playlists":
        await handle_search_type_selection(query, "search_playlists")
    
    elif action == "favorites":
        favorites = db.get_favorites(user_id)
        if not favorites:
            text = "💔 *No favorites yet\\!*\n\nSearch songs and tap 💖 to save them\\."
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.main_menu()
            )
        else:
            db.set_search_data(user_id, {
                'type': 'favorites',
                'results': favorites,
                'total': len(favorites)
            })
            
            text = f"💖 *Your Favorites*\n\n📊 {len(favorites)} songs saved"
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.song_list(favorites, page=0, total=len(favorites))
            )

    elif action == "history":
        history = db.get_history(user_id)
        if not history:
            text = "📜 *No history yet\\!*\n\nStart exploring music\\!"
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.main_menu()
            )
        else:
            db.set_search_data(user_id, {
                'type': 'history',
                'results': history,
                'total': len(history)
            })
            
            text = f"📜 *Your History*\n\n📊 {len(history)} songs"
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.song_list(history, page=0, total=len(history))
            )
            
    elif action == "settings":
        settings = db.get_all_settings(user_id)
        quality = settings.get('quality', '160kbps')
        
        text = f"""
⚙️ *Settings*

*Current Configuration:*
📶 Quality: `{escape_markdown(quality)}`
🌐 Language: `{escape_markdown(settings.get('language', 'Hindi'))}`

Tap below to change settings\\.
"""
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.settings(quality)
        )
        
    elif action == "help":
        text = """
❓ *Help & Support*

*How to use:*
1\\. Use /start to open menu
2\\. Search for any song
3\\. Download in 96kbps or higher
4\\. Create playlists & favorites

Need more help? Contact @UnivoraSupport
"""
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.main_menu()
        )


async def handle_search_type_selection(query, data, context):
    """
    Handle search type selection (songs, albums, etc.)
    Prompts user to enter query
    """
    search_type = data.split("_")[1]  # songs, albums, artists, playlists
    
    # Store search mode in user_data
    if context:
        context.user_data['search_mode'] = search_type
    
    emoji_map = {
        'songs': EMOJI['song'],
        'albums': EMOJI['album'],
        'artists': EMOJI['artist'],
        'playlists': EMOJI['playlist']
    }
    emo = emoji_map.get(search_type, "🔍")
    
    # NOTE: To actually restrict search to this type, we would need to store state.
    # Given the user just wants the UI "bot ek mssg send krega... type krne ke liye bolega",
    # we will send that message.
    
    label = search_type.title()[:-1] # Remove 's' -> Song, Album...
    if search_type == 'artists': label = "Artist" # Exception for Artist/Artists logic if needed
    if search_type == 'playlists': label = "Playlist"
    
    text = f"""
{emo} *Search {search_type.title()}*

Please type the name of the *{label}* you want to find\\.\\.\\.

_Example: "Aashiqui 2"_

\\(Send any text to start searching\\)
"""
    
    await query.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_search")]])
    )



# ============= SONG HANDLERS =============

async def show_song_detail(query, data, user_id):
    """Show detailed song information"""
    try:
        # Extract song index
        song_index = int(data.split("_")[1])
        
        # Get current search data
        search_data = db.get_search_data(user_id)
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ Search data expired. Please search again.", show_alert=True)
            return
        
        results = search_data['results']
        
        if song_index >= len(results):
            await query.answer("⚠️ Song not found!", show_alert=True)
            return
        
        song = results[song_index]
        
        # Check if favorite
        is_fav = db.is_favorite(user_id, song.get('id'))
        
        # Format song info
        song_info = format_song_info(song, include_album=True)
        
        # Get image (temporarily disabled for testing)
        # image_url = get_image_url(song, quality='500x500')
        
        # # Send with thumbnail if available
        # if image_url:
        #     try:
        #         await query.message.delete()
        #         await query.message.chat.send_photo(
        #             photo=image_url,
        #             caption=song_info,
        #             parse_mode=ParseMode.MARKDOWN_V2,
        #             reply_markup=kb.song_detail(song_index, is_fav, page=0)
        #         )
        #         return
        #     except:
        #         pass
        
        # Show as text message (for testing)
        await query.message.edit_text(
            song_info,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.song_detail(song_index, is_fav, page=0)
        )
    
    except Exception as e:
        logger.error(f"Error showing song detail: {e}")
        await query.answer("❌ Error loading song!", show_alert=True)


async def handle_download_request(update: Update, context: ContextTypes.DEFAULT_TYPE, query, data, user_id):
    """Handle download button click - directly start download with 96kbps"""
    try:
        song_index = int(data.split("_")[1])
        
        # Get song from database
        search_data = db.get_search_data(user_id)
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ Search data expired!", show_alert=True)
            return
        
        results = search_data['results']
        if song_index >= len(results):
            await query.answer("⚠️ Song not found!", show_alert=True)
            return
        
        song = results[song_index]
        
        # Directly start download with 96kbps (medium quality)
        await download_song(update, context, song, '96kbps')
    
    except Exception as e:
        logger.error(f"Error in download request: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_quality_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, query, data, user_id):
    """Handle quality selection and start download"""
    try:
        # Parse: q_160_5 -> quality=160kbps, song_index=5
        parts = data.split("_")
        quality = f"{parts[1]}kbps"
        song_index = int(parts[2])
        
        # Get song
        search_data = db.get_search_data(user_id)
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ Search data expired!", show_alert=True)
            return
        
        results = search_data['results']
        if song_index >= len(results):
            await query.answer("⚠️ Song not found!", show_alert=True)
            return
        
        song = results[song_index]
        
        # Start download with proper update and context
        await download_song(update, context, song, quality)
    
    except Exception as e:
        logger.error(f"Error in quality selection: {e}")
        await query.answer("❌ Download failed!", show_alert=True)


async def handle_add_favorite(query, data, user_id):
    """Add song to favorites"""
    try:
        song_index = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ Data expired!", show_alert=True)
            return
        
        song = search_data['results'][song_index]
        
        if db.add_to_favorites(user_id, song):
            await query.answer("💖 Added to favorites!", show_alert=False)
            # Update keyboard
            await query.message.edit_reply_markup(
                reply_markup=kb.song_detail(song_index, is_favorite=True, page=0)
            )
        else:
            await query.answer("ℹ️ Already in favorites!", show_alert=False)
    
    except Exception as e:
        logger.error(f"Favorite error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_remove_favorite(query, data, user_id):
    """Remove song from favorites"""
    try:
        song_index = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ Data expired!", show_alert=True)
            return
        
        song = search_data['results'][song_index]
        
        if db.remove_from_favorites(user_id, song.get('id')):
            await query.answer("💔 Removed from favorites!", show_alert=False)
            await query.message.edit_reply_markup(
                reply_markup=kb.song_detail(song_index, is_favorite=False, page=0)
            )
        else:
            await query.answer("⚠️ Not in favorites!", show_alert=False)
    
    except Exception as e:
        logger.error(f"Remove favorite error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def show_lyrics(query, data, user_id):
    """Show song lyrics"""
    await query.answer("🎼 Lyrics feature coming soon!", show_alert=True)


async def show_similar_songs(query, data, user_id):
    """Show similar songs"""
    await query.answer("🎵 Similar songs feature coming soon!", show_alert=True)


async def handle_share(query, data, user_id):
    """Share song link"""
    try:
        song_index = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ Data expired!", show_alert=True)
            return
        
        song = search_data['results'][song_index]
        url = song.get('url', '')
        
        if url:
            await query.answer(f"🔗 Link: {url}", show_alert=True)
        else:
            await query.answer("⚠️ No link available!", show_alert=True)
    
    except Exception as e:
        logger.error(f"Share error: {e}")
        await query.answer("❌ Error!", show_alert=True)


# ============= PAGINATION HANDLERS =============

async def handle_pagination(query, data, user_id):
    """Handle song list pagination"""
    try:
        page = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data:
            await query.answer("⚠️ Search expired!", show_alert=True)
            return
        
        results = search_data.get('results', [])
        total = search_data.get('total', len(results))
        
        await query.message.edit_reply_markup(
            reply_markup=kb.song_list(results, page=page, total=total)
        )
    
    except Exception as e:
        logger.error(f"Pagination error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_album_pagination(query, data, user_id):
    """Handle album list pagination"""
    try:
        page = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data:
            await query.answer("⚠️ Search expired!", show_alert=True)
            return
        
        results = search_data.get('results', [])
        
        await query.message.edit_reply_markup(
            reply_markup=kb.album_list(results, page=page)
        )
    
    except Exception as e:
        logger.error(f"Album pagination error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_artist_pagination(query, data, user_id):
    """Handle artist list pagination"""
    try:
        page = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data:
            await query.answer("⚠️ Search expired!", show_alert=True)
            return
        
        results = search_data.get('results', [])
        
        await query.message.edit_reply_markup(
            reply_markup=kb.artist_list(results, page=page)
        )
    
    except Exception as e:
        logger.error(f"Artist pagination error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_playlist_pagination(query, data, user_id):
    """Handle playlist list pagination"""
    try:
        page = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data:
            await query.answer("⚠️ Search expired!", show_alert=True)
            return
        
        results = search_data.get('results', [])
        
        await query.message.edit_reply_markup(
            reply_markup=kb.playlist_list(results, page=page)
        )
    
    except Exception as e:
        logger.error(f"Playlist pagination error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_back_navigation(query, data, user_id):
    """Go back to list from song detail"""
    try:
        page = int(data.split("_")[1])
        search_data = db.get_search_data(user_id)
        
        if not search_data:
            await query.answer("⚠️ Data expired!", show_alert=True)
            return
        
        results = search_data.get('results', [])
        total = search_data.get('total', len(results))
        
        text = f"🔍 *Search Results*\n\n📊 {total} results"
        
        await query.message.delete()
        await query.message.chat.send_message(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.song_list(results, page=page, total=total)
        )
    
    except Exception as e:
        logger.error(f"Back navigation error: {e}")
        await query.answer("❌ Error!", show_alert=True)


# ============= ALBUM/ARTIST/PLAYLIST HANDLERS =============

async def show_album_detail(query, data, user_id):
    """Show album details"""
    await query.answer("💿 Album details coming soon!", show_alert=True)


async def show_artist_detail(query, data, user_id):
    """Show artist details"""
    await query.answer("🎤 Artist details coming soon!", show_alert=True)


async def show_playlist_detail(query, data, user_id):
    """Show playlist details"""
    await query.answer("📋 Playlist details coming soon!", show_alert=True)


# ============= BULK ACTIONS =============

async def handle_download_all(update: Update, context: ContextTypes.DEFAULT_TYPE, query, user_id):
    """Download all songs in current list"""
    try:
        search_data = db.get_search_data(user_id)
        
        if not search_data or 'results' not in search_data:
            await query.answer("⚠️ No results to download!", show_alert=True)
            return
        
        results = search_data['results']
        quality = db.get_user_setting(user_id, 'quality', '160kbps')
        
        await download_multiple_songs(update, context, results, quality)
    
    except Exception as e:
        logger.error(f"Download all error: {e}")
        await query.answer("❌ Error!", show_alert=True)


async def handle_shuffle(query, user_id):
    """Shuffle current list"""
    await query.answer("🔀 Shuffle feature coming soon!", show_alert=True)





# ============= SETTINGS HANDLERS =============

async def handle_settings(query, data, user_id):
    """Handle settings changes"""
    action = data.replace("setting_", "")
    
    if action == "quality":
        text = """
📶 *Quality Settings*

Choose default download quality:

• *12kbps* \\- Preview \\(smallest, fastest\\)
• *48kbps* \\- Low quality
• *96kbps* \\- Medium quality
• *160kbps* \\- Good quality ⭐ \\(recommended\\)
• *320kbps* \\- Best quality \\(largest\\)

━━━━━━━━━━━━━━━━━━━━━
"""
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("12kbps", callback_data="setq_12")],
                [InlineKeyboardButton("48kbps", callback_data="setq_48")],
                [InlineKeyboardButton("96kbps", callback_data="setq_96")],
                [InlineKeyboardButton("160kbps ⭐", callback_data="setq_160")],
                [InlineKeyboardButton("320kbps 💎", callback_data="setq_320")],
                [InlineKeyboardButton("🔙 Back", callback_data="menu_settings")]
            ])
        )
    
    elif action == "language":
        await query.answer("🌐 Language settings coming soon!", show_alert=True)
    
    elif action == "notif":
        await query.answer("🔔 Notification settings coming soon!", show_alert=True)
    
    elif action == "clear_history":
        db.clear_history(user_id)
        await query.answer("✅ History cleared!", show_alert=True)
    
    elif action.startswith("q_"):
        # Handle quality set: setq_160 -> set to 160kbps
        quality = f"{action.split('_')[1]}kbps"
        db.set_user_setting(user_id, 'quality', quality)
        await query.answer(f"✅ Quality set to {quality}", show_alert=False)
        
        # Go back to settings
        settings = db.get_all_settings(user_id)
        text = f"""
⚙️ *Settings*

*Current Configuration:*
📶 Quality: `{escape_markdown(quality)}`
🌐 Language: `{escape_markdown(settings.get('language', 'Hindi'))}`

Tap below to change settings\\.
"""
        await query.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.settings(quality)
        )
    
    # Import for inline keyboard
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

