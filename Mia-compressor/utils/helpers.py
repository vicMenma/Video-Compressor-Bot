# utils/helpers.py
import subprocess
import asyncio
import os
from typing import Union

async def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and accessible"""
    try:
        # Check FFmpeg
        process = await asyncio.create_subprocess_exec(
            'ffmpeg', '-version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return False
        
        # Check FFprobe
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        return process.returncode == 0
        
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error checking FFmpeg: {e}")
        return False

def format_bytes(bytes_size: Union[int, float]) -> str:
    """Format bytes to human readable format"""
    try:
        bytes_size = float(bytes_size)
        
        if bytes_size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        size_index = 0
        
        while bytes_size >= 1024 and size_index < len(size_names) - 1:
            bytes_size /= 1024
            size_index += 1
        
        return f"{bytes_size:.2f} {size_names[size_index]}"
        
    except (ValueError, TypeError):
        return "0 B"

def format_duration(seconds: Union[int, float, None]) -> str:
    """Format duration in seconds to human readable format"""
    try:
        if seconds is None or seconds <= 0:
            return "Unknown"
        
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
            
    except (ValueError, TypeError):
        return "Unknown"

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    try:
        return os.path.splitext(filename)[1].lower()
    except:
        return ""

def is_video_file(filename: str) -> bool:
    """Check if file is a video file based on extension"""
    video_extensions = [
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
        '.3gp', '.webm', '.m4v', '.mpg', '.mpeg', '.ts'
    ]
    
    return get_file_extension(filename) in video_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "video"
    
    return filename

def create_progress_bar(progress: float, length: int = 20) -> str:
    """Create a progress bar string"""
    try:
        progress = max(0, min(100, progress))
        filled_length = int(length * progress / 100)
        
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}] {progress:.1f}%"
        
    except:
        return "[░░░░░░░░░░░░░░░░░░░░] 0.0%"

def estimate_compression_time(file_size: int, preset: str = "medium") -> str:
    """Estimate compression time based on file size and preset"""
    try:
        # Rough estimates in MB per minute
        speed_factors = {
            'ultrafast': 50,
            'fast': 30,
            'medium': 20,
            'slow': 10,
            'veryslow': 5
        }
        
        factor = speed_factors.get(preset, 20)
        file_size_mb = file_size / (1024 * 1024)
        
        estimated_minutes = file_size_mb / factor
        
        if estimated_minutes < 1:
            return "< 1 minute"
        elif estimated_minutes < 60:
            return f"~{int(estimated_minutes)} minutes"
        else:
            hours = int(estimated_minutes / 60)
            minutes = int(estimated_minutes % 60)
            return f"~{hours}h {minutes}m"
            
    except:
        return "Unknown"

async def cleanup_old_files(directory: str, max_age_hours: int = 24):
    """Clean up old files in directory"""
    try:
        import time
        
        if not os.path.exists(directory):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old file: {filename}")
                    except:
                        pass
                        
    except Exception as e:
        print(f"Error cleaning up files: {e}")

def get_video_codec_info(codec_name: str) -> str:
    """Get user-friendly codec information"""
    codec_info = {
        'h264': 'H.264 (MP4)',
        'h265': 'H.265 (HEVC)',
        'vp9': 'VP9 (WebM)',
        'av1': 'AV1',
        'mpeg4': 'MPEG-4',
        'mpeg2video': 'MPEG-2',
        'wmv3': 'Windows Media Video'
    }
    
    return codec_info.get(codec_name.lower(), codec_name.upper())

def get_audio_codec_info(codec_name: str) -> str:
    """Get user-friendly audio codec information"""
    codec_info = {
        'aac': 'AAC',
        'mp3': 'MP3',
        'opus': 'Opus',
        'vorbis': 'Vorbis',
        'ac3': 'AC-3',
        'eac3': 'E-AC-3',
        'dts': 'DTS'
    }
    
    return codec_info.get(codec_name.lower(), codec_name.upper())
