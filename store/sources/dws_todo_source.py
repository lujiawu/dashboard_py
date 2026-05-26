import asyncio
import json
import logging
from typing import List

from store.sources.base import DataSource
from models.types import Todo

logger = logging.getLogger(__name__)


class DwsTodoSource(DataSource[List[Todo]]):
    """Fetch todos from DWS CLI (dingtalk)."""

    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 60.0)
        self._page = config.get("page", 1)
        self._page_size = config.get("page_size", 100)
        self._executor_id = config.get("executor_id", "01455548515339212734")
        self._last_fp: int = 0
        self._cached: List[Todo] = []

    async def fetch(self) -> List[Todo]:
        return await self._fetch_by_status("false")

    async def _fetch_by_status(self, status: str) -> List[Todo]:
        cmd = ["dws", "todo", "task", "list",
               "--page", str(self._page), "--size", str(self._page_size),
               "--status", status, "--format", "json"]

        logger.info("[DwsTodo] running: %s", " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning("[DwsTodo] rc=%d stderr=%s", proc.returncode, stderr.decode(errors="replace").strip()[:200])
            return self._cached

        fp = hash(stdout)
        if fp == self._last_fp:
            return self._cached
        self._last_fp = fp

        try:
            data = json.loads(stdout.decode())
            cards = data.get("result", {}).get("todoCards", [])
            todos = [
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
            self._cached = todos
            logger.info("[DwsTodo] status=%s, got %d todos", status, len(todos))
            return todos
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("[DwsTodo] parse failed: %s, raw=%s", e, stdout.decode(errors="replace").strip()[:200])
            return self._cached

    async def set_done_status(self, task_id: str, completed: bool) -> bool:
        status = "true" if completed else "false"
        cmd = ["dws", "todo", "task", "done", "--task-id", task_id, "--status", status, "--format", "json"]
        logger.info("[DWS] set_done_status task_id=%s status=%s", task_id, status)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info("[DWS] set_done_status rc=%d stdout=%s stderr=%s",
            proc.returncode, stdout.decode().strip(), stderr.decode().strip())
        return proc.returncode == 0

    async def create_todo(self, title: str, executor: str = None) -> bool:
        if executor is None:
            executor = self._executor_id
        cmd = ["dws", "todo", "task", "create", "--title", title, "--executors", executor, "--format", "json", "-y"]
        logger.info("[DWS] create_todo title=%s executor=%s", title, executor)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info("[DWS] create_todo rc=%d stdout=%s stderr=%s",
            proc.returncode, stdout.decode().strip(), stderr.decode().strip())
        return proc.returncode == 0

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval