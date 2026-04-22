from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Static
from store.store import Store
from models.types import AppState, Agent, Todo, Note
from widgets.system_panel import SystemPanel
from widgets.agents_panel import AgentsPanel  
from widgets.todo_panel import TodoPanel
from widgets.notes_panel import NotesPanel
from store.sources.system_source import SystemDataSource
from store.sources.session_source import SessionDataSource


class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"

    def __init__(self):
        super().__init__()
        self.store = Store()

    def compose(self) -> ComposeResult:
        yield Grid(
            Static(id="system", classes="panel"),
            Static(id="agents", classes="panel"), 
            Static(id="todo", classes="panel"),
            Static(id="notes", classes="panel"),
            id="main-grid"
        )

    def on_mount(self):
        self.store.subscribe('system', self.on_system_change)
        self.store.subscribe('sessions', self.on_sessions_change)
        self.store.subscribe('app', self.on_state_change)
        
        # Create system and session data sources
        self.system_source = SystemDataSource(refresh_interval=2.0, top_processes_limit=5)
        self.session_source = SessionDataSource(sessions_dir="C:\\Users\\work\\.config\\opencode\\sessions", refresh_interval=30.0)
        
        # Start watching the sessions directory
        self.session_source.start_watching()
        
        # Regular intervals for data updates
        self.set_interval(self.system_source.refresh_interval, self.refresh_system_data)
        # We don't need to regularly fetch sessions as they're event-driven
        
        # Initialize data        
        self.refresh_system_data()
        self.init_demo_data()  # Still needed for todos and notes
        
        # Add notification
        self.notify("Press 't' to toggle first todo, 'q' to quit", timeout=5)

    async def refresh_system_data(self):
        """Refresh system data"""
        system_data_dict = await self.system_source.fetch()
        
        # Convert dictionary to SystemData object
        from models.types import SystemData
        system_data = SystemData(**system_data_dict)
        
        # Update system module
        self.store.update_module('system', system_data)

    def init_demo_data(self):
        """Initialize non-system-related demo data"""
        state = self.store.state
        # Demo todo data
        state.todos = [
            Todo("1", "迁移到Textual框架", True),
            Todo("2", "实现状态管理", False),
            Todo("3", "添加键盘交互", False)
        ]
        
        # Demo notes data
        state.notes = [
            Note("1", "Textual比预期更容易上手"),
            Note("2", "状态驱动架构很清晰"),
            Note("3", "下一步添加持久化")
        ]
        
        # Also update sessions initially
        self.refresh_sessions_data()
        
        self.store.set_state(state)

    def refresh_sessions_data(self):
        """Refresh session data from source"""
        try:
            sessions = self.session_source.sessions
            self.store.update_module('sessions', sessions)
        except Exception as e:
            # Silently fail since we might have permission issues with file locks
            pass

    def on_system_change(self, system_data):
        """Handle system data updates"""
        system_panel = SystemPanel()
        self.query_one("#system").update(system_panel.format_text(system_data))

    def on_sessions_change(self, sessions):
        """Handle session data updates"""
        agents_panel = AgentsPanel()
        self.query_one("#agents").update(agents_panel.format_text(sessions))

    def on_state_change(self, state: AppState):
        """Handle general state updates"""
        todo_panel = TodoPanel()
        self.query_one("#todo").update(todo_panel.format_text(state.todos))
        
        notes_panel = NotesPanel()
        self.query_one("#notes").update(notes_panel.format_text(state.notes))

    def on_key(self, event):
        if event.key == "t":
            # Toggle first todo status (demo feature)
            state = self.store.state
            if state.todos:
                state.todos[0].completed = not state.todos[0].completed
                self.store.set_state(state)
            event.stop()
        elif event.key == "q":
            # Stop the session observer before exiting
            self.session_source.stop_watching()
            self.exit()

    def on_exit(self):
        # Ensure the observer is stopped when the app exits
        self.session_source.stop_watching()
        super().on_exit()


if __name__ == "__main__":
    DashboardApp().run()