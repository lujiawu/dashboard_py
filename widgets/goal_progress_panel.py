import logging
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import GoalProgress

logger = logging.getLogger(__name__)


class GoalProgressPanel(VerticalScroll):

    BAR_WIDTH = 24

    def compose(self):
        yield Static(id="content", expand=True)

    def update_progress(self, items: list[GoalProgress]):
        content = self.query_one("#content", Static)
        content.update(self._format_cards(items))

    def _format_cards(self, items: list[GoalProgress]) -> str:
        if not items:
            return "No data"
        return "\n".join(self._render_card(item) for item in items)

    def _render_card(self, item: GoalProgress, indent: int = 0) -> str:
        pct = item.percentage
        filled = int(pct / 100 * self.BAR_WIDTH)
        is_warn = item.is_warning
        pad = "  " * indent

        bar_chars = "\u2501" * filled + " " * (self.BAR_WIDTH - filled)

        name_line = f"{pad}  {item.icon}  {item.name}  {item.current:.0f}{item.unit}  /  {item.goal:.0f}{item.unit}"
        if item.disabled:
            name_line += "  [\u505c\u7528]"

        bar_line = f"{pad}    {bar_chars} {pct:.0f}%"
        bar_line_colored = f"[red]{bar_line}[/]" if is_warn else bar_line

        lines = [name_line, bar_line_colored]
        if item.children:
            for child in item.children:
                lines.append(self._render_card(child, indent + 1))

        return "\n".join(lines)
