"""
VTuber filtering system for Italian and English markets
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime

class VTuberFilters:
    """Centralized VTuber filtering system for Italian and English markets"""
    
    def __init__(self):
        # Enhanced VTuber-specific keywords for Italian and English markets
        self.vtuber_keywords_high = [
            'vtuber', 'virtual youtuber', 'virtual streamer', 'vtubing',
            'live2d', 'rigging', 'anime avatar', 'virtual avatar',
            'virtual idol', 'virtual personality', 'virtual character',
            # Italian specific
            'vtuber italiana', 'virtual youtuber italiana', 'streamer virtuale',
            'avatar virtuale', 'personaggio virtuale', 'idol virtuale'
        ]
        
        # Medium weight keywords for Italian and English markets
        self.vtuber_keywords_medium = [
            'anime', 'kawaii', 'moe', 'otaku', 'weeb', 'japanese',
            'virtual', 'avatar', 'character', 'model', 'streamer',
            # Italian specific
            'anime italiano', 'kawaii italiano', 'otaku italiano',
            'personaggio', 'modello', 'streamer italiano'
        ]
        
        # VTuber-related terms in descriptions (Italian and English focused)
        self.vtuber_indicators = [
            'vtuber', 'virtual youtuber', 'virtual streamer', 'anime avatar',
            'live2d', 'rigging', 'model', 'character', 'vtubing',
            'virtual idol', 'virtual personality', 'virtual character', 'anime streamer',
            # Italian specific
            'vtuber italiana', 'virtual youtuber italiana', 'streamer virtuale',
            'avatar anime', 'personaggio virtuale', 'idol virtuale', 'vtubing italiano'
        ]
        
        # Negative keywords for Italian and English markets
        self.negative_keywords = [
            'irl', 'face cam', 'real person', 'no avatar', 'camera',
            'real streamer', 'non-vtuber', 'human streamer',
            # Italian specific
            'persona reale', 'faccia vera', 'senza avatar', 'streamer reale',
            'non vtuber', 'streamer umano', 'webcam', 'faccia in diretta'
        ]
        
        # VTuber agencies and companies (Italian and English focused)
        self.vtuber_agencies = [
            # International agencies
            'hololive', 'nijisanji', 'vshojo', 'vspo', 'anycolor',
            '774inc', 'upd8', 'reality', 'neo-porte', 'v4mirai',
            'kamitsubaki', 'noripro', 'sugar lyric', 'prism project',
            # Italian agencies and groups
            'vtuber italia', 'vtuber italiani', 'virtual youtuber italia',
            'anime italia', 'otaku italia', 'vtuber community italia',
            'italian vtuber', 'italy vtuber', 'italian virtual youtuber'
        ]
        
        # Language-specific terms and patterns
        self.italian_terms = [
            'italiana', 'italiano', 'italia', 'roma', 'milano', 'napoli',
            'torino', 'bologna', 'firenze', 'venezia', 'genova', 'palermo',
            'città', 'regione', 'provincia', 'comune', 'italia'
        ]
        
        self.english_terms = [
            'english', 'british', 'american', 'canadian', 'australian',
            'uk', 'usa', 'canada', 'australia', 'england', 'london',
            'new york', 'los angeles', 'toronto', 'sydney'
        ]
        
        # Common Italian and English VTuber name patterns
        self.name_patterns = [
            # Italian patterns
            r'[A-Za-z]+_ITA', r'[A-Za-z]+_Italia', r'[A-Za-z]+_Italian',
            r'ITA_[A-Za-z]+', r'Italia_[A-Za-z]+', r'Italian_[A-Za-z]+',
            # English patterns
            r'[A-Za-z]+_EN', r'[A-Za-z]+_English', r'[A-Za-z]+_UK',
            r'EN_[A-Za-z]+', r'English_[A-Za-z]+', r'UK_[A-Za-z]+',
            # Common suffixes
            r'[A-Za-z]+_VT', r'[A-Za-z]+_Vtuber', r'[A-Za-z]+_Virtual',
            r'VT_[A-Za-z]+', r'Vtuber_[A-Za-z]+', r'Virtual_[A-Za-z]+'
        ]
    
    def is_name_match(self, channel_name: str, search_name: str, debug: bool = False) -> bool:
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
            if match_percentage >= 0.6:
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
    
    def is_name_match_fuzzy(self, channel_name: str, search_name: str, threshold: float = 0.6, debug: bool = False) -> bool:
        """Enhanced name matching with fuzzy logic - more restrictive for better precision"""
        
        # Normalize names
        channel_clean = re.sub(r'[^\w\s]', '', channel_name.lower())
        search_clean = re.sub(r'[^\w\s]', '', search_name.lower())
        
        if debug:
            print(f"[DEBUG] Fuzzy matching: '{channel_clean}' vs '{search_clean}'")
        
        # Exact match (highest priority)
        if channel_clean == search_clean:
            if debug:
                print(f"[DEBUG] Exact match found!")
            return True
        
        # Check if search name is contained in channel name (but not just a common word)
        if search_clean in channel_clean:
            # Avoid matching common words like "gamer", "tv", "official", etc.
            common_words = ['gamer', 'tv', 'official', 'channel', 'live', 'stream', 'youtube', 'twitch']
            if search_clean not in common_words:
                if debug:
                    print(f"[DEBUG] Search name contained in channel name")
                return True
            else:
                if debug:
                    print(f"[DEBUG] Ignoring common word match: '{search_clean}'")
        
        # Check if channel name is contained in search name
        if channel_clean in search_clean:
            if debug:
                print(f"[DEBUG] Channel name contained in search name")
            return True
        
        # Word-based matching (more restrictive)
        search_words = search_clean.split()
        channel_words = channel_clean.split()
        
        if debug:
            print(f"[DEBUG] Search words: {search_words}")
            print(f"[DEBUG] Channel words: {channel_words}")
        
        # If search name has multiple words, check if most words match
        if len(search_words) > 1:
            matching_words = sum(1 for word in search_words if any(word in cw for cw in channel_words))
            match_percentage = matching_words / len(search_words)
            if debug:
                print(f"[DEBUG] Matching words: {matching_words}/{len(search_words)} ({match_percentage:.2f})")
            if match_percentage >= 0.7:  # Higher threshold for better precision
                return True
        
        # Single word search - more restrictive matching
        if len(search_words) == 1:
            search_word = search_words[0]
            # Avoid matching common words
            common_words = ['gamer', 'tv', 'official', 'channel', 'live', 'stream', 'youtube', 'twitch', 'vtuber', 'virtual']
            if search_word in common_words:
                if debug:
                    print(f"[DEBUG] Ignoring common word: '{search_word}'")
                return False
            
            # Check if the search word appears in any channel word (but be more restrictive)
            for channel_word in channel_words:
                # Only match if the word is substantial (not just a few characters)
                if len(search_word) >= 4 and len(channel_word) >= 4:
                    if search_word in channel_word or channel_word in search_word:
                        if debug:
                            print(f"[DEBUG] Substantial word match: '{search_word}' in '{channel_word}'")
                        return True
        
        # Check for partial word matches (more restrictive)
        for search_word in search_words:
            for channel_word in channel_words:
                # Only match if words are substantial and share a significant prefix
                if (len(search_word) >= 4 and len(channel_word) >= 4 and
                    (search_word[:4] in channel_word or channel_word[:4] in search_word)):
                    if debug:
                        print(f"[DEBUG] Substantial partial word match: '{search_word}' ~ '{channel_word}'")
                    return True
        
        if debug:
            print(f"[DEBUG] No fuzzy match found")
        
        return False
    
    def detect_language_focus(self, text: str) -> Tuple[int, str]:
        """Detect if text is focused on Italian or English VTuber content"""
        text_lower = text.lower()
        
        italian_score = 0
        english_score = 0
        reasons = []
        
        # Check for Italian terms
        italian_matches = [term for term in self.italian_terms if term in text_lower]
        if italian_matches:
            italian_score += 3
            reasons.append(f"Italian terms: {italian_matches}")
        
        # Check for English terms
        english_matches = [term for term in self.english_terms if term in text_lower]
        if english_matches:
            english_score += 2
            reasons.append(f"English terms: {english_matches}")
        
        # Check for language patterns in names
        for pattern in self.name_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if '_ITA' in pattern or '_Italia' in pattern or '_Italian' in pattern:
                    italian_score += 2
                    reasons.append(f"Italian name pattern: {pattern}")
                elif '_EN' in pattern or '_English' in pattern or '_UK' in pattern:
                    english_score += 2
                    reasons.append(f"English name pattern: {pattern}")
        
        # Check for language indicators in descriptions
        if 'italiano' in text_lower or 'italiana' in text_lower:
            italian_score += 1
            reasons.append("Italian language indicator")
        
        if 'english' in text_lower or 'british' in text_lower or 'american' in text_lower:
            english_score += 1
            reasons.append("English language indicator")
        
        return max(italian_score, english_score), '; '.join(reasons)
    
    def calculate_vtuber_score(self, channel_data: Dict[str, Any], platform: str = 'twitch') -> Tuple[int, str]:
        """Calculate VTuber likelihood score with Italian/English focus"""
        
        # Extract text based on platform
        if platform == 'twitch':
            display_name = channel_data.get('display_name', '').lower()
            title = channel_data.get('title', '').lower()
            description = channel_data.get('description', '').lower()
        elif platform == 'youtube':
            display_name = channel_data.get('snippet', {}).get('title', '').lower()
            title = ''  # YouTube doesn't have separate title
            description = channel_data.get('snippet', {}).get('description', '').lower()
        else:
            display_name = channel_data.get('name', '').lower()
            title = channel_data.get('title', '').lower()
            description = channel_data.get('description', '').lower()
        
        # Combine all text for analysis
        all_text = f"{display_name} {title} {description}".lower()
        
        score = 0
        reasons = []
        
        # Check for high-weight VTuber keywords in name/title
        name_high_keywords = [kw for kw in self.vtuber_keywords_high if kw in display_name]
        title_high_keywords = [kw for kw in self.vtuber_keywords_high if kw in title]
        
        if name_high_keywords:
            score += 5
            reasons.append(f"High VTuber keywords in name: {name_high_keywords}")
        
        if title_high_keywords:
            score += 4
            reasons.append(f"High VTuber keywords in title: {title_high_keywords}")
        
        # Check for medium-weight keywords
        name_medium_keywords = [kw for kw in self.vtuber_keywords_medium if kw in display_name]
        title_medium_keywords = [kw for kw in self.vtuber_keywords_medium if kw in title]
        
        if name_medium_keywords:
            score += 2
            reasons.append(f"Medium VTuber keywords in name: {name_medium_keywords}")
        
        if title_medium_keywords:
            score += 1
            reasons.append(f"Medium VTuber keywords in title: {title_medium_keywords}")
        
        # Check for VTuber indicators in description
        desc_indicators = [ind for ind in self.vtuber_indicators if ind in description]
        if desc_indicators:
            score += 4
            reasons.append(f"VTuber indicators in description: {desc_indicators}")
        
        # Check for VTuber agencies (strong indicator)
        agency_matches = [agency for agency in self.vtuber_agencies if agency in all_text]
        if agency_matches:
            score += 6
            reasons.append(f"VTuber agency detected: {agency_matches}")
        
        # Check for Italian/English focus (bonus for target markets)
        language_score, language_reasons = self.detect_language_focus(all_text)
        if language_score > 0:
            score += language_score
            reasons.append(f"Language focus: {language_reasons}")
        
        # Check for negative keywords (reduce score)
        negative_matches = [neg for neg in self.negative_keywords if neg in all_text]
        if negative_matches:
            score -= 5  # Increased penalty for negative indicators
            reasons.append(f"Negative indicators: {negative_matches}")
        
        # Additional penalty for clearly non-VTuber content
        non_vtuber_indicators = ['gaming', 'gameplay', 'review', 'tutorial', 'news', 'music', 'cooking', 'fitness']
        non_vtuber_matches = [ind for ind in non_vtuber_indicators if ind in all_text]
        if non_vtuber_matches and not any(vt in all_text for vt in self.vtuber_keywords_high + self.vtuber_keywords_medium):
            score -= 3
            reasons.append(f"Non-VTuber content indicators: {non_vtuber_matches}")
        
        # Check for anime-related terms (bonus)
        anime_terms = ['anime', 'kawaii', 'moe', 'otaku', 'weeb', 'japanese', 'manga']
        anime_matches = [term for term in anime_terms if term in all_text]
        if anime_matches:
            score += 1
            reasons.append(f"Anime-related terms: {anime_matches}")
        
        # Check for streaming/content creation terms (minor bonus)
        streaming_terms = ['streamer', 'content creator', 'live', 'gaming', 'chat']
        streaming_matches = [term for term in streaming_terms if term in all_text]
        if streaming_matches:
            score += 0.5
            reasons.append(f"Streaming terms: {streaming_matches}")
        
        # Check for emoji patterns common in VTuber names
        emoji_pattern = re.compile(r'[^\w\s]')
        emoji_matches = emoji_pattern.findall(display_name)
        if emoji_matches:
            score += 1
            reasons.append(f"Emoji/characters in name: {emoji_matches}")
        
        # Penalty for "gamer" channels without VTuber indicators
        if 'gamer' in display_name.lower() and not any(vt in all_text for vt in self.vtuber_keywords_high + self.vtuber_keywords_medium):
            score -= 2
            reasons.append("Gamer channel without VTuber indicators")
        
        # Check for Japanese characters (still relevant for anime VTubers)
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        if japanese_pattern.search(all_text):
            score += 1
            reasons.append("Japanese characters detected")
        
        return score, '; '.join(reasons)
    
    def calculate_vtuber_score_with_tags(self, channel_data: Dict[str, Any], tags: List[str] = None, platform: str = 'twitch') -> Tuple[int, str]:
        """Calculate VTuber likelihood score including tag analysis"""
        
        # Get base score
        base_score, base_reasons = self.calculate_vtuber_score(channel_data, platform)
        
        # Add tag-based scoring
        tag_score = 0
        tag_reasons = []
        
        if tags:
            # VTuber-specific tags (high weight)
            vtuber_tags = ['vtuber', 'virtual youtuber', 'virtual streamer', 'vtubing', 'live2d', 'virtual avatar']
            found_vtuber_tags = [tag.lower() for tag in tags if any(vt in tag.lower() for vt in vtuber_tags)]
            
            if found_vtuber_tags:
                tag_score += 8  # Very high weight for tag-based detection
                tag_reasons.append(f"VTuber tags detected: {found_vtuber_tags}")
            
            # Anime-related tags (medium weight)
            anime_tags = ['anime', 'kawaii', 'moe', 'otaku', 'japanese', 'manga']
            found_anime_tags = [tag.lower() for tag in tags if any(at in tag.lower() for at in anime_tags)]
            
            if found_anime_tags:
                tag_score += 3
                tag_reasons.append(f"Anime tags detected: {found_anime_tags}")
            
            # Italian/English specific tags
            italian_tags = ['italiana', 'italiano', 'italia', 'italian']
            found_italian_tags = [tag.lower() for tag in tags if any(it in tag.lower() for it in italian_tags)]
            
            if found_italian_tags:
                tag_score += 2
                tag_reasons.append(f"Italian tags detected: {found_italian_tags}")
            
            english_tags = ['english', 'british', 'american', 'uk', 'usa']
            found_english_tags = [tag.lower() for tag in tags if any(et in tag.lower() for et in english_tags)]
            
            if found_english_tags:
                tag_score += 2
                tag_reasons.append(f"English tags detected: {found_english_tags}")
        
        total_score = base_score + tag_score
        all_reasons = [base_reasons]
        if tag_reasons:
            all_reasons.extend(tag_reasons)
        
        return total_score, '; '.join(all_reasons)
    
    def is_vtuber_channel(self, channel_data: Dict[str, Any], platform: str = 'twitch', debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber based on enhanced scoring"""
        
        score, reasons = self.calculate_vtuber_score(channel_data, platform)
        
        if debug:
            channel_name = channel_data.get('display_name', channel_data.get('snippet', {}).get('title', 'Unknown'))
            print(f"[DEBUG] VTuber score for '{channel_name}': {score}")
            print(f"[DEBUG] Reasons: {reasons}")
        
        # Adaptive threshold based on platform
        if platform == 'youtube':
            # Balanced threshold for YouTube (not too permissive)
            threshold = 2.5
        else:
            # Higher threshold for better precision on other platforms
            threshold = 3
        
        return score >= threshold
    
    def is_vtuber_channel_with_tags(self, channel_data: Dict[str, Any], tags: List[str] = None, platform: str = 'twitch', debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber including tag analysis"""
        
        score, reasons = self.calculate_vtuber_score_with_tags(channel_data, tags, platform)
        
        if debug:
            channel_name = channel_data.get('display_name', channel_data.get('snippet', {}).get('title', 'Unknown'))
            print(f"[DEBUG] VTuber score (with tags) for '{channel_name}': {score}")
            print(f"[DEBUG] Reasons: {reasons}")
            if tags:
                print(f"[DEBUG] Tags: {tags}")
        
        # Adaptive threshold based on platform and tags
        if platform == 'youtube':
            # Much lower threshold for YouTube (more permissive)
            threshold = 1.0 if tags else 1.5
        else:
            # Lower threshold when tags are available (more confident)
            threshold = 2 if tags else 3
        
        return score >= threshold
    
    def get_language_focus(self, channel_data: Dict[str, Any], platform: str = 'twitch') -> str:
        """Get the language focus of a channel"""
        if platform == 'twitch':
            text = f"{channel_data.get('display_name', '')} {channel_data.get('description', '')}"
        elif platform == 'youtube':
            text = f"{channel_data.get('snippet', {}).get('title', '')} {channel_data.get('snippet', {}).get('description', '')}"
        else:
            text = f"{channel_data.get('name', '')} {channel_data.get('description', '')}"
        
        language_score, language_reasons = self.detect_language_focus(text)
        return language_reasons if language_score > 0 else 'International' 

    def has_vtuber_tags(self, tags: List[str]) -> Tuple[bool, List[str]]:
        """Check if tags contain VTuber-related tags"""
        if not tags:
            return False, []
        
        vtuber_tag_indicators = [
            'vtuber', 'virtual youtuber', 'virtual streamer', 'vtubing',
            'live2d', 'virtual avatar', 'anime avatar', 'virtual idol',
            'virtual personality', 'virtual character'
        ]
        
        found_tags = []
        for tag in tags:
            tag_lower = tag.lower()
            for indicator in vtuber_tag_indicators:
                if indicator in tag_lower:
                    found_tags.append(tag)
                    break
        
        return len(found_tags) > 0, found_tags
    
    def is_vtuber_by_tags_only(self, tags: List[str]) -> bool:
        """Check if channel is VTuber based solely on tags (highest priority)"""
        has_tags, found_tags = self.has_vtuber_tags(tags)
        return has_tags 

    def calculate_adaptive_score(self, channel_data: Dict[str, Any], platform: str = 'twitch') -> Tuple[int, str]:
        """Calculate VTuber score with adaptive thresholds and dynamic bonuses"""
        
        # Get base score
        base_score, base_reasons = self.calculate_vtuber_score(channel_data, platform)
        
        # Adaptive scoring based on platform and context
        adaptive_reasons = []
        
        if platform == 'twitch':
            # Lower threshold for Twitch (more VTuber activity)
            threshold = 2
            # Bonus for live streaming
            if channel_data.get('is_live', False):
                base_score += 1
                adaptive_reasons.append("Live streaming bonus")
            
            # Bonus for verified/partner channels
            broadcaster_type = channel_data.get('broadcaster_type', '')
            if broadcaster_type in ['partner', 'affiliate']:
                base_score += 2
                adaptive_reasons.append(f"Verified channel bonus ({broadcaster_type})")
            
            # Bonus for high viewer count (indicates established VTuber)
            viewer_count = channel_data.get('viewer_count', 0)
            if viewer_count > 100:
                base_score += 1
                adaptive_reasons.append(f"High viewer count bonus ({viewer_count})")
            
        else:  # YouTube
            # Balanced threshold for YouTube (not too permissive)
            threshold = 2.0
            
            # Bonus for high subscriber count
            subscriber_count = channel_data.get('subscriber_count', '0')
            try:
                sub_count = int(subscriber_count)
                if sub_count > 1000:
                    base_score += 1
                    adaptive_reasons.append(f"High subscriber count bonus ({sub_count})")
            except (ValueError, TypeError):
                pass
        
        # Bonus for recent activity (VTubers are typically active)
        discovered_at = channel_data.get('discovered_at')
        if discovered_at:
            try:
                discovery_time = datetime.fromisoformat(discovered_at.replace('Z', '+00:00'))
                if (datetime.now() - discovery_time).days < 7:
                    base_score += 0.5
                    adaptive_reasons.append("Recent activity bonus")
            except (ValueError, TypeError):
                pass
        
        # Combine reasons
        all_reasons = [base_reasons]
        if adaptive_reasons:
            all_reasons.extend(adaptive_reasons)
        
        return base_score, '; '.join(all_reasons), threshold
    
    def is_vtuber_channel_adaptive(self, channel_data: Dict[str, Any], platform: str = 'twitch', debug: bool = False) -> bool:
        """Check if a channel is likely a VTuber using adaptive scoring"""
        
        score, reasons, threshold = self.calculate_adaptive_score(channel_data, platform)
        
        if debug:
            channel_name = channel_data.get('display_name', channel_data.get('snippet', {}).get('title', 'Unknown'))
            print(f"[DEBUG] Adaptive VTuber score for '{channel_name}': {score} (threshold: {threshold})")
            print(f"[DEBUG] Reasons: {reasons}")
        
        # For YouTube, use slightly lower threshold but not too permissive
        if platform == 'youtube' and score < threshold:
            # Allow channels with moderate scores for YouTube (but not too low)
            if score >= 1.5:
                if debug:
                    print(f"[DEBUG] Allowing YouTube channel with moderate score: {score}")
                return True
        
        return score >= threshold 