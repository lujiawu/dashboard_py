import asyncio
import json
import urllib.request
from typing import List

from store.sources.base import DataSource
from models.types import AgentSession


class HttpSessionDataSource(DataSource[List[AgentSession]]):
    """Fetch agent sessions from a remote HTTP API endpoint."""

    def __init__(self, config: dict):
        self.api_url = config["api_url"]
        self.host_label = config.get("host_label", "remote")
        self._refresh_interval = config.get("refresh_interval", 2.0)
        self._timeout = config.get("timeout", 5)

    async def fetch(self) -> List[AgentSession]:
        def _get():
            with urllib.request.urlopen(self.api_url, timeout=self._timeout) as resp:
                return json.loads(resp.read())

        data = await asyncio.to_thread(_get)
        sessions = []
        for item in data:
            model = item.get("model", {})
            sessions.append(AgentSession(
                id=item.get("id", ""),
                title=model.get("title", ""),
                directory=model.get("directory", ""),
                status=model.get("status", "unknown"),
                start_time=model.get("startTime", ""),
                update_time=model.get("updatedTime", ""),
                error=model.get("error"),
                agent=model.get("agent", ""),
                model_id=model.get("modelId", ""),
                host=self.host_label,
            ))
        return sessions

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
