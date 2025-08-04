"""
YouTube scraper for discovering VTuber content creators
"""

import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeScraper:
    """Scrapes YouTube for VTuber content creators"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.youtube_service = build('youtube', 'v3', developerKey=api_key)
        
        # VTuber keywords for filtering
        self.vtuber_keywords = [
            'vtuber', 'virtual', 'avatar', 'anime', 'kawaii', 'hololive', 
            'nijisanji', 'vshojo', 'vspo', 'vtubing', 'live2d',
            'rigging', 'model', 'character', 'streamer', 'content creator',
            'virtual youtuber', 'virtual streamer', 'anime avatar'
        ]
        
        # VTuber-related terms in descriptions
        self.vtuber_indicators = [
            'vtuber', 'virtual youtuber', 'virtual streamer', 'anime avatar',
            'live2d', 'rigging', 'model', 'character', 'vtubing',
            'hololive', 'nijisanji', 'vshojo', 'vspo', 'vtuber'
        ]
    
    def _is_vtuber_channel(self, channel_info: Dict[str, Any], debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber based on various indicators"""
        
        # Get text to analyze
        title = channel_info.get('snippet', {}).get('title', '').lower()
        description = channel_info.get('snippet', {}).get('description', '').lower()
        
        # Combine all text for analysis
        all_text = f"{title} {description}".lower()
        
        # Check for VTuber keywords in title
        title_has_keywords = any(keyword in title for keyword in self.vtuber_keywords)
        
        # Check for VTuber indicators in description
        desc_has_indicators = any(indicator in description for indicator in self.vtuber_indicators)
        
        # Check for anime-related terms
        anime_terms = ['anime', 'kawaii', 'moe', 'otaku', 'weeb', 'japanese']
        has_anime_terms = any(term in all_text for term in anime_terms)
        
        # Check for streaming/content creation terms
        streaming_terms = ['streamer', 'content creator', 'live', 'gaming', 'chat']
        has_streaming_terms = any(term in all_text for term in streaming_terms)
        
        # Check for YouTube-specific VTuber terms
        youtube_vtuber_terms = ['virtual youtuber', 'vtuber', 'live2d', 'avatar']
        has_youtube_vtuber_terms = any(term in all_text for term in youtube_vtuber_terms)
        
        # Scoring system
        score = 0
        
        if title_has_keywords:
            score += 3
        if desc_has_indicators:
            score += 3
        if has_anime_terms:
            score += 1
        if has_streaming_terms:
            score += 1
        if has_youtube_vtuber_terms:
            score += 2
        
        # Debug mode
        if debug:
            print(f"[DEBUG] Channel: {title}")
            print(f"[DEBUG] Score: {score}")
            print(f"[DEBUG] Title keywords: {title_has_keywords}")
            print(f"[DEBUG] Desc indicators: {desc_has_indicators}")
            print(f"[DEBUG] Anime terms: {has_anime_terms}")
            print(f"[DEBUG] Streaming terms: {has_streaming_terms}")
            print(f"[DEBUG] YouTube VTuber terms: {has_youtube_vtuber_terms}")
            print(f"[DEBUG] Description: {description[:200]}...")
            print("---")
        
        # Lower threshold for YouTube (more permissive)
        return score >= 1  # Changed from 2 to 1
    
    def _is_name_match(self, channel_title: str, search_name: str, debug: bool = False) -> bool:
        """Check if the channel title matches the search name"""
        
        # Normalize both names for comparison
        channel_lower = channel_title.lower().strip()
        search_lower = search_name.lower().strip()
        
        if debug:
            print(f"[DEBUG] Comparing: '{channel_lower}' vs '{search_lower}'")
        
        # Exact match (highest priority)
        if channel_lower == search_lower:
            if debug:
                print(f"[DEBUG] Exact match found!")
            return True
        
        # Check if search name is contained in channel title
        if search_lower in channel_lower:
            if debug:
                print(f"[DEBUG] Search name contained in channel title")
            return True
        
        # Check if channel title is contained in search name
        if channel_lower in search_lower:
            if debug:
                print(f"[DEBUG] Channel title contained in search name")
            return True
        
        # Check for partial matches (words) - more flexible
        search_words = search_lower.split()
        channel_words = channel_lower.split()
        
        if debug:
            print(f"[DEBUG] Search words: {search_words}")
            print(f"[DEBUG] Channel words: {channel_words}")
        
        # If search name has multiple words, check if most words match
        if len(search_words) > 1:
            matching_words = sum(1 for word in search_words if any(word in cw for cw in channel_words))
            match_percentage = matching_words / len(search_words)
            if debug:
                print(f"[DEBUG] Matching words: {matching_words}/{len(search_words)} ({match_percentage:.2f})")
            if match_percentage >= 0.6:  # Lowered from 0.7 to 0.6
                return True
        
        # Single word search - more flexible matching
        if len(search_words) == 1:
            search_word = search_words[0]
            # Check if the search word appears in any channel word
            for channel_word in channel_words:
                if search_word in channel_word or channel_word in search_word:
                    if debug:
                        print(f"[DEBUG] Single word match: '{search_word}' in '{channel_word}'")
                    return True
        
        if debug:
            print(f"[DEBUG] No match found")
        
        return False
    
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