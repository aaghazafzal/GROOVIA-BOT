"""
🎵 Groovia Bot - JioSaavn API Client
Handles all API requests to the new Vercel API
"""

import requests
import logging
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    API_BASE_URL, 
    API_ENDPOINTS, 
    MAX_RETRIES, 
    REQUEST_TIMEOUT,
    DEFAULT_QUALITY
)

logger = logging.getLogger(__name__)


class JioSaavnAPI:
    """Modern API client for JioSaavn Vercel API"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = self._create_session()
    
    def _create_session(self):
        """Create session with retry logic"""
        session = requests.Session()
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504, 429]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def _request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make API request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"🌐 API Request: {url} | Params: {params}")
            
            response = self.session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"✅ API Success: {endpoint}")
                    return data.get('data')
                else:
                    logger.error(f"❌ API Error: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"❌ HTTP {response.status_code}: {endpoint}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"💥 Exception: {endpoint} - {e}")
            return None
    
    # ============= SEARCH METHODS =============
    
    def global_search(self, query: str) -> Optional[dict]:
        """
        Global search - returns songs, albums, artists, playlists
        
        Returns:
        {
            'topQuery': {...},
            'songs': {'results': [...]},
            'albums': {'results': [...]},
            'artists': {'results': [...]},
            'playlists': {'results': [...]}
        }
        """
        return self._request(API_ENDPOINTS['global_search'], {'query': query})
    
    def search_songs(self, query: str, page: int = 0, limit: int = 10) -> Optional[List[dict]]:
        """Search only songs"""
        data = self._request(
            API_ENDPOINTS['song_search'],
            {'query': query, 'page': page, 'limit': limit}
        )
        return data.get('results', []) if data else None
    
    def search_albums(self, query: str, page: int = 0, limit: int = 10) -> Optional[List[dict]]:
        """Search only albums"""
        data = self._request(
            API_ENDPOINTS['album_search'],
            {'query': query, 'page': page, 'limit': limit}
        )
        return data.get('results', []) if data else None
    
    def search_artists(self, query: str, page: int = 0, limit: int = 10) -> Optional[List[dict]]:
        """Search only artists"""
        data = self._request(
            API_ENDPOINTS['artist_search'],
            {'query': query, 'page': page, 'limit': limit}
        )
        return data.get('results', []) if data else None
    
    def search_playlists(self, query: str, page: int = 0, limit: int = 10) -> Optional[List[dict]]:
        """Search only playlists"""
        data = self._request(
            API_ENDPOINTS['playlist_search'],
            {'query': query, 'page': page, 'limit': limit}
        )
        return data.get('results', []) if data else None
    
    # ============= DETAIL METHODS =============
    
    def get_song_details(self, song_id: str) -> Optional[dict]:
        """Get detailed info about a song"""
        data = self._request(f"{API_ENDPOINTS['song_details']}/{song_id}")
        
        # API returns list with single song, extract first item
        if isinstance(data, list) and len(data) > 0:
            logger.info(f"✅ Got song details (from list): {data[0].get('name')}")
            return data[0]
        elif isinstance(data, dict):
            logger.info(f"✅ Got song details (dict): {data.get('name')}")
            return data
        else:
            logger.error(f"❌ Unexpected song details format: {type(data)}")
            return None
    
    def get_album_details(self, album_id: str) -> Optional[dict]:
        """Get album with all songs"""
        return self._request(f"{API_ENDPOINTS['album_details']}/{album_id}")
    
    def get_artist_details(self, artist_id: str) -> Optional[dict]:
        """Get artist info and songs"""
        return self._request(f"{API_ENDPOINTS['artist_details']}/{artist_id}")
    
    def get_playlist_details(self, playlist_id: str) -> Optional[dict]:
        """Get playlist with all songs"""
        return self._request(f"{API_ENDPOINTS['playlist_details']}/{playlist_id}")
    
    def get_lyrics(self, song_id: str) -> Optional[str]:
        """Get song lyrics"""
        endpoint = API_ENDPOINTS['lyrics'].format(id=song_id)
        data = self._request(endpoint)
        return data.get('lyrics') if data else None
    
    # ============= DOWNLOAD METHOD =============
    
    def get_download_url(self, song: dict, quality: str = DEFAULT_QUALITY) -> Optional[str]:
        """
        Get download URL for specific quality
        
        Args:
            song: Song dict with 'downloadUrl' array
            quality: Quality option (12kbps, 48kbps, 96kbps, 160kbps, 320kbps)
        
        Returns:
            Direct download URL
        """
        try:
            # Log the song object structure for debugging
            logger.info(f"🔍 Getting download URL for quality: {quality}")
            logger.info(f"🔍 Song ID: {song.get('id')}, Name: {song.get('name')}")
            
            download_urls = song.get('downloadUrl', [])
            logger.info(f"🔍 Download URLs found: {len(download_urls)} URLs")
            
            # Log available qualities
            if download_urls:
                available_qualities = [url.get('quality') for url in download_urls]
                logger.info(f"🔍 Available qualities: {available_qualities}")
            
            # Find the requested quality
            for url_data in download_urls:
                if url_data.get('quality') == quality:
                    url = url_data.get('url')
                    logger.info(f"✅ Found URL for {quality}: {url[:50]}...")
                    return url
            
            # Fallback to 160kbps
            logger.warning(f"⚠️ {quality} not found, trying 160kbps fallback")
            for url_data in download_urls:
                if url_data.get('quality') == '160kbps':
                    url = url_data.get('url')
                    logger.info(f"✅ Using fallback 160kbps: {url[:50]}...")
                    return url
            
            # Last resort - return any available
            if download_urls:
                url = download_urls[-1].get('url')
                logger.warning(f"⚠️ Using last available quality: {download_urls[-1].get('quality')}")
                return url
            
            logger.error("❌ No download URLs found in song object!")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting download URL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def download_song(self, url: str) -> Optional[bytes]:
        """Download song file"""
        try:
            response = self.session.get(
                url,
                timeout=REQUEST_TIMEOUT,
                stream=True,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Downloaded: {url}")
                return response.content
            else:
                logger.error(f"❌ Download failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"💥 Download error: {e}")
            return None


# Global API instance
api = JioSaavnAPI()
