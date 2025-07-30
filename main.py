# @title 🎥 Video Compressor Bot

# @title Main Configuration
# @markdown <div><center><h3>🎬 Telegram Video Compressor Bot</h3></center></div>
# @markdown <center><h4>Compress videos directly in Google Colab</h4></center>

# @markdown <br>

API_ID = 0  # @param {type: "integer"}
API_HASH = ""  # @param {type: "string"}
BOT_TOKEN = ""  # @param {type: "string"}
USER_ID = 0  # @param {type: "integer"}
DUMP_ID = 0  # @param {type: "integer"}

import subprocess
import time
import json
import shutil
import os
import asyncio
from IPython.display import clear_output
from threading import Thread

Working = True

banner = '''
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
'''

print(banner)

def Loading():
    chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while Working:
        for char in chars:
            print(f"\r{char} Setting up Video Compressor Bot...", end="", flush=True)
            time.sleep(0.1)
    clear_output()

_Thread = Thread(target=Loading, name="Setup", args=())
_Thread.start()

# Validate DUMP_ID format
if len(str(DUMP_ID)) == 10 and "-100" not in str(DUMP_ID):
    n_dump = "-100" + str(DUMP_ID)
    DUMP_ID = int(n_dump)

# Clean up sample data
if os.path.exists("/content/sample_data"):
    shutil.rmtree("/content/sample_data")

# Clone repository
print("\r📥 Cloning repository...")
cmd = "git clone https://github.com/YourUsername/Video-Compressor-Bot"
proc = subprocess.run(cmd, shell=True, capture_output=True)

# Create the bot directory structure
os.makedirs("/content/Video-Compressor-Bot", exist_ok=True)
os.makedirs("/content/Video-Compressor-Bot/bot", exist_ok=True)
os.makedirs("/content/Video-Compressor-Bot/utils", exist_ok=True)
os.makedirs("/content/Video-Compressor-Bot/plugins", exist_ok=True)

# Install dependencies
print("\r📦 Installing dependencies...")
cmd = "apt update && apt install -y ffmpeg aria2 mediainfo"
proc = subprocess.run(cmd, shell=True, capture_output=False)

# Install Python packages
packages = [
    "pyrogram==2.0.106",
    "tgcrypto",
    "Pillow",
    "psutil",
    "humanfriendly",
    "aiofiles",
    "motor",
    "dnspython",
    "python-dotenv",
    "pyromod"
]

for package in packages:
    subprocess.run(f"pip install {package}", shell=True, capture_output=True)

# Create credentials
credentials = {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "USER_ID": USER_ID,
    "DUMP_ID": DUMP_ID,
}

with open('/content/Video-Compressor-Bot/config.json', 'w') as file:
    json.dump(credentials, file, indent=4)

Working = False

# Create main bot files
print("\r🔧 Creating bot files...")

# Create main.py
main_py_content = """
import asyncio
import logging
from pyrogram import Client
from bot.config import Config
from bot.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CompressorBot:
    def __init__(self):
        self.app = Client(
            "VideoCompressorBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins")
        )
        self.db = Database()
    
    async def start(self):
        await self.app.start()
        await self.db.connect()
        print("🤖 Video Compressor Bot Started Successfully!")
        
    async def stop(self):
        await self.app.stop()
        await self.db.disconnect()

if __name__ == "__main__":
    bot = CompressorBot()
    asyncio.get_event_loop().run_until_complete(bot.start())
    asyncio.get_event_loop().run_forever()
"""

with open('/content/Video-Compressor-Bot/main.py', 'w') as f:
    f.write(main_py_content)

print("\r✅ Video Compressor Bot setup complete!")
print("\n🚀 Starting bot...")

# Change to bot directory and run
os.chdir('/content/Video-Compressor-Bot')
subprocess.run("python main.py", shell=True)