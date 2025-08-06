"""
Twitch scraper for discovering VTuber content creators
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .vtuber_filters import VTuberFilters

class TwitchScraper:
    """Scrapes Twitch for VTuber content creators (Italian and English focused)"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.twitch.tv/helix"
        
        # Initialize VTuber filters
        self.filters = VTuberFilters()
    
    def _is_name_match(self, channel_name: str, search_name: str, debug: bool = False) -> bool:
        """Check if the channel name matches the search name"""
        return self.filters.is_name_match(channel_name, search_name, debug)
    
    def _is_vtuber_channel(self, channel_info: Dict[str, Any], user_info: Dict[str, Any], debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber based on enhanced scoring"""
        # Combine channel and user info for analysis
        combined_data = {**channel_info, **user_info}
        return self.filters.is_vtuber_channel(combined_data, platform='twitch', debug=debug)
    
    async def _get_access_token(self) -> str:
        """Get Twitch access token"""
        if self.access_token:
            return self.access_token
        
        auth_url = "https://id.twitch.tv/oauth2/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data['access_token']
                    return self.access_token
                else:
                    raise Exception(f"Failed to get access token: {response.status}")
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Twitch API"""
        token = await self._get_access_token()
        
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/{endpoint}", headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"[ERROR] Twitch API request failed: {response.status}")
    
    async def search_channels(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for channels that match the query"""
        params = {
            'query': query,
            'first': min(max_results, 100),  # Twitch API limit
        }
        
        data = await self._make_request('search/channels', params)
        return data.get('data', [])

    async def get_user_info(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed user information"""
        if not user_ids:
            return []
        
        # Twitch API allows up to 100 user IDs per request
        all_users = []
        for i in range(0, len(user_ids), 100):
            batch = user_ids[i:i+100]
            params = {'id': batch}
            data = await self._make_request('users', params)
            all_users.extend(data.get('data', []))
        
        return all_users

    async def search_live_streams(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for live streams that match the query"""
        params = {
            'query': query,
            'first': min(max_results, 100),
            'type': 'live'  # Solo stream live
        }
        
        data = await self._make_request('search/channels', params)
        return data.get('data', [])

    async def get_stream_tags(self, stream_id: str) -> List[Dict[str, Any]]:
        """Get tags for a specific stream"""
        params = {'broadcaster_id': stream_id}
        data = await self._make_request('streams/tags', params)
        return data.get('data', [])
    
    async def get_video_tags(self, video_id: str) -> List[Dict[str, Any]]:
        """Get tags for a specific video"""
        params = {'id': video_id}
        data = await self._make_request('videos', params)
        videos = data.get('data', [])
        if videos:
            return videos[0].get('tags', [])
        return []
    
    async def search_streams_by_tag(self, tag: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for streams with specific tag"""
        params = {
            'tag_id': tag,
            'first': min(max_results, 100)
        }
        data = await self._make_request('streams', params)
        return data.get('data', [])
    
    async def get_available_tags(self) -> List[Dict[str, Any]]:
        """Get all available stream tags"""
        params = {'first': 1000}  # Get maximum tags
        data = await self._make_request('tags/streams', params)
        return data.get('data', [])
    
    async def find_vtuber_by_tags(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTubers using tag-based search (more precise)"""
        
        try:
            print(f"[INFO] Searching Twitch for VTuber by tags: {vtuber_name}")
            
            # VTuber-related tag IDs (these are Twitch's internal tag IDs)
            vtuber_tag_ids = [
                '6ea6bca4-4712-4ad9-8b54-3b5d9d2256f4',  # VTuber
                '9166ad14-41f1-4b04-a3b8-c8eb8388866f',  # Virtual YouTuber
                'c2542d6d-cd10-4532-919b-60d5674a5ef3',  # Anime
                'd4bb9c58-2141-4c54-9cb6-35b3a36b416e',  # Japanese
                'f7ed6b29-0f3d-4c2d-8a0f-40e6184169a5',  # Kawaii
                '9f1b9a4a-0b1d-4c2d-8a0f-40e6184169a5',  # Live2D
                '7c49ea59-aa85-4c2d-8a0f-40e6184169a5',  # Virtual Avatar
            ]
            
            vtubers = []
            
            # Search for streams with VTuber tags
            for tag_id in vtuber_tag_ids:
                if debug:
                    print(f"[DEBUG] Searching for tag ID: {tag_id}")
                
                streams = await self.search_streams_by_tag(tag_id, max_results=50)
                
                for stream in streams:
                    # Get detailed user info
                    user_info = await self.get_user_info([stream['user_id']])
                    if user_info:
                        user = user_info[0]
                        
                        # Get stream tags for additional verification
                        stream_tags = await self.get_stream_tags(stream['user_id'])
                        tag_names = [tag.get('localization_names', {}).get('en-us', '') for tag in stream_tags]
                        
                        # Check if any VTuber tags are present
                        vtuber_tag_present = any(
                            'vtuber' in tag.lower() or 
                            'virtual' in tag.lower() or 
                            'live2d' in tag.lower() or
                            'anime' in tag.lower()
                            for tag in tag_names
                        )
                        
                        if vtuber_tag_present:
                            # Check name match (but be more flexible)
                            stream_title = stream.get('title', '').lower()
                            user_name = user.get('display_name', '').lower()
                            search_name = vtuber_name.lower()
                            
                            # More flexible name matching for tag-based results
                            name_matches = (
                                search_name in stream_title or 
                                search_name in user_name or
                                user_name in search_name or
                                any(word in user_name for word in search_name.split()) or
                                any(word in stream_title for word in search_name.split())
                            )
                            
                            if name_matches or debug:  # Include all tag-based results in debug mode
                                if debug:
                                    print(f"[DEBUG] Found VTuber stream: {user_name}")
                                    print(f"[DEBUG] Stream tags: {tag_names}")
                                    print(f"[DEBUG] Name match: {name_matches}")
                                
                                vtuber = {
                                    'platform': 'twitch',
                                    'id': stream['user_id'],
                                    'name': user.get('display_name', user_name),
                                    'url': f"https://twitch.tv/{user['login']}",
                                    'language': user.get('broadcaster_language', ''),
                                    'avatar_url': user.get('profile_image_url', ''),
                                    'is_live': True,
                                    'broadcaster_type': user.get('broadcaster_type', ''),
                                    'description': user.get('description', ''),
                                    'stream_title': stream.get('title', ''),
                                    'viewer_count': stream.get('viewer_count', 0),
                                    'tags': tag_names,
                                    'vtuber_score': 10,  # High score for tag-based detection
                                    'vtuber_reasons': f"VTuber tag detected: {[tag for tag in tag_names if any(vt in tag.lower() for vt in ['vtuber', 'virtual', 'live2d', 'anime'])]}",
                                    'language_focus': self.filters.get_language_focus({**stream, **user}, platform='twitch'),
                                    'discovered_at': datetime.now().isoformat()
                                }
                                vtubers.append(vtuber)
            
            # Remove duplicates based on user ID
            unique_vtubers = {}
            for vtuber in vtubers:
                unique_vtubers[vtuber['id']] = vtuber
            
            result = list(unique_vtubers.values())
            result.sort(key=lambda x: x.get('viewer_count', 0), reverse=True)  # Sort by viewer count
            
            print(f"[INFO] Found {len(result)} VTubers using tag-based search")
            return result
            
        except Exception as e:
            print(f"[ERROR] Error in tag-based search for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTuber content creators on Twitch using enhanced multi-stage search"""
        
        try:
            print(f"[INFO] Searching Twitch for VTuber: {vtuber_name}")
            
            # Use enhanced multi-stage search
            results = await self.find_vtuber_enhanced(vtuber_name, debug=debug)
            
            if results:
                print(f"[INFO] Enhanced search found {len(results)} VTubers")
                return results
            
            # Fallback to traditional search if enhanced search fails
            print(f"[INFO] Enhanced search returned no results, using traditional search as fallback")
            
            # Prima cerca stream live
            live_channels = await self.search_live_streams(vtuber_name, max_results=50)
            
            # Poi cerca tutti i canali e filtra per tipo
            all_channels = await self.search_channels(vtuber_name, max_results=100)
            
            print(f"[INFO] Found {len(live_channels)} live channels and {len(all_channels)} total channels")
            
            # Combina e rimuovi duplicati
            all_channel_ids = set()
            live_channel_ids = {ch['id'] for ch in live_channels}
            
            # Get detailed information for all channels
            all_user_ids = list(set([ch['id'] for ch in all_channels + live_channels]))
            user_info = await self.get_user_info(all_user_ids)
            
            print(f"[INFO] Retrieved detailed info for {len(user_info)} users")
            
            # Process results with enhanced VTuber filtering
            vtubers = []
            processed_ids = set()
            filtered_out = 0
            name_mismatch = 0
            
            # Prima aggiungi i live streamers VTuber
            for channel in live_channels:
                user = next((u for u in user_info if u['id'] == channel['id']), None)
                if user:
                    # Check name match first
                    name_matches = self._is_name_match(channel['display_name'], vtuber_name, debug=debug)
                    
                    if debug:
                        print(f"[DEBUG] Live channel: '{channel['display_name']}' - Name match: {name_matches}")
                    
                    if name_matches and self._is_vtuber_channel(channel, user, debug=debug):
                        score, reasons = self.filters.calculate_vtuber_score({**channel, **user}, platform='twitch')
                        language_focus = self.filters.get_language_focus({**channel, **user}, platform='twitch')
                        
                        vtuber = {
                            'platform': 'twitch',
                            'id': channel['id'],
                            'name': channel['display_name'],
                            'url': f"https://twitch.tv/{user['login']}",
                            'language': user.get('broadcaster_language', ''),
                            'avatar_url': user.get('profile_image_url', ''),
                            'is_live': True,
                            'broadcaster_type': user.get('broadcaster_type', ''),
                            'description': user.get('description', ''),
                            'vtuber_score': score,
                            'vtuber_reasons': reasons,
                            'language_focus': language_focus,
                            'discovered_at': datetime.now().isoformat()
                        }
                        vtubers.append(vtuber)
                        processed_ids.add(channel['id'])
                    else:
                        if not name_matches:
                            name_mismatch += 1
                        else:
                            filtered_out += 1
            
            # Poi aggiungi canali VTuber verificati non live
            for channel in all_channels:
                if channel['id'] not in processed_ids:
                    user = next((u for u in user_info if u['id'] == channel['id']), None)
                    if user:
                        # Check name match first
                        name_matches = self._is_name_match(channel['display_name'], vtuber_name, debug=debug)
                        
                        if debug:
                            print(f"[DEBUG] Channel: '{channel['display_name']}' - Name match: {name_matches}")
                        
                        if name_matches and self._is_vtuber_channel(channel, user, debug=debug):
                            broadcaster_type = user.get('broadcaster_type', '')
                            score, reasons = self.filters.calculate_vtuber_score({**channel, **user}, platform='twitch')
                            language_focus = self.filters.get_language_focus({**channel, **user}, platform='twitch')
                            
                            # Prioritize verified channels
                            if broadcaster_type in ['partner', 'affiliate']:
                                vtuber = {
                                    'platform': 'twitch',
                                    'id': channel['id'],
                                    'name': channel['display_name'],
                                    'url': f"https://twitch.tv/{user['login']}",
                                    'language': user.get('broadcaster_language', ''),
                                    'avatar_url': user.get('profile_image_url', ''),
                                    'is_live': False,
                                    'broadcaster_type': broadcaster_type,
                                    'description': user.get('description', ''),
                                    'vtuber_score': score,
                                    'vtuber_reasons': reasons,
                                    'language_focus': language_focus,
                                    'discovered_at': datetime.now().isoformat()
                                }
                                vtubers.append(vtuber)
                        else:
                            if not name_matches:
                                name_mismatch += 1
                            else:
                                filtered_out += 1
            
            # Sort by VTuber score (highest first)
            vtubers.sort(key=lambda x: x.get('vtuber_score', 0), reverse=True)
            
            print(f"[INFO] Found {len(vtubers)} VTuber channels")
            print(f"[INFO] Filtered out {filtered_out} channels (not VTuber)")
            print(f"[INFO] Filtered out {name_mismatch} channels (name mismatch)")
            
            if debug and vtubers:
                print(f"[DEBUG] Top VTuber scores:")
                for vtuber in vtubers[:5]:
                    print(f"  {vtuber['name']}: {vtuber.get('vtuber_score', 0)} - {vtuber.get('language_focus', 'Unknown')}")
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error searching for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber_enhanced(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Enhanced VTuber search with multiple strategies"""
        
        try:
            print(f"[INFO] Starting enhanced search for VTuber: {vtuber_name}")
            
            results = []
            
            # Stage 1: Tag-based search (highest precision)
            print(f"[INFO] Stage 1: Tag-based search")
            tag_results = await self.find_vtuber_by_tags(vtuber_name, debug=debug)
            results.extend(tag_results)
            print(f"[INFO] Stage 1 found {len(tag_results)} results")
            
            # Stage 2: Fuzzy name search with relaxed VTuber filtering
            print(f"[INFO] Stage 2: Fuzzy name search")
            fuzzy_results = await self.find_vtuber_fuzzy(vtuber_name, debug=debug)
            results.extend(fuzzy_results)
            print(f"[INFO] Stage 2 found {len(fuzzy_results)} results")
            
            # Stage 3: Content-based search (analyze descriptions)
            print(f"[INFO] Stage 3: Content-based search")
            content_results = await self.find_vtuber_by_content(vtuber_name, debug=debug)
            results.extend(content_results)
            print(f"[INFO] Stage 3 found {len(content_results)} results")
            
            # Remove duplicates and sort by relevance
            unique_results = self.remove_duplicates(results)
            sorted_results = self.sort_by_relevance(unique_results)
            
            print(f"[INFO] Enhanced search completed. Total unique results: {len(sorted_results)}")
            return sorted_results
            
        except Exception as e:
            print(f"[ERROR] Error in enhanced search for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber_fuzzy(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTubers using fuzzy name matching with relaxed filtering"""
        
        try:
            print(f"[INFO] Fuzzy search for VTuber: {vtuber_name}")
            
            # Search for channels with broader query
            channels = await self.search_channels(vtuber_name, max_results=100)
            
            if not channels:
                return []
            
            # Get detailed user info
            user_ids = [ch['id'] for ch in channels]
            user_info = await self.get_user_info(user_ids)
            
            vtubers = []
            
            for channel in channels:
                user = next((u for u in user_info if u['id'] == channel['id']), None)
                if not user:
                    continue
                
                # Use fuzzy name matching
                name_matches = self.filters.is_name_match_fuzzy(
                    channel['display_name'], vtuber_name, debug=debug
                )
                
                if name_matches:
                    # Use adaptive scoring with lower threshold
                    combined_data = {**channel, **user}
                    is_vtuber = self.filters.is_vtuber_channel_adaptive(
                        combined_data, platform='twitch', debug=debug
                    )
                    
                    if is_vtuber:
                        score, reasons, threshold = self.filters.calculate_adaptive_score(
                            combined_data, platform='twitch'
                        )
                        
                        vtuber = {
                            'platform': 'twitch',
                            'id': channel['id'],
                            'name': channel['display_name'],
                            'url': f"https://twitch.tv/{user['login']}",
                            'language': user.get('broadcaster_language', ''),
                            'avatar_url': user.get('profile_image_url', ''),
                            'is_live': False,
                            'broadcaster_type': user.get('broadcaster_type', ''),
                            'description': user.get('description', ''),
                            'vtuber_score': score,
                            'vtuber_reasons': reasons,
                            'language_focus': self.filters.get_language_focus(combined_data, platform='twitch'),
                            'discovered_at': datetime.now().isoformat(),
                            'search_stage': 'fuzzy'
                        }
                        vtubers.append(vtuber)
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error in fuzzy search for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber_by_content(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTubers by analyzing content descriptions and titles"""
        
        try:
            print(f"[INFO] Content-based search for VTuber: {vtuber_name}")
            
            # Search for live streams to analyze content
            live_streams = await self.search_live_streams(vtuber_name, max_results=50)
            
            if not live_streams:
                return []
            
            # Get user info for streams
            user_ids = [stream['user_id'] for stream in live_streams]
            user_info = await self.get_user_info(user_ids)
            
            vtubers = []
            
            for stream in live_streams:
                user = next((u for u in user_info if u['id'] == stream['user_id']), None)
                if not user:
                    continue
                
                # Analyze stream title and description for VTuber content
                stream_title = stream.get('title', '').lower()
                user_description = user.get('description', '').lower()
                
                # Check for VTuber content indicators
                content_indicators = [
                    'vtuber', 'virtual', 'avatar', 'anime', 'live2d',
                    'kawaii', 'moe', 'otaku', 'japanese', 'character'
                ]
                
                has_vtuber_content = any(
                    indicator in stream_title or indicator in user_description
                    for indicator in content_indicators
                )
                
                if has_vtuber_content:
                    # Use name matching (can be more flexible for content-based search)
                    name_matches = self.filters.is_name_match(
                        user['display_name'], vtuber_name, debug=debug
                    )
                    
                    if name_matches:
                        combined_data = {**stream, **user}
                        score, reasons, threshold = self.filters.calculate_adaptive_score(
                            combined_data, platform='twitch'
                        )
                        
                        # Lower threshold for content-based results
                        if score >= max(threshold - 1, 1):
                            vtuber = {
                                'platform': 'twitch',
                                'id': stream['user_id'],
                                'name': user['display_name'],
                                'url': f"https://twitch.tv/{user['login']}",
                                'language': user.get('broadcaster_language', ''),
                                'avatar_url': user.get('profile_image_url', ''),
                                'is_live': True,
                                'broadcaster_type': user.get('broadcaster_type', ''),
                                'description': user.get('description', ''),
                                'stream_title': stream.get('title', ''),
                                'viewer_count': stream.get('viewer_count', 0),
                                'vtuber_score': score,
                                'vtuber_reasons': reasons,
                                'language_focus': self.filters.get_language_focus(combined_data, platform='twitch'),
                                'discovered_at': datetime.now().isoformat(),
                                'search_stage': 'content'
                            }
                            vtubers.append(vtuber)
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error in content-based search for '{vtuber_name}': {e}")
            return []
    
    def remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate VTubers based on user ID"""
        unique_results = {}
        
        for vtuber in results:
            vtuber_id = vtuber['id']
            if vtuber_id not in unique_results:
                unique_results[vtuber_id] = vtuber
            else:
                # Keep the one with higher score or more recent
                existing = unique_results[vtuber_id]
                if vtuber.get('vtuber_score', 0) > existing.get('vtuber_score', 0):
                    unique_results[vtuber_id] = vtuber
        
        return list(unique_results.values())
    
    def sort_by_relevance(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort results by relevance score"""
        
        def relevance_score(vtuber):
            score = vtuber.get('vtuber_score', 0)
            
            # Bonus for live streams
            if vtuber.get('is_live', False):
                score += 2
            
            # Bonus for verified channels
            if vtuber.get('broadcaster_type') in ['partner', 'affiliate']:
                score += 1
            
            # Bonus for high viewer count
            viewer_count = vtuber.get('viewer_count', 0)
            if viewer_count > 100:
                score += 0.5
            
            # Bonus for tag-based results (highest confidence)
            if vtuber.get('search_stage') == 'tags':
                score += 3
            
            return score
        
        return sorted(results, key=relevance_score, reverse=True)
    