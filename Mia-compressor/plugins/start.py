# plugins/start.py
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler
from bot.config import Config
from bot.database import Database

# Initialize components
db = Database()

# User authentication filter
def auth_filter(_, __, message):
    return message.from_user.id == Config.USER_ID

auth_user = filters.create(auth_filter)

async def start_command_handler(client: Client, message: Message):
    """Handle /start command"""
    user_data = {
        'first_name': message.from_user.first_name,
        'username': message.from_user.username,
        'join_date': datetime.now().isoformat()
    }
    
    await db.add_user(message.from_user.id, user_data)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Help", callback_data="help"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats"),
         InlineKeyboardButton("📋 Queue", callback_data="queue")]
    ])
    
    await message.reply_text(Config.START_MSG, reply_markup=keyboard)

async def help_command_handler(client: Client, message: Message):
    """Handle /help command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    
    await message.reply_text(Config.HELP_MSG, reply_markup=keyboard)

# Create handlers
start_command = MessageHandler(start_command_handler, filters.command("start") & auth_user)
help_command = MessageHandler(help_command_handler, filters.command("help") & auth_user)
