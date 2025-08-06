"""
Base scraper class for VTuber discovery
"""

import asyncio
from typing import List, Dict, Any, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from .vtuber_filters import VTuberFilters

class BaseScraper(ABC):
    """Base class for VTuber scrapers with common functionality"""
    
    def __init__(self):
        # Initialize VTuber filters
        self.filters = VTuberFilters()
    
    @abstractmethod
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to platform API"""
        pass
    
    @abstractmethod
    async def search_channels(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search for channels that match the query"""
        pass
    
    @abstractmethod
    async def get_user_info(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed user/channel information"""
        pass
    
    def _is_name_match(self, channel_name: str, search_name: str, debug: bool = False) -> bool:
        """Check if the channel name matches the search name"""
        return self.filters.is_name_match(channel_name, search_name, debug)
    
    def _is_name_match_fuzzy(self, channel_name: str, search_name: str, debug: bool = False) -> bool:
        """Check if the channel name matches the search name using fuzzy logic"""
        return self.filters.is_name_match_fuzzy(channel_name, search_name, debug)
    
    def _is_vtuber_channel(self, channel_data: Dict[str, Any], platform: str = 'twitch', debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber"""
        return self.filters.is_vtuber_channel_adaptive(channel_data, platform=platform, debug=debug)
    
    def remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate VTubers based on user/channel ID"""
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
    
    def sort_by_relevance(self, results: List[Dict[str, Any]], platform: str = 'twitch') -> List[Dict[str, Any]]:
        """Sort results by relevance score"""
        
        def relevance_score(vtuber):
            score = vtuber.get('vtuber_score', 0)
            
            if platform == 'twitch':
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
                    
            elif platform == 'youtube':
                # Bonus for high subscriber count
                subscriber_count = vtuber.get('subscriber_count', '0')
                try:
                    sub_count = int(subscriber_count)
                    if sub_count > 1000:
                        score += 1
                except (ValueError, TypeError):
                    pass
                
                # Bonus for high view count
                view_count = vtuber.get('view_count', '0')
                try:
                    views = int(view_count)
                    if views > 10000:
                        score += 0.5
                except (ValueError, TypeError):
                    pass
            
            # Bonus for tag-based results (highest confidence)
            if vtuber.get('search_stage') == 'tags':
                score += 3
            
            return score
        
        return sorted(results, key=relevance_score, reverse=True)
    
    async def find_vtuber_enhanced(self, vtuber_name: str, platform: str = 'twitch', debug: bool = False) -> List[Dict[str, Any]]:
        """Enhanced VTuber search with multiple strategies"""
        
        try:
            print(f"[INFO] Starting enhanced search for VTuber: {vtuber_name}")
            
            results = []
            
            # Stage 1: Tag-based search (if available)
            if hasattr(self, 'find_vtuber_by_tags'):
                print(f"[INFO] Stage 1: Tag-based search")
                tag_results = await self.find_vtuber_by_tags(vtuber_name, debug=debug)
                results.extend(tag_results)
                print(f"[INFO] Stage 1 found {len(tag_results)} results")
            
            # Stage 2: Fuzzy name search with relaxed VTuber filtering
            print(f"[INFO] Stage 2: Fuzzy name search")
            fuzzy_results = await self.find_vtuber_fuzzy(vtuber_name, platform=platform, debug=debug)
            results.extend(fuzzy_results)
            print(f"[INFO] Stage 2 found {len(fuzzy_results)} results")
            
            # Stage 3: Content-based search (analyze descriptions)
            print(f"[INFO] Stage 3: Content-based search")
            content_results = await self.find_vtuber_by_content(vtuber_name, platform=platform, debug=debug)
            results.extend(content_results)
            print(f"[INFO] Stage 3 found {len(content_results)} results")
            
            # Remove duplicates and sort by relevance
            unique_results = self.remove_duplicates(results)
            sorted_results = self.sort_by_relevance(unique_results, platform=platform)
            
            print(f"[INFO] Enhanced search completed. Total unique results: {len(sorted_results)}")
            return sorted_results
            
        except Exception as e:
            print(f"[ERROR] Error in enhanced search for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber_fuzzy(self, vtuber_name: str, platform: str = 'twitch', debug: bool = False) -> List[Dict[str, Any]]:
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
                name_matches = self._is_name_match_fuzzy(
                    channel.get('display_name', channel.get('snippet', {}).get('title', '')), 
                    vtuber_name, 
                    debug=debug
                )
                
                if name_matches:
                    # Use adaptive scoring with lower threshold
                    combined_data = {**channel, **user}
                    is_vtuber = self._is_vtuber_channel(combined_data, platform=platform, debug=debug)
                    
                    if is_vtuber:
                        score, reasons, threshold = self.filters.calculate_adaptive_score(
                            combined_data, platform=platform
                        )
                        
                        vtuber = self._create_vtuber_object(combined_data, platform, score, reasons, debug)
                        vtuber['search_stage'] = 'fuzzy'
                        vtubers.append(vtuber)
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error in fuzzy search for '{vtuber_name}': {e}")
            return []
    
    async def find_vtuber_by_content(self, vtuber_name: str, platform: str = 'twitch', debug: bool = False) -> List[Dict[str, Any]]:
        """Find VTubers by analyzing content descriptions and titles"""
        
        try:
            print(f"[INFO] Content-based search for VTuber: {vtuber_name}")
            
            # Search for live streams to analyze content (if available)
            if hasattr(self, 'search_live_streams'):
                live_streams = await self.search_live_streams(vtuber_name, max_results=50)
            else:
                # Fallback to channel search
                live_streams = await self.search_channels(vtuber_name, max_results=50)
            
            if not live_streams:
                return []
            
            # Get user info for streams/channels
            user_ids = [stream.get('user_id', stream.get('id')) for stream in live_streams]
            user_info = await self.get_user_info(user_ids)
            
            vtubers = []
            
            for stream in live_streams:
                user = next((u for u in user_info if u['id'] == stream.get('user_id', stream.get('id'))), None)
                if not user:
                    continue
                
                # Analyze stream/channel title and description for VTuber content
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
                    user_name = user.get('display_name', user.get('snippet', {}).get('title', ''))
                    name_matches = self._is_name_match(user_name, vtuber_name, debug=debug)
                    
                    if name_matches:
                        combined_data = {**stream, **user}
                        score, reasons, threshold = self.filters.calculate_adaptive_score(
                            combined_data, platform=platform
                        )
                        
                        # Lower threshold for content-based results
                        if score >= max(threshold - 1, 1):
                            vtuber = self._create_vtuber_object(combined_data, platform, score, reasons, debug)
                            vtuber['search_stage'] = 'content'
                            vtubers.append(vtuber)
            
            return vtubers
            
        except Exception as e:
            print(f"[ERROR] Error in content-based search for '{vtuber_name}': {e}")
            return []
    
    def _create_vtuber_object(self, data: Dict[str, Any], platform: str, score: int, reasons: str, debug: bool = False) -> Dict[str, Any]:
        """Create standardized VTuber object based on platform"""
        
        if platform == 'twitch':
            return {
                'platform': 'twitch',
                'id': data.get('id', data.get('user_id')),
                'name': data.get('display_name', ''),
                'url': f"https://twitch.tv/{data.get('login', '')}",
                'language': data.get('broadcaster_language', ''),
                'avatar_url': data.get('profile_image_url', ''),
                'is_live': data.get('is_live', False),
                'broadcaster_type': data.get('broadcaster_type', ''),
                'description': data.get('description', ''),
                'stream_title': data.get('title', ''),
                'viewer_count': data.get('viewer_count', 0),
                'vtuber_score': score,
                'vtuber_reasons': reasons,
                'language_focus': self.filters.get_language_focus(data, platform=platform),
                'discovered_at': datetime.now().isoformat()
            }
        elif platform == 'youtube':
            return {
                'platform': 'youtube',
                'id': data.get('id', ''),
                'name': data.get('snippet', {}).get('title', ''),
                'url': f"https://youtube.com/channel/{data.get('id', '')}",
                'language': data.get('snippet', {}).get('defaultLanguage', ''),
                'avatar_url': data.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url', ''),
                'subscriber_count': data.get('statistics', {}).get('subscriberCount', '0'),
                'video_count': data.get('statistics', {}).get('videoCount', '0'),
                'view_count': data.get('statistics', {}).get('viewCount', '0'),
                'description': data.get('snippet', {}).get('description', ''),
                'vtuber_score': score,
                'vtuber_reasons': reasons,
                'language_focus': self.filters.get_language_focus(data, platform=platform),
                'discovered_at': datetime.now().isoformat()
            }
        else:
            raise ValueError(f"Unsupported platform: {platform}") 