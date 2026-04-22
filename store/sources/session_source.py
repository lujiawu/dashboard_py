import json
import os
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from store.sources.base import DataSource
from models.types import AgentSession

# Maximum attempts when file is locked
MAX_RETRY_ATTEMPTS = 3
RETRY_INTERVAL_SEC = 0.5


class SessionDataSource(DataSource[List[AgentSession]]): 
    """
    Watches opencode sessions directory for changes using watchdog
    Loads all JSON files and maintains an up-to-date list of active sessions
    """

    def __init__(self, 
                 sessions_dir: str = "C:\\Users\\work\\.config\\opencode\\sessions", 
                 refresh_interval: float = 30.0):
        """
        Initialize the session data source
        :param sessions_dir: Directory containing opencode session JSON files
        :param refresh_interval: Interval to rescan directory (backup to file events)
        """
        self.sessions_dir = sessions_dir
        self._refresh_interval = refresh_interval
        
        # Set to store active sessions by ID
        self.sessions: List[AgentSession] = []
        
        # Initialize observer for file changes
        self.observer = Observer()
        self.event_handler = SessionFileHandler(self)
        
    def start_watching(self):
        """Start watching the sessions directory for changes"""
        self.observer.schedule(self.event_handler, self.sessions_dir, recursive=False)
        self.observer.start()
        
        # Load initial sessions
        self.load_all_sessions()
    
    def stop_watching(self):
        """Stop watching the directory"""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    def load_all_sessions(self):
        """Load all session JSON files from the directory"""
        new_sessions = []
        
        # Get all files in the sessions directory
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.sessions_dir, filename)
                
                session = self._load_json_session(filepath)
                if session:
                    new_sessions.append(session)
        
        # Update the stored sessions
        self.sessions = new_sessions
    
    def _load_json_session(self, filepath: str) -> Optional[AgentSession]:
        """Load and parse a single session JSON file with retry logic"""
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract required fields from JSON
                    id_val = data.get("id", "")
                    title = data.get("title", "")
                    directory = data.get("directory", "")
                    
                    # Priority 1: Use top-level status
                    # Priority 2: Use properties.status.type as fallback
                    status = data.get("status", "unknown")
                    if not status or status == "unknown":
                        properties_status = data.get("properties", {}).get("status", {})
                        if isinstance(properties_status, dict) and "type" in properties_status:
                            status = properties_status["type"]
                    
                    start_time = data.get("startTime", "")
                    update_time = data.get("updateTime", "")
                    error = data.get("error")
                    
                    return AgentSession(
                        id=id_val,
                        title=title,
                        directory=Path(directory).name if directory else "",  # Just folder name
                        status=status.lower(),
                        start_time=start_time,
                        update_time=update_time,
                        error=error
                    )
            except (PermissionError, FileNotFoundError, json.JSONDecodeError) as e:
                # If it's the last attempt, skip this file
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    return None
                # Otherwise, wait a bit and retry (for file locks)
                time.sleep(RETRY_INTERVAL_SEC)
            except Exception as e:
                # Unexpected error
                return None
                
        return None
    
    async def fetch(self) -> List[AgentSession]:
        """Return the currently loaded sessions"""
        # We always return the current sessions as they are dynamically updated by the observer
        return self.sessions

    @property
    def refresh_interval(self) -> float:
        """Get the interval for background tasks (not used here since we use event detection)"""
        return self._refresh_interval


class SessionFileHandler(FileSystemEventHandler):
    """Handles file system events for session JSON files"""
    
    def __init__(self, session_source: SessionDataSource):
        self.session_source = session_source
    
    def on_created(self, event: FileSystemEvent):
        """Handle when a session file is created"""
        if event.is_directory:
            return
            
        if event.src_path.endswith(".json"):
            # Reload all sessions when a new one appears
            self.session_source.load_all_sessions()
    
    def on_modified(self, event: FileSystemEvent):
        """Handle when a session file is modified"""
        if event.is_directory:
            return
            
        if event.src_path.endswith(".json"):
            # Reload all sessions when any file changes
            self.session_source.load_all_sessions()
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle when a session file is deleted"""
        if event.is_directory:
            return
            
        if event.src_path.endswith(".json"):
            # Reload all sessions when a file is removed
            self.session_source.load_all_sessions()