"""
YouTube scraper for discovering VTuber content creators
"""

import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .vtuber_filters import VTuberFilters

class YouTubeScraper:
    """Scrapes YouTube for VTuber content creators"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.youtube_service = build('youtube', 'v3', developerKey=api_key)
        
        # Initialize VTuber filters
        self.filters = VTuberFilters()
    
    def _is_vtuber_channel(self, channel_info: Dict[str, Any], debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber based on various indicators"""
        return self.filters.is_vtuber_channel_adaptive(channel_info, platform='youtube', debug=debug)
    
    def _is_name_match(self, channel_title: str, search_name: str, debug: bool = False) -> bool:
        """Check if the channel title matches the search name"""
        return self.filters.is_name_match_fuzzy(channel_title, search_name, debug)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to YouTube Data API"""
        if params is None:
            params = {}
        
        # Add API key to params
        params['key'] = self.api_key
        
        # Build URL
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"[ERROR] YouTube API request failed: {response.status}")
                    print(f"[ERROR] Error details: {error_text}")
                    return None
    
    async def search_channels(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for channels that match the query"""
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'channel',
            'maxResults': min(max_results, 50),  # YouTube API limit
            'order': 'relevance'
        }
        
        data = await self._make_request('search', params)
        return data.get('items', []) if data else []
    
    async def get_channel_info(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed channel information"""
        if not channel_ids:
            return []
        
        # YouTube API allows up to 50 channel IDs per request
        all_channels = []
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i:i+50]
            params = {
                'part': 'snippet,statistics,brandingSettings',
                'id': ','.join(batch)
            }
            data = await self._make_request('channels', params)
            all_channels.extend(data.get('items', []) if data else [])
        
        return all_channels
    
    async def find_vtuber(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTuber content creators on YouTube (filtered for VTubers only)"""
        try:
            print(f"[INFO] Searching YouTube for: {vtuber_name}")
            
            # Search for channels
            channels = await self.search_channels(vtuber_name, max_results=50)
            
            print(f"[INFO] Found {len(channels)} channels in search")
            
            if not channels:
                return []
            
            # Get channel IDs
            channel_ids = [channel['snippet']['channelId'] for channel in channels]
            
            # Get detailed information for each channel
            channel_info = await self.get_channel_info(channel_ids)
            
            print(f"[INFO] Retrieved detailed info for {len(channel_info)} channels")
            
            # Combine search and detailed information with VTuber filtering
            vtubers = []
            filtered_out = 0
            name_mismatch = 0
            
            for channel in channel_info:
                channel_title = channel['snippet']['title']
                
                # First check if the channel name matches the search query
                name_matches = self._is_name_match(channel_title, vtuber_name, debug=debug)
                
                if debug:
                    print(f"[DEBUG] Channel: '{channel_title}' - Name match: {name_matches}")
                
                # Only proceed if name matches
                if name_matches:
                    # Check if channel passes VTuber filter
                    is_vtuber = self._is_vtuber_channel(channel, debug=debug)
                    
                    if debug:
                        print(f"[DEBUG] Channel '{channel_title}' - VTuber: {is_vtuber}")
                    
                    if channel and is_vtuber:
                        score, reasons, threshold = self.filters.calculate_adaptive_score(channel, platform='youtube')
                        language_focus = self.filters.get_language_focus(channel, platform='youtube')
                        
                        vtuber = {
                            'platform': 'youtube',
                            'id': channel['id'],
                            'name': channel['snippet']['title'],
                            'url': f"https://youtube.com/channel/{channel['id']}",
                            'language': channel['snippet'].get('defaultLanguage', ''),
                            'avatar_url': channel['snippet'].get('thumbnails', {}).get('default', {}).get('url', ''),
                            'subscriber_count': channel.get('statistics', {}).get('subscriberCount', '0'),
                            'video_count': channel.get('statistics', {}).get('videoCount', '0'),
                            'view_count': channel.get('statistics', {}).get('viewCount', '0'),
                            'description': channel['snippet'].get('description', ''),
                            'vtuber_score': score,
                            'vtuber_reasons': reasons,
                            'language_focus': language_focus,
                            'discovered_at': datetime.now().isoformat()
                        }
                        vtubers.append(vtuber)
                    else:
                        filtered_out += 1
                else:
                    name_mismatch += 1
                    if debug:
                        print(f"[DEBUG] Filtered out '{channel_title}' - name doesn't match '{vtuber_name}'")
            
            print(f"[INFO] Found {len(vtubers)} VTuber channels")
            print(f"[INFO] Filtered out {filtered_out} channels (not VTuber)")
            print(f"[INFO] Filtered out {name_mismatch} channels (name mismatch)")
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error searching for '{vtuber_name}': {e}")
            return []