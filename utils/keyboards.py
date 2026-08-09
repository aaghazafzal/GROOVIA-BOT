"""
🎵 Groovia Bot - Keyboard Layouts
All inline keyboards for the bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import EMOJI, SONGS_PER_PAGE
from utils.formatters import truncate, format_duration, get_artist_names


class Keyboards:
    """All keyboard layouts"""
    
    @staticmethod
    def main_menu():
        """Main menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{EMOJI['search']} Search", callback_data="menu_search"),
                InlineKeyboardButton(f"{EMOJI['trending']} Trending", callback_data="menu_trending")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['song']} Songs", callback_data="menu_songs"),
                InlineKeyboardButton(f"{EMOJI['album']} Albums", callback_data="menu_albums")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['artist']} Artists", callback_data="menu_artists"),
                InlineKeyboardButton(f"{EMOJI['playlist']} Playlists", callback_data="menu_playlists")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['favorite']} Favorites", callback_data="menu_favorites"),
                InlineKeyboardButton(f"{EMOJI['history']} History", callback_data="menu_history")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['settings']} Settings", callback_data="menu_settings"),
                InlineKeyboardButton("❓ Help", callback_data="menu_help")
            ]
        ])

    @staticmethod
    def start_keyboard():
        """
        Special keyboard for /start command
        Contains external links as requested
        """
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚀 Open Web App (10x Features)", url="https://grooviamodern.vercel.app")
            ],
            [
                InlineKeyboardButton("📢 Join Channel", url="https://t.me/Univora88"),
                InlineKeyboardButton("🌐 Univora Site", url="https://univora.site")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['search']} Start Searching", callback_data="menu_search")
            ]
        ])
    
    @staticmethod
    def search_type():
        """Search type selection with better layout"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{EMOJI['song']} Search Songs", callback_data="search_songs"),
                InlineKeyboardButton(f"{EMOJI['album']} Search Albums", callback_data="search_albums")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['artist']} Search Artists", callback_data="search_artists"),
                InlineKeyboardButton(f"{EMOJI['playlist']} Search Playlists", callback_data="search_playlists")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['home']} Back to Menu", callback_data="menu")
            ]
        ])
    
    @staticmethod
    def song_list(songs: list, page: int = 0, total: int = None, search_type: str = 'song'):
        """
        Display list of songs with pagination
        
        Args:
            songs: List of song dicts
            page: Current page number
            total: Total number of songs
            search_type: Type of search (song, album, artist, playlist)
        """
        if total is None:
            total = len(songs)
        
        kb = []
        start = page * SONGS_PER_PAGE
        end = min(start + SONGS_PER_PAGE, len(songs))
        
        # Song buttons
        for i in range(start, end):
            if i >= len(songs):
                break
                
            song = songs[i]
            title = truncate(song.get('name') or song.get('title', 'Unknown'), 25)
            artist = truncate(get_artist_names(song), 15)
            duration = format_duration(song.get('duration', 0))
            
            button_text = f"{EMOJI['song']} {title} • {artist} [{duration}]"
            kb.append([InlineKeyboardButton(button_text, callback_data=f"song_{i}")])
        
        # Pagination buttons
        nav = []
        current_page = page + 1
        total_pages = (total + SONGS_PER_PAGE - 1) // SONGS_PER_PAGE
        
        if page > 0:
            nav.append(InlineKeyboardButton(f"{EMOJI['prev']} Prev", callback_data=f"page_{page-1}"))
        
        nav.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="page_info"))
        
        if end < total:
            nav.append(InlineKeyboardButton(f"Next {EMOJI['next']}", callback_data=f"page_{page+1}"))
        
        if nav:
            kb.append(nav)
        
        # Action buttons
        kb.append([
            InlineKeyboardButton(f"{EMOJI['download']} Download All", callback_data="download_all"),
            InlineKeyboardButton("🔀 Shuffle", callback_data="shuffle")
        ])
        
        # Back button
        kb.append([
            InlineKeyboardButton(f"{EMOJI['home']} Home", callback_data="menu"),
            InlineKeyboardButton(f"{EMOJI['close']} Close", callback_data="close")
        ])
        
        return InlineKeyboardMarkup(kb)
    
    @staticmethod
    def song_detail(song_index: int, is_favorite: bool = False, page: int = 0):
        """
        Song detail view with actions
        
        Args:
            song_index: Index of song in current list
            is_favorite: Whether song is in favorites
            page: Current page for back navigation
        """
        fav_text = "💔 Remove Favorite" if is_favorite else f"{EMOJI['favorite']} Add to Favorites"
        fav_callback = f"unfav_{song_index}" if is_favorite else f"fav_{song_index}"
        
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['download']} Download", callback_data=f"dl_{song_index}")],
            [
                InlineKeyboardButton("📝 Lyrics", callback_data=f"lyrics_{song_index}"),
                InlineKeyboardButton("📤 Share", callback_data=f"share_{song_index}")
            ],
            [
                InlineKeyboardButton(fav_text, callback_data=fav_callback),
                InlineKeyboardButton("🎵 Similar", callback_data=f"similar_{song_index}")
            ],
            [
                InlineKeyboardButton("🔙 Back to List", callback_data=f"back_{page}"),
                InlineKeyboardButton(f"{EMOJI['home']} Home", callback_data="menu")
            ]
        ])
    
    @staticmethod
    def quality_selector(song_index: int):
        """Quality selection for download"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📶 12kbps (Preview)", callback_data=f"q_12_{song_index}")],
            [InlineKeyboardButton("📶 48kbps (Low)", callback_data=f"q_48_{song_index}")],
            [InlineKeyboardButton("📶 96kbps (Medium)", callback_data=f"q_96_{song_index}")],
            [InlineKeyboardButton("🎵 160kbps (Good) ⭐", callback_data=f"q_160_{song_index}")],
            [InlineKeyboardButton("💎 320kbps (Best)", callback_data=f"q_320_{song_index}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"song_{song_index}")]
        ])
    
    @staticmethod
    def album_list(albums: list, page: int = 0):
        """Display list of albums"""
        kb = []
        start = page * SONGS_PER_PAGE
        end = min(start + SONGS_PER_PAGE, len(albums))
        
        for i in range(start, end):
            if i >= len(albums):
                break
                
            album = albums[i]
            name = truncate(album.get('name') or album.get('title', 'Unknown'), 30)
            artist = truncate(album.get('artist', 'Unknown'), 15)
            year = album.get('year', '')
            
            button_text = f"{EMOJI['album']} {name}"
            if artist != 'Unknown':
                button_text += f" • {artist}"
            if year:
                button_text += f" ({year})"
            
            kb.append([InlineKeyboardButton(button_text, callback_data=f"album_{i}")])
        
        # Navigation
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(f"{EMOJI['prev']} Prev", callback_data=f"albumpage_{page-1}"))
        if end < len(albums):
            nav.append(InlineKeyboardButton(f"Next {EMOJI['next']}", callback_data=f"albumpage_{page+1}"))
        if nav:
            kb.append(nav)
        
        kb.append([InlineKeyboardButton(f"{EMOJI['home']} Home", callback_data="menu")])
        
        return InlineKeyboardMarkup(kb)
    
    @staticmethod
    def artist_list(artists: list, page: int = 0):
        """Display list of artists"""
        kb = []
        start = page * SONGS_PER_PAGE
        end = min(start + SONGS_PER_PAGE, len(artists))
        
        for i in range(start, end):
            if i >= len(artists):
                break
                
            artist = artists[i]
            name = truncate(artist.get('name') or artist.get('title', 'Unknown'), 35)
            
            kb.append([InlineKeyboardButton(f"{EMOJI['artist']} {name}", callback_data=f"artist_{i}")])
        
        # Navigation
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(f"{EMOJI['prev']} Prev", callback_data=f"artistpage_{page-1}"))
        if end < len(artists):
            nav.append(InlineKeyboardButton(f"Next {EMOJI['next']}", callback_data=f"artistpage_{page+1}"))
        if nav:
            kb.append(nav)
        
        kb.append([InlineKeyboardButton(f"{EMOJI['home']} Home", callback_data="menu")])
        
        return InlineKeyboardMarkup(kb)
    
    @staticmethod
    def playlist_list(playlists: list, page: int = 0):
        """Display list of playlists"""
        kb = []
        start = page * SONGS_PER_PAGE
        end = min(start + SONGS_PER_PAGE, len(playlists))
        
        for i in range(start, end):
            if i >= len(playlists):
                break
                
            playlist = playlists[i]
            name = truncate(playlist.get('name') or playlist.get('title', 'Unknown'), 30)
            song_count = playlist.get('songCount', 0)
            
            button_text = f"{EMOJI['playlist']} {name}"
            if song_count:
                button_text += f" ({song_count} songs)"
            
            kb.append([InlineKeyboardButton(button_text, callback_data=f"playlist_{i}")])
        
        # Navigation
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(f"{EMOJI['prev']} Prev", callback_data=f"playlistpage_{page-1}"))
        if end < len(playlists):
            nav.append(InlineKeyboardButton(f"Next {EMOJI['next']}", callback_data=f"playlistpage_{page+1}"))
        if nav:
            kb.append(nav)
        
        kb.append([InlineKeyboardButton(f"{EMOJI['home']} Home", callback_data="menu")])
        
        return InlineKeyboardMarkup(kb)
    
    @staticmethod
    def settings(current_quality: str = '160kbps'):
        """Settings menu"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📶 Quality: {current_quality}", callback_data="setting_quality")],
            [InlineKeyboardButton("🌐 Language", callback_data="setting_language")],
            [InlineKeyboardButton("🔔 Notifications", callback_data="setting_notif")],
            [InlineKeyboardButton("🗑️ Clear History", callback_data="setting_clear_history")],
            [InlineKeyboardButton(f"{EMOJI['home']} Back to Menu", callback_data="menu")]
        ])
    
    @staticmethod
    def close_button():
        """Simple close button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['close']} Close", callback_data="close")]
        ])


# Global instance
kb = Keyboards()
