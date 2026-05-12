import logging
from textual.containers import VerticalScroll
from textual.widgets import Static

logger = logging.getLogger(__name__)


class YunxiaoPanel(VerticalScroll):

    def compose(self):
        yield Static(id="content", expand=True)

    def on_mount(self):
        self.query_one("#content", Static).update(
            "[dim]云效工作项\n待接入 API[/]"
        )
        logger.info("[YunxiaoPanel] mounted")
