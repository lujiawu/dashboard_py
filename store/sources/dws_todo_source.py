import asyncio
import json
from typing import List

from store.sources.base import DataSource
from models.types import Todo


class DwsTodoSource(DataSource[List[Todo]]):
    """Fetch todos from DWS CLI (dingtalk)."""

    def __init__(self, refresh_interval: float = 60.0):
        self._refresh_interval = refresh_interval

    async def fetch(self) -> List[Todo]:
        pending = await self._fetch_by_status("false")
        done = await self._fetch_by_status("true")
        return pending + done

    async def _fetch_by_status(self, status: str) -> List[Todo]:
        cmd = ["dws", "todo", "task", "list", "--page", "1", "--size", "100", "--status", status, "--format", "json"]

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
            cards = data.get("result", {}).get("todoCards", [])
            return [
                Todo(
                    id=item.get("taskId", ""),
                    subject=item.get("subject", ""),
                    completed=(status == "true"),
                    priority=item.get("priority", 0),
                    due_time=item.get("dueTime") or 0,
                    created_time=item.get("createdTime") or 0,
                )
                for item in cards
            ]
        except (json.JSONDecodeError, KeyError):
            return []

    async def mark_done(self, task_id: str) -> bool:
        cmd = ["dws", "todo", "task", "done", "--task-id", task_id, "--status", "true", "--format", "json"]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        return proc.returncode == 0

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval