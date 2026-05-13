import asyncio
import json
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from store.sources.base import DataSource

logger = logging.getLogger(__name__)

ORG_ID = "681f24490bd1e62a78d91516"
PROJECT_ID = "c121cbdbe805eb951e4c8cd254"

BUG_TYPES = [
    "37da3a07df4d08aef2e3b393",
    "17d33cb4ff7f985dc097626969",
]
TASK_TYPES = [
    "ba102e46bc6a8483d9b7f25c",
]
REQ_TYPES = [
    "9uy29901re573f561d69jn40",
    "bca48ee2a0976d38f4802fae",
]

ACTIVE_BUG_STATUS = [
    "28", "100010", "53e19cb99ba3b295fd38a3667b",
    "3e729203f51f6d60719dd35848", "30",
    "4e7a6897b94d883f7d716ee854", "e9c54fd14bc15561c13039fb7d",
]
ACTIVE_TASK_STATUS = ["100005", "100010"]
ACTIVE_REQ_STATUS = [
    "100005", "625489", "156603", "142838", "100012", "154395", "100010",
]

CATEGORY_CONFIGS = [
    ("Bug", BUG_TYPES, ACTIVE_BUG_STATUS),
    ("Task", TASK_TYPES, ACTIVE_TASK_STATUS),
    ("Req", REQ_TYPES, ACTIVE_REQ_STATUS),
]


class McpClient:
    """与 MCP Server 通过 stdio JSON-RPC 通信"""

    def __init__(self, server_cmd: list[str], env: dict[str, str]):
        self.server_cmd = server_cmd
        self.env = env
        self.proc: subprocess.Popen | None = None
        self._request_id = 0

    def start(self) -> None:
        self.proc = subprocess.Popen(
            self.server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **self.env},
            text=False,
            shell=True,
        )
        resp = self._call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "yunxiao-dashboard", "version": "1.0.0"},
        })
        name = resp.get("result", {}).get("serverInfo", {}).get("name", "unknown")
        logger.info("[Yunxiao] MCP 初始化完成: %s", name)
        self._notify("notifications/initialized", {})
        time.sleep(0.5)

    def stop(self) -> None:
        if self.proc:
            self.proc.stdin.close()
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
            logger.info("[Yunxiao] MCP 已停止")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._call("tools/call", {"name": name, "arguments": arguments})
        if "error" in result:
            raise RuntimeError(f"工具调用失败: {result['error']}")
        return result.get("result", result)

    def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        return self._send(request)

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params}, is_notification=True)

    def _send(self, payload: dict[str, Any], is_notification: bool = False) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False) + "\n"
        self.proc.stdin.write(body.encode("utf-8"))
        self.proc.stdin.flush()
        if is_notification:
            return {}
        line = self.proc.stdout.readline().decode("utf-8").strip()
        if not line:
            raise RuntimeError("MCP 响应为空")
        return json.loads(line)


class YunxiaoSource(DataSource[List[Dict[str, Any]]]):
    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 300.0)
        self._token = config.get("pat", "")
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def fetch(self) -> List[Dict[str, Any]]:
        if not self._token:
            logger.warning("[Yunxiao] token not configured")
            return []

        loop = asyncio.get_event_loop()
        try:
            items = await loop.run_in_executor(self._executor, self._fetch_sync)
            logger.info("[Yunxiao] fetched %d items", len(items))
            return items
        except Exception as e:
            logger.error("[Yunxiao] fetch error: %s", e)
            return []

    def _fetch_sync(self) -> List[Dict[str, Any]]:
        client = McpClient(
            server_cmd=["npx", "-y", "alibabacloud-devops-mcp-server"],
            env={"YUNXIAO_ACCESS_TOKEN": self._token},
        )
        try:
            client.start()
            all_items: List[Dict[str, Any]] = []
            for cat, tids, default_st in CATEGORY_CONFIGS:
                logger.info("[Yunxiao] 查询 %s ...", cat)
                result = self._search(client, cat, tids, default_st)
                items = self._parse_result(result, cat)
                logger.info("[Yunxiao] %s: %d items", cat, len(items))
                all_items.extend(items)
        finally:
            client.stop()
        return all_items

    def _search(self, client: McpClient, category: str, type_ids: list[str], status_ids: list[str]) -> dict:
        args: dict[str, Any] = {
            "organizationId": ORG_ID,
            "category": category,
            "spaceId": PROJECT_ID,
            "workitemType": ",".join(type_ids),
            "status": ",".join(status_ids),
            "orderBy": "gmtCreate",
            "sort": "desc",
            "assignedTo": "self",
            "page": 1,
            "perPage": 50,
        }
        return client.call_tool("search_workitems", args)

    def _parse_result(self, result: dict, category: str) -> List[Dict[str, Any]]:
        content = result.get("content", [])
        if not content:
            return []
        text = content[0].get("text", "{}")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        items = data.get("items", [])
        return [self._format(item, category) for item in items]

    def _format(self, item: dict, category: str) -> Dict[str, Any]:
        status = item.get("status", {}) or {}
        assignee = item.get("assignedTo", {}) or {}
        sn = item.get("serialNumber", "")
        item_id = item.get("id", "")
        url = f"https://devops.aliyun.com/projex/project/{PROJECT_ID}/{category.lower()}/{item_id}"
        return {
            "id": item_id,
            "sn": sn,
            "type": category,
            "title": item.get("subject", ""),
            "status": status.get("displayName") or status.get("name", ""),
            "assignee": assignee.get("name", ""),
            "url": url,
            "created_at": item.get("gmtCreate"),
        }

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
