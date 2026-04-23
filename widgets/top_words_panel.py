from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import RankedItem


class TopWordsPanel(VerticalScroll):
    def compose(self):
        self.log.info("[TopWordsPanel] compose start")
        yield Static(id="content", expand=True)
        self.log.info("[TopWordsPanel] compose end")

    def format_text(self, items: list[RankedItem]) -> str:
        if not items:
            return "No data"

        lines = []
        for item in items:
            bar_width = 30
            filled = int(item.percentage / 100 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            lines.append(f"{item.rank:>2}. {item.label:<35} {item.count:>6} {bar}")

        return "\n".join(lines)

    def update_mock_data(self):
        mock_data = [
            RankedItem(1, "for", 17637, 17637),
            RankedItem(2, "with", 13149, 17637),
            RankedItem(3, "172.18.0.22:8080", 9883, 17637),
            RankedItem(4, "172.18.0.27:8080", 9883, 17637),
            RankedItem(5, "frontend", 9883, 17637),
            RankedItem(6, "frontend-proxy:8080", 9883, 17637),
            RankedItem(7, "http/1.1", 9883, 17637),
            RankedItem(8, "via_upstream", 9847, 17637),
            RankedItem(9, "python-requests/2.32.3", 9750, 17637),
            RankedItem(10, "min-width", 9704, 17637),
            RankedItem(11, "some longer url field here", 9600, 17637),
            RankedItem(12, "another extended attribute", 9500, 17637),
            RankedItem(13, "even more attributes", 9400, 17637),
            RankedItem(14, "additional data field", 9300, 17637),
            RankedItem(15, "final attribute name", 9200, 17637),
        ]
        content = self.query_one("#content", Static)
        content.update(self.format_text(mock_data))
        self.app.log.info(f"[TopWordsPanel] updated: items={len(mock_data)}, panel_size={self.size}, content_size={content.size}")
