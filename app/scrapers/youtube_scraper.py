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
from .base_scraper import BaseScraper

class YouTubeScraper(BaseScraper):
    """Scrapes YouTube for VTuber content creators"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.youtube_service = build('youtube', 'v3', developerKey=api_key)
    
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
    
    async def get_user_info(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
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
    
    async def search_live_streams(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for live streams that match the query"""
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'eventType': 'live',  # Only live streams
            'maxResults': min(max_results, 50),
            'order': 'relevance'
        }
        
        data = await self._make_request('search', params)
        return data.get('items', []) if data else []
    
    async def get_video_tags(self, video_id: str) -> List[str]:
        """Get tags for a specific video"""
        params = {
            'part': 'snippet',
            'id': video_id
        }
        
        data = await self._make_request('videos', params)
        if data and data.get('items'):
            video = data['items'][0]
            return video.get('snippet', {}).get('tags', [])
        return []
    
    async def search_videos_by_tag(self, tag: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for videos with specific tag"""
        params = {
            'part': 'snippet',
            'q': tag,
            'type': 'video',
            'maxResults': min(max_results, 50),
            'order': 'relevance'
        }
        
        data = await self._make_request('search', params)
        return data.get('items', []) if data else []
    
    async def find_vtuber_by_content(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTubers by analyzing video content and descriptions"""
        
        try:
            print(f"[INFO] Content-based search for VTuber: {vtuber_name}")
            
            # Search for videos with VTuber-related keywords
            vtuber_keywords = ['vtuber', 'virtual youtuber', 'live2d', 'anime avatar', 'virtual avatar']
            vtubers = []
            
            for keyword in vtuber_keywords:
                videos = await self.search_videos_by_tag(keyword, max_results=20)
                
                for video in videos:
                    channel_id = video['snippet']['channelId']
                    channel_title = video['snippet']['channelTitle']
                    
                    # Check if channel name matches search
                    name_matches = self._is_name_match(channel_title, vtuber_name, debug=debug)
                    
                    if name_matches:
                        # Get detailed channel info
                        channel_info = await self.get_user_info([channel_id])
                        if channel_info:
                            channel = channel_info[0]
                            
                            # Check if it's a VTuber channel
                            is_vtuber = self._is_vtuber_channel(channel, platform='youtube', debug=debug)
                            
                            if is_vtuber:
                                score, reasons, threshold = self.filters.calculate_adaptive_score(channel, platform='youtube')
                                
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
                                    'language_focus': self.filters.get_language_focus(channel, platform='youtube'),
                                    'discovered_at': datetime.now().isoformat(),
                                    'search_stage': 'content'
                                }
                                vtubers.append(vtuber)
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error in content-based search for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTuber content creators on YouTube using enhanced multi-stage search"""
        try:
            print(f"[INFO] Searching YouTube for: {vtuber_name}")
            
            if debug:
                print(f"[DEBUG] Starting YouTube search for: {vtuber_name}")
                print(f"[DEBUG] YouTube API key configured: {'Yes' if self.api_key else 'No'}")
            
            # Use enhanced multi-stage search
            results = await self.find_vtuber_enhanced(vtuber_name, platform='youtube', debug=debug)
            
            if results:
                print(f"[INFO] Enhanced search found {len(results)} VTubers")
                return results
            
            # Fallback to traditional search with relaxed filtering
            print(f"[INFO] Enhanced search returned no results, using traditional search as fallback")
            
            # Search for channels
            channels = await self.search_channels(vtuber_name, max_results=50)
            
            print(f"[INFO] Found {len(channels)} channels in search")
            
            if not channels:
                return []
            
            # Get channel IDs
            channel_ids = [channel['snippet']['channelId'] for channel in channels]
            
            # Get detailed information for each channel
            channel_info = await self.get_user_info(channel_ids)
            
            print(f"[INFO] Retrieved detailed info for {len(channel_info)} channels")
            
            # Use relaxed filtering for YouTube
            vtubers = []
            filtered_out = 0
            name_mismatch = 0
            
            for channel in channel_info:
                channel_title = channel['snippet']['title']
                
                # Use fuzzy name matching instead of strict matching
                name_matches = self._is_name_match_fuzzy(channel_title, vtuber_name, debug=debug)
                
                if debug:
                    print(f"[DEBUG] Channel: '{channel_title}' - Name match: {name_matches}")
                
                # Only proceed if name matches
                if name_matches:
                    # Use adaptive scoring with lower threshold
                    score, reasons, threshold = self.filters.calculate_adaptive_score(channel, platform='youtube')
                    
                    if debug:
                        print(f"[DEBUG] Channel '{channel_title}' - Score: {score}, Threshold: {threshold}")
                    
                    # Balanced threshold for YouTube (not too permissive)
                    if score >= 2.0:  # Increased from 1.5 to 2.0
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
                            'language_focus': self.filters.get_language_focus(channel, platform='youtube'),
                            'discovered_at': datetime.now().isoformat()
                        }
                        vtubers.append(vtuber)
                    else:
                        filtered_out += 1
                        if debug:
                            print(f"[DEBUG] Filtered out '{channel_title}' - score {score} below threshold {threshold}")
                else:
                    name_mismatch += 1
                    if debug:
                        print(f"[DEBUG] Filtered out '{channel_title}' - name doesn't match '{vtuber_name}'")
            
            print(f"[INFO] Found {len(vtubers)} VTuber channels")
            print(f"[INFO] Filtered out {filtered_out} channels (not VTuber)")
            print(f"[INFO] Filtered out {name_mismatch} channels (name mismatch)")
            
            # If still no results, try permissive search
            if not vtubers:
                print(f"[INFO] Traditional search returned no results, trying permissive search")
                vtubers = await self.find_vtuber_permissive(vtuber_name, debug=debug)
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error searching for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber_permissive(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTubers with more permissive filtering for YouTube"""
        try:
            print(f"[INFO] Permissive search for VTuber: {vtuber_name}")
            
            # Search for channels
            channels = await self.search_channels(vtuber_name, max_results=100)
            
            if not channels:
                return []
            
            # Get channel IDs
            channel_ids = [channel['snippet']['channelId'] for channel in channels]
            
            # Get detailed information for each channel
            channel_info = await self.get_user_info(channel_ids)
            
            vtubers = []
            
            for channel in channel_info:
                channel_title = channel['snippet']['title']
                
                # Very permissive name matching
                name_matches = self._is_name_match_fuzzy(channel_title, vtuber_name, debug=debug)
                
                if name_matches:
                    # Very low threshold for VTuber detection
                    score, reasons, threshold = self.filters.calculate_adaptive_score(channel, platform='youtube')
                    
                    # Moderate threshold for permissive search
                    if score >= 1.5:  # Moderate threshold
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
                            'language_focus': self.filters.get_language_focus(channel, platform='youtube'),
                            'discovered_at': datetime.now().isoformat(),
                            'search_stage': 'permissive'
                        }
                        vtubers.append(vtuber)
                        if debug:
                            print(f"[DEBUG] Permissive search found: '{channel_title}' with score {score}")
            
            print(f"[INFO] Permissive search found {len(vtubers)} VTubers")
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error in permissive search for '{vtuber_name}': {e}")
            return []