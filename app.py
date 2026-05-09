import asyncio
import logging
from textual.app import App, ComposeResult
from textual.containers import Grid
from widgets.ai_agents_panel import AiAgentsPanel
from widgets.top_attributes_panel import TopAttributesPanel
from widgets.log_patterns_panel import LogPatternsPanel
from widgets.log_counts_panel import LogCountsPanel
from widgets.log_table_panel import LogTablePanel
from store.sources.session_source import SessionDataSource
from store.sources.http_session_source import HttpSessionDataSource

logging.basicConfig(
    filename="dashboard.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Remote server configuration
REMOTE_API_URL = "http://macmini2014.local:8000/"
REMOTE_HOST_LABEL = "macmini2014"


class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"

    def compose(self) -> ComposeResult:
        yield Grid(
            AiAgentsPanel(id="ai-agents", classes="panel"),
            TopAttributesPanel(id="top-attributes", classes="panel"),
            LogPatternsPanel(id="log-patterns", classes="panel"),
            LogCountsPanel(id="log-counts", classes="panel"),
            LogTablePanel(id="log-table"),
            id="main-grid"
        )

    def on_mount(self):
        logger.info("[App] on_mount start")

        self.session_source = SessionDataSource()
        self.session_source.start_watching()
        logger.info("[App] SessionDataSource watching started")

        # Remote HTTP data source
        self.remote_source = HttpSessionDataSource(REMOTE_API_URL, host_label=REMOTE_HOST_LABEL)
        logger.info(f"[App] RemoteSessionDataSource initialized: {REMOTE_API_URL}")

        self.set_interval(2, self._poll_sessions)

        self.query_one("#top-attributes", TopAttributesPanel).update_mock_data()
        self.query_one("#log-patterns", LogPatternsPanel).update_mock_data()
        self.query_one("#log-counts", LogCountsPanel).update_mock_data()
        logger.info("[App] on_mount end")

        self.notify("Press 'q' to quit, 'r' to refresh", timeout=5)

    async def _poll_sessions(self):
        """Fetch local + remote sessions and push to AiAgentsPanel."""
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
            panel = self.query_one("#ai-agents", AiAgentsPanel)
            panel.update_sessions(all_sessions)
        except Exception as e:
            logger.error(f"[App] Failed to poll sessions: {e}")

    def on_key(self, event):
        if event.key == "q":
            self.session_source.stop_watching()
            self.exit()
        elif event.key == "r":
            asyncio.create_task(self._poll_sessions())
            self.query_one("#top-attributes", TopAttributesPanel).update_mock_data()
            self.query_one("#log-patterns", LogPatternsPanel).update_mock_data()
            self.query_one("#log-counts", LogCountsPanel).update_mock_data()
            event.stop()


if __name__ == "__main__":
    DashboardApp().run()
