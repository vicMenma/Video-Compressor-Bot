# config.py
import json
import os
from typing import Optional

class Config:
    # Load from config.json
    config_path = "config.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    else:
        config_data = {}
    
    # Bot Configuration
    API_ID: int = config_data.get("API_ID", 0)
    API_HASH: str = config_data.get("API_HASH", "")
    BOT_TOKEN: str = config_data.get("BOT_TOKEN", "")
    
    # User Configuration
    USER_ID: int = config_data.get("USER_ID", 0)
    DUMP_ID: int = config_data.get("DUMP_ID", 0)
    
    # Bot Settings
    MAX_FILE_SIZE: int = 2000 * 1024 * 1024  # 2GB
    MAX_QUEUE_SIZE: int = 5
    COMPRESSION_TIMEOUT: int = 3600  # 1 hour
    
    # Paths
    DOWNLOAD_PATH: str = "/content/downloads"
    COMPRESSED_PATH: str = "/content/compressed"
    THUMBNAIL_PATH: str = "/content/thumbnails"
    
    # FFmpeg presets
    COMPRESSION_PRESETS = {
        "ultra_fast": {
            "crf": "28",
            "preset": "ultrafast",
            "description": "Ultra Fast (Lowest Quality)"
        },
        "fast": {
            "crf": "26", 
            "preset": "fast",
            "description": "Fast (Low Quality)"
        },
        "medium": {
            "crf": "24",
            "preset": "medium", 
            "description": "Medium (Balanced)"
        },
        "slow": {
            "crf": "22",
            "preset": "slow",
            "description": "Slow (High Quality)"
        },
        "veryslow": {
            "crf": "20",
            "preset": "veryslow",
            "description": "Very Slow (Highest Quality)"
        }
    }
    
    # Resolution presets
    RESOLUTION_PRESETS = {
        "240p": "426x240",
        "360p": "640x360", 
        "480p": "854x480",
        "720p": "1280x720",
        "1080p": "1920x1080",
        "keep": "original"
    }
    
    # Audio bitrates
    AUDIO_BITRATES = {
        "32k": "32k",
        "64k": "64k", 
        "128k": "128k",
        "192k": "192k",
        "256k": "256k",
        "320k": "320k"
    }
    
    # Video bitrates
    VIDEO_BITRATES = {
        "100k": "100k",
        "500k": "500k",
        "1000k": "1000k", 
        "2000k": "2000k",
        "4000k": "4000k",
        "8000k": "8000k"
    }
    
    # Messages
    START_MSG = """
🎬 **Welcome to Video Compressor Bot!**

I can help you compress videos with various quality settings.

**Features:**
• Multiple compression presets
• Custom resolution options  
• Audio bitrate control
• Video bitrate control
• Thumbnail generation
• Progress tracking

Send me a video to get started!
    """
    
    HELP_MSG = """
🔧 **How to Use:**

1. Send any video file (up to 2GB)
2. Choose compression settings
3. Wait for processing
4. Download compressed video

**Commands:**
/start - Start the bot
/help - Show this help
/settings - Configure default settings
/queue - View compression queue
/cancel - Cancel current process

**Supported Formats:**
MP4, AVI, MKV, MOV, WMV, FLV, 3GP, WEBM
    """
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.DOWNLOAD_PATH,
            cls.COMPRESSED_PATH, 
            cls.THUMBNAIL_PATH
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        required_fields = ['API_ID', 'API_HASH', 'BOT_TOKEN', 'USER_ID']
        
        for field in required_fields:
            if not getattr(cls, field):
                print(f"❌ Missing required config: {field}")
                return False
        
        return True