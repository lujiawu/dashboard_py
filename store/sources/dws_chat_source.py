import asyncio
import json
import logging
from typing import List

from store.sources.base import DataSource
from models.types import ChatConversation

logger = logging.getLogger(__name__)


class DwsChatSource(DataSource[List[ChatConversation]]):
    def __init__(self, config: dict):
        self._refresh_interval = config.get("refresh_interval", 60.0)

    async def fetch(self) -> List[ChatConversation]:
        cmd = ["dws", "chat", "message", "list-unread-conversations", "--format", "json"]
        logger.info("[DwsChat] running: %s", " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning("[DwsChat] rc=%d stderr=%s", proc.returncode, stderr.decode(errors="replace").strip()[:200])
            return []

        try:
            data = json.loads(stdout.decode())
            convs = data.get("result", {}).get("conversations", [])
            conversations = [
                ChatConversation(
                    conversation_id=item.get("openConversationId", ""),
                    title=item.get("title", ""),
                    unread_count=item.get("unreadPoint", 0),
                    is_single_chat=item.get("singleChat", False),
                )
                for item in convs
            ]
            logger.info("[DwsChat] got %d conversations (unread: %d)",
                len(conversations), sum(c.unread_count for c in conversations))
            return conversations
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("[DwsChat] parse failed: %s, raw=%s", e, stdout.decode(errors="replace").strip()[:200])
            return []

    @property
    def refresh_interval(self) -> float:
        return self._refresh_interval
