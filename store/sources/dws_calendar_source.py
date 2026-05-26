import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List

from store.sources.base import DataSource
from models.types import CalendarEvent

logger = logging.getLogger(__name__)


_TZ = timezone(timedelta(hours=8))


def _week_iso_range():
    now = datetime.now(_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=0)
    return start.strftime("%Y-%m-%dT%H:%M:%S+08:00"), end.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def _parse_iso_to_ms(iso_str: str) -> int:
    try:
        dt = datetime.fromisoformat(iso_str)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError):
        return 0


class DwsCalendarSource(DataSource[List[CalendarEvent]]):
    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 300.0)
        self._last_fp: int = 0
        self._cached: List[CalendarEvent] = []

    async def fetch(self) -> List[CalendarEvent]:
        start_iso, end_iso = _week_iso_range()
        cmd = [
            "dws", "calendar", "event", "list",
            "--start", start_iso,
            "--end", end_iso,
            "--format", "json",
        ]
        logger.info("[DwsCalendar] running: %s", " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning("[DwsCalendar] rc=%d stderr=%s", proc.returncode, stderr.decode(errors="replace").strip()[:200])
            return self._cached

        fp = hash(stdout)
        if fp == self._last_fp:
            return self._cached
        self._last_fp = fp

        try:
            data = json.loads(stdout.decode())
            events = data.get("result", {}).get("events", [])
            calendar_events = [
                CalendarEvent(
                    event_id=item.get("id", ""),
                    title=item.get("summary", ""),
                    start_time=_parse_iso_to_ms(item.get("start", {}).get("dateTime", "")),
                    end_time=_parse_iso_to_ms(item.get("end", {}).get("dateTime", "")),
                )
                for item in events
            ]
            self._cached = calendar_events
            logger.info("[DwsCalendar] range=%s..%s, got %d events",
                start_iso[:10], end_iso[:10], len(calendar_events))
            return calendar_events
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("[DwsCalendar] parse failed: %s, raw=%s", e, stdout.decode(errors="replace").strip()[:200])
            return self._cached

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
