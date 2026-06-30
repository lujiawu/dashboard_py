import asyncio
import json
import logging
import urllib.request
from typing import Any, Dict, List

from store.sources.base import DataSource

logger = logging.getLogger(__name__)

BUG_ACTIVE_STATUS = [
    "28",        # 待确认
    "100010",    # 处理中
    "53e19cb99ba3b295fd38a3667b",  # 待开发自验
    "30",        # 再次打开
]
TASK_ACTIVE_STATUS = [
    "100005",    # 待处理
    "100010",    # 处理中
]
TYPE_SORT = {"Bug": 0, "Task": 1}
STATUS_SORT_ORDER = [
    "待处理", "待确认",
    "已拒绝", "重新打开",
    "处理中",
    "待测试回归", "待测试", "待测试复现",
    "重复缺陷", "暂不修复",
    "已完成", "已关闭", "无效缺陷",
]


class YunxiaoSource(DataSource[List[Dict[str, Any]]]):
    def __init__(self, config: dict):
        self._domain = config.get("domain", "openapi-rdc.aliyuncs.com")
        self._org_id = config.get("org_id", "")
        self._project_ids = [p.strip() for p in config.get("project_id", "").split(",") if p.strip()]
        self._token = config.get("pat", "")
        self._user_id = config.get("user_id", "")
        self._categories = config.get("categories", ["Bug", "Task"])
        self._refresh_interval = config.get("refresh_interval", 300.0)
        self._max_concurrency = max(1, int(config.get("max_concurrency", 4)))
        self._cached: List[Dict[str, Any]] = []

    async def fetch(self) -> List[Dict[str, Any]]:
        if not self._token:
            logger.warning("[Yunxiao] token not configured")
            return []

        jobs = [(proj_id, category) for proj_id in self._project_ids for category in self._categories]
        if not jobs:
            return []

        sem = asyncio.Semaphore(self._max_concurrency)

        async def _run(proj_id: str, category: str) -> List[Dict[str, Any]] | None:
            async with sem:
                try:
                    items = await self._search_project(proj_id, category)
                    logger.info("[Yunxiao] %s %s: %d items", proj_id, category, len(items))
                    return items
                except Exception as e:
                    logger.error("[Yunxiao] search error: proj=%s cat=%s err=%s", proj_id, category, e)
                    return None

        results = await asyncio.gather(*(_run(proj_id, category) for proj_id, category in jobs))
        successful = [items for items in results if items is not None]
        if not successful:
            return self._cached

        all_items = [item for items in successful for item in items]
        all_items.sort(key=self._sort_key)
        self._cached = all_items
        return all_items

    def _build_conditions(self, category: str = "") -> str:
        status_ids = TASK_ACTIVE_STATUS if category == "Task" else BUG_ACTIVE_STATUS
        filters = [
            {
                "fieldIdentifier": "status",
                "operator": "CONTAINS",
                "value": status_ids,
                "toValue": None,
                "className": "status",
                "format": "multiList",
            },
        ]
        if self._user_id:
            filters.append({
                "fieldIdentifier": "assignedTo",
                "operator": "CONTAINS",
                "value": [self._user_id],
                "toValue": None,
                "className": "user",
                "format": "list",
            })
        return json.dumps({"conditionGroups": [filters]}, ensure_ascii=False)

    async def _search_project(self, project_id: str, category: str) -> List[Dict[str, Any]]:
        url = f"https://{self._domain}/oapi/v1/projex/organizations/{self._org_id}/workitems:search"
        body = {
            "category": category,
            "conditions": self._build_conditions(category),
            "orderBy": "gmtCreate",
            "page": 1,
            "perPage": 50,
            "sort": "desc",
            "spaceId": project_id,
            "spaceType": "Project",
        }
        headers = {
            "Content-Type": "application/json",
            "x-yunxiao-token": self._token,
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        def _post():
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                total = resp.headers.get("x-total", "0")
                logger.info("[Yunxiao] project search %s %s: x-total=%s", project_id, category, total)
                return resp.read()

        raw = await asyncio.to_thread(_post)
        items = json.loads(raw)
        return [self._format(item, category, project_id) for item in items]

    @staticmethod
    def _clean_title(title: str) -> str:
        if title and title.startswith("\u3010"):
            last = title.rfind("\u3011")
            if last >= 0 and last < len(title) - 1:
                return title[last + 1:].strip()
        return title

    @staticmethod
    def _sort_key(item: dict) -> tuple:
        type_priority = TYPE_SORT.get(item["type"], 9)
        status = item["status"]
        if status in STATUS_SORT_ORDER:
            status_priority = STATUS_SORT_ORDER.index(status)
        else:
            status_priority = len(STATUS_SORT_ORDER)
        return (type_priority, status_priority)

    def _format(self, item: dict, category: str = "", project_id: str = "") -> Dict[str, Any]:
        status = item.get("status", {}) or {}
        sn = item.get("serialNumber", "")
        item_id = item.get("id", "")
        if not project_id:
            project_id = (item.get("space", {}) or {}).get("identifier", "")
        if not category:
            category = item.get("workitemType", {}).get("categoryIdentifier", "")
        url = f"https://devops.aliyun.com/projex/project/{project_id}/{category.lower()}/{item_id}" if project_id else ""
        status_name = status.get("displayName") or status.get("name", "")
        raw_title = item.get("subject", "")
        return {
            "id": item_id,
            "sn": sn,
            "type": category,
            "title": f"[{status_name}] {self._clean_title(raw_title)}",
            "status": status_name,
            "assignee": (item.get("assignedTo") or {}).get("name", ""),
            "url": url,
            "created_at": item.get("gmtCreate"),
        }

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
