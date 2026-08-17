import asyncio
import logging
import urllib.request

# Bypass system proxy — Python urllib ignores Windows ProxyOverride
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Static, TextArea
from widgets.todo_panel import TodoPanel
from widgets.yunxiao_panel import YunxiaoPanel
from store.sources.dws_todo_source import DwsTodoSource
from store.sources.yunxiao_source import YunxiaoSource
from store.dws_client import DwsClient
from widgets.chat_panel import ChatPanel
from widgets.git_status_panel import GitStatusPanel
from config import cfg

logging.basicConfig(
    filename=cfg["app"]["log_file"],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


MIN_ROW_HEIGHT = 5
PANEL_IDS = {"todo-list", "chat", "git-status", "yunxiao"}
MIN_PANEL_WIDTHS = {
    "todo-list": 30,
    "chat": 40,
    "git-status": 20,
    "yunxiao": 101,
}


def resize_rows(top: int, bottom: int, delta: int) -> tuple[int, int]:
    delta = max(MIN_ROW_HEIGHT - top, min(delta, bottom - MIN_ROW_HEIGHT))
    return top + delta, bottom - delta


def resize_columns(left: int, right: int, delta: int, min_left: int, min_right: int) -> tuple[int, int]:
    delta = max(min_left - left, min(delta, right - min_right))
    return left + delta, right - delta


class RowDivider(Static):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_y: int | None = None

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._start_y = int(event.screen_y)
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._start_y is not None:
            current_y = int(event.screen_y)
            self.app.resize_rows(current_y - self._start_y)
            self._start_y = current_y
            event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._start_y is not None:
            self._start_y = None
            self.release_mouse()
            event.stop()


class ColumnDivider(Static):
    def __init__(self, left_id: str, right_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left_id = left_id
        self.right_id = right_id
        self._start_x: int | None = None

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._start_x = int(event.screen_x)
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._start_x is not None:
            current_x = int(event.screen_x)
            self.app.resize_columns(self.left_id, self.right_id, current_x - self._start_x)
            self._start_x = current_x
            event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._start_x is not None:
            self._start_x = None
            self.release_mouse()
            event.stop()

class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"
    BINDINGS = [Binding("z", "toggle_fullscreen", "Fullscreen", priority=True)]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                TodoPanel(id="todo-list", classes="panel"),
                ColumnDivider("todo-list", "chat", id="todo-chat-divider"),
                ChatPanel(DwsClient(), id="chat", classes="panel"),
                id="top-row"
            ),
            Horizontal(
                GitStatusPanel(id="git-status", classes="panel"),
                ColumnDivider("git-status", "yunxiao", id="git-yunxiao-divider"),
                YunxiaoPanel(id="yunxiao", classes="panel"),
                id="bottom-row"
            ),
            RowDivider(id="middle-divider"),
            id="main-layout"
        )

    def on_resize(self, _event: events.Resize) -> None:
        self.call_after_refresh(self._position_dividers)

    def _position_dividers(self) -> None:
        main = self.query_one("#main-layout")
        top = self.query_one("#top-row")

        middle_divider = self.query_one("#middle-divider", RowDivider)
        middle_divider.styles.offset = (0, top.region.bottom - main.region.y)
        middle_divider.styles.width = main.region.width

    def resize_rows(self, delta: int) -> None:
        top = self.query_one("#top-row")
        bottom = self.query_one("#bottom-row")
        top_height, bottom_height = resize_rows(top.size.height, bottom.size.height, delta)
        top.styles.height = top_height
        bottom.styles.height = bottom_height
        self.call_after_refresh(self._position_dividers)

    def resize_columns(self, left_id: str, right_id: str, delta: int) -> None:
        left = self.query_one(f"#{left_id}")
        right = self.query_one(f"#{right_id}")
        left_width, right_width = resize_columns(
            left.region.width,
            right.region.width,
            delta,
            MIN_PANEL_WIDTHS[left_id],
            MIN_PANEL_WIDTHS[right_id],
        )
        left.styles.width = left_width
        right.styles.width = right_width

    def action_toggle_fullscreen(self) -> None:
        if self.screen.maximized:
            self.screen.minimize()
            return

        widget = self.focused
        if isinstance(widget, (Input, TextArea)):
            return
        while widget is not None and widget.id not in PANEL_IDS:
            widget = widget.parent
        if widget is not None:
            self.screen.maximize(widget, container=False)

    def on_mount(self):
        logger.info("[App] on_mount start")

        self.set_timer(0.01, self._position_dividers)

        self.dws_todo_source = DwsTodoSource(cfg["dws"]["todo"])
        self.yunxiao_source = YunxiaoSource(cfg["yunxiao"])
        self.chat_client = self.query_one("#chat", ChatPanel).client
        if self.chat_client.available():
            asyncio.create_task(self.chat_client.load_self())

        asyncio.create_task(self._refresh_all())

        self.set_interval(self.yunxiao_source.refresh_interval, self._poll_yunxiao)
        self.set_interval(cfg["git"]["refresh_interval"], self._poll_git_status)
        logger.info("[App] on_mount end")

        self.notify("'q' quit, 'r' refresh, 't' toggle todo, 'z' fullscreen", timeout=5)

    async def _refresh_all(self):
        self.notify("\u27f3 Refreshing...", timeout=1)
        await asyncio.gather(
            self._poll_todos(),
            self._poll_yunxiao(),
            self._poll_git_status(),
        )

    async def _poll_todos(self):
        if getattr(self, "_todo_editing", False):
            return
        try:
            todos = await self.dws_todo_source.fetch()
            logger.info("[Poll] todos: %d items", len(todos))
            panel = self.query_one("#todo-list", TodoPanel)
            panel.update_todos(todos)
        except Exception as e:
            logger.error(f"[App] Failed to poll todos: {e}")

    async def _poll_yunxiao(self):
        if getattr(self, "_polling_yunxiao", False):
            logger.info("[App] Skip yunxiao poll: previous poll still running")
            return
        self._polling_yunxiao = True
        try:
            items = await self.yunxiao_source.fetch()
            logger.info("[Poll] yunxiao: %d items", len(items))
            panel = self.query_one("#yunxiao", YunxiaoPanel)
            panel.update_items(items)
        except Exception as e:
            logger.error(f"[App] Failed to poll yunxiao: {e}")
        finally:
            self._polling_yunxiao = False

    async def _poll_git_status(self):
        logger.info("[App] _poll_git_status triggered")
        try:
            panel = self.query_one("#git-status", GitStatusPanel)
            await panel.refresh_status()
        except Exception as e:
            logger.error(f"[App] Failed to poll git status: {e}")

    async def _toggle_todo(self):
        try:
            panel = self.query_one("#todo-list", TodoPanel)
            todo = panel.mark_local_toggle(panel.cursor_row)
            if todo is None:
                return
            action = "done" if todo.completed else "undone"
            logger.info(f"[Toggle] id={todo.id} subject={todo.subject[:60]} action={action}")
            self.notify(f"[{action}] {todo.subject[:60]}", timeout=2)
            ok = await self.dws_todo_source.set_done_status(todo.id, todo.completed)
            logger.info(f"[Toggle] DWS result: ok={ok} id={todo.id}")
        except Exception as e:
            logger.error(f"[App] Failed to toggle todo: {e}")

    def on_key(self, event):
        if event.key == "q":
            self.exit()
        elif event.key == "r":
            asyncio.create_task(self._refresh_all())
            event.stop()
        elif event.key == "t":
            asyncio.create_task(self._toggle_todo())
            event.stop()
        elif event.key == "e" and not getattr(self, "_todo_editing", False):
            self.query_one("#todo-list", TodoPanel).action_edit_todo()
            event.stop()
        elif event.key == "z":
            self.action_toggle_fullscreen()
            event.stop()

    def copy_to_clipboard(self, text: str):
        self.run_worker(self._clipboard_write(text))

    async def _clipboard_write(self, text: str):
        try:
            super().copy_to_clipboard(text)
        except Exception:
            pass


def main():
    import sys
    sys.argv.append("-r")
    DashboardApp().run()


if __name__ == "__main__":
    main()
