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

    def _render_card(self, item: GoalProgress) -> str:
        pct = item.percentage
        filled = int(pct / 100 * self.BAR_WIDTH)
        is_warn = item.is_warning

        bar_chars = "━" * filled + " " * (self.BAR_WIDTH - filled)

        line1 = f"{item.icon}  {item.name}  {item.used:.0f}{item.unit}  /  {item.goal:.0f}{item.unit}"
        if item.disabled:
            line1 += "  [停用]"

        line2 = f"  {bar_chars} {pct:.0f}%"

        if is_warn:
            return "\n".join([
                f"  {line1}",
                f"  [red]{line2}[/]",
            ])
        return "\n".join([f"  {line1}", f"  {line2}"])
