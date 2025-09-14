# Transcoding Service for Watch Media Server
import os
import subprocess
import threading
import time
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta
import sqlite3

class TranscodingService:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.temp_dir = tempfile.mkdtemp(prefix='watch_transcode_')
        self.active_transcodes = {}
        self.transcode_queue = []
        self.max_concurrent_transcodes = int(os.getenv('MAX_CONCURRENT_TRANSCODES', '2'))
        self.ffmpeg_path = self.find_ffmpeg()
        self.supported_formats = {
            'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'],
            'audio': ['mp3', 'aac', 'flac', 'ogg', 'wav', 'm4a']
        }
        
        # Quality presets
        self.quality_presets = {
            '240p': {
                'video_bitrate': '500k',
                'audio_bitrate': '64k',
                'resolution': '426x240',
                'crf': 28
            },
            '360p': {
                'video_bitrate': '800k',
                'audio_bitrate': '96k',
                'resolution': '640x360',
                'crf': 26
            },
            '480p': {
                'video_bitrate': '1200k',
                'audio_bitrate': '128k',
                'resolution': '854x480',
                'crf': 24
            },
            '720p': {
                'video_bitrate': '2500k',
                'audio_bitrate': '192k',
                'resolution': '1280x720',
                'crf': 22
            },
            '1080p': {
                'video_bitrate': '5000k',
                'audio_bitrate': '256k',
                'resolution': '1920x1080',
                'crf': 20
            },
            '4k': {
                'video_bitrate': '15000k',
                'audio_bitrate': '320k',
                'resolution': '3840x2160',
                'crf': 18
            }
        }
        
        self.init_transcoding_tables()
        self.start_transcode_worker()
    
    def find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        possible_paths = [
            'ffmpeg',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            'C:\\ffmpeg\\bin\\ffmpeg.exe'
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def init_transcoding_tables(self):
        """Initialize transcoding-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Transcoding jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcoding_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER,
                input_path TEXT NOT NULL,
                output_path TEXT,
                quality TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        # Transcoding cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcoding_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER,
                quality TEXT,
                file_path TEXT UNIQUE NOT NULL,
                file_size INTEGER,
                duration REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (media_id) REFERENCES media_files (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_media_info(self, file_path: str) -> Dict:
        """Get media file information using FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {}
            
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            audio_stream = None
            
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            return {
                'duration': float(info.get('format', {}).get('duration', 0)),
                'size': int(info.get('format', {}).get('size', 0)),
                'bitrate': int(info.get('format', {}).get('bit_rate', 0)),
                'video': {
                    'codec': video_stream.get('codec_name', '') if video_stream else '',
                    'width': video_stream.get('width', 0) if video_stream else 0,
                    'height': video_stream.get('height', 0) if video_stream else 0,
                    'bitrate': int(video_stream.get('bit_rate', 0)) if video_stream else 0,
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0
                } if video_stream else None,
                'audio': {
                    'codec': audio_stream.get('codec_name', '') if audio_stream else '',
                    'channels': audio_stream.get('channels', 0) if audio_stream else 0,
                    'bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else 0,
                    'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream else 0
                } if audio_stream else None
            }
        except Exception as e:
            print(f"Error getting media info: {e}")
            return {}
    
    def get_optimal_quality(self, media_info: Dict, requested_quality: str) -> str:
        """Determine optimal quality based on source and request"""
        if not media_info.get('video'):
            return requested_quality
        
        source_height = media_info['video']['height']
        
        # If source is lower quality than requested, return source quality
        quality_order = ['240p', '360p', '480p', '720p', '1080p', '4k']
        source_quality = None
        
        if source_height <= 240:
            source_quality = '240p'
        elif source_height <= 360:
            source_quality = '360p'
        elif source_height <= 480:
            source_quality = '480p'
        elif source_height <= 720:
            source_quality = '720p'
        elif source_height <= 1080:
            source_quality = '1080p'
        else:
            source_quality = '4k'
        
        # Return the lower of source and requested quality
        source_index = quality_order.index(source_quality)
        requested_index = quality_order.index(requested_quality)
        
        return quality_order[min(source_index, requested_index)]
    
    def get_cached_transcode(self, media_id: int, quality: str) -> Optional[str]:
        """Check if transcoded version already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path FROM transcoding_cache
            WHERE media_id = ? AND quality = ? AND file_path IS NOT NULL
        ''', (media_id, quality))
        
        result = cursor.fetchone()
        if result and os.path.exists(result[0]):
            # Update last accessed time
            cursor.execute('''
                UPDATE transcoding_cache SET last_accessed = CURRENT_TIMESTAMP
                WHERE media_id = ? AND quality = ?
            ''', (media_id, quality))
            conn.commit()
            conn.close()
            return result[0]
        
        conn.close()
        return None
    
    def queue_transcode(self, media_id: int, input_path: str, quality: str) -> int:
        """Queue a transcoding job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transcoding_jobs (media_id, input_path, quality, status)
            VALUES (?, ?, ?, 'pending')
        ''', (media_id, input_path, quality))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add to processing queue
        self.transcode_queue.append(job_id)
        
        return job_id
    
    def start_transcode_worker(self):
        """Start background worker for transcoding"""
        def worker():
            while True:
                try:
                    if (len(self.active_transcodes) < self.max_concurrent_transcodes and 
                        self.transcode_queue):
                        
                        job_id = self.transcode_queue.pop(0)
                        self.process_transcode_job(job_id)
                    
                    time.sleep(1)
                except Exception as e:
                    print(f"Transcode worker error: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def process_transcode_job(self, job_id: int):
        """Process a transcoding job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT media_id, input_path, quality FROM transcoding_jobs
            WHERE id = ? AND status = 'pending'
        ''', (job_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        media_id, input_path, quality = result
        
        # Check if already cached
        cached_path = self.get_cached_transcode(media_id, quality)
        if cached_path:
            cursor.execute('''
                UPDATE transcoding_jobs SET 
                    status = 'completed', 
                    output_path = ?,
                    progress = 100,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (cached_path, job_id))
            conn.commit()
            conn.close()
            return
        
        # Start transcoding
        self.active_transcodes[job_id] = {
            'process': None,
            'start_time': time.time()
        }
        
        try:
            cursor.execute('''
                UPDATE transcoding_jobs SET 
                    status = 'processing',
                    started_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (job_id,))
            conn.commit()
            
            output_path = self.transcode_file(input_path, quality, job_id)
            
            if output_path and os.path.exists(output_path):
                # Update job as completed
                cursor.execute('''
                    UPDATE transcoding_jobs SET 
                        status = 'completed',
                        output_path = ?,
                        progress = 100,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (output_path, job_id))
                
                # Add to cache
                file_size = os.path.getsize(output_path)
                media_info = self.get_media_info(output_path)
                duration = media_info.get('duration', 0)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO transcoding_cache 
                    (media_id, quality, file_path, file_size, duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (media_id, quality, output_path, file_size, duration))
                
                conn.commit()
            else:
                cursor.execute('''
                    UPDATE transcoding_jobs SET 
                        status = 'failed',
                        error_message = 'Transcoding failed'
                    WHERE id = ?
                ''', (job_id,))
                conn.commit()
        
        except Exception as e:
            cursor.execute('''
                UPDATE transcoding_jobs SET 
                    status = 'failed',
                    error_message = ?
                WHERE id = ?
            ''', (str(e), job_id))
            conn.commit()
        
        finally:
            conn.close()
            if job_id in self.active_transcodes:
                del self.active_transcodes[job_id]
    
    def transcode_file(self, input_path: str, quality: str, job_id: int) -> Optional[str]:
        """Transcode a file to specified quality"""
        try:
            # Get media info
            media_info = self.get_media_info(input_path)
            if not media_info:
                return None
            
            # Determine optimal quality
            optimal_quality = self.get_optimal_quality(media_info, quality)
            preset = self.quality_presets[optimal_quality]
            
            # Generate output filename
            input_file = Path(input_path)
            output_filename = f"{input_file.stem}_{optimal_quality}{input_file.suffix}"
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Build FFmpeg command
            cmd = [
                self.ffmpeg_path, '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:v', preset['video_bitrate'],
                '-b:a', preset['audio_bitrate'],
                '-s', preset['resolution'],
                '-crf', str(preset['crf']),
                '-preset', 'fast',
                '-movflags', '+faststart',
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Start transcoding process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.active_transcodes[job_id]['process'] = process
            
            # Monitor progress
            duration = media_info.get('duration', 0)
            if duration > 0:
                self.monitor_transcode_progress(job_id, duration)
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                print(f"Transcoding failed: {stderr}")
                return None
        
        except Exception as e:
            print(f"Transcoding error: {e}")
            return None
    
    def monitor_transcode_progress(self, job_id: int, duration: float):
        """Monitor transcoding progress"""
        def monitor():
            while job_id in self.active_transcodes:
                process = self.active_transcodes[job_id]['process']
                if not process or process.poll() is not None:
                    break
                
                # Parse FFmpeg output for progress (simplified)
                # In a real implementation, you'd parse stderr for time progress
                time.sleep(2)
                
                # Update progress in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Simple progress estimation based on elapsed time
                elapsed = time.time() - self.active_transcodes[job_id]['start_time']
                estimated_total = elapsed * 2  # Rough estimate
                progress = min(90, (elapsed / estimated_total) * 100)
                
                cursor.execute('''
                    UPDATE transcoding_jobs SET progress = ? WHERE id = ?
                ''', (progress, job_id))
                conn.commit()
                conn.close()
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def get_transcode_status(self, job_id: int) -> Dict:
        """Get transcoding job status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, progress, error_message, output_path, started_at, completed_at
            FROM transcoding_jobs WHERE id = ?
        ''', (job_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'error': 'Job not found'}
        
        status, progress, error_message, output_path, started_at, completed_at = result
        
        return {
            'job_id': job_id,
            'status': status,
            'progress': progress,
            'error_message': error_message,
            'output_path': output_path,
            'started_at': started_at,
            'completed_at': completed_at
        }
    
    def cleanup_old_transcodes(self, max_age_hours: int = 24):
        """Clean up old transcoded files"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find old cache entries
        cursor.execute('''
            SELECT file_path FROM transcoding_cache
            WHERE last_accessed < ?
        ''', (cutoff_time.isoformat(),))
        
        old_files = cursor.fetchall()
        
        # Delete files and database entries
        for (file_path,) in old_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                cursor.execute('DELETE FROM transcoding_cache WHERE file_path = ?', (file_path,))
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")
        
        conn.commit()
        conn.close()
    
    def get_available_qualities(self, media_id: int) -> List[str]:
        """Get available transcoded qualities for a media file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT quality FROM transcoding_cache
            WHERE media_id = ? AND file_path IS NOT NULL
        ''', (media_id,))
        
        qualities = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return qualities
    
    def get_stream_url(self, media_id: int, quality: str = '720p') -> Optional[str]:
        """Get streaming URL for media at specified quality"""
        # Check cache first
        cached_path = self.get_cached_transcode(media_id, quality)
        if cached_path:
            return f"/api/stream/{media_id}?quality={quality}"
        
        # Check if original quality is suitable
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM media_files WHERE id = ?', (media_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            original_path = result[0]
            media_info = self.get_media_info(original_path)
            optimal_quality = self.get_optimal_quality(media_info, quality)
            
            if optimal_quality == quality:
                # Original is suitable, stream directly
                return f"/api/stream/{media_id}"
            else:
                # Queue transcoding
                job_id = self.queue_transcode(media_id, original_path, quality)
                return f"/api/stream/{media_id}?quality={quality}&job_id={job_id}"
        
        return None
