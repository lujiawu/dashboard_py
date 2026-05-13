import asyncio
import json
import logging
import platform
from concurrent.futures import ThreadPoolExecutor
from typing import List

from store.sources.base import DataSource
from models.types import YunxiaoItem

logger = logging.getLogger(__name__)

class YunxiaoSource(DataSource[List[YunxiaoItem]]):

    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 300.0)
        self._token = config.get("pat", "")
        self._org_id = config.get("org_id", "")
        project_ids = config.get("project_id", "")
        if isinstance(project_ids, str):
            self._project_ids = [p.strip() for p in project_ids.split(",") if p.strip()]
        else:
            self._project_ids = project_ids or []
        self._categories = config.get("categories", ["Task", "Bug"])
        self._npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def fetch(self) -> List[YunxiaoItem]:
        if not self._token or not self._org_id:
            logger.warning("[Yunxiao] token or org_id not configured")
            return []

        logger.info("[Yunxiao] fetching projects=%s categories=%s",
            self._project_ids or "ALL", self._categories)
        loop = asyncio.get_event_loop()
        try:
            items = await loop.run_in_executor(self._executor, self._fetch_sync)
            logger.info("[Yunxiao] got %d items", len(items))
            return items
        except Exception as e:
            logger.error("[Yunxiao] fetch error: %s", e)
            return []

    def _fetch_sync(self) -> List[YunxiaoItem]:
        import asyncio as _asyncio
        
        items = []
        
        async def _do_fetch():
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
            
            server_params = StdioServerParameters(
                command=self._npx_cmd,
                args=["-y", "alibabacloud-devops-mcp-server"],
                env={"YUNXIAO_ACCESS_TOKEN": self._token}
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    if not self._project_ids:
                        self._project_ids = await self._fetch_all_projects_sync(session)
                        logger.info("[Yunxiao] resolved %d projects", len(self._project_ids))
                    
                    for space_id in self._project_ids:
                        for category in self._categories:
                            try:
                                logger.debug("[Yunxiao] querying space=%s category=%s", space_id, category)
                                result = await session.call_tool("search_workitems", {
                                    "organizationId": self._org_id,
                                    "spaceId": space_id,
                                    "category": category,
                                    "page": 1,
                                    "perPage": 50,
                                    "includeDetails": True
                                })
                                data = json.loads(result.content[0].text)
                                work_items = data.get("items", [])
                                logger.info("[Yunxiao] space=%s category=%s: %d items",
                                    space_id, category, len(work_items))
                                for wi in work_items:
                                    item = self._parse_work_item(wi, category)
                                    if item:
                                        items.append(item)
                            except Exception as e:
                                logger.error(f"[Yunxiao] search error {space_id}/{category}: {e}")
        
        # 在新的事件循环中运行
        try:
            _asyncio.run(_do_fetch())
        except Exception as e:
            logger.error(f"[Yunxiao] sync fetch error: {e}")
        
        return items

    async def _fetch_all_projects_sync(self, session) -> List[str]:
        try:
            result = await session.call_tool("search_projects", {
                "organizationId": self._org_id,
                "page": 1,
                "perPage": 100
            })
            data = json.loads(result.content[0].text)
            projects = data if isinstance(data, list) else data.get("projects", [])
            return [p.get("id", "") for p in projects if p.get("id")]
        except Exception as e:
            logger.error(f"[Yunxiao] fetch projects error: {e}")
            return []

    def _parse_work_item(self, wi: dict, category: str) -> YunxiaoItem | None:
        try:
            status = wi.get("status", {})
            status_name = status.get("displayName", status.get("name", "")) if isinstance(status, dict) else status

            assigned = wi.get("assignedTo", {})
            assignee = assigned.get("name", "") if assigned else ""

            priority = ""
            due_time = 0
            custom_fields = wi.get("customFieldValues", [])
            for field in custom_fields:
                field_id = field.get("fieldId", "")
                if field_id == "priority":
                    vals = field.get("values", [])
                    if vals:
                        priority = vals[0].get("displayValue", "")
                elif field_id == "80":
                    vals = field.get("values", [])
                    if vals:
                        date_str = vals[0].get("identifier", "")
                        if date_str:
                            try:
                                from datetime import datetime, timezone, timedelta
                                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                                dt = dt.replace(tzinfo=timezone(timedelta(hours=8)))
                                due_time = int(dt.timestamp() * 1000)
                            except ValueError:
                                pass

            space = wi.get("space", {})
            project = space.get("name", "") if isinstance(space, dict) else ""

            return YunxiaoItem(
                id=wi.get("id", ""),
                title=wi.get("subject", ""),
                type=category,
                status=status_name,
                priority=priority,
                assignee=assignee,
                due_time=due_time,
                project=project,
            )
        except Exception as e:
            logger.error(f"[Yunxiao] parse error: {e}")
            return None

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
