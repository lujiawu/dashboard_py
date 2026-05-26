import logging
import webbrowser
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from textual import on
from textual.message import Message
from textual.widgets import DataTable
from textual.containers import Vertical
from textual.events import Click
from rich.text import Text

logger = logging.getLogger(__name__)

_TYPE_ICON = {
    "Bug": Text("\U0001f41b", style="red"),
    "Task": Text("\u2699", style="blue"),
    "Req": Text("\U0001f4cb", style="green"),
}


def _format_created_at(ts: int) -> str:
    if not ts:
        return "--"
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%m-%d")


class _YunxiaoTable(DataTable):
    class CtrlClicked(Message):
        def __init__(self, row_index: int):
            super().__init__()
            self.row_index = row_index

    class EnterPressed(Message):
        def __init__(self, row_index: int):
            super().__init__()
            self.row_index = row_index

    def action_select_cursor(self):
        super().action_select_cursor()
        logger.info("[_YunxiaoTable] action_select_cursor row=%d", self.cursor_row)
        if self.cursor_row >= 0:
            self.post_message(self.EnterPressed(self.cursor_row))

    def on_click(self, event: Click):
        logger.info("[_YunxiaoTable] on_click button=%d ctrl=%s", event.button, event.ctrl)
        if event.ctrl and event.button == 1 and self.cursor_row >= 0:
            logger.info("[_YunxiaoTable] CtrlClicked row=%d", self.cursor_row)
            self.post_message(self.CtrlClicked(self.cursor_row))


class YunxiaoPanel(Vertical):

    def compose(self):
        self._table = _YunxiaoTable()
        self._table.zebra_stripes = True
        self._table.cursor_type = "row"
        self._table.styles.height = "1fr"
        self._last_items: List[Dict[str, Any]] | None = None
        yield self._table

    def on_mount(self):
        self._table.add_column("Type", width=4)
        self._table.add_column("Title")
        created_col = self._table.add_column("Created", width=5)
        self._table.columns[created_col].justify = "right"
        self._item_map: dict[int, Dict[str, Any]] = {}

    def update_items(self, items: List[Dict[str, Any]]):
        if items is self._last_items:
            return
        self._last_items = items
        self._table.clear()
        self._item_map = {}
        if not items:
            self._table.add_rows([(Text("", style=""), Text("📭 暂无工作项", style="dim"), Text("", style=""))])
            return

        rows = []
        for i, item in enumerate(items):
            self._item_map[i] = item
            icon = _TYPE_ICON.get(item.get("type", ""), Text("\u2022", style="dim"))
            title = item.get("title", "")
            created = _format_created_at(item.get("created_at"))
            rows.append((icon, title, created))

        self._table.add_rows(rows)
        logger.info("[YunxiaoPanel] updated with %d items", len(items))

    def _open_url(self, row_index: int):
        item = self._item_map.get(row_index)
        if not item:
            logger.warning("[YunxiaoPanel] _open_url row=%d no item", row_index)
            return
        url = item.get("url")
        if url:
            logger.info("[YunxiaoPanel] _open_url row=%d url=%s", row_index, url)
            webbrowser.open(url)
        else:
            logger.warning("[YunxiaoPanel] _open_url row=%d no url in item", row_index)

    @on(_YunxiaoTable.EnterPressed)
    def on_enter_pressed(self, event: _YunxiaoTable.EnterPressed):
        logger.info("[YunxiaoPanel] EnterPressed row=%d", event.row_index)
        event.stop()
        self._open_url(event.row_index)

    @on(_YunxiaoTable.CtrlClicked)
    def on_ctrl_clicked(self, event: _YunxiaoTable.CtrlClicked):
        logger.info("[YunxiaoPanel] CtrlClicked row=%d", event.row_index)
        event.stop()
        self._open_url(event.row_index)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected):
        logger.info("[YunxiaoPanel] RowSelected row=%d", event.cursor_row)
        event.stop()
