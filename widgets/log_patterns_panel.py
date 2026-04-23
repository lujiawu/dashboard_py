import logging
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import LogPattern

logger = logging.getLogger(__name__)


class LogPatternsPanel(VerticalScroll):
    COLORS = {
        "red": "on_red",
        "orange": "on_dark_orange",
        "yellow": "on_yellow",
        "blue": "on_blue",
        "green": "on_green",
        "purple": "on_magenta",
    }

    def compose(self):
        yield Static(id="content", expand=True)

    def format_text(self, patterns: list[LogPattern]) -> str:
        if not patterns:
            return "No patterns"

        lines = []
        for pattern in patterns:
            bar_width = 10
            filled = max(1, int(pattern.percentage / 100 * bar_width))
            color_class = self.COLORS.get(pattern.color, "on_gray")
            bar = "█" * filled + "░" * (bar_width - filled)
            lines.append(f"[{color_class}]{bar}[/{color_class}] {pattern.percentage:>5.1f}%  {pattern.pattern}")

        return "\n".join(lines)

    def update_mock_data(self):
        mock_data = [
            LogPattern("*** *** *** HTTP/1.1 *** - via_upstream ...", 22.6, 29587, "red"),
            LogPattern("GetCartAsync called with userId={userId}", 12.5, 16375, "orange"),
            LogPattern("Convert conversion successful", 9.8, 12834, "yellow"),
            LogPattern("Calculated quote", 6.0, 7860, "blue"),
            LogPattern("no baggage found in context", 6.0, 7860, "green"),
            LogPattern("AddItemAsync called with userId={userId},...", 5.9, 7729, "purple"),
            LogPattern("Targeted ad request received for ***", 3.0, 3930, "blue"),
            LogPattern("Deleted *** index ***", 2.0, 2620, "green"),
            LogPattern("Some additional log pattern", 1.8, 2300, "red"),
            LogPattern("Yet another pattern here", 1.5, 2000, "orange"),
            LogPattern("Additional pattern for scrolling", 1.2, 1800, "yellow"),
            LogPattern("More patterns for vertical scrolling", 1.0, 1600, "blue"),
            LogPattern("Final pattern in list", 0.8, 1400, "purple"),
        ]
        content = self.query_one("#content", Static)
        content.update(self.format_text(mock_data))
        logger.info(f"[LogPatternsPanel] updated: items={len(mock_data)}, panel_size={self.size}, content_size={content.size}")
