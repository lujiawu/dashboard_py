import json
import tempfile
import unittest
from pathlib import Path

from store.sources.session_parser import parse_session_file


class SessionParserTest(unittest.TestCase):
    def test_parses_agent_status_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "agent-status.json"
            path.write_text(json.dumps([{
                "session_id": "ses_123",
                "status": "working",
                "cwd": "/tmp/project",
                "workspace": "project",
                "title": "Implement dashboard",
            }]), encoding="utf-8")

            sessions = parse_session_file(str(path))

        self.assertIsNotNone(sessions)
        self.assertEqual(1, len(sessions))
        self.assertEqual("ses_123", sessions[0].id)
        self.assertEqual("working", sessions[0].status)
        self.assertEqual("project", sessions[0].directory)
