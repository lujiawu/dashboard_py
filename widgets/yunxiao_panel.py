import logging
from datetime import datetime, timezone, timedelta
from textual.widgets import DataTable
from textual.containers import Vertical
from models.types import YunxiaoItem

logger = logging.getLogger(__name__)


def _priority_label(priority: str) -> str:
    if not priority:
        return "-"
    priority_map = {
        "紧急": "!!!",
        "高": "!!",
        "中": "!",
        "低": ".",
    }
    return priority_map.get(priority, priority)


def _format_due(due_time: int) -> str:
    if not due_time:
        return "--"
    try:
        dt = datetime.fromtimestamp(due_time / 1000, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%m-%d")
    except (ValueError, OSError):
        return "--"


def _type_icon(type_str: str) -> str:
    type_map = {
        "Req": "📋",
        "Task": "⚙️",
        "Bug": "🐛",
    }
    return type_map.get(type_str, "•")


class YunxiaoPanel(Vertical):

    def compose(self):
        self._table = DataTable()
        self._table.zebra_stripes = True
        self._table.cursor_type = "row"
        self._table.styles.height = "1fr"
        yield self._table

    def on_mount(self):
        self._table.add_column("T", width=2)
        self._table.add_column("P", width=3)
        self._table.add_column("Due", width=8)
        self._table.add_column("Status", width=10)
        self._table.add_column("Title")

    def update_items(self, items: list[YunxiaoItem]):
        self._table.clear()
        if not items:
            return

        # 按优先级和截止时间排序
        priority_order = {"紧急": 0, "高": 1, "中": 2, "低": 3, "": 4}
        items.sort(key=lambda x: (
            priority_order.get(x.priority, 4),
            x.due_time if x.due_time else 2**63,
        ))

        for item in items:
            type_icon = _type_icon(item.type)
            p_label = _priority_label(item.priority)
            due = _format_due(item.due_time)
            status = item.status[:10] if len(item.status) > 10 else item.status
            title = f"{item.title}"
            if item.project:
                title = f"[{item.project}] {title}"

            self._table.add_row(type_icon, p_label, due, status, title)

        logger.info(f"[YunxiaoPanel] updated with {len(items)} items")
