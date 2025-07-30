# main.py
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, ApiIdPublishedFlood, AccessTokenInvalid

# Import bot components
from bot.config import Config
from bot.database import Database
from utils.helpers import check_ffmpeg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class VideoCompressorBot:
    def __init__(self):
        """Initialize the Video Compressor Bot"""
        self.app = None
        self.db = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize bot components"""
        try:
            # Validate configuration
            if not Config.validate_config():
                logger.error("❌ Invalid configuration. Please check your settings.")
                return False
            
            # Create necessary directories
            Config.create_directories()
            
            # Check FFmpeg availability
            if not await check_ffmpeg():
                logger.error("❌ FFmpeg not found. Please install FFmpeg.")
                return False
            
            # Initialize database
            self.db = Database()
            await self.db.connect()
            
            # Initialize Pyrogram client
            self.app = Client(
                name="VideoCompressorBot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN,
                plugins=dict(root="plugins"),
                workdir=str(project_root)
            )
            
            logger.info("✅ Bot components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        try:
            if not await self.initialize():
                return False
            
            await self.app.start()
            self.is_running = True
            
            # Get bot info
            bot_info = await self.app.get_me()
            logger.info(f"🤖 Bot started successfully: @{bot_info.username}")
            logger.info(f"👤 Authorized user: {Config.USER_ID}")
            logger.info(f"📁 Dump channel: {Config.DUMP_ID}")
            
            # Send startup notification
            try:
                startup_msg = f"""
🚀 **Video Compressor Bot Started!**

**Bot:** @{bot_info.username}
**Version:** 2.0
**Status:** Online ✅

**Features:**
• Multiple compression presets
• Custom quality settings
• Progress tracking
• Queue management
• Statistics tracking

Ready to compress videos!
"""
                await self.app.send_message(Config.USER_ID, startup_msg)
            except Exception as e:
                logger.warning(f"Could not send startup notification: {e}")
            
            return True
            
        except ApiIdInvalid:
            logger.error("❌ Invalid API ID. Please check your configuration.")
            return False
        except ApiIdPublishedFlood:
            logger.error("❌ API ID published flood. Please wait and try again.")
            return False
        except AccessTokenInvalid:
            logger.error("❌ Invalid bot token. Please check your bot token.")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            return False
    
    async def stop(self):
        """Stop the bot"""
        try:
            if self.is_running:
                self.is_running = False
                
                # Send shutdown notification
                try:
                    await self.app.send_message(
                        Config.USER_ID, 
                        "🛑 **Video Compressor Bot Stopped**\n\nBot is now offline."
                    )
                except:
                    pass
                
                # Stop Pyrogram client
                if self.app:
                    await self.app.stop()
                
                # Disconnect database
                if self.db:
                    await self.db.disconnect()
                
                logger.info("🛑 Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")
    
    async def run(self):
        """Run the bot with error handling"""
        try:
            if await self.start():
                logger.info("🎬 Video Compressor Bot is running...")
                logger.info("📋 Send /start to begin compressing videos")
                logger.info("⏹️ Press Ctrl+C to stop the bot")
                
                # Keep the bot running
                while self.is_running:
                    await asyncio.sleep(1)
            else:
                logger.error("❌ Failed to start bot")
                return False
                
        except KeyboardInterrupt:
            logger.info("🛑 Received stop signal...")
            await self.stop()
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            await self.stop()
            return False
        
        return True

async def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║    ██╗   ██╗██╗██████╗ ███████╗ ██████╗      ██████╗ ██████╗ ███╗   ███╗██████╗ ║
║    ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗║
║    ██║   ██║██║██║  ██║█████╗  ██║   ██║    ██║     ██║   ██║██╔████╔██║██████╔╝║
║    ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ║
║     ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ║
║      ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ║
║                                                                                  ║
║                          🎬 TELEGRAM VIDEO COMPRESSOR 🎬                        ║
║                                  v2.0 - 2025                                    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create and run bot
    bot = VideoCompressorBot()
    success = await bot.run()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)