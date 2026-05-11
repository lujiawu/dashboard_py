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
        return await self._fetch_by_status("false")

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

    async def set_done_status(self, task_id: str, completed: bool) -> bool:
        import logging
        _log = logging.getLogger(__name__)
        status = "true" if completed else "false"
        cmd = ["dws", "todo", "task", "done", "--task-id", task_id, "--status", status, "--format", "json"]
        _log.info(f"[DWS] set_done_status task_id={task_id} status={status}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        _log.info(f"[DWS] set_done_status rc={proc.returncode} stdout={stdout.decode().strip()!r} stderr={stderr.decode().strip()!r}")
        return proc.returncode == 0

    async def create_todo(self, title: str, executor: str = "01455548515339212734") -> bool:
        import logging
        _log = logging.getLogger(__name__)
        cmd = ["dws", "todo", "task", "create", "--title", title, "--executors", executor, "--format", "json", "-y"]
        _log.info(f"[DWS] create_todo title={title!r} executor={executor}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        _log.info(f"[DWS] create_todo rc={proc.returncode} stdout={stdout.decode().strip()!r} stderr={stderr.decode().strip()!r}")
        return proc.returncode == 0

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval