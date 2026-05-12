import asyncio
import json
from typing import List

from store.sources.base import DataSource
from models.types import ChatConversation


class DwsChatSource(DataSource[List[ChatConversation]]):
    def __init__(self, refresh_interval: float = 60.0):
        self._refresh_interval = refresh_interval

    async def fetch(self) -> List[ChatConversation]:
        cmd = ["dws", "chat", "message", "list-unread-conversations", "--format", "json"]

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
            convs = data.get("result", {}).get("conversations", [])
            return [
                ChatConversation(
                    conversation_id=item.get("openConversationId", ""),
                    title=item.get("title", ""),
                    unread_count=item.get("unreadPoint", 0),
                    is_single_chat=item.get("singleChat", False),
                )
                for item in convs
            ]
        except (json.JSONDecodeError, KeyError):
            return []

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
