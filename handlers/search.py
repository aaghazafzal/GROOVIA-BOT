"""
🎵 Groovia Bot - Search Handlers
Handle all search queries
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.api_client import api
from services.database import db
from utils.keyboards import kb
from utils.formatters import escape_markdown
from config import SEARCH_MSGS

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle plain text messages - treat as search query
    """
    query = update.message.text.strip()
    user_id = update.effective_user.id
    
    if len(query) < 2:
        await update.message.reply_text(
            "❌ *Query too short\\!*\n\nPlease enter at least 2 characters\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # Show loading message
    loading_msg = random.choice(SEARCH_MSGS)
    status_message = await update.message.reply_text(
        escape_markdown(loading_msg),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    try:
        # Check for specific search mode (from menu selection)
        search_mode = context.user_data.get('search_mode')
        
        if search_mode and search_mode in ['songs', 'albums', 'artists', 'playlists']:
            logger.info(f"🔍 Specific Search ({search_mode}): User {user_id}, Query: {query}")
            await search_by_type(update, context, search_mode)
            
            # Clear mode after search (one-shot)
            context.user_data.pop('search_mode', None)
            
            # Clean up the loading message displayed above (since search_by_type sends its own)
            await status_message.delete()
            return

        # Perform global search
        logger.info(f"🔍 Search: User {user_id}, Query: {query}")
        results = await perform_global_search(user_id, query)
        
        if not results:
            await status_message.edit_text(
                f"❌ *No results found for:*\n`{escape_markdown(query)}`\n\nTry different keywords\\!",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.main_menu()
            )
            return
        
        # Display results
        await display_search_results(status_message, user_id, query, results)
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        await status_message.edit_text(
            "❌ *Search failed\\!*\n\nPlease try again later\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.main_menu()
        )


async def perform_global_search(user_id: int, query: str):
    """
    Perform global search and return best results
    
    Returns dict with songs, albums, artists, playlists
    """
    try:
        # Call API
        data = api.global_search(query)
        
        if not data:
            return None
        
        # Extract results
        songs = data.get('songs', {}).get('results', [])
        albums = data.get('albums', {}).get('results', [])
        artists = data.get('artists', {}).get('results', [])
        playlists = data.get('playlists', {}).get('results', [])
        
        # Store in database
        db.set_search_data(user_id, {
            'type': 'global',
            'query': query,
            'songs': songs,
            'albums': albums,
            'artists': artists,
            'playlists': playlists
        })
        
        return {
            'songs': songs,
            'albums': albums,
            'artists': artists,
            'playlists': playlists
        }
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return None


async def display_search_results(message, user_id: int, query: str, results: dict):
    """Display search results with tabs/categories"""
    
    songs = results.get('songs', [])
    albums = results.get('albums', [])
    artists = results.get('artists', [])
    playlists = results.get('playlists', [])
    
    # Count results
    song_count = len(songs)
    album_count = len(albums)
    artist_count = len(artists)
    playlist_count = len(playlists)
    
    # If we have songs, show them by default
    if song_count > 0:
        # Store songs as current results
        db.set_search_data(user_id, {
            'type': 'songs',
            'query': query,
            'results': songs,
            'total': song_count
        })
        
        result_text = f"""
🔍 *Search Results for:* `{escape_markdown(query)}`

📊 *Found:*
🎵 {song_count} Songs
💿 {album_count} Albums
🎤 {artist_count} Artists
📋 {playlist_count} Playlists

*Showing songs:*
"""
        
        await message.edit_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.song_list(songs, page=0, total=song_count)
        )
    else:
        # No songs, show summary
        summary = f"""
🔍 *Search Results for:* `{escape_markdown(query)}`

📊 *Found:*
💿 {album_count} Albums
🎤 {artist_count} Artists
📋 {playlist_count} Playlists

Use the menu to search specific categories\\.
"""
        
        await message.edit_text(
            summary,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb.search_type()
        )


async def search_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE, search_type: str):
    """
    Search for specific type (songs, albums, artists, playlists)
    
    Args:
        search_type: One of 'songs', 'albums', 'artists', 'playlists'
    """
    query = update.message.text.strip()
    user_id = update.effective_user.id
    
    if len(query) < 2:
        await update.message.reply_text(
            "❌ *Query too short\\!*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    # Loading message
    status_message = await update.message.reply_text(
        f"🔍 Searching for {search_type}\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    try:
        results = None
        
        if search_type == 'songs':
            results = api.search_songs(query, limit=50)
        elif search_type == 'albums':
            results = api.search_albums(query, limit=50)
        elif search_type == 'artists':
            results = api.search_artists(query, limit=50)
        elif search_type == 'playlists':
            results = api.search_playlists(query, limit=50)
        
        if not results:
            await status_message.edit_text(
                f"❌ *No {search_type} found for:*\n`{escape_markdown(query)}`",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.main_menu()
            )
            return
        
        # Store results
        db.set_search_data(user_id, {
            'type': search_type,
            'query': query,
            'results': results,
            'total': len(results)
        })
        
        # Display appropriate keyboard
        result_text = f"🔍 *{search_type.title()} for:* `{escape_markdown(query)}`\n\n📊 Found {len(results)} results"
        
        if search_type == 'songs':
            keyboard = kb.song_list(results, page=0, total=len(results))
        elif search_type == 'albums':
            keyboard = kb.album_list(results, page=0)
        elif search_type == 'artists':
            keyboard = kb.artist_list(results, page=0)
        elif search_type == 'playlists':
            keyboard = kb.playlist_list(results, page=0)
        else:
            keyboard = kb.main_menu()
        
        await status_message.edit_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard
        )
        
        logger.info(f"✅ Search {search_type}: User {user_id}, Query: {query}, Results: {len(results)}")
        
    except Exception as e:
        logger.error(f"Search error ({search_type}): {e}")
        await status_message.edit_text(
            f"❌ *Search failed\\!*\n\nTry again later\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
