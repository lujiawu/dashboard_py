import asyncio
import json
from typing import List

from store.sources.base import DataSource
from models.types import GoalProgress


class RunningShoeSource(DataSource[List[GoalProgress]]):

    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 86400.0)
        self._base_id = config["base_id"]
        self._table_id = config["table_id"]
        self._field_ids = config["field_ids"]
        self._field_name = config["field_name"]
        self._field_goal = config["field_goal"]
        self._field_used = config["field_used"]
        self._field_status = config["field_status"]
        self._filter_status = config["filter_status_value"]

    async def fetch(self) -> List[GoalProgress]:
        filters = json.dumps({
            "operator": "and",
            "operands": [{"operator": "eq", "operands": [self._field_status, self._filter_status]}]
        })

        cmd = [
            "dws", "aitable", "record", "query",
            "--base-id", self._base_id,
            "--table-id", self._table_id,
            "--field-ids", self._field_ids,
            "--filters", filters,
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
            records = data.get("data", {}).get("records", [])
        except (json.JSONDecodeError, KeyError):
            return []

        result: list[GoalProgress] = []
        for record in records:
            cells = record.get("cells", {})
            name = cells.get(self._field_name, "")

            goal_raw = cells.get(self._field_goal)
            if goal_raw is None:
                continue
            goal = float(goal_raw)

            used_raw = cells.get(self._field_used, {})
            used = float(used_raw.get("value", ["0"])[0]) if isinstance(used_raw, dict) else 0.0

            result.append(GoalProgress(name=name, used=used, goal=goal, unit="km", icon="👟"))

        return result

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
