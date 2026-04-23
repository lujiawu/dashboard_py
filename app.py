from textual.app import App, ComposeResult
from textual.containers import Grid
from widgets.top_words_panel import TopWordsPanel
from widgets.top_attributes_panel import TopAttributesPanel
from widgets.log_patterns_panel import LogPatternsPanel
from widgets.log_counts_panel import LogCountsPanel
from widgets.log_table_panel import LogTablePanel


class DashboardApp(App):
    CSS_PATH = "styles/app.tcss"
    LOG_PATH = "dashboard.log"

    def compose(self) -> ComposeResult:
        yield Grid(
            TopWordsPanel(id="top-words", classes="panel"),
            TopAttributesPanel(id="top-attributes", classes="panel"),
            LogPatternsPanel(id="log-patterns", classes="panel"),
            LogCountsPanel(id="log-counts", classes="panel"),
            LogTablePanel(id="log-table"),
            id="main-grid"
        )

    def on_mount(self):
        self.log.info("[App] on_mount start")
        self.query_one("#top-words", TopWordsPanel).update_mock_data()
        self.query_one("#top-attributes", TopAttributesPanel).update_mock_data()
        self.query_one("#log-patterns", LogPatternsPanel).update_mock_data()
        self.query_one("#log-counts", LogCountsPanel).update_mock_data()
        self.log.info("[App] on_mount end")

        self.notify("Press 'q' to quit, 'r' to refresh", timeout=5)

    def on_key(self, event):
        if event.key == "q":
            self.exit()
        elif event.key == "r":
            self.query_one("#top-words", TopWordsPanel).update_mock_data()
            self.query_one("#top-attributes", TopAttributesPanel).update_mock_data()
            self.query_one("#log-patterns", LogPatternsPanel).update_mock_data()
            self.query_one("#log-counts", LogCountsPanel).update_mock_data()
            event.stop()


if __name__ == "__main__":
    DashboardApp().run()
