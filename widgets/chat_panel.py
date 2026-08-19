import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, ListItem, ListView, RichLog, Static
from rich.text import Text

from store.dws_client import Conversation, Ding, DwsClient, DwsError, Message, _conversation_order, _message_order, conversation_time, format_ding_blocks, format_message_blocks, merge_pending_messages


DING_CID = "__ding__"


class ConversationItem(ListItem):
    def __init__(self, conversation: Conversation):
        prefix = "● " if conversation.unread else "  "
        if conversation.unread and conversation.unread_count > 0:
            prefix += f"{conversation.unread_count} "
        label = prefix + (conversation.name or conversation.cid)
        if not conversation.unread and conversation.last_message_at:
            label += f"  [dim]{conversation_time(conversation.last_message_at)}[/]"
        super().__init__(Label(label))
        self.conversation = conversation


class GroupHeader(ListItem):
    def __init__(self, title: str):
        super().__init__(Label(f"[dim]— {title} —[/]"), disabled=True)


class ChatPanel(Horizontal):
    ALLOW_MAXIMIZE = True

    def __init__(self, client: DwsClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.conversations: list[Conversation] = []
        self.active: Conversation | None = None
        self.messages_by_cid: dict[str, list[Message]] = {}
        self.pending_messages_by_cid: dict[str, list[Message]] = {}
        self._message_load_lock = asyncio.Lock()
        self.dings: list[Ding] = []
        self.dings_opened = False

    def compose(self):
        yield ListView(id="chat-conversations")
        yield Vertical(
            RichLog(id="chat-messages", wrap=True, markup=True),
            Input(placeholder="Message", id="chat-input"),
            Static("Starting...", id="chat-status"),
            id="chat-conversation-pane",
        )

    async def on_mount(self) -> None:
        await self.refresh_chat()
        self.set_interval(30.0, self.refresh_chat)

    async def refresh_chat(self) -> None:
        if not self.client.available():
            self._status("dws not found in PATH")
            return
        try:
            all_conversations = await self.client.conversations()
            self.conversations = all_conversations
            self.dings = await self.client.unread_dings()
            self.dings_opened = False
            self.conversations.sort(key=lambda item: (not item.unread, -_conversation_order(item).timestamp()))
            await self._render_conversations()
            if self.active and self.active.cid != DING_CID:
                await self._load_messages(self.active)
            unread_count = sum(1 for item in self.conversations if item.unread)
            self.border_title = f"CHAT · {unread_count} unread" if unread_count else "CHAT"
            self._status(f"Unread conversations: {unread_count}")
        except DwsError as error:
            self._status(f"Refresh failed: {error}")

    async def _render_conversations(self) -> None:
        view = self.query_one("#chat-conversations", ListView)
        view.query("ListItem").remove()
        items: list[ListItem] = [GroupHeader("DING")]
        ding = Conversation(DING_CID, "DING", bool(self.dings) and not self.dings_opened, len(self.dings))
        items.append(ConversationItem(ding))
        unread_items = [item for item in self.conversations if item.unread]
        read_items = [item for item in self.conversations if not item.unread][:10]
        if unread_items:
            items.append(GroupHeader("未读"))
            items.extend(ConversationItem(item) for item in unread_items)
        if read_items:
            items.append(GroupHeader("已读"))
            items.extend(ConversationItem(item) for item in read_items)
        await view.mount(*items)

    async def _load_dings(self) -> None:
        try:
            dings = await self.client.unread_dings()
            if not self.active or self.active.cid != DING_CID:
                return
            self.dings = dings
            self.dings_opened = True
            log = self.query_one("#chat-messages", RichLog)
            log.clear()
            for i, block in enumerate(format_ding_blocks(dings)):
                if i:
                    log.write(Text("─" * 24, style="dim"))
                log.write(block)
            log.scroll_end(animate=False)
            await self._render_conversations()
        except DwsError as error:
            self._status(f"DING failed: {error}")

    async def _load_messages(self, conversation: Conversation, mark_read: bool = False) -> None:
        async with self._message_load_lock:
            try:
                for attempt in range(3):
                    messages = await self.client.messages(conversation.cid, 50)
                    pending = self.pending_messages_by_cid.get(conversation.cid, [])
                    messages = merge_pending_messages(messages, pending)
                    self.pending_messages_by_cid[conversation.cid] = [item for item in pending if item in messages and item.message_id.startswith("local:")]
                    self.messages_by_cid[conversation.cid] = messages
                    if self.active and self.active.cid == conversation.cid:
                        self._render_messages(messages)
                    if not self.pending_messages_by_cid[conversation.cid] or attempt == 2:
                        break
                    await asyncio.sleep(0.5)
                if not self.active or self.active.cid != conversation.cid:
                    return
                messages = self.messages_by_cid[conversation.cid]
                message_id = next((item.message_id for item in sorted(messages, key=_message_order, reverse=True) if item.message_id), "")
                if mark_read and message_id:
                    try:
                        await self.client.mark_read(conversation.cid, message_id)
                    except DwsError:
                        return
                    if not self.active or self.active.cid != conversation.cid:
                        return
                    self.conversations = [replace(item, unread=False, unread_count=0) if item.cid == conversation.cid else item for item in self.conversations]
                    await self._render_conversations()
            except DwsError as error:
                self._status(f"Conversation failed: {error}")

    def _render_messages(self, messages: list[Message]) -> None:
        log = self.query_one("#chat-messages", RichLog)
        log.clear()
        for block in format_message_blocks(messages, self.client.self_id):
            log.write(block)
        log.scroll_end(animate=False)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        conversation = getattr(event.item, "conversation", None)
        if conversation is None:
            return
        self.active = conversation
        input = self.query_one("#chat-input", Input)
        input.disabled = self.active.cid == DING_CID
        if self.active.cid == DING_CID:
            await self._load_dings()
            return
        await self._load_messages(self.active, mark_read=True)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self.active or self.active.cid == DING_CID or not event.value.strip():
            return
        text = event.value
        event.input.disabled = True
        try:
            await self.client.send(self.active.cid, text)
            event.input.value = ""
            pending = Message(f"local:{uuid4().hex}", "我", self.client.self_id, text, datetime.now(timezone.utc).isoformat())
            self.pending_messages_by_cid.setdefault(self.active.cid, []).append(pending)
            self.messages_by_cid.setdefault(self.active.cid, []).append(pending)
            self._render_messages(self.messages_by_cid[self.active.cid])
            await self._load_messages(self.active)
            self._status("Sent")
        except DwsError as error:
            self._status(f"Send failed: {error}")
        finally:
            event.input.disabled = False

    def _status(self, text: str) -> None:
        if self.is_mounted:
            self.query_one("#chat-status", Static).update(text)
