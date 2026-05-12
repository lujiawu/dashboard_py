import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List

from store.sources.base import DataSource
from models.types import CalendarEvent


_TZ = timezone(timedelta(hours=8))


def _today_iso_range():
    now = datetime.now(_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return start.strftime("%Y-%m-%dT%H:%M:%S+08:00"), end.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _parse_iso_to_ms(iso_str: str) -> int:
    try:
        dt = datetime.fromisoformat(iso_str)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return 0


class DwsCalendarSource(DataSource[List[CalendarEvent]]):
    def __init__(self, refresh_interval: float = 300.0):
        self._refresh_interval = refresh_interval

    async def fetch(self) -> List[CalendarEvent]:
        start_iso, end_iso = _today_iso_range()
        cmd = [
            "dws", "calendar", "event", "list",
            "--start", start_iso,
            "--end", end_iso,
            "--format", "json",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return []

        try:
            data = json.loads(stdout.decode())
            events = data.get("result", {}).get("events", [])
            return [
                CalendarEvent(
                    event_id=item.get("eventId", ""),
                    title=item.get("title", ""),
                    start_time=_parse_iso_to_ms(item.get("start", "")),
                    end_time=_parse_iso_to_ms(item.get("end", "")),
                )
                for item in events
            ]
        except (json.JSONDecodeError, KeyError):
            return []

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
