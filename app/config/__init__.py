"""
Configuration loader for VTuber Searcher application
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List

class Config:
    """Loads and manages application configuration"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_twitch_client_id(self) -> str:
        """Get Twitch client ID"""
        return self.config.get('twitch', {}).get('client_id', '')
    
    def get_twitch_client_secret(self) -> str:
        """Get Twitch client secret"""
        return self.config.get('twitch', {}).get('client_secret', '')
    
    def get_youtube_api_key(self) -> str:
        """Get YouTube API key"""
        return self.config.get('youtube', {}).get('api_key', '')
    
    def get_database_path(self) -> str:
        """Get database path"""
        return self.config.get('database', {}).get('path', 'data/vtuber_searcher.db')
    
    def get_flask_address(self) -> str:
        """Get Flask address"""
        return self.config.get('flask', {}).get('address', '0.0.0.0')
    
    def get_flask_port(self) -> int:
        """Get Flask port"""
        return self.config.get('flask', {}).get('port', 5000)