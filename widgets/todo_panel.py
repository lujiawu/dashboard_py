from textual.widgets import ListView, ListItem, Label
from textual.events import Click
from models.types import Todo


class TodoPanel(ListView):
    BINDINGS = [
        ("space", "toggle_complete", "Toggle"),
        ("c", "copy_item", "Copy"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._todos: list[Todo] = []

    def on_mount(self):
        self._load_mock_data()
        self.focus()

    def _load_mock_data(self):
        mock_todos = [
            Todo("1", "Review PR #42 for auth module", False),
            Todo("2", "Update TODO list in README", False),
            Todo("3", "Deploy staging environment", False),
            Todo("4", "Write unit tests for payment service", True),
            Todo("5", "Fix timezone bug in reports", False),
            Todo("6", "Refactor database connection pool", False),
            Todo("7", "Update dependencies to latest versions", True),
            Todo("8", "Review architecture decision record", False),
        ]
        self.set_todos(mock_todos)

    def set_todos(self, todos: list[Todo]):
        self._todos = todos
        self.query("ListItem").remove()
        for todo in todos:
            self.mount(ListItem(self._make_label(todo)))

    def _make_label(self, todo: Todo) -> Label:
        mark = "[x]" if todo.completed else "[ ]"
        label = Label(f"{mark} {todo.content}", id=f"label-{todo.id}")
        if todo.completed:
            label.styles.text_style = "strike"
        return label

    def _get_todo_at_index(self, index: int) -> Todo | None:
        if 0 <= index < len(self._todos):
            return self._todos[index]
        return None

    def _update_item(self, index: int):
        todo = self._get_todo_at_index(index)
        if todo is None:
            return
        label_widget = self.query_one(f"#label-{todo.id}", Label)
        mark = "[x]" if todo.completed else "[ ]"
        label_widget.update(f"{mark} {todo.content}")
        if todo.completed:
            label_widget.styles.text_style = "strike"
        else:
            label_widget.styles.text_style = ""

    def action_toggle_complete(self):
        index = self.index
        todo = self._get_todo_at_index(index)
        if todo is None:
            return
        todo.completed = not todo.completed
        self._update_item(index)
        status = "completed" if todo.completed else "uncompleted"
        self.notify(f"[{status}] {todo.content[:60]}{'...' if len(todo.content) > 60 else ''}", timeout=2)

    def on_click(self, event: Click):
        if event.button == 3:
            self.action_copy_item()

    def action_copy_item(self):
        index = self.index
        todo = self._get_todo_at_index(index)
        if todo is None:
            return
        self.app.copy_to_clipboard(todo.content)
        self.notify(f"Copied: {todo.content[:60]}{'...' if len(todo.content) > 60 else ''}", timeout=2)
