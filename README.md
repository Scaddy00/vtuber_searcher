# VTuber Searcher

A powerful tool for discovering VTuber content creators across multiple platforms. This application searches for VTubers on Twitch and YouTube using intelligent filtering to ensure accurate and relevant results.

## 🎯 Features

### **Multi-Platform Search**
- **Twitch Integration**: Search for VTubers on Twitch with live streaming detection
- **YouTube Integration**: Search for VTubers on YouTube with detailed channel information
- **Parallel Processing**: Simultaneous searches across both platforms for faster results

### **Intelligent Filtering**
- **Name Matching**: Advanced name matching algorithm to ensure results correspond to the search query
- **VTuber Detection**: Smart filtering system that identifies likely VTuber channels
- **Quality Control**: Filters out irrelevant results and false positives

### **Comprehensive Results**
- **Detailed Information**: Channel names, URLs, avatars, subscriber counts, and more
- **Live Status**: Indicates if channels are currently live streaming (Twitch)
- **Statistics**: View counts, video counts, and subscriber information (YouTube)
- **Metadata**: Discovery timestamps and platform-specific data

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Twitch API credentials
- YouTube Data API v3 key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vtuber_searcher
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   
   Create a `config/config.yaml` file:
   ```yaml
   twitch:
     client_id: "your_twitch_client_id"
     client_secret: "your_twitch_client_secret"
   
   youtube:
     api_key: "your_youtube_api_key"
   ```

### Usage

```python
from app.scrapers import search_vtuber
import asyncio

async def main():
    # Search for a VTuber
    results = await search_vtuber(
        vtuber_name="example_vtuber",
        twitch_client_id="your_twitch_client_id",
        twitch_client_secret="your_twitch_client_secret",
        youtube_api_key="your_youtube_api_key",
        debug=True  # Enable debug logging
    )
    
    print(f"Found {results['total_results']} VTubers:")
    print(f"Twitch: {len(results['twitch'])} channels")
    print(f"YouTube: {len(results['youtube'])} channels")

# Run the search
asyncio.run(main())
```

## 🔧 Configuration

### API Setup

#### Twitch API
1. Go to [Twitch Developer Console](https://dev.twitch.tv/console)
2. Create a new application
3. Get your Client ID and Client Secret
4. Add them to `config/config.yaml`

#### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)
5. Add the API key to `config/config.yaml`

## 📊 Project Structure

```
vtuber_searcher/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   └── __init__.py          # Configuration loader
│   └── scrapers/
│       ├── __init__.py          # Main search function
│       ├── twitch_scraper.py    # Twitch API integration
│       └── youtube_scraper.py   # YouTube API integration
├── config/
│   └── config.yaml              # API configuration
├── app.py                       # Main application
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## 🧠 How It Works

### Search Process
1. **Query Processing**: Normalizes search terms for better matching
2. **Parallel API Calls**: Simultaneously searches both platforms
3. **Name Filtering**: Ensures results match the search query
4. **VTuber Detection**: Applies intelligent filtering to identify VTuber channels
5. **Result Aggregation**: Combines and deduplicates results

### Filtering Algorithm
- **Name Matching**: Exact, partial, and word-based matching
- **VTuber Scoring**: Multi-factor scoring system based on:
  - VTuber keywords in channel name/title
  - VTuber indicators in descriptions
  - Anime-related terms
  - Streaming/content creation terms
- **Quality Thresholds**: Configurable scoring thresholds per platform

### Debug Features
- **Detailed Logging**: Shows each step of the search process
- **Filter Analysis**: Explains why channels are included or excluded
- **Performance Metrics**: Tracks search time and result counts

## 📈 Example Results

```json
{
  "twitch": [
    {
      "platform": "twitch",
      "id": "123456789",
      "name": "ExampleVTuber",
      "url": "https://twitch.tv/examplevtuber",
      "language": "en",
      "avatar_url": "https://example.com/avatar.jpg",
      "is_live": true,
      "broadcaster_type": "partner",
      "description": "VTuber content creator...",
      "discovered_at": "2025-01-01T12:00:00.000000"
    }
  ],
  "youtube": [
    {
      "platform": "youtube",
      "id": "UC1234567890abcdef",
      "name": "Example VTuber Channel",
      "url": "https://youtube.com/channel/UC1234567890abcdef",
      "subscriber_count": "1000",
      "video_count": "50",
      "view_count": "100000",
      "discovered_at": "2025-01-01T12:00:00.000000"
    }
  ],
  "total_results": 2
}
```

## 🔍 Advanced Usage

### Debug Mode
Enable detailed logging to understand the search process:

```python
results = await search_vtuber(
    vtuber_name="example",
    twitch_client_id="...",
    twitch_client_secret="...",
    youtube_api_key="...",
    debug=True
)
```

### Custom Filtering
Modify the VTuber detection algorithm by editing the scraper classes:

```python
# In app/scrapers/twitch_scraper.py or youtube_scraper.py
self.vtuber_keywords = [
    'vtuber', 'virtual', 'avatar', 'anime', 'kawaii',
    # Add your custom keywords here
]
```

## 📋 Dependencies

- **aiohttp**: Asynchronous HTTP client for API requests
- **google-api-python-client**: YouTube Data API v3 client
- **pyyaml**: YAML configuration file parsing
- **asyncio**: Asynchronous programming support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the debug output for detailed information
2. Verify your API credentials are correct
3. Ensure all dependencies are installed
4. Check the API rate limits for your accounts

## 🔮 Future Enhancements

- **Database Integration**: Store and cache search results
- **Web Interface**: GUI for easier searching
- **More Platforms**: Support for additional streaming platforms
- **Advanced Analytics**: Search trends and VTuber discovery metrics
- **Real-time Updates**: Live monitoring of VTuber activity
