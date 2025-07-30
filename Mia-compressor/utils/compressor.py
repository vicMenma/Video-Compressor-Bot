# compressor.py
import os
import asyncio
import subprocess
import json
import time
from typing import Dict, Any, Callable, Optional
from PIL import Image
import aiofiles

class VideoCompressor:
    def __init__(self):
        self.active_processes = {}
    
    async def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                
                # Extract video stream info
                video_stream = None
                audio_stream = None
                
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video' and not video_stream:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and not audio_stream:
                        audio_stream = stream
                
                return {
                    'duration': float(info['format'].get('duration', 0)),
                    'size': int(info['format'].get('size', 0)),
                    'bitrate': int(info['format'].get('bit_rate', 0)),
                    'format': info['format'].get('format_name', ''),
                    'video': {
                        'codec': video_stream.get('codec_name', '') if video_stream else '',
                        'width': int(video_stream.get('width', 0)) if video_stream else 0,
                        'height': int(video_stream.get('height', 0)) if video_stream else 0,
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
                        'bitrate': int(video_stream.get('bit_rate', 0)) if video_stream else 0
                    },
                    'audio': {
                        'codec': audio_stream.get('codec_name', '') if audio_stream else '',
                        'bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else 0,
                        'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream else 0,
                        'channels': int(audio_stream.get('channels', 0)) if audio_stream else 0
                    } if audio_stream else None
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}
    
    async def generate_thumbnail(self, video_path: str, output_path: str, 
                               timestamp: float = None) -> bool:
        """Generate video thumbnail"""
        try:
            if timestamp is None:
                # Get duration and use middle frame
                info = await self.get_video_info(video_path)
                timestamp = info.get('duration', 0) / 2
            
            cmd = [
                'ffmpeg', '-i', video_path, '-ss', str(timestamp),
                '-vframes', '1', '-q:v', '2', '-y', output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Resize thumbnail to reasonable size
                with Image.open(output_path) as img:
                    img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                    img.save(output_path)
                return True
                
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
        
        return False
    
    async def compress_video(self, input_path: str, output_path: str,
                           settings: Dict[str, Any], task_id: str,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Compress video with given settings"""
        
        # Get video info
        video_info = await self.get_video_info(input_path)
        if not video_info:
            return {'success': False, 'error': 'Could not analyze video'}
        
        # Build FFmpeg command
        cmd = ['ffmpeg', '-i', input_path]
        
        # Video codec and quality
        preset = settings.get('preset', 'medium')
        crf = settings.get('crf', '24')
        
        cmd.extend(['-c:v', 'libx264', '-preset', preset, '-crf', crf])
        
        # Resolution
        resolution = settings.get('resolution', 'keep')
        if resolution != 'keep' and resolution in ['240p', '360p', '480p', '720p', '1080p']:
            resolution_map = {
                '240p': '426:240',
                '360p': '640:360', 
                '480p': '854:480',
                '720p': '1280:720',
                '1080p': '1920:1080'
            }
            cmd.extend(['-vf', f'scale={resolution_map[resolution]}'])
        
        # Video bitrate
        video_bitrate = settings.get('video_bitrate')
        if video_bitrate and video_bitrate != 'auto':
            cmd.extend(['-b:v', video_bitrate])
        
        # Audio settings
        if settings.get('remove_audio', False):
            cmd.extend(['-an'])
        else:
            cmd.extend(['-c:a', 'aac'])
            audio_bitrate = settings.get('audio_bitrate', '128k')
            cmd.extend(['-b:a', audio_bitrate])
        
        # Output settings
        cmd.extend(['-movflags', '+faststart', '-y', output_path])
        
        # Start compression
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.active_processes[task_id] = process
            
            # Monitor progress
            if progress_callback:
                asyncio.create_task(
                    self._monitor_progress(process, video_info['duration'], 
                                         progress_callback, task_id)
                )
            
            stdout, stderr = await process.communicate()
            
            # Remove from active processes
            if task_id in self.active_processes:
                del self.active_processes[task_id]
            
            if process.returncode == 0:
                # Get output file info
                output_info = await self.get_video_info(output_path)
                compression_time = time.time() - start_time
                
                original_size = video_info.get('size', 0)
                compressed_size = output_info.get('size', 0)
                size_reduction = original_size - compressed_size
                compression_ratio = (size_reduction / original_size * 100) if original_size > 0 else 0
                
                return {
                    'success': True,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'size_reduction': size_reduction,
                    'compression_ratio': compression_ratio,
                    'compression_time': compression_time,
                    'output_info': output_info
                }
            else:
                error_msg = stderr.decode() if stderr else 'Unknown compression error'
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            if task_id in self.active_processes:
                del self.active_processes[task_id]
            return {'success': False, 'error': str(e)}
    
    async def _monitor_progress(self, process, duration, callback, task_id):
        """Monitor FFmpeg progress"""
        try:
            while process.returncode is None:
                if process.stderr:
                    line = await process.stderr.readline()
                    if line:
                        line = line.decode().strip()
                        if 'time=' in line:
                            # Extract time progress
                            time_str = line.split('time=')[1].split(' ')[0]
                            try:
                                time_parts = time_str.split(':')
                                current_seconds = (float(time_parts[0]) * 3600 + 
                                                 float(time_parts[1]) * 60 + 
                                                 float(time_parts[2]))
                                
                                progress = min(100, (current_seconds / duration) * 100)
                                await callback(task_id, int(progress))
                            except:
                                pass
                
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Progress monitoring error: {e}")
    
    async def cancel_compression(self, task_id: str) -> bool:
        """Cancel active compression"""
        if task_id in self.active_processes:
            try:
                process = self.active_processes[task_id]
                process.terminate()
                await asyncio.sleep(2)
                
                if process.returncode is None:
                    process.kill()
                
                del self.active_processes[task_id]
                return True
            except Exception as e:
                print(f"Error canceling compression: {e}")
        
        return False
    
    def get_format_info(self, file_path: str) -> Dict[str, str]:
        """Get basic format information"""
        name, ext = os.path.splitext(os.path.basename(file_path))
        
        return {
            'name': name,
            'extension': ext.lower(),
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }