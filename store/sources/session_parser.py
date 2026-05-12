import json
import time
import os
from typing import Optional
from pathlib import Path
from models.types import AgentSession
from config import cfg

_MAX_RETRY_ATTEMPTS = cfg["session_parser"].get("max_retry_attempts", 3)
_RETRY_INTERVAL_SEC = cfg["session_parser"].get("retry_interval_sec", 0.5)


def parse_session_file(filepath: str) -> Optional[AgentSession]:
    """Load and parse a single session JSON file with retry logic.
    Compatible with both new (model-nested) and old (flat) JSON structures.
    """
    for attempt in range(_MAX_RETRY_ATTEMPTS):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            id_val = data.get("id", "")
            m = data.get("model", {})

            title = m.get("title") or data.get("title", "")
            directory = m.get("directory") or data.get("directory", "")
            status = m.get("status") or data.get("status", "unknown")
            if not status or status == "unknown":
                properties_status = data.get("properties", {}).get("status", {})
                if isinstance(properties_status, dict) and "type" in properties_status:
                    status = properties_status["type"]

            start_time = m.get("startTime") or data.get("startTime", "")
            update_time = m.get("updatedTime") or data.get("updateTime", "")
            error = m.get("error") or data.get("error")
            agent = m.get("agent", "")
            model_id = m.get("modelId", "")

            return AgentSession(
                id=id_val,
                title=title,
                directory=Path(directory).name if directory else "",
                status=status.lower(),
                start_time=start_time,
                update_time=update_time,
                error=error,
                agent=agent,
                model_id=model_id,
            )
        except (PermissionError, FileNotFoundError, json.JSONDecodeError):
            if attempt == _MAX_RETRY_ATTEMPTS - 1:
                return None
            time.sleep(_RETRY_INTERVAL_SEC)
        except Exception:
            return None

    return None
