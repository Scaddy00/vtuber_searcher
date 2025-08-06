"""
VTuber scrapers module
"""

from typing import Dict, List, Any
import asyncio
from .base_scraper import BaseScraper
from .twitch_scraper import TwitchScraper
from .youtube_scraper import YouTubeScraper

__all__ = ['BaseScraper', 'TwitchScraper', 'YouTubeScraper']

async def search_vtuber(
    vtuber_name: str, 
    twitch_client_id: str, 
    twitch_client_secret: str, 
    youtube_api_key: str,
    debug: bool = False
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for VTuber on both Twitch and YouTube platforms
    
    Args:
        vtuber_name: Name of the VTuber to search for
        twitch_client_id: Twitch API client ID
        twitch_client_secret: Twitch API client secret
        youtube_api_key: YouTube Data API key
        debug: Enable debug logging
    
    Returns:
        Dictionary with results from both platforms
    """
    
    # Initialize scrapers
    twitch_scraper = TwitchScraper(
        client_id=twitch_client_id,
        client_secret=twitch_client_secret
    )
    
    youtube_scraper = YouTubeScraper(
        api_key=youtube_api_key
    )
    
    # Search on both platforms in parallel
    try:
        twitch_results, youtube_results = await asyncio.gather(
            twitch_scraper.find_vtuber(vtuber_name, debug=debug),
            youtube_scraper.find_vtuber(vtuber_name, debug=debug),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(twitch_results, Exception):
            print(f"[ERROR] Twitch search failed: {twitch_results}")
            twitch_results = []
            
        if isinstance(youtube_results, Exception):
            print(f"[ERROR] YouTube search failed: {youtube_results}")
            youtube_results = []
        
        return {
            'twitch': twitch_results,
            'youtube': youtube_results,
            'total_results': len(twitch_results) + len(youtube_results)
        }
        
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        return {
            'twitch': [],
            'youtube': [],
            'total_results': 0
        }