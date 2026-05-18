import logging
from textual.containers import VerticalScroll
from textual.widgets import Collapsible, Static
from models.types import GoalProgress

logger = logging.getLogger(__name__)
BAR_WIDTH = 24


def _build_title(item: GoalProgress) -> str:
    pct = item.percentage
    filled = int(pct / 100 * BAR_WIDTH)
    bar = "\u2501" * filled + " " * (BAR_WIDTH - filled)
    if item.is_warning:
        bar = f"[red]{bar}[/]"
    title = f"{item.icon} {item.name}  {item.current:.0f}{item.unit}/{item.goal:.0f}{item.unit}  {bar} {pct:.0f}%"
    if item.disabled:
        title += "  [\u505c\u7528]"
    return title


def _build_children_text(children: list[GoalProgress]) -> str:
    lines = []
    for child in children:
        pct = child.percentage
        lines.append(f"  {child.icon} {child.name}  {child.current:.0f}{child.unit}/{child.goal:.0f}{child.unit}  {pct:.0f}%")
    return "\n".join(lines)


class GoalTreePanel(VerticalScroll):

    def compose(self):
        yield Static(id="content", expand=True)

    def update_progress(self, items: list[GoalProgress]):
        logger.info("[GoalPanel] update_progress with %d items", len(items))
        self.query(".goal-tree-item").remove()
        no_data = self.query_one("#content", Static)
        if not items:
            no_data.remove_class("hidden")
            return
        no_data.add_class("hidden")
        for item in items:
            content = []
            if item.children:
                content.append(Static(
                    _build_children_text(item.children),
                    classes="goal-children"
                ))
            self.mount(Collapsible(
                *content,
                title=_build_title(item),
                collapsed=True,
                collapsed_symbol="\u25b6",
                expanded_symbol="\u25bc",
                classes="goal-tree-item",
            ))
