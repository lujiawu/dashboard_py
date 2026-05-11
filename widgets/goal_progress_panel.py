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
        return "\n\n".join(self._render_card(item) for item in items)

    def _render_card(self, item: GoalProgress) -> str:
        pct = item.percentage
        filled = int(pct / 100 * self.BAR_WIDTH)
        is_warn = item.is_warning

        bar_chars = "█" * filled + "░" * (self.BAR_WIDTH - filled)

        line1 = f"{item.icon}  {item.name}  USED: {item.used}{item.unit}  /  GOAL: {item.goal}{item.unit}"
        if item.disabled:
            line1 += "  [停用]"

        line2 = f"│  {bar_chars} {pct:.0f}%"

        if is_warn:
            return "\n".join([
                f"[bold red on #330000]  {line1}[/]",
                f"[red on #330000]  {line2}[/]",
            ])
        return "\n".join([f"  {line1}", f"  {line2}"])

    def update_mock_data(self):
        mock = [
            GoalProgress("24.2 summit1", 791.55, 1000, unit="km"),
            GoalProgress("24.8 速度马赫4 pro", 985.2, 1000, unit="km", disabled=True),
            GoalProgress("25.2C26", 982.1, 1000, unit="km", disabled=True),
        ]
        self.update_progress(mock)
