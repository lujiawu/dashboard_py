from datetime import datetime, timezone, timedelta
from textual.widgets import DataTable
from textual.events import Click
from textual import on
from rich.text import Text
from models.types import Todo


def _priority_label(priority: int) -> str:
    if priority >= 30:
        return "!!!"
    if priority == 20:
        return "!!"
    return "!"


def _format_due(due_time: int) -> str:
    if not due_time:
        return "--"
    try:
        dt = datetime.fromtimestamp(due_time / 1000, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%m-%d")
    except (ValueError, OSError):
        return "--"


class TodoPanel(DataTable):
    BINDINGS = [
        ("c", "copy_item", "Copy"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zebra_stripes = True
        self._todo_map: dict[int, Todo] = {}

    def on_mount(self):
        self.cursor_type = "row"
        self.add_column("P", width=3)
        self.add_column("Due", width=8)
        self._subject_key = self.add_column("Subject", width=None)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        event.stop()

    def update_todos(self, todos: list[Todo]):
        self._todo_map = {}
        self.clear()
        rows = self._build_rows(todos)
        self._row_keys = self.add_rows(rows)

    def _build_rows(self, todos: list[Todo]) -> list[tuple]:
        if not todos:
            return []

        todos.sort(key=lambda t: (-t.priority, t.due_time if t.due_time else 2**31))
        self._todo_map = {i: todo for i, todo in enumerate(todos)}

        rows = []
        for todo in todos:
            p_str = _priority_label(todo.priority)
            due_str = _format_due(todo.due_time)
            subject = Text(todo.subject or "?", style="strike" if todo.completed else "")
            rows.append((p_str, due_str, subject))

        return rows

    def _all_todos(self) -> list[Todo]:
        return [self._todo_map[i] for i in sorted(self._todo_map)]

    def _get_todo_at_index(self, index: int) -> Todo | None:
        return self._todo_map.get(index)

    def mark_local_toggle(self, index: int) -> Todo | None:
        todo = self._get_todo_at_index(index)
        if todo is None:
            return None
        todo.completed = not todo.completed
        subject = Text(todo.subject or "?", style="strike" if todo.completed else "")
        self.update_cell(self._row_keys[index], self._subject_key, subject)
        return todo

    def action_copy_item(self):
        index = self.cursor_row
        todo = self._get_todo_at_index(index)
        if todo is None:
            return
        self.app.copy_to_clipboard(todo.subject)

    def on_click(self, event: Click):
        if event.button == 3:
            if self.cursor_row >= 0:
                todo = self._get_todo_at_index(self.cursor_row)
                if todo:
                    self.app.copy_to_clipboard(todo.subject)