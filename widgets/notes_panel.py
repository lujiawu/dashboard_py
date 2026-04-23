from textual.widgets import Static
from textual.widgets import MarkdownViewer
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio
import time


class NotesPanel(MarkdownViewer):
    def __init__(self, notes_file: str = "notes.md"):
        super().__init__(show_table_of_contents=False)
        self.notes_file = notes_file
        self._observer = Observer()
        self._last_modified = 0
        self._debounce_delay = 0.3  # 300ms 防抖
        self._pending_reload = False
        
    def on_mount(self):
        self._load_notes()
        # Setup file watcher
        event_handler = NotesFileHandler(self.notes_file, self)
        self._observer.schedule(event_handler, ".", recursive=False)
        self._observer.start()
        
    def _load_notes(self):
        try:
            stat_result = Path(self.notes_file).stat()
            current_mtime = stat_result.st_mtime
            
            # 防抖：只有在文件真正有新修改时才加载
            if current_mtime > self._last_modified:
                self._last_modified = current_mtime
                content = Path(self.notes_file).read_text(encoding='utf-8')
                self.update(content)
        except FileNotFoundError:
            self.update("# No notes found\nTry creating a notes.md file")
    
    def update(self, markdown: str) -> None:
        """Override update method to work with MarkdownViewer"""
        # Access the underlying Markdown document and update it
        self.document.update(markdown)
    
    def refresh_content(self):
        """Called by file watcher when file changes"""
        # 防抖：延迟加载，避免频繁修改时重复加载
        if self._pending_reload:
            return
            
        async def delayed_reload():
            await asyncio.sleep(self._debounce_delay)
            self._pending_reload = False
            self._load_notes()
            
        self._pending_reload = True  
        asyncio.create_task(delayed_reload())
    
    def on_exit(self):
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()


class NotesFileHandler(FileSystemEventHandler):
    def __init__(self, watched_file, panel):
        super().__init__()
        self.watched_file = watched_file
        self.panel = panel
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.watched_file):
            self.panel.refresh_content()