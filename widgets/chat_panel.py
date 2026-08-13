import asyncio

from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, ListItem, ListView, RichLog, Static

from store.dws_client import Conversation, DwsClient, DwsError, Message, format_message_blocks


class ConversationItem(ListItem):
    def __init__(self, conversation: Conversation):
        super().__init__(Label(("● " if conversation.unread else "  ") + (conversation.name or conversation.cid)))
        self.conversation = conversation


class ChatPanel(Horizontal):
    ALLOW_MAXIMIZE = True

    def __init__(self, client: DwsClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.conversations: list[Conversation] = []
        self.active: Conversation | None = None
        self.messages_by_cid: dict[str, list[Message]] = {}
        self._order: dict[str, int] = {}

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
            unread = await self.client.unread_conversations()
            unread_ids = {item.cid for item in unread}
            known = {item.cid: item for item in self.conversations}
            known.update({item.cid: item for item in unread})
            for item in unread:
                self._order.setdefault(item.cid, len(self._order))
            self.conversations = [Conversation(item.cid, item.name, item.cid in unread_ids) for item in known.values()]
            self.conversations.sort(key=lambda item: (not item.unread, self._order[item.cid]))
            await self._render_conversations()
            if self.active:
                await self._load_messages(self.active)
            self._status(f"Unread conversations: {len(unread)}")
        except DwsError as error:
            self._status(f"Refresh failed: {error}")

    async def _render_conversations(self) -> None:
        view = self.query_one("#chat-conversations", ListView)
        view.query("ListItem").remove()
        await view.mount(*[ConversationItem(item) for item in self.conversations])

    async def _load_messages(self, conversation: Conversation) -> None:
        try:
            messages = await self.client.messages(conversation.cid, 50)
            self.messages_by_cid[conversation.cid] = messages
            log = self.query_one("#chat-messages", RichLog)
            log.clear()
            for block in format_message_blocks(messages, self.client.self_id):
                log.write(block)
            log.scroll_end(animate=False)
        except DwsError as error:
            self._status(f"Conversation failed: {error}")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.active = event.item.conversation
        await self._load_messages(self.active)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if not self.active or not event.value.strip():
            return
        text = event.value
        event.input.disabled = True
        try:
            await self.client.send(self.active.cid, text)
            event.input.value = ""
            await self._load_messages(self.active)
            self._status("Sent")
        except DwsError as error:
            self._status(f"Send failed: {error}")
        finally:
            event.input.disabled = False

    def _status(self, text: str) -> None:
        if self.is_mounted:
            self.query_one("#chat-status", Static).update(text)
