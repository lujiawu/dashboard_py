import asyncio
import logging
import threading
import urllib.request

# Bypass system proxy — Python urllib ignores Windows ProxyOverride
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static
from widgets.ai_agents_panel import AiAgentsPanel
from widgets.todo_panel import TodoPanel
from widgets.yunxiao_panel import YunxiaoPanel
from widgets.bottom_panel import BottomPanel
from store.sources.session_source import SessionDataSource
from store.sources.dws_todo_source import DwsTodoSource
from store.sources.dws_chat_source import DwsChatSource
from store.sources.dws_calendar_source import DwsCalendarSource
from store.sources.yunxiao_source import YunxiaoSource
from store.sources.mihomo_source import MihomoSource
from widgets.dws_info_panel import DwsInfoPanel
from widgets.git_status_panel import GitStatusPanel
from widgets.mihomo_panel import MihomoPanel
from config import cfg

logging.basicConfig(
    filename=cfg["app"]["log_file"],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


MIN_ROW_HEIGHT = 5


def resize_rows(top: int, middle: int, bottom: int, divider: str, delta: int) -> tuple[int, int]:
    """Resize the two rows adjacent to a divider without crossing their minimums."""
    if divider == "top-divider":
        delta = max(MIN_ROW_HEIGHT - top, min(delta, middle - MIN_ROW_HEIGHT))
        return top + delta, middle - delta

    delta = max(MIN_ROW_HEIGHT - middle, min(delta, bottom - MIN_ROW_HEIGHT))
    return middle + delta, bottom - delta


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
            self.app.resize_rows(self.id, current_y - self._start_y)
            self._start_y = current_y
            event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._start_y is not None:
            self._start_y = None
            self.release_mouse()
            event.stop()


class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                AiAgentsPanel(id="ai-agents", classes="panel"),
                DwsInfoPanel(id="dws-info", classes="panel"),
                id="top-row"
            ),
            RowDivider(id="top-divider"),
            Horizontal(
                TodoPanel(id="todo-list", classes="panel"),
                BottomPanel(id="bottom-area", classes="panel side-panel"),
                id="middle-row"
            ),
            RowDivider(id="middle-divider"),
            Horizontal(
                GitStatusPanel(id="git-status", classes="panel"),
                MihomoPanel(id="mihomo", classes="panel"),
                YunxiaoPanel(id="yunxiao", classes="panel"),
                id="bottom-row"
            ),
            id="main-layout"
        )

    def resize_rows(self, divider: str, delta: int) -> None:
        top = self.query_one("#top-row")
        middle = self.query_one("#middle-row")
        bottom = self.query_one("#bottom-row")
        first_height, second_height = resize_rows(
            top.size.height,
            middle.size.height,
            bottom.size.height,
            divider,
            delta,
        )
        if divider == "top-divider":
            top.styles.height = first_height
            middle.styles.height = second_height
        else:
            middle.styles.height = first_height

    def on_mount(self):
        logger.info("[App] on_mount start")

        self.session_source = SessionDataSource(cfg["sessions"])
        self.session_source.start_watching()
        self.session_source.set_on_reload(
            lambda: (
                self.call_from_thread(self._push_sessions_to_tui)
                if threading.current_thread() is not threading.main_thread()
                else asyncio.create_task(self._push_sessions_to_tui())
            )
        )
        logger.info("[App] SessionDataSource watching started")

        self.dws_todo_source = DwsTodoSource(cfg["dws"]["todo"])
        self.dws_chat_source = DwsChatSource(cfg["dws"]["chat"])
        self.dws_calendar_source = DwsCalendarSource(cfg["dws"]["calendar"])
        self.yunxiao_source = YunxiaoSource(cfg["yunxiao"])
        self.mihomo_source = MihomoSource(cfg["mihomo"])

        asyncio.create_task(self._refresh_all())

        self.set_interval(self.dws_chat_source.refresh_interval, self._poll_dws_info)
        self.set_interval(self.yunxiao_source.refresh_interval, self._poll_yunxiao)
        self.set_interval(cfg["git"]["refresh_interval"], self._poll_git_status)
        self.set_interval(self.mihomo_source.refresh_interval, self._poll_mihomo)
        self.set_interval(2.0, self._compensation_poll_sessions)
        logger.info("[App] on_mount end")

        self.notify("'q' quit, 'r' refresh, 't' toggle todo", timeout=5)

    async def _refresh_all(self):
        self.notify("\u27f3 Refreshing...", timeout=1)
        await asyncio.gather(
            self._poll_sessions(),
            self._poll_todos(),
            self._poll_dws_info(),
            self._poll_yunxiao(),
            self._poll_git_status(),
            self._poll_mihomo(),
        )

    async def _poll_sessions(self):
        try:
            local_sessions = await self.session_source.fetch()
            for s in local_sessions:
                s.host = "local"

            logger.info("[Poll] sessions: local=%d", len(local_sessions))
            panel = self.query_one("#ai-agents", AiAgentsPanel)
            panel.update_sessions(local_sessions)
        except Exception as e:
            logger.error(f"[App] Failed to poll sessions: {e}")

    async def _push_sessions_to_tui(self):
        await self._poll_sessions()

    def _compensation_poll_sessions(self):
        self.session_source.compensation_poll()

    async def _poll_todos(self):
        try:
            todos = await self.dws_todo_source.fetch()
            logger.info("[Poll] todos: %d items", len(todos))
            panel = self.query_one("#todo-list", TodoPanel)
            panel.update_todos(todos)
        except Exception as e:
            logger.error(f"[App] Failed to poll todos: {e}")

    async def _poll_dws_info(self):
        try:
            conversations, events = await asyncio.gather(
                self.dws_chat_source.fetch(),
                self.dws_calendar_source.fetch(),
            )
            logger.info("[Poll] dws: %d chats, %d events", len(conversations), len(events))
            panel = self.query_one("#dws-info", DwsInfoPanel)
            panel.update(conversations, events)
        except Exception as e:
            logger.error(f"[App] Failed to poll dws info: {e}")

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

    async def _poll_mihomo(self):
        if getattr(self, "_polling_mihomo", False):
            return
        self._polling_mihomo = True
        try:
            data = await self.mihomo_source.fetch()
            panel = self.query_one("#mihomo", MihomoPanel)
            panel.update_status(data)
        except Exception as e:
            logger.error(f"[App] Failed to poll mihomo: {e}")
        finally:
            self._polling_mihomo = False

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
            self.session_source.stop_watching()
            self.exit()
        elif event.key == "r":
            asyncio.create_task(self._refresh_all())
            event.stop()
        elif event.key == "t":
            asyncio.create_task(self._toggle_todo())
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
