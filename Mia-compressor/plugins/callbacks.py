# plugins/callbacks.py
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import CallbackQueryHandler
from bot.config import Config
from bot.database import Database
from utils.helpers import format_bytes
from utils.compressor import VideoCompressor

# Initialize components
db = Database()
compressor = VideoCompressor()

# User authentication filter
def auth_filter(_, __, callback_query):
    return callback_query.from_user.id == Config.USER_ID

auth_user = filters.create(auth_filter)

async def handle_callback(client: Client, callback_query: CallbackQuery):
    """Handle callback queries"""
    data = callback_query.data
    
    try:
        if data == "start":
            await show_start_menu(callback_query)
        elif data == "help":
            await show_help_menu(callback_query)
        elif data == "settings":
            await show_settings_menu(callback_query)
        elif data == "stats":
            await show_stats_menu(callback_query)
        elif data == "queue":
            await show_queue_menu(callback_query)
        elif data.startswith("set_"):
            await handle_setting_change(callback_query, data)
        elif data.startswith("compress_"):
            await handle_compression_request(client, callback_query, data)
        elif data.startswith("video_info_"):
            await show_video_info(client, callback_query, data)
        elif data.startswith("preset_"):
            await handle_preset_selection(callback_query, data)
        elif data.startswith("resolution_"):
            await handle_resolution_selection(callback_query, data)
        elif data.startswith("audio_bitrate_"):
            await handle_audio_selection(callback_query, data)
        elif data.startswith("video_bitrate_"):
            await handle_video_selection(callback_query, data)
        else:
            await callback_query.answer("Unknown action")
    except Exception as e:
        print(f"Callback error: {e}")
        await callback_query.answer("An error occurred")

async def show_start_menu(callback_query: CallbackQuery):
    """Show start menu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Help", callback_data="help"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats"),
         InlineKeyboardButton("📋 Queue", callback_data="queue")]
    ])
    
    await callback_query.edit_message_text(Config.START_MSG, reply_markup=keyboard)

async def show_help_menu(callback_query: CallbackQuery):
    """Show help menu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    
    await callback_query.edit_message_text(Config.HELP_MSG, reply_markup=keyboard)

async def show_settings_menu(callback_query: CallbackQuery):
    """Show settings menu"""
    user = await db.get_user(callback_query.from_user.id)
    settings = user.get('settings', {}) if user else {}
    
    text = f"""
⚙️ **Current Settings:**

**Compression Preset:** `{settings.get('preset', 'medium')}`
**Resolution:** `{settings.get('resolution', 'keep')}`
**Audio Bitrate:** `{settings.get('audio_bitrate', '128k')}`
**Video Bitrate:** `{settings.get('video_bitrate', '2000k')}`
**Remove Audio:** `{'Yes' if settings.get('remove_audio') else 'No'}`
**Generate Thumbnail:** `{'Yes' if settings.get('thumbnail') else 'No'}`
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Preset", callback_data="set_preset"),
         InlineKeyboardButton("📺 Resolution", callback_data="set_resolution")],
        [InlineKeyboardButton("🔊 Audio", callback_data="set_audio"),
         InlineKeyboardButton("🎬 Video", callback_data="set_video")],
        [InlineKeyboardButton("🖼️ Thumbnail", callback_data="toggle_thumbnail"),
         InlineKeyboardButton("🔇 Remove Audio", callback_data="toggle_audio")],
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_stats_menu(callback_query: CallbackQuery):
    """Show user statistics"""
    user = await db.get_user(callback_query.from_user.id)
    total_users = await db.get_total_users()
    total_compressions = await db.get_total_compressions()
    
    text = f"""
📊 **Your Statistics:**

**Videos Compressed:** `{user.get('total_compressed', 0) if user else 0}`
**Total Size Saved:** `{format_bytes(user.get('total_size_saved', 0) if user else 0)}`
**Join Date:** `{user.get('join_date', 'Unknown')[:10] if user else 'Unknown'}`

**Global Stats:**
**Total Users:** `{total_users}`
**Total Compressions:** `{total_compressions}`
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ])
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_queue_menu(callback_query: CallbackQuery):
    """Show queue menu"""
    user_queue = await db.get_user_queue(callback_query.from_user.id)
    
    if not user_queue:
        text = "📋 Your queue is empty."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
    else:
        text = "📋 **Your Compression Queue:**\n\n"
        
        for i, (task_id, task) in enumerate(user_queue.items(), 1):
            status_emoji = {
                'queued': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(task['status'], '❓')
            
            progress = task.get('progress', 0)
            text += f"{i}. {status_emoji} `{task['file_name']}`\n"
            text += f"   Status: {task['status'].title()}"
            
            if task['status'] == 'processing':
                text += f" ({progress}%)"
            
            text += "\n\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="queue"),
             InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def handle_setting_change(callback_query: CallbackQuery, data: str):
    """Handle setting changes"""
    setting_type = data.replace("set_", "").replace("toggle_", "")
    
    if setting_type == "preset":
        await show_preset_options(callback_query)
    elif setting_type == "resolution":
        await show_resolution_options(callback_query)
    elif setting_type == "audio":
        await show_audio_options(callback_query)
    elif setting_type == "video":
        await show_video_options(callback_query)
    elif data == "toggle_thumbnail":
        await toggle_thumbnail_setting(callback_query)
    elif data == "toggle_audio":
        await toggle_audio_setting(callback_query)

async def show_preset_options(callback_query: CallbackQuery):
    """Show compression preset options"""
    presets = getattr(Config, 'COMPRESSION_PRESETS', {
        'ultrafast': {'description': '⚡ Ultra Fast'},
        'fast': {'description': '🚀 Fast'},
        'medium': {'description': '⚖️ Medium'},
        'slow': {'description': '🐌 Slow'},
        'veryslow': {'description': '🐌 Very Slow'}
    })
    
    buttons = []
    for preset_key, preset_data in presets.items():
        buttons.append([InlineKeyboardButton(
            preset_data['description'], 
            callback_data=f"preset_{preset_key}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
    keyboard = InlineKeyboardMarkup(buttons)
    
    text = """
🎯 **Choose Compression Preset:**

**Ultra Fast** - Fastest compression, largest file size
**Fast** - Quick compression, good for testing
**Medium** - Balanced speed and quality (Recommended)
**Slow** - Better quality, slower compression
**Very Slow** - Best quality, slowest compression
"""
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_resolution_options(callback_query: CallbackQuery):
    """Show resolution options"""
    resolutions = getattr(Config, 'RESOLUTION_PRESETS', {
        'keep': 'Keep Original',
        '720p': '1280x720',
        '480p': '854x480',
        '360p': '640x360'
    })
    
    buttons = []
    for res_key, res_value in resolutions.items():
        display_text = res_key if res_key != "keep" else "Keep Original"
        buttons.append([InlineKeyboardButton(
            display_text, 
            callback_data=f"resolution_{res_key}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
    keyboard = InlineKeyboardMarkup(buttons)
    
    text = "📺 **Choose Output Resolution:**"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_audio_options(callback_query: CallbackQuery):
    """Show audio bitrate options"""
    bitrates = getattr(Config, 'AUDIO_BITRATES', {
        '64k': '64 kbps',
        '128k': '128 kbps',
        '192k': '192 kbps',
        '256k': '256 kbps'
    })
    
    buttons = []
    for bitrate_key in bitrates.keys():
        buttons.append([InlineKeyboardButton(
            bitrate_key, 
            callback_data=f"audio_bitrate_{bitrate_key}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
    keyboard = InlineKeyboardMarkup(buttons)
    
    text = "🔊 **Choose Audio Bitrate:**"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_video_options(callback_query: CallbackQuery):
    """Show video bitrate options"""
    bitrates = getattr(Config, 'VIDEO_BITRATES', {
        '500k': '500 kbps',
        '1000k': '1 Mbps',
        '2000k': '2 Mbps',
        '4000k': '4 Mbps'
    })
    
    buttons = []
    for bitrate_key in bitrates.keys():
        buttons.append([InlineKeyboardButton(
            bitrate_key, 
            callback_data=f"video_bitrate_{bitrate_key}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
    keyboard = InlineKeyboardMarkup(buttons)
    
    text = "🎬 **Choose Video Bitrate:**"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

# Handler functions for selections
async def handle_preset_selection(callback_query: CallbackQuery, data: str):
    preset = data.replace("preset_", "")
    await db.update_user_setting(callback_query.from_user.id, 'preset', preset)
    await callback_query.answer(f"✅ Preset set to {preset}")
    await show_settings_menu(callback_query)

async def handle_resolution_selection(callback_query: CallbackQuery, data: str):
    resolution = data.replace("resolution_", "")
    await db.update_user_setting(callback_query.from_user.id, 'resolution', resolution)
    await callback_query.answer(f"✅ Resolution set to {resolution}")
    await show_settings_menu(callback_query)

async def handle_audio_selection(callback_query: CallbackQuery, data: str):
    bitrate = data.replace("audio_bitrate_", "")
    await db.update_user_setting(callback_query.from_user.id, 'audio_bitrate', bitrate)
    await callback_query.answer(f"✅ Audio bitrate set to {bitrate}")
    await show_settings_menu(callback_query)

async def handle_video_selection(callback_query: CallbackQuery, data: str):
    bitrate = data.replace("video_bitrate_", "")
    await db.update_user_setting(callback_query.from_user.id, 'video_bitrate', bitrate)
    await callback_query.answer(f"✅ Video bitrate set to {bitrate}")
    await show_settings_menu(callback_query)

async def toggle_thumbnail_setting(callback_query: CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    current = user.get('settings', {}).get('thumbnail', False) if user else False
    new_value = not current
    await db.update_user_setting(callback_query.from_user.id, 'thumbnail', new_value)
    await callback_query.answer(f"✅ Thumbnail {'enabled' if new_value else 'disabled'}")
    await show_settings_menu(callback_query)

async def toggle_audio_setting(callback_query: CallbackQuery):
    user = await db.get_user(callback_query.from_user.id)
    current = user.get('settings', {}).get('remove_audio', False) if user else False
    new_value = not current
    await db.update_user_setting(callback_query.from_user.id, 'remove_audio', new_value)
    await callback_query.answer(f"✅ Remove audio {'enabled' if new_value else 'disabled'}")
    await show_settings_menu(callback_query)

async def handle_compression_request(client: Client, callback_query: CallbackQuery, data: str):
    """Handle compression requests"""
    try:
        parts = data.split("_")
        compression_type = parts[1]  # quick or custom
        message_id = int(parts[2])
        
        await callback_query.answer("🔄 Starting compression...")
        
        # Get the original message
        try:
            original_message = await client.get_messages(
                callback_query.message.chat.id, 
                message_id
            )
        except:
            await callback_query.edit_message_text("❌ Original message not found.")
            return
        
        # Get file info
        if original_message.video:
            file_obj = original_message.video
            file_name = file_obj.file_name or f"video_{message_id}.mp4"
        elif original_message.document:
            file_obj = original_message.document
            file_name = file_obj.file_name
        else:
            await callback_query.edit_message_text("❌ No video found in the message.")
            return
        
        # Get user settings
        user = await db.get_user(callback_query.from_user.id)
        settings = user.get('settings', {}) if user else {}
        
        # Create compression task
        task_id = f"{callback_query.from_user.id}_{message_id}_{int(asyncio.get_event_loop().time())}"
        
        task_data = {
            'user_id': callback_query.from_user.id,
            'message_id': message_id,
            'file_name': file_name,
            'file_size': file_obj.file_size,
            'status': 'queued',
            'progress': 0,
            'settings': settings if compression_type == 'custom' else {'preset': 'medium'},
            'created_at': asyncio.get_event_loop().time()
        }
        
        # Add to queue
        await db.add_compression_task(task_id, task_data)
        
        # Start compression
        asyncio.create_task(start_compression(client, task_id, original_message, task_data))
        
        # Update message
        await callback_query.edit_message_text(
            f"✅ **Compression Started!**\n\n"
            f"**File:** `{file_name}`\n"
            f"**Task ID:** `{task_id}`\n"
            f"**Status:** Queued\n\n"
            f"You can check progress in /queue"
        )
        
    except Exception as e:
        print(f"Compression request error: {e}")
        await callback_query.edit_message_text(f"❌ Error starting compression: {str(e)}")

async def start_compression(client: Client, task_id: str, message, task_data: dict):
    """Start video compression"""
    try:
        # Update status to processing
        await db.update_compression_task(task_id, {'status': 'processing', 'progress': 0})
        
        # Download the file
        await db.update_compression_task(task_id, {'progress': 10})
        
        # Get file
        if message.video:
            file_obj = message.video
        else:
            file_obj = message.document
        
        # Create downloads directory
        download_dir = Config.DOWNLOAD_DIR
        os.makedirs(download_dir, exist_ok=True)
        
        # Download file
        input_path = os.path.join(download_dir, f"input_{task_id}_{task_data['file_name']}")
        await message.download(input_path)
        
        await db.update_compression_task(task_id, {'progress': 30})
        
        # Compress video
        output_path = os.path.join(download_dir, f"compressed_{task_id}_{task_data['file_name']}")
        
        success = await compressor.compress_video(
            input_path=input_path,
            output_path=output_path,
            settings=task_data['settings'],
            progress_callback=lambda p: asyncio.create_task(
                db.update_compression_task(task_id, {'progress': 30 + int(p * 0.6)})
            )
        )
        
        if not success:
            await db.update_compression_task(task_id, {'status': 'failed'})
            await client.send_message(
                task_data['user_id'],
                f"❌ **Compression Failed!**\n\nTask ID: `{task_id}`"
            )
            return
        
        await db.update_compression_task(task_id, {'progress': 90})
        
        # Upload compressed video
        try:
            # Get file sizes
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            size_saved = original_size - compressed_size
            
            # Send compressed video
            caption = f"""
✅ **Video Compressed Successfully!**

**Original Size:** `{format_bytes(original_size)}`
**Compressed Size:** `{format_bytes(compressed_size)}`
**Size Saved:** `{format_bytes(size_saved)}` ({size_saved/original_size*100:.1f}%)

**Settings Used:**
**Preset:** `{task_data['settings'].get('preset', 'medium')}`
**Resolution:** `{task_data['settings'].get('resolution', 'keep')}`
"""
            
            await client.send_video(
                chat_id=task_data['user_id'],
                video=output_path,
                caption=caption,
                supports_streaming=True
            )
            
            # Upload to dump channel if configured
            if hasattr(Config, 'DUMP_ID') and Config.DUMP_ID:
                try:
                    await client.send_video(
                        chat_id=Config.DUMP_ID,
                        video=output_path,
                        caption=f"Compressed by User {task_data['user_id']}\n{caption}"
                    )
                except:
                    pass
            
            # Update database
            await db.update_compression_task(task_id, {'status': 'completed', 'progress': 100})
            await db.update_user_stats(task_data['user_id'], size_saved)
            
            # Clean up files
            try:
                os.remove(input_path)
                os.remove(output_path)
            except:
                pass
                
        except Exception as e:
            print(f"Upload error: {e}")
            await db.update_compression_task(task_id, {'status': 'failed'})
            await client.send_message(
                task_data['user_id'],
                f"❌ **Upload Failed!**\n\nTask ID: `{task_id}`\nError: {str(e)}"
            )
            
    except Exception as e:
        print(f"Compression error: {e}")
        await db.update_compression_task(task_id, {'status': 'failed'})
        await client.send_message(
            task_data['user_id'],
            f"❌ **Compression Failed!**\n\nTask ID: `{task_id}`\nError: {str(e)}"
        )
        
        # Clean up files
        try:
            if 'input_path' in locals():
                os.remove(input_path)
            if 'output_path' in locals():
                os.remove(output_path)
        except:
            pass

async def show_video_info(client: Client, callback_query: CallbackQuery, data: str):
    """Show video information"""
    try:
        message_id = int(data.replace("video_info_", ""))
        
        # Get the original message
        original_message = await client.get_messages(
            callback_query.message.chat.id, 
            message_id
        )
        
        if original_message.video:
            file_obj = original_message.video
            file_type = "Video"
        elif original_message.document:
            file_obj = original_message.document
            file_type = "Document"
        else:
            await callback_query.answer("❌ File not found")
            return
        
        info_text = f"""
📊 **{file_type} Information:**

**Name:** `{file_obj.file_name or 'Unknown'}`
**Size:** `{format_bytes(file_obj.file_size)}`
**MIME Type:** `{getattr(file_obj, 'mime_type', 'Unknown')}`
"""
        
        if hasattr(file_obj, 'duration') and file_obj.duration:
            info_text += f"**Duration:** `{file_obj.duration}s`\n"
        
        if hasattr(file_obj, 'width') and hasattr(file_obj, 'height'):
            info_text += f"**Resolution:** `{file_obj.width}x{file_obj.height}`\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Quick Compress", 
                                callback_data=f"compress_quick_{message_id}")],
            [InlineKeyboardButton("⚙️ Custom Settings", 
                                callback_data=f"compress_custom_{message_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
        
        await callback_query.edit_message_text(info_text, reply_markup=keyboard)
        
    except Exception as e:
        print(f"Video info error: {e}")
        await callback_query.answer("❌ Error getting video info")

# Create the handler
handle_callback = CallbackQueryHandler(handle_callback, auth_user)
