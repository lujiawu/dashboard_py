import asyncio
import json
import urllib.request
from typing import List

from store.sources.base import DataSource
from models.types import GoalProgress


class GearHttpSource(DataSource[List[GoalProgress]]):

    def __init__(self, config: dict):
        self._api_url = config["api_url"]
        self._refresh_interval = config.get("refresh_interval", 86400.0)

    async def fetch(self) -> List[GoalProgress]:
        data = await self._fetch_json(self._api_url)
        payload = data.get("data", {})
        records = payload.get("records", [])

        result: List[GoalProgress] = []
        for record in records:
            cells = record.get("cells", {})
            name = cells.get("VCAIrdC", "")

            goal_raw = cells.get("Dj9zate")
            if goal_raw is None:
                continue
            goal = float(goal_raw)

            used_raw = cells.get("Ayza2UW", {})
            if isinstance(used_raw, dict):
                used = float(used_raw.get("value", ["0"])[0])
            else:
                used = 0.0

            result.append(GoalProgress(name=name, used=used, goal=goal, unit="km", icon="👟"))

        return result

    async def _fetch_json(self, url: str) -> dict:
        def _get():
            with urllib.request.urlopen(url, timeout=10) as resp:
                return json.loads(resp.read())

        return await asyncio.to_thread(_get)

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
