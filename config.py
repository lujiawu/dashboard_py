import json
import copy
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "dashboard"
CONFIG_FILE = CONFIG_DIR / "config.json"

_DEFAULTS = {
    "dws": {
        "todo": {
            "executor_id": "01455548515339212734",
            "page": 1,
            "page_size": 100,
            "timeout": 60,
            "refresh_interval": 60.0,
        },
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
        "domain": "openapi-rdc.aliyuncs.com",
        "org_id": "",
        "project_id": "",
        "pat": "",
        "user_id": "",
        "categories": ["Task", "Bug"],
        "refresh_interval": 300.0,
        "max_concurrency": 4,
    },
    "git": {
        "repos": [],
        "refresh_interval": 30.0,
        "fetch": True,
    },
    "mihomo": {
        "api_url": "http://127.0.0.1:9090",
        "router": "192.168.1.1",
        "route_start": "白嫖机场",
        "iface": "",
        "traffic_interval": 2.0,
        "status_interval": 30.0,
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
