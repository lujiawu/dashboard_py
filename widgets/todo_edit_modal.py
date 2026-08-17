import re
from datetime import datetime, timezone, timedelta

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Static
from textual.containers import Horizontal, Vertical
from textual import on

from models.types import Todo

_BJ_TZ = timezone(timedelta(hours=8))
_PRIORITY_OPTIONS = [("低", 10), ("普通", 20), ("较高", 30), ("紧急", 40)]


class TodoEditModal(ModalScreen):
    BINDINGS = [("escape", "cancel", "取消")]
    CSS = """
    TodoEditModal {
        background: rgba(0, 0, 0, 0.5);
        align: center middle;
    }
    TodoEditModal > Vertical {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 60;
        height: auto;
    }
    """

    def __init__(self, todo: Todo, **kwargs):
        super().__init__(**kwargs)
        self._todo = todo
        self._priority = todo.priority if todo.priority in (10, 20, 30, 40) else 20

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("编辑待办", classes="modal-title"),
            Input(value=self._todo.subject or "", placeholder="标题", id="edit-subject"),
            Select(_PRIORITY_OPTIONS, value=self._priority, prompt="优先级", id="edit-priority"),
            Input(placeholder="截止：+1 明天 / +2 后天…，留空不修改", id="edit-due"),
            Horizontal(
                Button("保存", variant="primary", id="edit-save"),
                Button("取消", id="edit-cancel"),
            ),
        )

    def on_mount(self):
        self.app._todo_editing = True
        self.query_one("#edit-subject", Input).focus()

    def on_unmount(self):
        self.app._todo_editing = False

    @staticmethod
    def _parse_due(text: str):
        if not text:
            return None
        m = re.fullmatch(r"\+(\d+)", text.strip())
        if not m:
            raise ValueError("截止时间格式应为 +N，如 +1 表示明天")
        days = int(m.group(1))
        now = datetime.now(tz=_BJ_TZ).replace(hour=23, minute=59, second=59, microsecond=0)
        return int((now + timedelta(days=days)).timestamp() * 1000)

    @on(Button.Pressed, "#edit-save")
    async def on_save(self):
        subject = self.query_one("#edit-subject", Input).value.strip() or None
        priority = self.query_one("#edit-priority", Select).value
        try:
            due_time = self._parse_due(self.query_one("#edit-due", Input).value)
        except ValueError as e:
            self.notify(str(e), severity="error", timeout=4)
            return
        ok = await self.app.dws_todo_source.update_todo(
            self._todo.id, title=subject, priority=priority, due_time=due_time)
        if not ok:
            self.notify("❌ 更新失败", severity="error", timeout=4)
            return
        self.app._todo_editing = False
        self.app.pop_screen()
        await self.app._poll_todos()

    @on(Button.Pressed, "#edit-cancel")
    def on_cancel(self):
        self.action_cancel()

    def action_cancel(self):
        self.app.pop_screen()