from flask import Flask, render_template, request, jsonify
from app.config import Config
from app.scrapers import search_vtuber
import asyncio
import os
from pathlib import Path

app = Flask(__name__)

# Load configuration
config_path = Path(__file__).parent / 'config' / 'config.yaml'
config = Config(str(config_path))

@app.route('/')
def index():
    """Main search page"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Search for VTubers"""
    try:
        data = request.get_json()
        vtuber_name = data.get('query', '').strip()
        
        if not vtuber_name:
            return jsonify({'error': 'Please provide a VTuber name'}), 400
        
        # Get API credentials
        twitch_client_id = config.get_twitch_client_id()
        twitch_client_secret = config.get_twitch_client_secret()
        youtube_api_key = config.get_youtube_api_key()
        
        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                search_vtuber(
                    vtuber_name=vtuber_name,
                    twitch_client_id=twitch_client_id,
                    twitch_client_secret=twitch_client_secret,
                    youtube_api_key=youtube_api_key
                )
            )
        finally:
            loop.close()
        
        # Format results for frontend
        formatted_results = []
        
        # Add Twitch results
        for vtuber in results.get('twitch', []):
            formatted_results.append({
                'platform': 'twitch',
                'name': vtuber['name'],
                'url': vtuber['url'],
                'avatar_url': vtuber.get('avatar_url', ''),
                'is_live': vtuber.get('is_live', False),
                'language': vtuber.get('language', ''),
                'broadcaster_type': vtuber.get('broadcaster_type', '')
            })
        
        # Add YouTube results
        for vtuber in results.get('youtube', []):
            formatted_results.append({
                'platform': 'youtube',
                'name': vtuber['name'],
                'url': vtuber['url'],
                'avatar_url': vtuber.get('avatar_url', ''),
                'subscriber_count': vtuber.get('subscriber_count', '0'),
                'video_count': vtuber.get('video_count', '0'),
                'view_count': vtuber.get('view_count', '0')
            })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'total_results': len(formatted_results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host=config.get_flask_address(), port=config.get_flask_port())