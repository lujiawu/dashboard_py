# DWS Info Panel — Dashboard Integration Design

## Summary

Replace the mock `TopAttributesPanel` with a live `DwsInfoPanel` showing DingTalk unread conversations and today's calendar agenda, fetched via DWS CLI.

## Architecture

```
DwsChatSource.fetch()       → List[ChatConversation]
DwsCalendarSource.fetch()   → List[CalendarEvent]
        ↓ (concurrent)
app.py _poll_dws_info() merges results
        ↓
DwsInfoPanel.update(conversations, events) → Rich markup render
```

## Data Models (`models/types.py`)

```python
@dataclass
class ChatConversation:
    conversation_id: str
    title: str
    unread_count: int
    is_single_chat: bool = False
    def __hash__(self): return id(self)

@dataclass
class CalendarEvent:
    event_id: str
    title: str
    start_time: int    # unix ms
    end_time: int      # unix ms
    def __hash__(self): return id(self)
```

## Data Sources

### `store/sources/dws_chat_source.py`
- Inherits `DataSource[List[ChatConversation]]`
- Runs `dws chat message list-unread-conversations --format json`
- Parses `result.conversations[]` → `ChatConversation`
- Refresh interval: 60s
- On failure: returns empty list, logs error

### `store/sources/dws_calendar_source.py`
- Inherits `DataSource[List[CalendarEvent]]`
- Computes today's start/end in ISO-8601 (Asia/Shanghai)
- Runs `dws calendar event list --start <today_start> --end <today_end> --format json`
- Parses `result.events[]` → `CalendarEvent`
- Refresh interval: 300s (calendar rarely changes mid-day)
- On failure: returns empty list, logs error

## Widget (`widgets/dws_info_panel.py`)

- Inherits `VerticalScroll` (matches replacement footprint)
- Contains a single `Static` widget for rich text content
- Layout (chat on top, calendar below):

```
┌─ DWS Info ──────────────────────┐
│ 💬 未读消息                      │
│   软件开发部                 2条 │
│   侦测产品沟通               2条 │
│                                  │
│ 📅 今日日程                      │
│   09:00  站会                    │
│   14:00  Q1复盘会                │
└──────────────────────────────────┘
```

- `update(conversations, events)`: builds a Rich `Text` or plain string with styling
  - Chat: one line per conversation, `{title:<30} {count:>3}条`
  - Calendar: one line per event, `{HH:mm}  {title}`, sorted by start_time
  - Empty states: "暂无未读消息" / "今日无日程"

## App Integration (`app.py`)

| Change | Detail |
|--------|--------|
| Import | Replace `TopAttributesPanel` with `DwsInfoPanel` |
| Compose | `DwsInfoPanel(id="dws-info", classes="panel")` replaces `TopAttributesPanel` |
| Mount | Add `dws_calendar_source = DwsCalendarSource()` |
| Poll | Add `_poll_dws_info()`: concurrently fetches chat + calendar, calls panel.update() |
| Poll interval | `self.set_interval(60, self._poll_dws_info)` |
| Key `r` | Refresh `_poll_dws_info()` alongside other sources |
| Cleanup | Remove `query_one("#top-attributes").update_mock_data()` calls (3 places) |

## Error Handling

- CLI failures (dws not installed, not authenticated) → empty data shown gracefully
- Each source independently handles errors; one failing doesn't block the other
- Logging via `logging.getLogger(__name__)`
- No retry — next poll cycle picks up if transient

## Files Changed

| File | Action |
|------|--------|
| `models/types.py` | +2 dataclasses (ChatConversation, CalendarEvent) |
| `store/sources/dws_chat_source.py` | New file |
| `store/sources/dws_calendar_source.py` | New file |
| `widgets/dws_info_panel.py` | New file |
| `widgets/top_attributes_panel.py` | Keep (not imported from app), or remove |
| `app.py` | Substitute TopAttributesPanel → DwsInfoPanel |
| `styles/app.tcss` | Unchanged |
