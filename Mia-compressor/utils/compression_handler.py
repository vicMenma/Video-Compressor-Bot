# utils/compression_handler.py
import os
import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
from bot.config import Config
from bot.database import Database
from utils.compressor import VideoCompressor
from utils.helpers import format_bytes, format_duration, get_progress_bar

class CompressionHandler:
    def __init__(self):
        self.db = Database()
        self.compressor = VideoCompressor()
        self.active_compressions = {}
    
    async def handle_compression_request(self, callback_query: CallbackQuery, data: str):
        """Handle compression requests"""
        try:
            action, message_id = data.rsplit('_', 1)
            message_id = int(message_id)
            
            # Get the original message
            original_message = None
            async for message in callback_query.message.chat.iter_history():
                if message.id == message_id:
                    original_message = message
                    break
            
            if not original_message:
                await callback_query.answer("❌ Original message not found")
                return
            
            # Get video file
            video_file = original_message.video or original_message.document
            if not video_file:
                await callback_query.answer("❌ No video file found")
                return
            
            if action == "compress_quick":
                await self._start_quick_compression(callback_query, original_message, video_file)
            elif action == "compress_custom":
                await self._show_custom_options(callback_query, original_message, video_file)
            
        except Exception as e:
            await callback_query.answer(f"❌ Error: {str(e)}")
    
    async def _start_quick_compression(self, callback_query: CallbackQuery, 
                                     original_message: Message, video_file):
        """Start quick compression with default settings"""
        user = await self.db.get_user(callback_query.from_user.id)
        settings = user.get('settings', {})
        
        # Use default settings for quick compression
        compression_settings = {
            'preset': settings.get('preset', 'medium'),
            'crf': Config.COMPRESSION_PRESETS[settings.get('preset', 'medium')]['crf'],
            'resolution': 'keep',
            'audio_bitrate': '128k',
            'video_bitrate': 'auto',
            'remove_audio': False
        }
        
        await self._start_compression(callback_query, original_message, 
                                    video_file, compression_settings)
    
    async def _show_custom_options(self, callback_query: CallbackQuery, 
                                 original_message: Message, video_file):
        """Show custom compression options"""
        # Store the message reference for later use
        self.pending_compressions = getattr(self, 'pending_compressions', {})
        self.pending_compressions[f"{callback_query.from_user.id}_{original_message.id}"] = {
            'original_message': original_message,
            'video_file': video_file,
            'settings': {}
        }
        
        keyboard = [
            [{"text": "🎯 Preset: Medium", "callback_data": f"custom_preset_{original_message.id}"}],
            [{"text": "📺 Resolution: Keep Original", "callback_data": f"custom_resolution_{original_message.id}"}],
            [{"text": "🔊 Audio: 128k", "callback_data": f"custom_audio_{original_message.id}"}],
            [{"text": "🎬 Video: Auto", "callback_data": f"custom_video_{original_message.id}"}],
            [{"text": "✅ Start Compression", "callback_data": f"start_custom_{original_message.id}"},
             {"text": "❌ Cancel", "callback_data": "start"}]
        ]
        
        keyboard_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) 
             for btn in row] for row in keyboard
        ])
        
        text = f"""
⚙️ **Custom Compression Settings**

**File:** `{video_file.file_name or 'video.mp4'}`
**Size:** `{format_bytes(video_file.file_size)}`

Configure your compression settings:
"""
        
        await callback_query.edit_message_text(text, reply_markup=keyboard_markup)
    
    async def _start_compression(self, callback_query: CallbackQuery, 
                               original_message: Message, video_file, settings):
        """Start the compression process"""
        try:
            # Create task in database
            task_data = {
                'created_at': datetime.now().isoformat(),
                'file_name': video_file.file_name or 'video.mp4',
                'file_size': video_file.file_size,
                'settings': settings
            }
            
            task_id = await self.db.add_to_queue(callback_query.from_user.id, task_data)
            
            # Show processing message
            processing_text = f"""
🔄 **Processing Video...**

**File:** `{task_data['file_name']}`
**Size:** `{format_bytes(task_data['file_size'])}`
**Status:** Downloading...

{get_progress_bar(0)}
"""
            
            keyboard = [[{"text": "❌ Cancel", "callback_data": f"cancel_{task_id}"}]]
            keyboard_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) 
                 for btn in row] for row in keyboard
            ])
            
            status_message = await callback_query.edit_message_text(
                processing_text, reply_markup=keyboard_markup
            )
            
            # Start compression in background
            asyncio.create_task(
                self._process_compression(callback_query.message.chat.id, 
                                        status_message.id, original_message, 
                                        video_file, settings, task_id)
            )
            
        except Exception as e:
            await callback_query.answer(f"❌ Error starting compression: {str(e)}")
    
    async def _process_compression(self, chat_id: int, status_msg_id: int,
                                 original_message: Message, video_file, 
                                 settings: dict, task_id: str):
        """Process video compression"""
        client = original_message._client
        
        try:
            # Update status to processing
            await self.db.update_queue_status(task_id, 'processing', 0)
            
            # Download video
            await self._update_status(client, chat_id, status_msg_id, 
                                    "📥 Downloading video...", 0, task_id)
            
            Config.create_directories()
            
            input_path = os.path.join(Config.DOWNLOAD_PATH, 
                                    f"{task_id}_{video_file.file_name or 'video.mp4'}")
            output_path = os.path.join(Config.COMPRESSED_PATH, 
                                     f"compressed_{task_id}_{video_file.file_name or 'video.mp4'}")
            
            # Download with progress
            await original_message.download(
                input_path,
                progress=lambda current, total: asyncio.create_task(
                    self._download_progress(client, chat_id, status_msg_id, 
                                          current, total, task_id)
                )
            )
            
            # Start compression
            await self._update_status(client, chat_id, status_msg_id, 
                                    "🔄 Compressing video...", 0, task_id)
            
            # Progress callback for compression
            async def progress_callback(task_id, progress):
                await self._update_status(client, chat_id, status_msg_id, 
                                        "🔄 Compressing video...", progress, task_id)
                await self.db.update_queue_status(task_id, 'processing', progress)
            
            # Compress video
            result = await self.compressor.compress_video(
                input_path, output_path, settings, task_id, progress_callback
            )
            
            if result['success']:
                # Generate thumbnail if enabled
                thumbnail_path = None
                if settings.get('thumbnail', True):
                    thumbnail_path = os.path.join(Config.THUMBNAIL_PATH, f"thumb_{task_id}.jpg")
                    await self.compressor.generate_thumbnail(output_path, thumbnail_path)
                
                # Upload compressed video
                await self._update_status(client, chat_id, status_msg_id, 
                                        "📤 Uploading compressed video...", 95, task_id)
                
                # Prepare file info
                file_name = video_file.file_name or 'compressed_video.mp4'
                if not file_name.startswith('compressed_'):
                    file_name = f"compressed_{file_name}"
                
                caption = f"""
✅ **Compression Complete!**

**Original Size:** `{format_bytes(result['original_size'])}`
**Compressed Size:** `{format_bytes(result['compressed_size'])}`
**Size Reduction:** `{format_bytes(result['size_reduction'])} ({result['compression_ratio']:.1f}%)`
**Time Taken:** `{format_duration(int(result['compression_time']))}`

**Settings Used:**
• Preset: `{settings['preset']}`
• Resolution: `{settings.get('resolution', 'keep')}`
• Audio Bitrate: `{settings.get('audio_bitrate', 'original')}`
"""
                
                # Send compressed video
                sent_message = await client.send_video(
                    chat_id=Config.DUMP_ID,
                    video=output_path,
                    caption=caption,
                    thumb=thumbnail_path,
                    supports_streaming=True,
                    progress=lambda current, total: asyncio.create_task(
                        self._upload_progress(client, chat_id, status_msg_id, 
                                            current, total, task_id)
                    )
                )
                
                # Update user stats
                await self.db.increment_user_stats(
                    original_message.from_user.id, 
                    result['size_reduction']
                )
                
                # Send completion message
                keyboard = [[{"text": "📁 Get File", "url": f"https://t.me/c/{str(Config.DUMP_ID)[4:]}/{sent_message.id}"}]]
                keyboard_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(btn["text"], url=btn["url"]) 
                     for btn in row] for row in keyboard
                ])
                
                completion_text = f"""
✅ **Compression Successful!**

**File:** `{file_name}`
**Reduced by:** `{format_bytes(result['size_reduction'])} ({result['compression_ratio']:.1f}%)`
**Time:** `{format_duration(int(result['compression_time']))}`

Your compressed video is ready!
"""
                
                await client.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    text=completion_text,
                    reply_markup=keyboard_markup
                )
                
                await self.db.update_queue_status(task_id, 'completed', 100)
                
            else:
                # Compression failed
                error_text = f"""
❌ **Compression Failed**

**Error:** `{result.get('error', 'Unknown error')}`

The video could not be compressed. Please try again with different settings or contact support.
"""
                
                await client.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    text=error_text
                )
                
                await self.db.update_queue_status(task_id, 'failed')
            
            # Cleanup files
            self._cleanup_files([input_path, output_path, thumbnail_path])
            await self.db.remove_from_queue(task_id)
            
        except Exception as e:
            # Handle any errors during processing
            error_text = f"""
❌ **Processing Error**

**Error:** `{str(e)}`

An error occurred during processing. Please try again.
"""
            
            try:
                await client.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    text=error_text
                )
            except:
                pass
            
            await self.db.update_queue_status(task_id, 'failed')
            
            # Cleanup files
            try:
                input_path = os.path.join(Config.DOWNLOAD_PATH, f"{task_id}_*")
                output_path = os.path.join(Config.COMPRESSED_PATH, f"compressed_{task_id}_*")
                self._cleanup_files([input_path, output_path])
            except:
                pass
    
    async def _download_progress(self, client, chat_id: int, status_msg_id: int, 
                               current: int, total: int, task_id: str):
        """Handle download progress updates"""
        progress = int((current / total) * 30)  # 30% for download
        
        try:
            await self._update_status(client, chat_id, status_msg_id, 
                                    "📥 Downloading video...", progress, task_id)
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error updating download progress: {e}")
    
    async def _upload_progress(self, client, chat_id: int, status_msg_id: int, 
                             current: int, total: int, task_id: str):
        """Handle upload progress updates"""
        progress = 95 + int((current / total) * 5)  # 95-100% for upload
        
        try:
            await self._update_status(client, chat_id, status_msg_id, 
                                    "📤 Uploading video...", progress, task_id)
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error updating upload progress: {e}")
    
    async def _update_status(self, client, chat_id: int, status_msg_id: int, 
                           status: str, progress: int, task_id: str):
        """Update compression status message"""
        try:
            task_data = await self.db.queue_data.get(task_id, {})
            file_name = task_data.get('file_name', 'video.mp4')
            file_size = task_data.get('file_size', 0)
            
            status_text = f"""
🔄 **Processing Video...**

**File:** `{file_name}`
**Size:** `{format_bytes(file_size)}`
**Status:** {status}

{get_progress_bar(progress)} {progress}%
"""
            
            keyboard = [[{"text": "❌ Cancel", "callback_data": f"cancel_{task_id}"}]]
            keyboard_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) 
                 for btn in row] for row in keyboard
            ])
            
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text=status_text,
                reply_markup=keyboard_markup
            )
            
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def _cleanup_files(self, file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")

# Additional handler functions that were previously at the bottom of the file
# These should be in handlers.py instead of compression_handler.py
async def toggle_thumbnail_setting(callback_query: CallbackQuery, db):
    """Toggle thumbnail generation setting"""
    user = await db.get_user(callback_query.from_user.id)
    current_setting = user.get('settings', {}).get('thumbnail', True)
    new_setting = not current_setting
    
    await db.update_user_settings(callback_query.from_user.id, {'thumbnail': new_setting})
    await callback_query.answer(f"Thumbnail {'enabled' if new_setting else 'disabled'}")

async def toggle_audio_setting(callback_query: CallbackQuery, db):
    """Toggle remove audio setting"""
    user = await db.get_user(callback_query.from_user.id)
    current_setting = user.get('settings', {}).get('remove_audio', False)
    new_setting = not current_setting
    
    await db.update_user_settings(callback_query.from_user.id, {'remove_audio': new_setting})
    await callback_query.answer(f"Remove audio {'enabled' if new_setting else 'disabled'}")

async def show_video_info(callback_query: CallbackQuery, data: str):
    """Show detailed video information"""
    try:
        message_id = int(data.split('_')[-1])
        
        # Get the original message
        original_message = None
        async for message in callback_query.message.chat.iter_history():
            if message.id == message_id:
                original_message = message
                break
        
        if not original_message:
            await callback_query.answer("❌ Original message not found")
            return
        
        # Get video file
        video_file = original_message.video or original_message.document
        if not video_file:
            await callback_query.answer("❌ No video file found")
            return
        
        # Download a small portion to analyze
        temp_path = f"/tmp/temp_analysis_{message_id}.mp4"
        
        try:
            # Download just a small part for analysis
            await original_message.download(temp_path, file_size=min(video_file.file_size, 10*1024*1024))
            
            # Get detailed info
            compressor = VideoCompressor()
            info = await compressor.get_video_info(temp_path)
            
            if info:
                video_info_text = f"""
📊 **Detailed Video Information**

**📁 File Details:**
• Name: `{video_file.file_name or 'video.mp4'}`
• Size: `{format_bytes(video_file.file_size)}`
• Duration: `{format_duration(int(info.get('duration', 0)))}`
• Format: `{info.get('format', 'Unknown')}`
• Bitrate: `{info.get('bitrate', 0)} bps`

**🎬 Video Stream:**
• Codec: `{info.get('video', {}).get('codec', 'Unknown')}`
• Resolution: `{info.get('video', {}).get('width', 0)}x{info.get('video', {}).get('height', 0)}`
• FPS: `{info.get('video', {}).get('fps', 0):.2f}`
• Video Bitrate: `{info.get('video', {}).get('bitrate', 0)} bps`

**🔊 Audio Stream:**
"""
                
                if info.get('audio'):
                    audio_info_text = f"""• Codec: `{info['audio'].get('codec', 'Unknown')}`
• Bitrate: `{info['audio'].get('bitrate', 0)} bps`
• Sample Rate: `{info['audio'].get('sample_rate', 0)} Hz`
• Channels: `{info['audio'].get('channels', 0)}`"""
                else:
                    audio_info_text = "• No audio stream found"
                
                video_info_text += audio_info_text
                
            else:
                video_info_text = "❌ Could not analyze video file"
            
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        except Exception as e:
            video_info_text = f"❌ Error analyzing video: {str(e)}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Quick Compress", 
                                callback_data=f"compress_quick_{message_id}"),
             InlineKeyboardButton("⚙️ Custom Settings", 
                                callback_data=f"compress_custom_{message_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ])
        
        await callback_query.edit_message_text(video_info_text, reply_markup=keyboard)
        
    except Exception as e:
        await callback_query.answer(f"❌ Error: {str(e)}")

# Initialize compression handler
compression_handler = CompressionHandler()