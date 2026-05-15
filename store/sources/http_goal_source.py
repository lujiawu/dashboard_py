import asyncio
import json
import logging
import urllib.request
from typing import List

from store.sources.base import DataSource
from models.types import GoalProgress

logger = logging.getLogger(__name__)


class HttpGoalSource(DataSource[List[GoalProgress]]):

    def __init__(self, config: dict):
        self._api_url = config["api_url"]
        self._refresh_interval = config.get("refresh_interval", 86400.0)

    async def fetch(self) -> List[GoalProgress]:
        logger.info("[HttpGoal] fetching %s", self._api_url)
        raw = await self._fetch_json(self._api_url)
        records = raw if isinstance(raw, list) else raw.get("data", [])
        if not isinstance(records, list):
            logger.warning("[HttpGoal] unexpected response shape, expected array or {data: [...]}")
            return []

        result: List[GoalProgress] = []
        for r in records:
            try:
                obj = GoalProgress(
                    name=r["name"],
                    current=float(r.get("current", 0)),
                    goal=float(r["goal"]),
                    unit=r.get("unit", ""),
                    disabled=r.get("disabled", False),
                    icon=r.get("icon", "◆"),
                    children=[GoalProgress(
                        name=c["name"],
                        current=float(c.get("current", 0)),
                        goal=float(c["goal"]),
                        unit=c.get("unit", ""),
                        icon=c.get("icon", "◆"),
                    ) for c in r.get("children", [])],
                )
                result.append(obj)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning("[HttpGoal] skip malformed record %s: %s", r, e)

        logger.info("[HttpGoal] got %d records", len(result))
        return result

    async def _fetch_json(self, url: str):
        def _get():
            with urllib.request.urlopen(url, timeout=10) as resp:
                return json.loads(resp.read())

        return await asyncio.to_thread(_get)

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
