# utils/compressor.py
import asyncio
import os
import re
import subprocess
from typing import Dict, Optional, Callable
from bot.config import Config

class VideoCompressor:
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"
    
    async def compress_video(
        self, 
        input_path: str, 
        output_path: str, 
        settings: Dict, 
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Compress video with given settings"""
        try:
            # Build FFmpeg command
            cmd = await self._build_ffmpeg_command(input_path, output_path, settings)
            
            print(f"FFmpeg command: {' '.join(cmd)}")
            
            # Get video duration for progress calculation
            duration = await self._get_video_duration(input_path)
            
            # Start compression process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress
            if progress_callback and duration > 0:
                await self._monitor_progress(process, duration, progress_callback)
            
            # Wait for completion
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print("Compression completed successfully")
                return True
            else:
                print(f"Compression failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"Compression error: {e}")
            return False
    
    async def _build_ffmpeg_command(self, input_path: str, output_path: str, settings: Dict) -> list:
        """Build FFmpeg command based on settings"""
        cmd = [self.ffmpeg_path, "-i", input_path]
        
        # Video codec
        cmd.extend(["-c:v", "libx264"])
        
        # Compression preset
        preset = settings.get('preset', 'medium')
        cmd.extend(["-preset", preset])
        
        # Video bitrate
        video_bitrate = settings.get('video_bitrate', '2000k')
        cmd.extend(["-b:v", video_bitrate])
        
        # Resolution
        resolution = settings.get('resolution', 'keep')
        if resolution != 'keep':
            if resolution == '720p':
                cmd.extend(["-vf", "scale=1280:720"])
            elif resolution == '480p':
                cmd.extend(["-vf", "scale=854:480"])
            elif resolution == '360p':
                cmd.extend(["-vf", "scale=640:360"])
        
        # Audio settings
        if settings.get('remove_audio', False):
            cmd.extend(["-an"])  # Remove audio
        else:
            cmd.extend(["-c:a", "aac"])
            audio_bitrate = settings.get('audio_bitrate', '128k')
            cmd.extend(["-b:a", audio_bitrate])
        
        # Output settings
        cmd.extend(["-movflags", "+faststart"])  # Enable streaming
        cmd.extend(["-y"])  # Overwrite output file
        cmd.append(output_path)
        
        return cmd
    
    async def _get_video_duration(self, input_path: str) -> float:
        """Get video duration in seconds"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-show_entries", 
                "format=duration", "-of", "csv=p=0", input_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                duration_str = stdout.decode().strip()
                return float(duration_str)
            
        except Exception as e:
            print(f"Error getting duration: {e}")
        
        return 0.0
    
    async def _monitor_progress(self, process, total_duration: float, progress_callback: Callable):
        """Monitor FFmpeg progress"""
        try:
            while process.returncode is None:
                try:
                    # Check if process is still running
                    if process.stderr.at_eof():
                        break
                    
                    # Read stderr line
                    line = await asyncio.wait_for(
                        process.stderr.readline(), 
                        timeout=1.0
                    )
                    
                    if not line:
                        continue
                    
                    line = line.decode().strip()
                    
                    # Parse time from FFmpeg output
                    time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if time_match:
                        hours = int(time_match.group(1))
                        minutes = int(time_match.group(2))
                        seconds = float(time_match.group(3))
                        
                        current_time = hours * 3600 + minutes * 60 + seconds
                        progress = (current_time / total_duration) * 100
                        
                        # Call progress callback
                        await progress_callback(min(progress, 99))
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Progress monitoring error: {e}")
                    break
                    
        except Exception as e:
            print(f"Progress monitoring error: {e}")
    
    async def get_video_info(self, file_path: str) -> Dict:
        """Get detailed video information"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode())
                return self._parse_video_info(info)
            else:
                print(f"FFprobe error: {stderr.decode()}")
                
        except Exception as e:
            print(f"Error getting video info: {e}")
        
        return {}
    
    def _parse_video_info(self, ffprobe_output: Dict) -> Dict:
        """Parse FFprobe output into readable format"""
        info = {}
        
        try:
            # Format information
            format_info = ffprobe_output.get('format', {})
            info['duration'] = float(format_info.get('duration', 0))
            info['size'] = int(format_info.get('size', 0))
            info['bitrate'] = int(format_info.get('bit_rate', 0))
            info['format_name'] = format_info.get('format_name', 'Unknown')
            
            # Stream information
            streams = ffprobe_output.get('streams', [])
            
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    info['width'] = stream.get('width', 0)
                    info['height'] = stream.get('height', 0)
                    info['fps'] = eval(stream.get('r_frame_rate', '0/1'))
                    info['video_codec'] = stream.get('codec_name', 'Unknown')
                    info['video_bitrate'] = int(stream.get('bit_rate', 0))
                    
                elif stream.get('codec_type') == 'audio':
                    info['audio_codec'] = stream.get('codec_name', 'Unknown')
                    info['audio_bitrate'] = int(stream.get('bit_rate', 0))
                    info['sample_rate'] = int(stream.get('sample_rate', 0))
                    info['channels'] = stream.get('channels', 0)
            
        except Exception as e:
            print(f"Error parsing video info: {e}")
        
        return info
    
    async def generate_thumbnail(self, input_path: str, output_path: str, time_offset: str = "00:00:01") -> bool:
        """Generate thumbnail from video"""
        try:
            cmd = [
                self.ffmpeg_path, "-i", input_path,
                "-ss", time_offset, "-vframes", "1",
                "-q:v", "2", "-y", output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            return process.returncode == 0
            
        except Exception as e:
            print(f"Thumbnail generation error: {e}")
            return False
