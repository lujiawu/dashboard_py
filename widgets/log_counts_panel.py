from textual.widgets import Static
from models.types import LogLevelStats


class LogCountsPanel(Static):
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
        histogram = [8, 12, 9, 10, 11, 25, 8, 7, 3, 2]
        stats = LogLevelStats(
            fatal=0,
            error=0,
            warn=0,
            info=0,
            debug=0,
            trace=0,
            total=0
        )
        self.update(self.format_text(histogram, stats))
