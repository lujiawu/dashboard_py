import logging
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import LogLevelStats

logger = logging.getLogger(__name__)


class LogCountsPanel(VerticalScroll):
    def compose(self):
        yield Static(id="content", expand=True)

    def format_text(self, histogram: list[int], stats: LogLevelStats) -> str:
        if not histogram:
            return "No data"

        max_val = max(histogram) if histogram else 1
        min_val = min(histogram) if histogram else 0

        bars = []
        for val in histogram:
            bar_height = int(val / max_val * 6) if max_val > 0 else 0
            bar_chars = " ▁▂▃▄▅▆▇█"
            bars.append(f"[blue]{bar_chars[bar_height]}[/blue]")

        histogram_line = "".join(bars)

        stats_lines = [
            f"[red]FATAL : {stats.fatal}[/red]",
            f"[red]ERROR : {stats.error}[/red]",
            f"[yellow]WARN  : {stats.warn}[/yellow]",
            f"[green]INFO  : {stats.info}[/green]",
            f"[blue]DEBUG : {stats.debug}[/blue]",
            f"[magenta]TRACE : {stats.trace}[/magenta]",
            f"TOTAL : {stats.total}",
        ]

        header = f"Min: {min_val} | Max: {max_val}"

        return f"{header}\n{histogram_line}\n\n" + "\n".join(stats_lines)

    def update_mock_data(self):
        histogram = [8, 12, 9, 10, 11, 25, 8, 7, 3, 2, 15, 11, 9, 8, 7, 6, 8, 9, 10, 11, 12, 13]
        stats = LogLevelStats(
            fatal=2,
            error=5,
            warn=10,
            info=15,
            debug=20,
            trace=8,
            total=60
        )
        content = self.query_one("#content", Static)
        content.update(self.format_text(histogram, stats))
        logger.info(f"[LogCountsPanel] updated: histogram_len={len(histogram)}, panel_size={self.size}, content_size={content.size}")
