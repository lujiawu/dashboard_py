import json
import time
from typing import Optional
from pathlib import Path
from models.types import AgentSession
from config import cfg

_MAX_RETRY_ATTEMPTS = cfg["session_parser"].get("max_retry_attempts", 3)
_RETRY_INTERVAL_SEC = cfg["session_parser"].get("retry_interval_sec", 0.5)


def parse_session_file(filepath: str) -> Optional[list[AgentSession]]:
    """Load agent-status.json with retry logic."""
    for attempt in range(_MAX_RETRY_ATTEMPTS):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                return None
            return [
                AgentSession(
                    id=item.get("session_id", ""),
                    title=item.get("title", ""),
                    directory=item.get("workspace") or Path(item.get("cwd", "")).name,
                    status=item.get("status", "unknown").lower(),
                )
                for item in data
                if isinstance(item, dict)
            ]
        except (PermissionError, FileNotFoundError, json.JSONDecodeError):
            if attempt == _MAX_RETRY_ATTEMPTS - 1:
                return None
            time.sleep(_RETRY_INTERVAL_SEC)
        except Exception:
            return None

    return None
