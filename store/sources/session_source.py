import os
import time
import logging
from pathlib import Path
from typing import List

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from store.sources.base import DataSource
from store.sources.session_parser import parse_session_file
from models.types import AgentSession

logger = logging.getLogger(__name__)


class SessionDataSource(DataSource[List[AgentSession]]): 
    """
    Watches opencode sessions directory for changes using watchdog
    Loads all JSON files and maintains an up-to-date list of active sessions
    """

    def __init__(self, config: dict):
        sessions_dir = config.get("directory")
        if sessions_dir is None:
            sessions_dir = os.path.join(Path.home(), ".config", "opencode", "sessions")
        self.sessions_dir = str(Path(sessions_dir).expanduser())
        self._refresh_interval = config.get("refresh_interval", 30.0)
        
        self.sessions: List[AgentSession] = []
        self._last_reload_time: float = 0.0
        self._throttle_delay: float = 1.0
        self._throttle_skipped: bool = False
        
        self.observer = Observer()
        self.event_handler = SessionFileHandler(self)
        
    def start_watching(self):
        """Start watching the sessions directory for changes"""
        if os.path.isdir(self.sessions_dir):
            logger.info("[Session] start watching: %s", self.sessions_dir)
            self.observer.schedule(self.event_handler, self.sessions_dir, recursive=False)
            self.observer.start()
            self.load_all_sessions()
        else:
            logger.warning("[Session] directory not found: %s", self.sessions_dir)
    
    def stop_watching(self):
        """Stop watching the directory"""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    def _throttled_reload(self):
        now = time.time()
        elapsed = now - self._last_reload_time
        if elapsed < self._throttle_delay:
            self._throttle_skipped = True
            return
        had_pending = self._throttle_skipped
        self._last_reload_time = now
        self._throttle_skipped = False
        self.load_all_sessions()
        if had_pending:
            self._last_reload_time = time.time()
            self.load_all_sessions()

    def load_all_sessions(self):
        """Load all session JSON files from the directory"""
        if not os.path.isdir(self.sessions_dir):
            return
        new_sessions = []

        json_files = [f for f in os.listdir(self.sessions_dir) if f.endswith(".json")]
        for filename in json_files:
            filepath = os.path.join(self.sessions_dir, filename)
            session = parse_session_file(filepath)
            if session:
                new_sessions.append(session)

        self.sessions = new_sessions
        logger.info("[Session] loaded %d sessions from %d files", len(new_sessions), len(json_files))
    
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

        src = event.src_path
        if src.endswith(".json") and os.path.basename(src).startswith("ses_"):
            logger.info("[Session] file created: %s", src)
            self.session_source._throttled_reload()

    def on_modified(self, event: FileSystemEvent):
        """Handle when a session file is modified"""
        if event.is_directory:
            return

        src = event.src_path
        if src.endswith(".json") and os.path.basename(src).startswith("ses_"):
            logger.info("[Session] file modified: %s", src)
            self.session_source._throttled_reload()

    def on_deleted(self, event: FileSystemEvent):
        """Handle when a session file is deleted"""
        if event.is_directory:
            return

        src = event.src_path
        if src.endswith(".json") and os.path.basename(src).startswith("ses_"):
            logger.info("[Session] file deleted: %s", src)
            self.session_source._throttled_reload()