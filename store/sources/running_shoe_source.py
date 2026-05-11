import asyncio
import json
from typing import List

from store.sources.base import DataSource
from models.types import GoalProgress


BASE_ID = "l6Pm2Db8D42a4dNLc9Z67P6E8xLq0Ee4"
TABLE_ID = "PmIpDEs"
FIELD_IDS = "VCAIrdC,Dj9zate,Ayza2UW,DmagDUP"

FIELD_NAME = "VCAIrdC"
FIELD_GOAL = "Dj9zate"
FIELD_USED = "Ayza2UW"
FIELD_STATUS = "DmagDUP"


class RunningShoeSource(DataSource[List[GoalProgress]]):

    def __init__(self, refresh_interval: float = 86400.0):
        self._refresh_interval = refresh_interval

    async def fetch(self) -> List[GoalProgress]:
        filters = json.dumps({
            "operator": "and",
            "operands": [{"operator": "eq", "operands": [FIELD_STATUS, "在用"]}]
        })

        cmd = [
            "dws", "aitable", "record", "query",
            "--base-id", BASE_ID,
            "--table-id", TABLE_ID,
            "--field-ids", FIELD_IDS,
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
            name = cells.get(FIELD_NAME, "")

            goal_raw = cells.get(FIELD_GOAL)
            if goal_raw is None:
                continue
            goal = float(goal_raw)

            used_raw = cells.get(FIELD_USED, {})
            used = float(used_raw.get("value", ["0"])[0]) if isinstance(used_raw, dict) else 0.0

            result.append(GoalProgress(name=name, used=used, goal=goal, unit="km", icon="👟"))

        return result

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
