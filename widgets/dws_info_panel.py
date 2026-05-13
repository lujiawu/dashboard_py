from datetime import datetime, timezone, timedelta
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.cells import cell_len

from models.types import ChatConversation, CalendarEvent

_TZ = timezone(timedelta(hours=8))


_WEEKDAY = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _relative_day(d: datetime.date, today: datetime.date) -> str:
    diff = (d - today).days
    if diff == 0:
        return "今天"
    if diff == 1:
        return "明天"
    if diff == 2:
        return "后天"
    return _WEEKDAY[d.weekday()]


def _pad_cjk(text: str, width: int) -> str:
    """Pad/truncate text to exactly `width` display columns (CJK = 2 cols)."""
    result = ""
    for ch in text:
        if cell_len(result + ch) > width:
            break
        result += ch
    pad = width - cell_len(result)
    return result + " " * pad


class DwsInfoPanel(VerticalScroll):
    def compose(self):
        self._content = Static()
        yield self._content

    def update(self, conversations: list[ChatConversation], events: list[CalendarEvent]):
        self._content.update(self._format_content(conversations, events))

    def _format_content(self, conversations: list[ChatConversation], events: list[CalendarEvent]) -> str:
        parts = []

        parts.append("[bold]💬 未读消息[/bold]")
        if not conversations:
            parts.append("  [dim]✨ 暂无新消息[/dim]")
        else:
            for c in conversations:
                title = _pad_cjk(c.title, 30)
                parts.append(f"  {title} {c.unread_count:>3}")

        parts.append("")
        parts.append("[bold]📅 近7日日程[/bold]")
        if not events:
            parts.append("  [dim]✨ 暂无日程[/dim]")
        else:
            today = datetime.now(_TZ).date()
            for e in sorted(events, key=lambda x: x.start_time):
                dt = datetime.fromtimestamp(e.start_time / 1000, tz=_TZ)
                label = _relative_day(dt.date(), today)
                parts.append(f"  {label} {dt.strftime('%H:%M'):>5}  {e.title}")

        return "\n".join(parts)
