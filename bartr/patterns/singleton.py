"""
Singleton Pattern Implementation for Bartr
Handles shared resources and ensures single instances
"""

import threading
import time
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from bartr.models import malaysia_now


class SingletonMeta(type):
    """Metaclass for implementing thread-safe Singleton pattern"""
    
    _instances = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                # Double-check locking pattern
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class ConfigManager(metaclass=SingletonMeta):
    """Singleton configuration manager for application settings"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._config_file = 'config.json'
        self._lock = threading.Lock()
        self._last_loaded = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r') as f:
                    self._config = json.load(f)
                self._last_loaded = malaysia_now()
            else:
                self._config = self._get_default_config()
                self._save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            'app': {
                'name': 'Bartr',
                'version': '1.0.0',
                'debug': False,
                'secret_key': 'default-secret-key',
                'session_timeout': 3600
            },
            'database': {
                'pool_size': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'echo': False
            },
            'cache': {
                'default_timeout': 300,
                'max_entries': 1000,
                'cleanup_interval': 600
            },
            'search': {
                'default_strategy': 'basic',
                'max_results': 50,
                'fuzzy_threshold': 0.3
            },
            'notifications': {
                'batch_size': 100,
                'retry_attempts': 3,
                'retry_delay': 60
            },
            'upload': {
                'max_file_size': 5242880,  # 5MB
                'allowed_extensions': ['.jpg', '.jpeg', '.png', '.gif'],
                'upload_folder': 'uploads'
            },
            'trade': {
                'fairness_threshold': 50,
                'auto_expire_days': 30,
                'max_proposals_per_user': 10
            }
        }
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self._config_file, 'w') as f:
                json.dump(self._config, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value using dot notation"""
        with self._lock:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any, save: bool = True):
        """Set configuration value using dot notation"""
        with self._lock:
            keys = key.split('.')
            config = self._config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            if save:
                self._save_config()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, {})
    
    def reload(self):
        """Reload configuration from file"""
        with self._lock:
            self._load_config()
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if configuration is stale and needs reloading"""
        if not self._last_loaded:
            return True
        
        age = (malaysia_now() - self._last_loaded).total_seconds()
        return age > max_age_seconds


class CacheManager(metaclass=SingletonMeta):
    """Singleton cache manager for application-wide caching"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._config = ConfigManager()
        self._default_timeout = self._config.get('cache.default_timeout', 300)
        self._max_entries = self._config.get('cache.max_entries', 1000)
        self._cleanup_interval = self._config.get('cache.cleanup_interval', 600)
        self._last_cleanup = time.time()
    
    def get(self, key: str, default=None) -> Any:
        """Get value from cache"""
        with self._lock:
            self._cleanup_if_needed()
            
            if key in self._cache:
                entry = self._cache[key]
                if self._is_expired(entry):
                    del self._cache[key]
                    return default
                
                # Update access time
                entry['accessed_at'] = time.time()
                return entry['value']
            
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            self._cleanup_if_needed()
            
            if timeout is None:
                timeout = self._default_timeout
            
            # Check cache size limit
            if len(self._cache) >= self._max_entries and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = {
                'value': value,
                'created_at': time.time(),
                'accessed_at': time.time(),
                'expires_at': time.time() + timeout if timeout > 0 else None
            }
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if self._is_expired(entry):
                    del self._cache[key]
                    return False
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if self._is_expired(entry))
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'max_entries': self._max_entries,
                'default_timeout': self._default_timeout,
                'last_cleanup': self._last_cleanup
            }
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        if entry.get('expires_at') is None:
            return False
        return time.time() > entry['expires_at']
    
    def _cleanup_if_needed(self):
        """Cleanup expired entries if needed"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self._cache[key]
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['accessed_at']
        )
        del self._cache[lru_key]


class DatabaseManager(metaclass=SingletonMeta):
    """Singleton database connection manager"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config = ConfigManager()
        self._connections = {}
        self._lock = threading.Lock()
        self._pool_size = self._config.get('database.pool_size', 10)
        self._pool_timeout = self._config.get('database.pool_timeout', 30)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        return {
            'pool_size': self._pool_size,
            'pool_timeout': self._pool_timeout,
            'active_connections': len(self._connections),
            'pool_recycle': self._config.get('database.pool_recycle', 3600),
            'echo': self._config.get('database.echo', False)
        }
    
    def get_engine_params(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine parameters"""
        return {
            'pool_size': self._pool_size,
            'pool_timeout': self._pool_timeout,
            'pool_recycle': self._config.get('database.pool_recycle', 3600),
            'echo': self._config.get('database.echo', False)
        }


class NotificationManager(metaclass=SingletonMeta):
    """Singleton notification queue manager"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config = ConfigManager()
        self._queue = []
        self._lock = threading.Lock()
        self._batch_size = self._config.get('notifications.batch_size', 100)
        self._retry_attempts = self._config.get('notifications.retry_attempts', 3)
        self._retry_delay = self._config.get('notifications.retry_delay', 60)
        self._failed_notifications = []
    
    def add_notification(self, notification_data: Dict[str, Any]):
        """Add notification to queue"""
        with self._lock:
            notification_data['created_at'] = malaysia_now()
            notification_data['attempts'] = 0
            self._queue.append(notification_data)
    
    def get_batch(self, size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get batch of notifications for processing"""
        if size is None:
            size = self._batch_size
        
        with self._lock:
            batch = self._queue[:size]
            self._queue = self._queue[size:]
            return batch
    
    def mark_failed(self, notification: Dict[str, Any]):
        """Mark notification as failed"""
        with self._lock:
            notification['attempts'] += 1
            notification['last_attempt'] = malaysia_now()
            
            if notification['attempts'] < self._retry_attempts:
                # Schedule for retry
                retry_time = malaysia_now() + timedelta(seconds=self._retry_delay)
                notification['retry_at'] = retry_time
                self._failed_notifications.append(notification)
            else:
                # Give up after max attempts
                print(f"Notification failed after {self._retry_attempts} attempts: {notification}")
    
    def get_retry_notifications(self) -> List[Dict[str, Any]]:
        """Get notifications ready for retry"""
        with self._lock:
            current_time = malaysia_now()
            ready_for_retry = [
                n for n in self._failed_notifications
                if n.get('retry_at', current_time) <= current_time
            ]
            
            # Remove from failed list
            for notification in ready_for_retry:
                self._failed_notifications.remove(notification)
            
            return ready_for_retry
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification queue statistics"""
        with self._lock:
            return {
                'queue_size': len(self._queue),
                'failed_count': len(self._failed_notifications),
                'batch_size': self._batch_size,
                'retry_attempts': self._retry_attempts,
                'retry_delay': self._retry_delay
            }


class SessionManager(metaclass=SingletonMeta):
    """Singleton session manager for user sessions"""
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config = ConfigManager()
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._session_timeout = self._config.get('app.session_timeout', 3600)
    
    def create_session(self, user_id: int, session_data: Dict[str, Any] = None) -> str:
        """Create a new session"""
        import secrets
        
        with self._lock:
            session_id = secrets.token_urlsafe(32)
            
            self._sessions[session_id] = {
                'user_id': user_id,
                'created_at': malaysia_now(),
                'last_accessed': malaysia_now(),
                'data': session_data or {}
            }
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                
                # Check if session is expired
                if self._is_session_expired(session):
                    del self._sessions[session_id]
                    return None
                
                # Update last accessed time
                session['last_accessed'] = malaysia_now()
                return session
            
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]):
        """Update session data"""
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                if not self._is_session_expired(session):
                    session['data'].update(data)
                    session['last_accessed'] = malaysia_now()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with self._lock:
            expired_sessions = [
                session_id for session_id, session in self._sessions.items()
                if self._is_session_expired(session)
            ]
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        with self._lock:
            return len(self._sessions)
    
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """Check if session is expired"""
        last_accessed = session.get('last_accessed', malaysia_now())
        age = (malaysia_now() - last_accessed).total_seconds()
        return age > self._session_timeout


# Convenience functions to get singleton instances
def get_config() -> ConfigManager:
    """Get the global configuration manager instance"""
    return ConfigManager()


def get_cache() -> CacheManager:
    """Get the global cache manager instance"""
    return CacheManager()


def get_database() -> DatabaseManager:
    """Get the global database manager instance"""
    return DatabaseManager()


def get_notifications() -> NotificationManager:
    """Get the global notification manager instance"""
    return NotificationManager()


def get_sessions() -> SessionManager:
    """Get the global session manager instance"""
    return SessionManager()