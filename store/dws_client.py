from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
import shutil

from rich.markup import escape


class DwsError(RuntimeError):
    pass


@dataclass(frozen=True)
class Conversation:
    cid: str
    name: str
    unread: bool = True
    unread_count: int = 0
    last_message_at: str = ""


@dataclass(frozen=True)
class Message:
    message_id: str
    sender: str
    sender_id: str
    text: str
    create_time: str


@dataclass(frozen=True)
class Ding:
    content: str
    sender: str
    create_time: str


def _result(data: dict) -> dict:
    result = data.get("result", data)
    return result if isinstance(result, dict) else {}


def parse_conversations(data: dict) -> list[Conversation]:
    items = _result(data).get("conversations", [])
    result = []
    for item in items:
        unread_count = item.get("unreadPoint", 0)
        result.append(Conversation(item.get("conversationId", item.get("openConversationId", "")), item.get("name", item.get("title", "")), unread_count > 0, unread_count, item.get("lastMsgCreateAt", "")))
    return result


def parse_messages(data: dict) -> list[Message]:
    items = _result(data).get("messages", [])
    return [Message(item.get("messageId", ""), item.get("sender", ""), item.get("senderId", ""), item.get("text", ""), item.get("createTime", "")) for item in items]


def parse_dings(data: dict) -> list[Ding]:
    items = _result(data).get("dingMessages", [])
    return [Ding(item.get("dingContent", ""), item.get("senderNick", ""), item.get("sendTime", "")) for item in items]


def message_time(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M")
    except (TypeError, ValueError):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        except (TypeError, ValueError):
            return value


def format_message_blocks(messages: list[Message], self_id: str) -> list[str]:
    blocks = []
    for message in sorted(messages, key=_message_order):
        metadata = f"[dim]{escape(message_time(message.create_time))}[/]  "
        metadata += f"[green]{escape(message.sender)}[/]" if message.sender_id == self_id else escape(message.sender)
        blocks.append(f"{metadata}\n{escape(message.text or '')}\n")
    return blocks


def format_ding_blocks(dings: list[Ding]) -> list[str]:
    return [f"[dim]{escape(message_time(ding.create_time))}[/]  {escape(ding.sender)}\n{escape(ding.content)}\n" for ding in dings]


def _conversation_datetime(value: str) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        try:
            return datetime.fromtimestamp(int(value) / 1000)
        except (TypeError, ValueError, OverflowError):
            return datetime.min


def _conversation_order(conversation: Conversation) -> datetime:
    return _conversation_datetime(conversation.last_message_at)


def conversation_time(value: str) -> str:
    dt = _conversation_datetime(value)
    if dt is datetime.min:
        return ""
    today = datetime.now().astimezone().date()
    if dt.date() == today:
        return dt.strftime("%H:%M")
    if (today - dt.date()).days == 1:
        return "昨天"
    return dt.strftime("%m-%d")


def _message_order(message: Message) -> datetime:
    try:
        return datetime.fromisoformat(message.create_time.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        try:
            return datetime.strptime(message.create_time, "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            return datetime.min


class DwsClient:
    def __init__(self, yes: bool = True):
        self.yes = yes
        self.self_id = ""

    @staticmethod
    def available() -> bool:
        return shutil.which("dws") is not None

    async def _run(self, *args: str, write: bool = False) -> dict:
        command = ["dws", *args, "--format", "json"]
        if write and self.yes:
            command.append("--yes")
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode:
            raise DwsError(stderr.decode(errors="replace").strip() or f"dws exited with {process.returncode}")
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as error:
            raise DwsError(f"invalid dws JSON: {error}") from error

    async def conversations(self) -> list[Conversation]:
        return parse_conversations(await self._run("chat", "list-all-conversations", "--limit", "100", "--cursor", "0"))

    async def unread_dings(self) -> list[Ding]:
        return parse_dings(await self._run("ding", "+list", "--type", "UNREAD", "--cursor", "0"))

    async def messages(self, cid: str, limit: int) -> list[Message]:
        return parse_messages(await self._run("chat", "+chat-messages", "--group", cid, "--direction", "older", "--limit", str(limit)))

    async def send(self, cid: str, text: str) -> None:
        await self._run("chat", "+messages-send", "--as", "user", "--chat-id", cid, "--text", text, write=True)

    async def mark_read(self, cid: str, message_id: str) -> None:
        await self._run("chat", "+conversation-mark-read", "--conversation-id", cid, "--message-id", message_id, write=True)

    async def load_self(self) -> str:
        data = await self._run("contact", "get-self")
        result = data.get("result", data)
        if isinstance(result, list):
            result = result[0] if result else {}
        employee = result.get("orgEmployeeModel", result)
        self.self_id = employee.get("openDingTalkId", "")
        return self.self_id
