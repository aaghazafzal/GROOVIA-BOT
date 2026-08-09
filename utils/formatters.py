"""
🎵 Groovia Bot - Text Formatters
Helper functions for formatting text and data
"""

from typing import Optional


def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    if not text:
        return ""
    
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = str(text).replace(char, f'\\{char}')
    
    return text


def truncate(text: str, max_length: int = 30) -> str:
    """Truncate text with ellipsis"""
    if not text:
        return "Unknown"
    
    text = str(text)
    return f"{text[:max_length]}…" if len(text) > max_length else text


def format_duration(seconds) -> str:
    """Format duration in seconds to MM:SS"""
    try:
        sec = int(seconds)
        minutes = sec // 60
        secs = sec % 60
        return f"{minutes}:{secs:02d}"
    except:
        return "0:00"


def format_number(num: int) -> str:
    """Format large numbers (e.g., 1000000 -> 1M)"""
    try:
        num = int(num)
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return str(num)
    except:
        return "0"


def get_artist_names(song: dict) -> str:
    """Extract artist names from new API format"""
    try:
        # Try primary artists first
        artists = song.get('artists', {})
        primary = artists.get('primary', [])
        
        if primary:
            names = [artist.get('name', '') for artist in primary if artist.get('name')]
            if names:
                return ', '.join(names)
        
        # Fallback to other fields
        if song.get('primaryArtists'):
            return song['primaryArtists']
        
        if song.get('singers'):
            return song['singers']
        
        return "Unknown Artist"
        
    except Exception as e:
        return "Unknown Artist"


def get_image_url(item: dict, quality: str = '500x500') -> Optional[str]:
    """
    Get image URL from new API format
    
    Args:
        item: Song/Album/Artist/Playlist dict
        quality: Image quality (50x50, 150x150, 500x500)
    
    Returns:
        Image URL or None
    """
    try:
        images = item.get('image', [])
        
        if not images:
            return None
        
        # Find requested quality
        for img in images:
            if img.get('quality') == quality:
                return img.get('url')
        
        # Fallback to highest quality (last in list)
        if images:
            return images[-1].get('url')
        
        return None
        
    except:
        return None


def format_song_info(song: dict, include_album: bool = True) -> str:
    """
    Format song information for display
    
    Returns a formatted string with song details
    """
    title = escape_markdown(song.get('name') or song.get('title', 'Unknown'))
    artists = escape_markdown(get_artist_names(song))
    duration = format_duration(song.get('duration', 0))
    
    info = f"🎵 *{title}*\n"
    info += f"👤 {artists}\n"
    info += f"⏱️ {duration}"
    
    if include_album:
        album_name = song.get('album', {})
        if isinstance(album_name, dict):
            album_name = album_name.get('name', '')
        
        if album_name:
            info += f"\n💿 {escape_markdown(album_name)}"
    
    # Play count
    play_count = song.get('playCount', 0)
    if play_count:
        info += f"\n▶️ {escape_markdown(format_number(play_count))} plays"
    
    # Year
    year = song.get('year')
    if year:
        info += f"\n📅 {year}"
    
    # Language
    language = song.get('language', '').title()
    if language:
        info += f"\n🌐 {language}"
    
    return info


def format_album_info(album: dict) -> str:
    """Format album information"""
    title = escape_markdown(album.get('name') or album.get('title', 'Unknown'))
    artist = escape_markdown(album.get('artist', 'Unknown'))
    year = album.get('year', '')
    song_count = album.get('songCount') or len(album.get('songs', []))
    
    info = f"💿 *{title}*\n"
    info += f"👤 {artist}\n"
    
    if year:
        info += f"📅 {year}\n"
    
    if song_count:
        info += f"🎵 {song_count} songs"
    
    return info


def format_artist_info(artist: dict) -> str:
    """Format artist information"""
    name = escape_markdown(artist.get('name') or artist.get('title', 'Unknown'))
    
    info = f"🎤 *{name}*\n"
    
    # Follower count (if available)
    follower_count = artist.get('followerCount')
    if follower_count:
        info += f"👥 {escape_markdown(format_number(follower_count))} followers\n"
    
    # Description
    description = artist.get('description')
    bio = artist.get('bio')
    
    if bio:
        info += f"\n{escape_markdown(truncate(bio, 100))}"
    elif description:
        info += f"\n{escape_markdown(description)}"
    
    return info


def format_playlist_info(playlist: dict) -> str:
    """Format playlist information"""
    title = escape_markdown(playlist.get('name') or playlist.get('title', 'Unknown'))
    song_count = playlist.get('songCount') or len(playlist.get('songs', []))
    
    info = f"📋 *{title}*\n"
    
    if song_count:
        info += f"🎵 {song_count} songs"
    
    description = playlist.get('description')
    if description:
        info += f"\n\n{escape_markdown(truncate(description, 100))}"
    
    return info
