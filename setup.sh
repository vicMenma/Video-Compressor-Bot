# setup.sh - Installation script
#!/bin/bash

echo "🎬 Video Compressor Bot Setup"
echo "============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on Google Colab
if [ -d "/content" ]; then
    echo -e "${BLUE}Detected Google Colab environment${NC}"
    COLAB=true
    BASE_DIR="/content/Video-Compressor-Bot"
else
    echo -e "${BLUE}Detected local environment${NC}"
    COLAB=false
    BASE_DIR="$(pwd)"
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Update system packages
echo -e "${BLUE}📦 Updating system packages...${NC}"
if [ "$COLAB" = true ]; then
    apt-get update -qq
    apt-get install -y -qq ffmpeg aria2 mediainfo
else
    # Check if we have sudo
    if command -v sudo >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq ffmpeg aria2 mediainfo
    else
        print_warning "Cannot install system packages without sudo. Please install ffmpeg, aria2, and mediainfo manually."
    fi
fi

# Check if Python 3.8+ is installed
echo -e "${BLUE}🐍 Checking Python version...${NC}"
if ! command -v python3 >/dev/null 2>&1; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [ "$(printf '3.8\n%s\n' "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]; then
    print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi
print_status "Python $PYTHON_VERSION found"

# Create virtual environment
echo -e "${BLUE}🏗️ Creating virtual environment...${NC}"
if [ "$COLAB" = false ]; then
    python3 -m venv venv
    source venv/bin/activate
    print_status "Virtual environment created and activated"
fi

# Install Python packages
echo -e "${BLUE}📋 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
print_status "Python dependencies installed"

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p downloads compressed thumbnails logs data temp
print_status "Directories created"

# Check FFmpeg installation
echo -e "${BLUE}🎥 Verifying FFmpeg installation...${NC}"
if command -v ffmpeg >/dev/null 2>&1; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    print_status "FFmpeg $FFMPEG_VERSION is installed"
else
    print_error "FFmpeg is not installed or not in PATH"
    exit 1
fi

# Create config template if it doesn't exist
if [ ! -f "config.json" ]; then
    echo -e "${BLUE}⚙️ Creating configuration template...${NC}"
    cat > config.json << EOL
{
    "API_ID": 0,
    "API_HASH": "",
    "BOT_TOKEN": "",
    "USER_ID": 0,
    "DUMP_ID": 0
}
EOL
    print_warning "Please edit config.json with your bot credentials"
fi

# Create systemd service file (for non-Colab environments)
if [ "$COLAB" = false ] && command -v systemctl >/dev/null 2>&1; then
    echo -e "${BLUE}🔧 Creating systemd service...${NC}"
    cat > video-compressor-bot.service << EOL
[Unit]
Description=Video Compressor Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BASE_DIR
Environment=PATH=$BASE_DIR/venv/bin
ExecStart=$BASE_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL
    print_status "Systemd service file created (video-compressor-bot.service)"
fi

echo -e "${GREEN}"
echo "🎉 Setup completed successfully!"
echo "================================"
echo -e "${NC}"
echo "Next steps:"
echo "1. Edit config.json with your bot credentials"
echo "2. Run: python main.py"
if [ "$COLAB" = false ]; then
    echo "3. (Optional) Install service: sudo cp video-compressor-bot.service /etc/systemd/system/"
fi
echo ""
echo -e "${BLUE}For help, check the README.md file${NC}"

# README.md content
cat > README.md << 'EOL'
# 🎬 Video Compressor Telegram Bot

A powerful Telegram bot for compressing videos with multiple quality presets and custom settings, designed to work seamlessly on Google Colab and local environments.

## ✨ Features

- **Multiple Compression Presets**: Ultra Fast, Fast, Medium, Slow, Very Slow
- **Custom Resolution Options**: 240p, 360p, 480p, 720p, 1080p, or keep original
- **Flexible Bitrate Control**: Audio and video bitrate customization
- **Progress Tracking**: Real-time compression progress updates
- **Queue Management**: Handle multiple compression tasks
- **Statistics Tracking**: Monitor compression stats and savings
- **Thumbnail Generation**: Auto-generate video thumbnails
- **User Authentication**: Secure access control
- **Google Colab Ready**: Optimized for Colab environments

## 🚀 Quick Start

### Google Colab

1. Open the main notebook in Google Colab
2. Fill in your bot credentials:
   - `API_ID`: Your Telegram API ID
   - `API_HASH`: Your Telegram API Hash
   - `BOT_TOKEN`: Your bot token from @BotFather
   - `USER_ID`: Your Telegram user ID
   - `DUMP_ID`: Channel/group ID for storing compressed videos

3. Run the setup cell
4. The bot will start automatically

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/video-compressor-bot
cd video-compressor-bot
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Edit configuration:
```bash
nano config.json
```

4. Start the bot:
```bash
python main.py
```

## ⚙️ Configuration

Create a `config.json` file with the following structure:

```json
{
    "API_ID": 12345678,
    "API_HASH": "your_api_hash_here",
    "BOT_TOKEN": "your_bot_token_here",
    "USER_ID": 123456789,
    "DUMP_ID": -1001234567890
}
```

### Getting Credentials

1. **API_ID & API_HASH**: Get from [my.telegram.org](https://my.telegram.org)
2. **BOT_TOKEN**: Create a bot with [@BotFather](https://t.me/BotFather)
3. **USER_ID**: Your Telegram user ID (use [@userinfobot](https://t.me/userinfobot))
4. **DUMP_ID**: Create a channel/group and get its ID

## 🎯 Usage

1. Start the bot: `/start`
2. Send any video file (up to 2GB)
3. Choose compression options:
   - **Quick Compress**: Use default settings
   - **Custom Settings**: Configure compression parameters
   - **Video Info**: View detailed video information

### Available Commands

- `/start` - Start the bot and show main menu
- `/help` - Show help information
- `/settings` - Configure default compression settings
- `/queue` - View compression queue
- `/cancel` - Cancel current compression

## 🔧 Compression Settings

### Presets
- **Ultra Fast**: Fastest compression, larger file size
- **Fast**: Quick compression, good for testing
- **Medium**: Balanced speed and quality (recommended)
- **Slow**: Better quality, slower compression
- **Very Slow**: Best quality, slowest compression

### Resolution Options
- Keep original resolution
- 240p (426x240)
- 360p (640x360)
- 480p (854x480)
- 720p (1280x720)
- 1080p (1920x1080)

### Bitrate Options
- **Audio**: 32k, 64k, 128k, 192k, 256k, 320k
- **Video**: 100k, 500k, 1000k, 2000k, 4000k, 8000k

## 📊 System Requirements

### Minimum Requirements
- Python 3.8+
- FFmpeg 4.0+
- 2GB RAM
- 5GB free disk space

### Recommended (Google Colab)
- Standard Colab runtime
- GPU runtime for faster processing (optional)

### Dependencies
- pyrogram
- tgcrypto
- Pillow
- psutil
- aiofiles
- Other dependencies in `requirements.txt`

## 🐳 Docker Deployment

1. Build the image:
```bash
docker build -t video-compressor-bot .
```

2. Run with docker-compose:
```bash
docker-compose up -d
```

## 📁 Project Structure

```
video-compressor-bot/
├── main.py                 # Main bot file
├── bot/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   └── database.py        # Database operations
├── utils/
│   ├── __init__.py
│   ├── compressor.py      # Video compression engine
│   ├── helpers.py         # Utility functions
│   └── compression_handler.py
├── plugins/
│   ├── __init__.py
│   └── handlers.py        # Command handlers
├── requirements.txt       # Python dependencies
├── config.json           # Bot configuration
├── setup.sh              # Setup script
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose
└── README.md            # This file
```

## 🔐 Security Features

- User authentication by ID
- Input validation and sanitization
- File size limits
- Timeout protection
- Error handling and logging

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Install FFmpeg: `apt install ffmpeg`
   - Check PATH: `which ffmpeg`

2. **Bot token invalid**
   - Verify token from @BotFather
   - Check for extra spaces in config

3. **Permission denied**
   - Check file permissions
   - Ensure proper directory access

4. **Memory errors**
   - Reduce concurrent compressions
   - Use faster presets for large files

### Logs

Check `bot.log` for detailed error information:
```bash
tail -f bot.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Pyrogram](https://github.com/pyrogram/pyrogram) for the Telegram client
- [FFmpeg](https://ffmpeg.org/) for video processing
- Google Colab for free computing resources

## 📞 Support

- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

**Note**: This bot is designed for personal use. Ensure you comply with Telegram's Terms of Service and respect copyright laws when compressing videos.
EOL

print_status "README.md created"
echo -e "${GREEN}Setup script completed!${NC}"