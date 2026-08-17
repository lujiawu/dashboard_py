import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
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
            descriptions = await asyncio.gather(
                *(self._fetch_description(item.get("taskId", "")) for item in cards),
                return_exceptions=True,
            )
            todos = [
                Todo(
                    id=item.get("taskId", ""),
                    subject=item.get("subject", ""),
                    description=description if isinstance(description, str) else "",
                    completed=(status == "true"),
                    priority=item.get("priority", 0),
                    due_time=item.get("dueTime") or 0,
                    created_time=item.get("createdTime") or 0,
                )
                for item, description in zip(cards, descriptions)
            ]
            self._cached = todos
            logger.info("[DwsTodo] status=%s, got %d todos", status, len(todos))
            return todos
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("[DwsTodo] parse failed: %s, raw=%s", e, stdout.decode(errors="replace").strip()[:200])
            return self._cached

    async def _fetch_description(self, task_id: str) -> str:
        if not task_id:
            return ""
        proc = await asyncio.create_subprocess_exec(
            "dws", "todo", "task", "get", "--task-id", task_id, "--format", "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return ""
        try:
            data = json.loads(stdout.decode())
            return data.get("result", {}).get("todoDetailModel", {}).get("description", "") or ""
        except (json.JSONDecodeError, AttributeError):
            return ""

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

    async def update_todo(self, task_id: str, title: str = None, priority: int = None, due_time: int = None) -> bool:
        cmd = ["dws", "todo", "task", "update", "--task-id", task_id, "--format", "json", "-y"]
        if title is not None:
            cmd += ["--title", title]
        if priority is not None:
            cmd += ["--priority", str(priority)]
        if due_time:
            dt = datetime.fromtimestamp(due_time / 1000, tz=timezone(timedelta(hours=8)))
            cmd += ["--due", dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")]
        logger.info("[DWS] update_todo task_id=%s args=%s", task_id, cmd)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info("[DWS] update_todo rc=%d stdout=%s stderr=%s",
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
