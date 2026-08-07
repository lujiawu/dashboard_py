import os
import time
import logging
from pathlib import Path
from typing import Callable, List, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from store.sources.base import DataSource
from store.sources.session_parser import parse_session_file
from models.types import AgentSession

logger = logging.getLogger(__name__)


class SessionDataSource(DataSource[List[AgentSession]]): 
    """
    Watches agent-status.json for changes using watchdog.
    """

    def __init__(self, config: dict):
        status_file = config.get("directory")
        if status_file is None:
            status_file = os.path.join(Path.home(), ".cache", "agent-status.json")
        self.status_file = str(Path(status_file).expanduser())
        self._refresh_interval = config.get("refresh_interval", 30.0)
        
        self.sessions: List[AgentSession] = []
        self._last_reload_time: float = 0.0
        self._throttle_delay: float = 1.0
        self._pending: bool = False
        self._on_reload: Optional[Callable[[], None]] = None

        self.observer = Observer()
        self.event_handler = SessionFileHandler(self)
        
    def start_watching(self):
        watch_dir = os.path.dirname(self.status_file) or "."
        if os.path.isfile(self.status_file):
            logger.info("[Session] start watching: %s", self.status_file)
            self.observer.schedule(self.event_handler, watch_dir, recursive=False)
            self.observer.start()
            self._do_reload()
        else:
            logger.warning("[Session] file not found: %s", self.status_file)
    
    def stop_watching(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    def set_on_reload(self, callback: Optional[Callable[[], None]]):
        self._on_reload = callback

    def _schedule_reload(self):
        now = time.time()
        gap = now - self._last_reload_time
        if gap < self._throttle_delay:
            self._pending = True
            logger.debug("[Session] throttle skip (%.0fms < %dms), pending=True", gap * 1000, self._throttle_delay * 1000)
            return
        logger.info("[Session] throttle fire after %.0fms", gap * 1000)
        self._do_reload()

    def _do_reload(self):
        t0 = time.perf_counter()
        self.load_sessions()
        self._last_reload_time = time.time()
        self._pending = False
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("[Session] reload done in %.0fms", elapsed)
        if self._on_reload:
            self._on_reload()

    def compensation_poll(self):
        if self._pending and time.time() - self._last_reload_time >= self._throttle_delay:
            logger.info("[Session] compensation poll fired")
            self._do_reload()

    def load_sessions(self):
        if not os.path.isfile(self.status_file):
            return
        self.sessions = parse_session_file(self.status_file) or []
        logger.info("[Session] loaded %d sessions", len(self.sessions))
    
    async def fetch(self) -> List[AgentSession]:
        return self.sessions

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval


class SessionFileHandler(FileSystemEventHandler):
    
    def __init__(self, session_source: SessionDataSource):
        self.session_source = session_source
    
    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return

        src = os.path.abspath(event.src_path)
        if src == self.session_source.status_file:
            logger.info("[Session] file created: %s", src)
            self.session_source._schedule_reload()

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return

        src = os.path.abspath(event.src_path)
        if src == self.session_source.status_file:
            logger.info("[Session] file modified: %s", src)
            self.session_source._schedule_reload()

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory:
            return

        src = os.path.abspath(event.src_path)
        if src == self.session_source.status_file:
            logger.info("[Session] file deleted: %s", src)
            self.session_source._schedule_reload()
