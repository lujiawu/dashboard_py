from datetime import date, datetime, timezone, timedelta
from textual.widgets import DataTable, Input
from textual.containers import Vertical
from textual.events import Click
from textual import on
from rich.text import Text
from models.types import Todo
from widgets.todo_edit_modal import TodoEditModal


_BJ_TZ = timezone(timedelta(hours=8))
_GROUPS = (
    ("overdue", "已逾期"),
    ("today", "今日待办"),
    ("tomorrow", "明日待办"),
    ("future", "未来待办"),
    ("no_due", "无截止日期"),
)


def group_todos(todos: list[Todo], today: date | None = None) -> list[tuple[str, list[Todo]]]:
    today = today or datetime.now(tz=_BJ_TZ).date()
    grouped = {key: [] for key, _label in _GROUPS}

    for todo in todos:
        if not todo.due_time:
            grouped["no_due"].append(todo)
            continue
        try:
            due_date = datetime.fromtimestamp(todo.due_time / 1000, tz=_BJ_TZ).date()
        except (OverflowError, OSError, TypeError, ValueError):
            grouped["no_due"].append(todo)
            continue
        if due_date < today:
            grouped["overdue"].append(todo)
        elif due_date == today:
            grouped["today"].append(todo)
        elif due_date == today + timedelta(days=1):
            grouped["tomorrow"].append(todo)
        else:
            grouped["future"].append(todo)

    for group in grouped.values():
        group.sort(key=lambda todo: (
            -todo.priority,
            todo.due_time if isinstance(todo.due_time, (int, float)) else 2**31,
        ))
    return [(key, grouped[key]) for key, _label in _GROUPS if grouped[key]]


def _priority_label(priority: int) -> Text:
    if priority >= 30:
        return Text("!!!", style="bold red")
    if priority == 20:
        return Text("!!", style="bold yellow")
    return Text("!", style="dim yellow")


def _format_due(due_time: int) -> str:
    if not due_time:
        return "--"
    try:
        dt = datetime.fromtimestamp(due_time / 1000, tz=_BJ_TZ)
        return dt.strftime("%m-%d")
    except (OverflowError, OSError, TypeError, ValueError):
        return "--"


class TodoPanel(Vertical):
    ALLOW_MAXIMIZE = True
    BINDINGS = [
        ("c", "copy_item", "Copy"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._todo_map: dict[int, Todo] = {}
        self._row_keys = []
        self._last_todos: list[Todo] | None = None

    def compose(self):
        self._table = DataTable()
        self._table.zebra_stripes = True
        self._table.cursor_type = "row"
        self._table.styles.height = "1fr"
        yield self._table

        inp = Input(placeholder="Add a todo...", id="todo-add-input")
        yield inp

    def on_mount(self):
        self._table.add_column("P", width=3)
        self._table.add_column("Due", width=8)
        self._subject_key = self._table.add_column("Subject", width=None)
        self._description_key = self._table.add_column("Description", width=24)
        self.border_title = "TODO"
        self._table.focus()

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        event.stop()

    @property
    def cursor_row(self):
        return self._table.cursor_row

    def update_todos(self, todos: list[Todo]):
        if todos is self._last_todos:
            return
        self._last_todos = todos
        self._todo_map = {}
        self._table.clear()
        rows = self._build_rows(todos)
        if not rows:
            self._row_keys = self._table.add_rows([(Text("", style=""), Text("", style=""), Text("🎉 暂无待办", style="dim"), Text("", style=""))])
        else:
            self._row_keys = self._table.add_rows(rows)
        self.border_title = f"TODO · {len(todos)}"

    def _build_rows(self, todos: list[Todo]) -> list[tuple]:
        if not todos:
            return []

        rows = []
        row_index = 0
        labels = dict(_GROUPS)
        for group_key, group_todos_list in group_todos(todos):
            rows.append((Text(""), Text(""), Text(labels[group_key], style="bold cyan"), Text("")))
            row_index += 1
            for todo in group_todos_list:
                p_str = _priority_label(todo.priority)
                due_str = _format_due(todo.due_time)
                subject = f"✅ {todo.subject or '?'}" if todo.completed else (todo.subject or "?")
                rows.append((p_str, due_str, subject, todo.description or ""))
                self._todo_map[row_index] = todo
                row_index += 1

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
        subject = f"✅ {todo.subject or '?'}" if todo.completed else (todo.subject or "?")
        self._table.update_cell(self._row_keys[index], self._subject_key, subject)
        return todo

    def action_copy_item(self):
        index = self.cursor_row
        todo = self._get_todo_at_index(index)
        if todo is None:
            return
        self.app.copy_to_clipboard(todo.subject)

    def action_edit_todo(self):
        todo = self._get_todo_at_index(self.cursor_row)
        if todo is None:
            return
        self.app.push_screen(TodoEditModal(todo))

    def on_click(self, event: Click):
        if event.button == 3:
            if self.cursor_row >= 0:
                todo = self._get_todo_at_index(self.cursor_row)
                if todo:
                    self.app.copy_to_clipboard(todo.subject)

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id != "todo-add-input":
            return
        title = event.value.strip()
        if title:
            event.input.clear()
            self.run_worker(self._create_todo(title))

    async def _create_todo(self, title: str):
        ok = await self.app.dws_todo_source.create_todo(title)
        if ok:
            await self.app._poll_todos()
