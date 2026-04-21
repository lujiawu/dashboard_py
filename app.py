from textual.app import App, ComposeResult
from textual.containers import Grid
from store.store import Store
from models.types import AppState, Agent, Todo, Note
from widgets.system_panel import SystemPanel
from widgets.agents_panel import AgentsPanel  
from widgets.todo_panel import TodoPanel
from widgets.notes_panel import NotesPanel

class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"

    def __init__(self):
        super().__init__()
        self.store = Store()

    def compose(self) -> ComposeResult:
        yield Grid(
            SystemPanel(id="system"),
            AgentsPanel(id="agents"),
            TodoPanel(id="todo"),
            NotesPanel(id="notes"),
            id="main-grid"
        )

    def on_mount(self):
        self.store.subscribe(self.on_state_change)
        self.set_interval(2, self.refresh_data)
        # 初始化demo数据
        self.refresh_data()
        # 添加通知
        self.notify("Press 't' to toggle first todo, 'q' to quit", timeout=5)

    def refresh_data(self):
        state = self.store.state
        
        # Demo系统数据
        state.system.cpu = (state.system.cpu + 5) % 100
        state.system.memory = (state.system.memory + 3) % 80
        state.system.disk = 45.0
        
        # Demo agent数据
        state.agents = [
            Agent("opencode-core", "running"),
            Agent("browser-agent", "idle"),
            Agent("skill-manager", "running"),
            Agent("debug-helper", "stopped")
        ]
        
        # Demo todo数据
        state.todos = [
            Todo("1", "迁移到Textual框架", True),
            Todo("2", "实现状态管理", False),
            Todo("3", "添加键盘交互", False)
        ]
        
        # Demo notes数据
        state.notes = [
            Note("1", "Textual比预期更容易上手"),
            Note("2", "状态驱动架构很清晰"),
            Note("3", "下一步添加持久化")
        ]
        
        self.store.set_state(state)

    def on_state_change(self, state: AppState):
        self.query_one("#system").update_data(state.system)
        self.query_one("#agents").update_agents(state.agents)
        self.query_one("#todo").set_todos(state.todos)
        self.query_one("#notes").update_notes(state.notes)

    def on_key(self, event):
        if event.key == "t":
            # 切换第一个todo的状态（demo功能）
            state = self.store.state
            if state.todos:
                state.todos[0].completed = not state.todos[0].completed
                self.store.set_state(state)
            event.stop()
        elif event.key == "q":
            self.exit()


if __name__ == "__main__":
    DashboardApp().run()