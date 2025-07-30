# helpers.py
import os
import time
import math
from typing import Union

def format_bytes(size: Union[int, float]) -> str:
    """Format bytes to human readable format"""
    if size == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    
    return f"{s} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format seconds to human readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"

def get_progress_bar(percentage: float, length: int = 20) -> str:
    """Generate progress bar"""
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"

def estimate_compression_time(file_size: int, preset: str) -> int:
    """Estimate compression time based on file size and preset"""
    # Base compression speed in MB/s for different presets
    speeds = {
        'ultra_fast': 10.0,
        'fast': 8.0,
        'medium': 5.0,
        'slow': 3.0,
        'veryslow': 1.5
    }
    
    speed = speeds.get(preset, 5.0)
    file_size_mb = file_size / (1024 * 1024)
    estimated_seconds = file_size_mb / speed
    
    return int(estimated_seconds)

def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    video_extensions = {
        '.mp4': 'MP4 Video',
        '.avi': 'AVI Video',
        '.mkv': 'Matroska Video',
        '.mov': 'QuickTime Video',
        '.wmv': 'Windows Media Video',
        '.flv': 'Flash Video',
        '.3gp': '3GP Video',
        '.webm': 'WebM Video',
        '.m4v': 'MPEG-4 Video',
        '.mpg': 'MPEG Video',
        '.mpeg': 'MPEG Video'
    }
    
    ext = os.path.splitext(filename)[1].lower()
    return video_extensions.get(ext, 'Video File')

def clean_filename(filename: str) -> str:
    """Clean filename for safe usage"""
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext

def calculate_bitrate(file_size: int, duration: float) -> int:
    """Calculate average bitrate from file size and duration"""
    if duration <= 0:
        return 0
    
    # Convert file size to bits and divide by duration
    bitrate = (file_size * 8) / duration
    return int(bitrate)

def get_optimal_settings(video_info: dict) -> dict:
    """Get optimal compression settings based on video info"""
    width = video_info.get('video', {}).get('width', 0)
    height = video_info.get('video', {}).get('height', 0)
    duration = video_info.get('duration', 0)
    file_size = video_info.get('size', 0)
    
    # Determine optimal preset based on file size
    if file_size > 500 * 1024 * 1024:  # > 500MB
        preset = 'fast'
    elif file_size > 100 * 1024 * 1024:  # > 100MB
        preset = 'medium'
    else:
        preset = 'slow'
    
    # Determine optimal resolution
    if height > 1080:
        resolution = '1080p'
    elif height > 720:
        resolution = '720p'  
    elif height > 480:
        resolution = '480p'
    else:
        resolution = 'keep'
    
    # Determine optimal bitrates
    if width * height > 1920 * 1080:  # 4K+
        video_bitrate = '8000k'
        audio_bitrate = '256k'
    elif width * height > 1280 * 720:  # 1080p
        video_bitrate = '4000k'
        audio_bitrate = '192k'
    elif width * height > 854 * 480:  # 720p
        video_bitrate = '2000k'
        audio_bitrate = '128k'
    else:  # 480p and below
        video_bitrate = '1000k'
        audio_bitrate = '128k'
    
    return {
        'preset': preset,
        'resolution': resolution,
        'video_bitrate': video_bitrate,
        'audio_bitrate': audio_bitrate
    }

def validate_settings(settings: dict) -> tuple[bool, str]:
    """Validate compression settings"""
    from bot.config import Config
    
    # Check preset
    if settings.get('preset') not in Config.COMPRESSION_PRESETS:
        return False, "Invalid compression preset"
    
    # Check resolution
    if settings.get('resolution') not in Config.RESOLUTION_PRESETS:
        return False, "Invalid resolution setting"
    
    # Check audio bitrate
    if settings.get('audio_bitrate') not in Config.AUDIO_BITRATES:
        return False, "Invalid audio bitrate"
    
    # Check video bitrate
    if settings.get('video_bitrate') not in Config.VIDEO_BITRATES and settings.get('video_bitrate') != 'auto':
        return False, "Invalid video bitrate"
    
    return True, "Settings are valid"

def get_compression_stats(original_size: int, compressed_size: int, 
                         compression_time: float) -> dict:
    """Calculate compression statistics"""
    size_reduction = original_size - compressed_size
    compression_ratio = (size_reduction / original_size * 100) if original_size > 0 else 0
    compression_speed = (original_size / (1024 * 1024)) / compression_time if compression_time > 0 else 0
    
    return {
        'size_reduction': size_reduction,
        'compression_ratio': compression_ratio,
        'compression_speed': compression_speed,
        'time_saved': estimate_upload_time_saved(size_reduction)
    }

def estimate_upload_time_saved(size_reduction: int) -> int:
    """Estimate upload time saved based on size reduction"""
    # Assume average upload speed of 1 Mbps
    avg_upload_speed = 1024 * 1024 / 8  # bytes per second
    time_saved = size_reduction / avg_upload_speed
    return int(time_saved)

def format_eta(seconds: int) -> str:
    """Format ETA in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_quality_description(preset: str, crf: str) -> str:
    """Get quality description for preset and CRF"""
    quality_map = {
        ('ultra_fast', '28'): 'Fastest compression, lower quality',
        ('fast', '26'): 'Fast compression, good quality',
        ('medium', '24'): 'Balanced speed and quality',
        ('slow', '22'): 'Slower compression, high quality',
        ('veryslow', '20'): 'Slowest compression, highest quality'
    }
    
    return quality_map.get((preset, crf), 'Custom quality settings')

def sanitize_callback_data(data: str) -> str:
    """Sanitize callback data to prevent issues"""
    # Telegram callback data has 64 byte limit
    if len(data.encode()) > 64:
        # Hash longer data
        import hashlib
        return hashlib.md5(data.encode()).hexdigest()[:32]
    return data

def parse_video_codec(codec_name: str) -> str:
    """Parse video codec name to human readable format"""
    codec_map = {
        'h264': 'H.264/AVC',
        'h265': 'H.265/HEVC', 
        'hevc': 'H.265/HEVC',
        'vp8': 'VP8',
        'vp9': 'VP9',
        'av1': 'AV1',
        'mpeg4': 'MPEG-4',
        'mpeg2': 'MPEG-2',
        'xvid': 'Xvid',
        'divx': 'DivX'
    }
    
    return codec_map.get(codec_name.lower(), codec_name.upper())

def parse_audio_codec(codec_name: str) -> str:
    """Parse audio codec name to human readable format"""
    codec_map = {
        'aac': 'AAC',
        'mp3': 'MP3',
        'ac3': 'AC-3',
        'eac3': 'E-AC-3',
        'dts': 'DTS',
        'flac': 'FLAC',
        'vorbis': 'Vorbis',
        'opus': 'Opus',
        'pcm': 'PCM'
    }
    
    return codec_map.get(codec_name.lower(), codec_name.upper())

# Async utilities
import asyncio

async def run_command(command: list, timeout: int = 3600) -> tuple[int, str, str]:
    """Run command asynchronously with timeout"""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )
        
        return process.returncode, stdout.decode(), stderr.decode()
        
    except asyncio.TimeoutError:
        if process:
            process.terminate()
            await asyncio.sleep(2)
            if process.returncode is None:
                process.kill()
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

async def check_ffmpeg() -> bool:
    """Check if FFmpeg is available"""
    try:
        returncode, _, _ = await run_command(['ffmpeg', '-version'], timeout=10)
        return returncode == 0
    except:
        return False

async def get_system_info() -> dict:
    """Get system information"""
    import psutil
    
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'available_memory': psutil.virtual_memory().available,
        'total_memory': psutil.virtual_memory().total
    }