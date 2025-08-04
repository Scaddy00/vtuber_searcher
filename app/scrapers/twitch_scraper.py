"""
Twitch scraper for discovering VTuber content creators
"""

import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime

class TwitchScraper:
    """Scrapes Twitch for VTuber content creators"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.twitch.tv/helix"
        
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
    
    def _is_name_match(self, channel_name: str, search_name: str, debug: bool = False) -> bool:
        """Check if the channel name matches the search name"""
        
        # Normalize both names for comparison
        channel_lower = channel_name.lower().strip()
        search_lower = search_name.lower().strip()
        
        if debug:
            print(f"[DEBUG] Comparing: '{channel_lower}' vs '{search_lower}'")
        
        # Exact match (highest priority)
        if channel_lower == search_lower:
            if debug:
                print(f"[DEBUG] Exact match found!")
            return True
        
        # Check if search name is contained in channel name
        if search_lower in channel_lower:
            if debug:
                print(f"[DEBUG] Search name contained in channel name")
            return True
        
        # Check if channel name is contained in search name
        if channel_lower in search_lower:
            if debug:
                print(f"[DEBUG] Channel name contained in search name")
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
    
    def _is_vtuber_channel(self, channel_info: Dict[str, Any], user_info: Dict[str, Any]) -> bool:
        """Check if a channel is likely a VTuber based on various indicators"""
        
        # Get text to analyze
        display_name = channel_info.get('display_name', '').lower()
        title = channel_info.get('title', '').lower()
        description = user_info.get('description', '').lower()
        
        # Combine all text for analysis
        all_text = f"{display_name} {title} {description}".lower()
        
        # Check for VTuber keywords in name/title
        name_has_keywords = any(keyword in display_name for keyword in self.vtuber_keywords)
        title_has_keywords = any(keyword in title for keyword in self.vtuber_keywords)
        
        # Check for VTuber indicators in description
        desc_has_indicators = any(indicator in description for indicator in self.vtuber_indicators)
        
        # Check for anime-related terms
        anime_terms = ['anime', 'kawaii', 'moe', 'otaku', 'weeb', 'japanese']
        has_anime_terms = any(term in all_text for term in anime_terms)
        
        # Check for streaming/content creation terms
        streaming_terms = ['streamer', 'content creator', 'live', 'gaming', 'chat']
        has_streaming_terms = any(term in all_text for term in streaming_terms)
        
        # Scoring system
        score = 0
        
        if name_has_keywords:
            score += 3
        if title_has_keywords:
            score += 2
        if desc_has_indicators:
            score += 3
        if has_anime_terms:
            score += 1
        if has_streaming_terms:
            score += 1
        
        # Lower threshold for Twitch (more permissive) - changed from 2 to 1
        return score >= 1  # Changed from 2 to 1
    
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

    async def find_vtuber(self, vtuber_name: str, debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTuber content creators on Twitch (filtered for VTubers only)"""
        
        try:
            print(f"[INFO] Searching Twitch for: {vtuber_name}")
            
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
            
            # Process results with VTuber filtering
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
                    
                    if name_matches and self._is_vtuber_channel(channel, user):
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
                        
                        if name_matches and self._is_vtuber_channel(channel, user):
                            broadcaster_type = user.get('broadcaster_type', '')
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
                                    'discovered_at': datetime.now().isoformat()
                                }
                                vtubers.append(vtuber)
                        else:
                            if not name_matches:
                                name_mismatch += 1
                            else:
                                filtered_out += 1
            
            print(f"[INFO] Found {len(vtubers)} VTuber channels")
            print(f"[INFO] Filtered out {filtered_out} channels (not VTuber)")
            print(f"[INFO] Filtered out {name_mismatch} channels (name mismatch)")
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error searching for '{vtuber_name}': {e}")
            return []
    