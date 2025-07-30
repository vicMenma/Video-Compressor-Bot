# plugins/video.py
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler
from bot.config import Config
from bot.database import Database
from utils.helpers import format_bytes, format_duration

# Initialize components
db = Database()

# User authentication filter
def auth_filter(_, __, message):
    return message.from_user.id == Config.USER_ID

auth_user = filters.create(auth_filter)

async def handle_video_handler(client: Client, message: Message):
    """Handle video files"""
    # Check file size
    if message.video.file_size > Config.MAX_FILE_SIZE:
        await message.reply_text(
            f"❌ File too large! Maximum size: {format_bytes(Config.MAX_FILE_SIZE)}"
        )
        return
    
    # Check queue size
    user_queue = await db.get_user_queue(message.from_user.id)
    if len(user_queue) >= Config.MAX_QUEUE_SIZE:
        await message.reply_text(
            f"❌ Queue full! Maximum {Config.MAX_QUEUE_SIZE} files allowed."
        )
        return
    
    # Get user settings
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.reply_text("❌ User not found. Please /start first.")
        return
    
    # Show compression options
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Quick Compress", 
                            callback_data=f"compress_quick_{message.id}")],
        [InlineKeyboardButton("⚙️ Custom Settings", 
                            callback_data=f"compress_custom_{message.id}")],
        [InlineKeyboardButton("📊 Video Info", 
                            callback_data=f"video_info_{message.id}")]
    ])
    
    file_info = f"""
📹 **Video Received:**

**Name:** `{message.video.file_name or 'video.mp4'}`
**Size:** `{format_bytes(message.video.file_size)}`
**Duration:** `{format_duration(message.video.duration)}`
**Resolution:** `{message.video.width}x{message.video.height}`

Choose compression option:
    """
    
    await message.reply_text(file_info, reply_markup=keyboard)

async def handle_document_handler(client: Client, message: Message):
    """Handle video documents"""
    if not message.document.file_name:
        return
    
    # Check if it's a video file
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.3gp', '.webm']
    file_ext = os.path.splitext(message.document.file_name)[1].lower()
    
    if file_ext not in video_extensions:
        return
    
    # Check file size
    if message.document.file_size > Config.MAX_FILE_SIZE:
        await message.reply_text(
            f"❌ File too large! Maximum size: {format_bytes(Config.MAX_FILE_SIZE)}"
        )
        return
    
    # Check queue size
    user_queue = await db.get_user_queue(message.from_user.id)
    if len(user_queue) >= Config.MAX_QUEUE_SIZE:
        await message.reply_text(
            f"❌ Queue full! Maximum {Config.MAX_QUEUE_SIZE} files allowed."
        )
        return
    
    # Show compression options
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Quick Compress", 
                            callback_data=f"compress_quick_{message.id}")],
        [InlineKeyboardButton("⚙️ Custom Settings", 
                            callback_data=f"compress_custom_{message.id}")],
        [InlineKeyboardButton("📊 Video Info", 
                            callback_data=f"video_info_{message.id}")]
    ])
    
    file_info = f"""
📹 **Video Document Received:**

**Name:** `{message.document.file_name}`
**Size:** `{format_bytes(message.document.file_size)}`
**Type:** `{message.document.mime_type or 'video'}`

Choose compression option:
    """
    
    await message.reply_text(file_info, reply_markup=keyboard)

# Create handlers
handle_video = MessageHandler(handle_video_handler, filters.video & auth_user)
handle_document = MessageHandler(handle_document_handler, filters.document & auth_user)
