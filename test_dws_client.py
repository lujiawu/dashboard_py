import unittest

from store.dws_client import format_message_blocks, parse_conversations, parse_messages


class DwsClientTest(unittest.TestCase):
    def test_parses_nested_payloads(self):
        conversations = parse_conversations({"result": {"conversations": [{"conversationId": "c1", "name": "Team"}]}})
        messages = parse_messages({"messages": [{"messageId": "m1", "sender": "A", "senderId": "u1", "text": "Hi", "createTime": "2026-08-13T12:34:00Z"}]})
        self.assertEqual(conversations[0].name, "Team")
        self.assertEqual(messages[0].message_id, "m1")

    def test_formats_messages_in_time_order(self):
        messages = parse_messages({"messages": [
            {"messageId": "2", "sender": "B", "senderId": "u2", "text": "Later", "createTime": "2026-08-13T12:35:00Z"},
            {"messageId": "1", "sender": "A", "senderId": "u1", "text": "Earlier", "createTime": "2026-08-13T12:34:00Z"},
        ]})
        blocks = format_message_blocks(messages, "u1")
        self.assertIn("Earlier", blocks[0])
        self.assertIn("Later", blocks[1])


if __name__ == "__main__":
    unittest.main()
