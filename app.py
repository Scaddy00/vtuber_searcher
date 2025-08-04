from app.config import Config
from app.scrapers import search_vtuber
import asyncio
from os import path
import json

async def main():
    config = Config(path.join(path.dirname(__file__), 'config/config.yaml'))
    
    vtuber_name = "claneko"
    twitch_client_id = config.get_twitch_client_id()
    twitch_client_secret = config.get_twitch_client_secret()
    youtube_api_key = config.get_youtube_api_key()
    
    # Attiva il debug per vedere cosa succede
    results = await search_vtuber(vtuber_name, twitch_client_id, twitch_client_secret, youtube_api_key, debug=False)
    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    asyncio.run(main())