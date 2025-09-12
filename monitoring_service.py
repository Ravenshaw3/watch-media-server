# Performance Monitoring Service for Watch Media Server
import os
import time
import psutil
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import request, Response, current_app
import sqlite3
import threading

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('watch_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('watch_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('watch_active_connections', 'Active connections')
MEDIA_FILES_COUNT = Gauge('watch_media_files_total', 'Total media files')
USERS_COUNT = Gauge('watch_users_total', 'Total users')
CACHE_HIT_RATE = Gauge('watch_cache_hit_rate', 'Cache hit rate percentage')
DISK_USAGE = Gauge('watch_disk_usage_bytes', 'Disk usage in bytes', ['path'])
MEMORY_USAGE = Gauge('watch_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('watch_cpu_usage_percent', 'CPU usage percentage')
TRANSCODE_JOBS = Gauge('watch_transcode_jobs_total', 'Transcoding jobs', ['status'])

class PerformanceMonitor:
    def __init__(self, db_path: str = 'watch.db'):
        self.db_path = db_path
        self.start_time = time.time()
        self.request_times = {}
        self.active_requests = 0
        self.performance_data = {
            'requests_per_minute': [],
            'response_times': [],
            'error_rates': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        self.monitoring_enabled = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
        
        if self.monitoring_enabled:
            self.start_background_monitoring()
    
    def start_background_monitoring(self):
        """Start background monitoring thread"""
        def monitor():
            while True:
                try:
                    self.collect_system_metrics()
                    self.update_prometheus_metrics()
                    time.sleep(30)  # Collect metrics every 30 seconds
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        logger.info("Performance monitoring started")
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Disk usage for media library
            media_path = os.getenv('MEDIA_LIBRARY_PATH', '/media')
            if os.path.exists(media_path):
                disk_usage = psutil.disk_usage(media_path)
                DISK_USAGE.labels(path=media_path).set(disk_usage.used)
            
            # Store historical data
            current_time = datetime.now()
            self.performance_data['memory_usage'].append({
                'timestamp': current_time,
                'value': memory.used,
                'percent': memory.percent
            })
            
            self.performance_data['cpu_usage'].append({
                'timestamp': current_time,
                'value': cpu_percent
            })
            
            # Keep only last 100 data points
            for key in self.performance_data:
                if len(self.performance_data[key]) > 100:
                    self.performance_data[key] = self.performance_data[key][-100:]
        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def update_prometheus_metrics(self):
        """Update Prometheus metrics"""
        try:
            # Update media files count
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM media_files')
            media_count = cursor.fetchone()[0]
            MEDIA_FILES_COUNT.set(media_count)
            
            # Update users count
            cursor.execute('SELECT COUNT(*) FROM users')
            users_count = cursor.fetchone()[0]
            USERS_COUNT.set(users_count)
            
            # Update transcoding jobs
            cursor.execute('SELECT status, COUNT(*) FROM transcoding_jobs GROUP BY status')
            transcode_jobs = cursor.fetchall()
            for status, count in transcode_jobs:
                TRANSCODE_JOBS.labels(status=status).set(count)
            
            conn.close()
            
            # Update active connections
            ACTIVE_CONNECTIONS.set(self.active_requests)
        
        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record request metrics"""
        if not self.monitoring_enabled:
            return
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Store historical data
        current_time = datetime.now()
        self.performance_data['requests_per_minute'].append({
            'timestamp': current_time,
            'method': method,
            'endpoint': endpoint,
            'status': status_code
        })
        
        self.performance_data['response_times'].append({
            'timestamp': current_time,
            'duration': duration,
            'endpoint': endpoint
        })
        
        if status_code >= 400:
            self.performance_data['error_rates'].append({
                'timestamp': current_time,
                'status': status_code,
                'endpoint': endpoint
            })
        
        # Keep only last 1000 data points
        for key in self.performance_data:
            if len(self.performance_data[key]) > 1000:
                self.performance_data[key] = self.performance_data[key][-1000:]
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        uptime = time.time() - self.start_time
        
        # Calculate requests per minute
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            req for req in self.performance_data['requests_per_minute']
            if req['timestamp'] > one_minute_ago
        ]
        requests_per_minute = len(recent_requests)
        
        # Calculate average response time
        recent_responses = [
            resp for resp in self.performance_data['response_times']
            if resp['timestamp'] > one_minute_ago
        ]
        avg_response_time = 0
        if recent_responses:
            avg_response_time = sum(resp['duration'] for resp in recent_responses) / len(recent_responses)
        
        # Calculate error rate
        recent_errors = [
            err for err in self.performance_data['error_rates']
            if err['timestamp'] > one_minute_ago
        ]
        error_rate = 0
        if recent_requests:
            error_rate = (len(recent_errors) / len(recent_requests)) * 100
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        return {
            'uptime_seconds': uptime,
            'uptime_human': str(timedelta(seconds=int(uptime))),
            'requests_per_minute': requests_per_minute,
            'average_response_time': round(avg_response_time, 3),
            'error_rate_percent': round(error_rate, 2),
            'memory_usage_percent': memory.percent,
            'memory_usage_mb': round(memory.used / 1024 / 1024, 2),
            'cpu_usage_percent': cpu_percent,
            'active_requests': self.active_requests,
            'monitoring_enabled': self.monitoring_enabled
        }
    
    def get_detailed_metrics(self, hours: int = 24) -> Dict:
        """Get detailed metrics for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_data = {}
        for key, data in self.performance_data.items():
            filtered_data[key] = [
                item for item in data
                if item['timestamp'] > cutoff_time
            ]
        
        return {
            'time_period_hours': hours,
            'data_points': {key: len(data) for key, data in filtered_data.items()},
            'metrics': filtered_data
        }
    
    def get_health_status(self) -> Dict:
        """Get system health status"""
        try:
            # Check database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            db_status = 'healthy'
            conn.close()
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        # Check system resources
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        disk = psutil.disk_usage('/')
        
        # Determine overall health
        health_status = 'healthy'
        issues = []
        
        if memory.percent > 90:
            health_status = 'warning'
            issues.append('High memory usage')
        
        if cpu_percent > 90:
            health_status = 'warning'
            issues.append('High CPU usage')
        
        if disk.percent > 90:
            health_status = 'warning'
            issues.append('High disk usage')
        
        if db_status != 'healthy':
            health_status = 'critical'
            issues.append('Database issues')
        
        return {
            'status': health_status,
            'issues': issues,
            'database': db_status,
            'memory_percent': memory.percent,
            'cpu_percent': cpu_percent,
            'disk_percent': disk.percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up old performance data"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for key in self.performance_data:
            self.performance_data[key] = [
                item for item in self.performance_data[key]
                if item['timestamp'] > cutoff_time
            ]
        
        logger.info(f"Cleaned up performance data older than {days} days")

# Performance monitoring decorators
def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            status_code = 200
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.endpoint or func.__name__
            method = request.method or 'GET'
            
            # Record metrics if monitoring is enabled
            if hasattr(current_app, 'performance_monitor'):
                current_app.performance_monitor.record_request(method, endpoint, status_code, duration)
    
    return wrapper

def track_active_requests(func):
    """Decorator to track active requests"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if hasattr(current_app, 'performance_monitor'):
            current_app.performance_monitor.active_requests += 1
        
        try:
            return func(*args, **kwargs)
        finally:
            if hasattr(current_app, 'performance_monitor'):
                current_app.performance_monitor.active_requests -= 1
    
    return wrapper

# Performance monitor instance
performance_monitor = PerformanceMonitor()
