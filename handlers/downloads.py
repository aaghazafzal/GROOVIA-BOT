"""
🎵 Groovia Bot - Download Handler
Handle song downloads
"""

import logging
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.api_client import api
from services.database import db
from utils.formatters import escape_markdown, format_song_info, get_image_url, get_artist_names
from utils.keyboards import kb

logger = logging.getLogger(__name__)


async def download_song(update: Update, context: ContextTypes.DEFAULT_TYPE, song: dict, quality: str = '160kbps'):
    """
    Download and send song to user
    
    Args:
        update: Telegram update
        context: Bot context
        song: Song dict from API
        quality: Quality to download (12kbps, 48kbps, 96kbps, 160kbps, 320kbps)
    """
    user_id = update.effective_user.id
    
    try:
        # Get the message to edit (either callback query message or original message)
        if update.callback_query:
            message = update.callback_query.message
        else:
            message = update.message
        
        # Show downloading status
        status_text = f"""
⬇️ *Downloading\\.\\.\\.*

🎵 {escape_markdown(song.get('name', 'Unknown'))}
👤 {escape_markdown(get_artist_names(song))}
📶 Quality: `{escape_markdown(quality)}`

⏳ Please wait\\.\\.\\.
"""
        
        if update.callback_query:
            await update.callback_query.answer("Downloading...")
            await message.edit_text(status_text, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            status_message = await message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN_V2)
            message = status_message
        
        # Get full song details (search results don't have download URLs)
        song_id = song.get('id')
        if not song_id:
            await message.edit_text(
                "❌ *Download failed\\!*\n\nSong ID not found\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.close_button()
            )
            return
        
        logger.info(f"📥 Fetching song details: {song_id}")
        full_song = api.get_song_details(song_id)
        
        if not full_song:
            await message.edit_text(
                "❌ *Download failed\\!*\n\nCouldn't fetch song details\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.close_button()
            )
            return
        
        # Get download URL from full song details
        download_url = api.get_download_url(full_song, quality)
        
        if not download_url:
            await message.edit_text(
                f"❌ *Download failed\\!*\n\nCouldn't get download link for {escape_markdown(quality)}\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.close_button()
            )
            return
        
        logger.info(f"📥 Downloading: {song.get('name')} ({quality}) for user {user_id}")
        
        # Download the file
        audio_data = api.download_song(download_url)
        
        if not audio_data:
            await message.edit_text(
                "❌ *Download failed\\!*\n\nPlease try again later\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=kb.close_button()
            )
            return
        
        # Prepare file info from full song details
        title = full_song.get('name', 'Unknown Song')
        artist = get_artist_names(full_song)
        filename = f"{title} - {artist}.m4a"
        
        # Clean filename (remove invalid characters)
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        filename = filename[:100]  # Limit length
        
        # Get thumbnail from full song
        thumbnail_url = get_image_url(full_song, quality='500x500')
        thumbnail_data = None
        
        if thumbnail_url:
            try:
                thumbnail_data = api.download_song(thumbnail_url)
            except:
                pass
        
        # Send the audio file
        await message.edit_text(
            "📤 *Sending\\.\\.\\.*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Create BytesIO object
        audio_file = BytesIO(audio_data)
        audio_file.name = filename
        
        # Simple caption (as requested)
        caption = f"🎵 {title}\n👤 {artist}\n\nDownloaded via @GrooviaBot"
        
        # Send audio with retry on timeout
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"📤 Sending audio (attempt {attempt + 1}/{max_retries})")
                
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    title=title,
                    performer=artist,
                    thumbnail=BytesIO(thumbnail_data) if thumbnail_data else None,
                    caption=caption,
                    read_timeout=120,  # 2 minutes for large files
                    write_timeout=120,
                    connect_timeout=30
                )
                
                logger.info(f"✅ Audio sent successfully!")
                break  # Success, exit retry loop
                
            except Exception as send_error:
                logger.error(f"❌ Send audio error (attempt {attempt + 1}): {send_error}")
                
                if attempt < max_retries - 1:
                    # Retry
                    logger.info("🔄 Retrying...")
                    audio_file.seek(0)  # Reset file pointer
                    continue
                else:
                    # Final attempt failed
                    raise send_error
        
        # Delete status message
        await message.delete()
        
        # Update statistics
        db.increment_downloads(user_id)
        db.add_to_history(user_id, song)
        
        logger.info(f"✅ Download complete: {title} for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        try:
            error_text = f"""
❌ *Download failed\\!*

Error: {escape_markdown(str(e)[:100])}

Please try again later\\.
"""
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    error_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=kb.close_button()
                )
            else:
                await update.message.reply_text(
                    error_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        except:
            pass


async def download_multiple_songs(update: Update, context: ContextTypes.DEFAULT_TYPE, songs: list, quality: str = '160kbps'):
    """
    Download multiple songs (for playlists/albums)
    
    Args:
        songs: List of song dicts
        quality: Download quality
    """
    user_id = update.effective_user.id
    
    # Limit to prevent abuse
    max_downloads = 10
    if len(songs) > max_downloads:
        await update.callback_query.answer(
            f"⚠️ Limited to {max_downloads} songs at once!",
            show_alert=True
        )
        songs = songs[:max_downloads]
    
    await update.callback_query.answer(f"Downloading {len(songs)} songs...")
    
    status_message = await update.callback_query.message.reply_text(
        f"⬇️ *Downloading {len(songs)} songs\\.\\.\\.*\n\n⏳ Please wait\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    success_count = 0
    
    for i, song in enumerate(songs):
        try:
            # Update status
            await status_message.edit_text(
                f"⬇️ *Downloading song {i+1}/{len(songs)}\\.\\.\\.*\n\n🎵 {escape_markdown(song.get('name', 'Unknown'))}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
            
            # Download
            download_url = api.get_download_url(song, quality)
            if not download_url:
                continue
            
            audio_data = api.download_song(download_url)
            if not audio_data:
                continue
            
            # Send
            title = song.get('name', 'Unknown Song')
            artist = get_artist_names(song)
            filename = f"{title} - {artist}.m4a"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()[:100]
            
            audio_file = BytesIO(audio_data)
            audio_file.name = filename
            
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=audio_file,
                title=title,
                performer=artist,
                caption=f"🎵 {title}\n👤 {artist}\n📶 {quality}"
            )
            
            success_count += 1
            db.add_to_history(user_id, song)
            
        except Exception as e:
            logger.error(f"Error downloading song {i+1}: {e}")
            continue
    
    # Update stats
    for _ in range(success_count):
        db.increment_downloads(user_id)
    
    # Final status
    await status_message.edit_text(
        f"✅ *Download complete\\!*\n\n📥 {success_count}/{len(songs)} songs sent successfully\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=kb.close_button()
    )
    
    logger.info(f"✅ Batch download: {success_count}/{len(songs)} for user {user_id}")
