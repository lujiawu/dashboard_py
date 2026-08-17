import asyncio
import unittest
from unittest.mock import AsyncMock

from store.dws_client import DwsClient, Message, conversation_time, format_message_blocks, merge_pending_messages, parse_conversations, parse_dings, parse_messages


class DwsClientTest(unittest.TestCase):
    def test_parses_nested_payloads(self):
        conversations = parse_conversations({"result": {"conversations": [{"openConversationId": "c1", "title": "Team", "unreadPoint": 3, "lastMsgCreateAt": "2026-08-13T12:34:00+08:00"}]}})
        messages = parse_messages({"messages": [{"messageId": "m1", "sender": "A", "senderId": "u1", "text": "Hi", "createTime": "2026-08-13T12:34:00Z"}]})
        self.assertEqual(conversations[0].name, "Team")
        self.assertTrue(conversations[0].unread)
        self.assertEqual(conversations[0].unread_count, 3)
        self.assertIn("12:34", conversations[0].last_message_at)
        self.assertEqual(messages[0].message_id, "m1")

    def test_conversation_time_formats(self):
        self.assertEqual(conversation_time(""), "")
        self.assertEqual(conversation_time("not-a-time"), "")

    def test_formats_messages_in_time_order(self):
        messages = parse_messages({"messages": [
            {"messageId": "2", "sender": "B", "senderId": "u2", "text": "Later", "createTime": "2026-08-13T12:35:00Z"},
            {"messageId": "1", "sender": "A", "senderId": "u1", "text": "Earlier", "createTime": "2026-08-13T12:34:00Z"},
        ]})
        blocks = format_message_blocks(messages, "u1")
        self.assertIn("Earlier", blocks[0])
        self.assertIn("Later", blocks[1])

    def test_merges_recent_server_message_with_pending_message(self):
        pending = Message("local:1", "A", "u1", "Hi", "2026-08-13T12:34:00Z")
        server = Message("m1", "A", "u1", "Hi", "2026-08-13T12:34:02Z")
        self.assertEqual(merge_pending_messages([server], [pending]), [server])

    def test_marks_a_conversation_read(self):
        client = DwsClient()
        client._run = AsyncMock()
        asyncio.run(client.mark_read("c1", "m1"))
        client._run.assert_awaited_once_with("chat", "+conversation-mark-read", "--conversation-id", "c1", "--message-id", "m1", write=True)

    def test_parses_and_loads_unread_dings(self):
        dings = parse_dings({"result": {"dingMessages": [{"dingContent": "Reminder", "senderNick": "A", "sendTime": "2026-08-13 12:34:00"}]}})
        self.assertEqual(dings[0].content, "Reminder")
        client = DwsClient()
        client._run = AsyncMock(return_value={"result": {"dingMessages": []}})
        asyncio.run(client.unread_dings())
        client._run.assert_awaited_once_with("ding", "+list", "--type", "UNREAD", "--cursor", "0")


if __name__ == "__main__":
    unittest.main()
