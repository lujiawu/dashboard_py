#!/usr/bin/env python3
"""HTTP API server that exposes opencode agent session data.

Deploy to remote server alongside the project
Run: python scripts/remote_agent_api.py --port 8765
"""

import json
import os
import sys
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store.sources.session_parser import parse_session_file


SESSIONS_DIR = os.path.expanduser("~/.config/opencode/sessions")


def get_sessions():
    sessions = []
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith(".json"):
            session = parse_session_file(os.path.join(SESSIONS_DIR, filename))
            if session:
                sessions.append({
                    "id": session.id,
                    "title": session.title,
                    "directory": session.directory,
                    "status": session.status,
                    "start_time": session.start_time,
                    "update_time": session.update_time,
                    "error": session.error,
                    "agent": session.agent,
                    "model_id": session.model_id,
                })
    return sessions


class SessionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/sessions":
            data = get_sessions()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Agent session API server")
    parser.add_argument("--port", type=int, default=8765, help="Listen port (default: 8765)")
    parser.add_argument("--bind", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    args = parser.parse_args()

    server = HTTPServer((args.bind, args.port), SessionHandler)
    print(f"[remote_agent_api] serving on {args.bind}:{args.port}")
    print(f"[remote_agent_api] sessions dir: {SESSIONS_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[remote_agent_api] shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
