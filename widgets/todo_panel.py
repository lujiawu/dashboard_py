from textual.widgets import ListView, ListItem, Label
from models.types import Todo

class TodoPanel(ListView):
    def set_todos(self, todos: list[Todo]):
        self.clear()
        for todo in todos:
            mark = "[x]" if todo.completed else "[ ]"
            self.append(ListItem(Label(f"{mark} {todo.content}"), id=f"todo-{todo.id}"))