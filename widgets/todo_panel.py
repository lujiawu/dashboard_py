from textual.widgets import Static
from models.types import Todo

class TodoPanel(Static):
    def set_todos(self, todos: list[Todo]):
        self.query("ListItem").remove()
        for todo in todos:
            mark = "[x]" if todo.completed else "[ ]"
            self.mount(ListItem(Label(f"{mark} {todo.content}")))
    
    def format_text(self, todos: list[Todo]):
        lines = []
        for todo in todos:
            mark = "[x]" if todo.completed else "[ ]"
            lines.append(f"{mark} {todo.content}")
        
        return "\n".join(lines) if lines else "No tasks"