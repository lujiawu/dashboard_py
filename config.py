import json
import copy
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "dashboard"
CONFIG_FILE = CONFIG_DIR / "config.json"

_DEFAULTS = {
    "remote": {
        "api_url": "http://192.168.1.165:8000/",
        "host_label": "remote",
        "timeout": 5,
        "refresh_interval": 2.0,
    },
    "sessions": {
        "directory": "~/.config/opencode/sessions",
        "refresh_interval": 30.0,
    },
    "dws": {
        "todo": {
            "executor_id": "01455548515339212734",
            "page": 1,
            "page_size": 100,
            "refresh_interval": 60.0,
        },
        "chat": {
            "refresh_interval": 60.0,
        },
        "calendar": {
            "refresh_interval": 300.0,
        },
    },
    "goals": {
        "api_url": "http://192.168.1.165:8000/goals",
        "refresh_interval": 86400.0,
    },
    "system": {
        "disk_path": "/",
        "top_processes_limit": 5,
        "refresh_interval": 2.0,
    },
    "app": {
        "log_file": "dashboard.log",
    },
    "yunxiao": {
        "org_id": "",
        "project_id": "",
        "pat": "",
        "refresh_interval": 300.0,
    },
    "git": {
        "repos": [],
        "refresh_interval": 30.0,
        "fetch": True,
    },
    "snippet_file": "~/.config/dashboard/snippets.md",
    "session_parser": {
        "max_retry_attempts": 3,
        "retry_interval_sec": 0.5,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def _generate_config_file():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(_DEFAULTS, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        _generate_config_file()
        return copy.deepcopy(_DEFAULTS)

    try:
        loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        loaded = {}

    merged = copy.deepcopy(_DEFAULTS)
    _deep_merge(merged, loaded)
    return merged


cfg = load_config()
