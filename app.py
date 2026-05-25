import asyncio
import logging
import threading
import urllib.request

# Bypass system proxy — Python urllib ignores Windows ProxyOverride
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from widgets.ai_agents_panel import AiAgentsPanel
from widgets.todo_panel import TodoPanel
from widgets.goal_progress_panel import GoalTreePanel
from widgets.yunxiao_panel import YunxiaoPanel
from widgets.bottom_panel import BottomPanel
from store.sources.session_source import SessionDataSource
from store.sources.http_session_source import HttpSessionDataSource
from store.sources.dws_todo_source import DwsTodoSource
from store.sources.dws_chat_source import DwsChatSource
from store.sources.dws_calendar_source import DwsCalendarSource
from store.sources.http_goal_source import HttpGoalSource
from store.sources.yunxiao_source import YunxiaoSource
from widgets.dws_info_panel import DwsInfoPanel
from widgets.git_status_panel import GitStatusPanel
from config import cfg

logging.basicConfig(
    filename=cfg["app"]["log_file"],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                AiAgentsPanel(id="ai-agents", classes="panel"),
                DwsInfoPanel(id="dws-info", classes="panel"),
                id="top-row"
            ),
            Horizontal(
                TodoPanel(id="todo-list", classes="panel"),
                GoalTreePanel(id="goal-progress", classes="panel side-panel hidden"),
                YunxiaoPanel(id="yunxiao", classes="panel side-panel"),
                id="middle-row"
            ),
            Horizontal(
                GitStatusPanel(id="git-status", classes="panel"),
                BottomPanel(id="bottom-area", classes="panel"),
                id="bottom-row"
            ),
            id="main-layout"
        )

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

        self.remote_source = HttpSessionDataSource(cfg["remote"])
        logger.info(f"[App] RemoteSessionDataSource initialized: {cfg['remote']['api_url']}")

        self.dws_todo_source = DwsTodoSource(cfg["dws"]["todo"])
        self.dws_chat_source = DwsChatSource(cfg["dws"]["chat"])
        self.dws_calendar_source = DwsCalendarSource(cfg["dws"]["calendar"])
        self.goal_source = HttpGoalSource(cfg["goals"])
        self.yunxiao_source = YunxiaoSource(cfg["yunxiao"])

        asyncio.create_task(self._refresh_all())

        self.set_interval(self.remote_source.refresh_interval, self._poll_sessions)
        self.set_interval(self.dws_chat_source.refresh_interval, self._poll_dws_info)
        self.set_interval(self.yunxiao_source.refresh_interval, self._poll_yunxiao)
        self.set_interval(cfg["git"]["refresh_interval"], self._poll_git_status)
        self.set_interval(2.0, self._compensation_poll_sessions)
        self.set_interval(cfg["goals"]["refresh_interval"], self._poll_goals)
        logger.info("[App] on_mount end")

        self.notify("'q' quit, 'r' refresh, 't' toggle todo, 'g' toggle goal panel", timeout=5)

    async def _refresh_all(self):
        self.notify("\u27f3 Refreshing...", timeout=1)
        await asyncio.gather(
            self._poll_sessions(),
            self._poll_todos(),
            self._poll_goals(),
            self._poll_dws_info(),
            self._poll_yunxiao(),
            self._poll_git_status(),
        )

    async def _poll_sessions(self):
        try:
            local_sessions = await self.session_source.fetch()
            for s in local_sessions:
                s.host = "local"

            remote_sessions = []
            try:
                remote_sessions = await self.remote_source.fetch()
            except Exception as e:
                logger.warning(f"[App] Remote fetch failed: {e}")

            all_sessions = local_sessions + remote_sessions
            logger.info("[Poll] sessions: local=%d remote=%d total=%d", len(local_sessions), len(remote_sessions), len(all_sessions))
            panel = self.query_one("#ai-agents", AiAgentsPanel)
            panel.update_sessions(all_sessions)
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

    async def _poll_goals(self):
        try:
            items = await self.goal_source.fetch()
            logger.info("[Poll] goals: %d items", len(items))
            panel = self.query_one("#goal-progress", GoalTreePanel)
            panel.update_progress(items)
        except Exception as e:
            logger.error(f"[App] Failed to poll goals: {e}")
            self.notify(f"[red]Goal fetch failed: {e}[/]", timeout=3)

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
        try:
            items = await self.yunxiao_source.fetch()
            logger.info("[Poll] yunxiao: %d items", len(items))
            panel = self.query_one("#yunxiao", YunxiaoPanel)
            panel.update_items(items)
        except Exception as e:
            logger.error(f"[App] Failed to poll yunxiao: {e}")

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

    def _toggle_goal_panel(self):
        goal = self.query_one("#goal-progress", GoalTreePanel)
        yunxiao = self.query_one("#yunxiao", YunxiaoPanel)
        logger.info("[Toggle] goal has_class('hidden')=%s", goal.has_class("hidden"))
        if goal.has_class("hidden"):
            goal.remove_class("hidden")
            yunxiao.add_class("hidden")
            self.notify("Goal panel visible", timeout=1)
            logger.info("[Toggle] goal visible, yunxiao hidden")
        else:
            goal.add_class("hidden")
            yunxiao.remove_class("hidden")
            self.notify("Goal panel hidden", timeout=1)
            logger.info("[Toggle] goal hidden, yunxiao visible")
        self.refresh(layout=True)

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
        elif event.key == "g":
            self._toggle_goal_panel()
            event.stop()

    def copy_to_clipboard(self, text: str):
        self.run_worker(self._clipboard_write(text))

    async def _clipboard_write(self, text: str):
        try:
            super().copy_to_clipboard(text)
        except Exception:
            pass


if __name__ == "__main__":
    import sys
    sys.argv.append("-r")
    DashboardApp().run()
