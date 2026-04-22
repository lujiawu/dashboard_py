from textual.widgets import ListView, ListItem, Label

class TodoPanel(ListView):
    def set_todos(self, todos: list[Todo]):
        self.query("ListItem").remove()
        for todo in todos:
            mark = "[x]" if todo.completed else "[ ]"
            self.mount(ListItem(Label(f"{mark} {todo.content}")))