from textual.widgets import Static
from textual.containers import Container
from models.types import LogPattern


class LogPatternsPanel(Static):
    COLORS = {
        "red": "on_red",
        "orange": "on_dark_orange",
        "yellow": "on_yellow",
        "blue": "on_blue",
        "green": "on_green",
        "purple": "on_magenta",
    }
    
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
        ]
        self.update(self.format_text(mock_data))
