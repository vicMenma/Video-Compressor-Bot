# database.py
import json
import os
import aiofiles
from typing import Dict, Any, Optional
import asyncio

class Database:
    def __init__(self):
        self.db_path = "/content/Video-Compressor-Bot/database.json"
        self.users_data = {}
        self.queue_data = {}
        self.lock = asyncio.Lock()
    
    async def connect(self):
        """Initialize database"""
        if os.path.exists(self.db_path):
            async with aiofiles.open(self.db_path, 'r') as f:
                content = await f.read()
                data = json.loads(content) if content else {}
                self.users_data = data.get('users', {})
                self.queue_data = data.get('queue', {})
        
        print("🗄️ Database connected")
    
    async def disconnect(self):
        """Save and close database"""
        await self.save_data()
        print("🗄️ Database disconnected")
    
    async def save_data(self):
        """Save data to file"""
        async with self.lock:
            data = {
                'users': self.users_data,
                'queue': self.queue_data
            }
            
            async with aiofiles.open(self.db_path, 'w') as f:
                await f.write(json.dumps(data, indent=4))
    
    # User management
    async def add_user(self, user_id: int, user_data: Dict[str, Any]):
        """Add or update user"""
        async with self.lock:
            self.users_data[str(user_id)] = {
                'id': user_id,
                'first_name': user_data.get('first_name', ''),
                'username': user_data.get('username', ''),
                'join_date': user_data.get('join_date', ''),
                'settings': self.get_default_settings(),
                'total_compressed': 0,
                'total_size_saved': 0
            }
        await self.save_data()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data"""
        return self.users_data.get(str(user_id))
    
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]):
        """Update user settings"""
        async with self.lock:
            if str(user_id) in self.users_data:
                self.users_data[str(user_id)]['settings'].update(settings)
        await self.save_data()
    
    async def increment_user_stats(self, user_id: int, size_saved: int):
        """Increment user compression stats"""
        async with self.lock:
            if str(user_id) in self.users_data:
                self.users_data[str(user_id)]['total_compressed'] += 1
                self.users_data[str(user_id)]['total_size_saved'] += size_saved
        await self.save_data()
    
    # Queue management
    async def add_to_queue(self, user_id: int, task_data: Dict[str, Any]):
        """Add task to queue"""
        async with self.lock:
            task_id = f"{user_id}_{len(self.queue_data)}"
            self.queue_data[task_id] = {
                'user_id': user_id,
                'status': 'queued',
                'created_at': task_data.get('created_at'),
                'file_name': task_data.get('file_name'),
                'file_size': task_data.get('file_size'),
                'settings': task_data.get('settings', {})
            }
        await self.save_data()
        return task_id
    
    async def update_queue_status(self, task_id: str, status: str, progress: int = 0):
        """Update queue task status"""
        async with self.lock:
            if task_id in self.queue_data:
                self.queue_data[task_id]['status'] = status
                self.queue_data[task_id]['progress'] = progress
        await self.save_data()
    
    async def remove_from_queue(self, task_id: str):
        """Remove task from queue"""
        async with self.lock:
            if task_id in self.queue_data:
                del self.queue_data[task_id]
        await self.save_data()
    
    async def get_user_queue(self, user_id: int) -> Dict[str, Any]:
        """Get user's queue tasks"""
        user_tasks = {}
        for task_id, task_data in self.queue_data.items():
            if task_data['user_id'] == user_id:
                user_tasks[task_id] = task_data
        return user_tasks
    
    async def get_queue_position(self, task_id: str) -> int:
        """Get task position in queue"""
        queued_tasks = [tid for tid, task in self.queue_data.items() 
                       if task['status'] == 'queued']
        try:
            return queued_tasks.index(task_id) + 1
        except ValueError:
            return 0
    
    # Statistics
    async def get_total_users(self) -> int:
        """Get total users count"""
        return len(self.users_data)
    
    async def get_total_compressions(self) -> int:
        """Get total compressions count"""
        return sum(user.get('total_compressed', 0) for user in self.users_data.values())
    
    def get_default_settings(self) -> Dict[str, str]:
        """Get default user settings"""
        return {
            'preset': 'medium',
            'resolution': 'keep',
            'audio_bitrate': '128k',
            'video_bitrate': '2000k',
            'remove_audio': False,
            'custom_name': '',
            'thumbnail': True
        }