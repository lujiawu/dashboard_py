import asyncio
import json
import urllib.request
from typing import List

from store.sources.base import DataSource
from models.types import AgentSession


class HttpSessionDataSource(DataSource[List[AgentSession]]):
    """Fetch agent sessions from a remote HTTP API endpoint."""

    def __init__(self, api_url: str, host_label: str = "remote"):
        self.api_url = api_url
        self.host_label = host_label
        self._refresh_interval = 2.0

    async def fetch(self) -> List[AgentSession]:
        def _get():
            with urllib.request.urlopen(self.api_url, timeout=5) as resp:
                return json.loads(resp.read())

        data = await asyncio.to_thread(_get)
        sessions = []
        for item in data:
            sessions.append(AgentSession(
                id=item.get("id", ""),
                title=item.get("title", ""),
                directory=item.get("directory", ""),
                status=item.get("status", "unknown"),
                start_time=item.get("start_time", ""),
                update_time=item.get("update_time", ""),
                error=item.get("error"),
                agent=item.get("agent", ""),
                model_id=item.get("model_id", ""),
                host=self.host_label,
            ))
        return sessions

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
