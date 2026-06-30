#!/usr/bin/env python3
"""
云效任务大盘 CLI - 通过 OpenAPI 查询个人工作项（Bug/Task）

用法:
    .venv/bin/python cli/yunxiao.py          # 推荐（有 rich 表格）
    python3 cli/yunxiao.py                   # 需 rich（pip install rich）
    python3 cli/yunxiao.py --json            # JSON 输出无需 rich
"""

import argparse
import concurrent.futures
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

# ============================================================================
# 常量
# ============================================================================
BUG_ACTIVE_STATUS = [
    "28",        # 待确认
    "100010",    # 处理中
    "53e19cb99ba3b295fd38a3667b",  # 待开发自验
    "30",        # 再次打开
]
TASK_ACTIVE_STATUS = [
    "100005",    # 待处理
    "100010",    # 处理中
]
TYPE_SORT = {"Bug": 0, "Task": 1}
STATUS_SORT_ORDER = [
    "待处理", "待确认",
    "已拒绝", "重新打开",
    "处理中",
    "待测试回归", "待测试", "待测试复现",
    "重复缺陷", "暂不修复",
    "已完成", "已关闭", "无效缺陷",
]

CONFIG_PATH = Path.home() / ".config" / "dashboard" / "config.json"


# ============================================================================
# 配置加载
# ============================================================================
def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            yunxiao = data.get("yunxiao", {})
            if yunxiao.get("pat") and yunxiao.get("org_id"):
                return yunxiao
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "domain": os.environ.get("YUNXIAO_DOMAIN", "openapi-rdc.aliyuncs.com"),
        "org_id": os.environ.get("YUNXIAO_ORG_ID", ""),
        "project_id": os.environ.get("YUNXIAO_PROJECT_ID", ""),
        "pat": os.environ.get("YUNXIAO_TOKEN", ""),
        "user_id": os.environ.get("YUNXIAO_USER_ID", ""),
    }


# ============================================================================
# OpenAPI 查询
# ============================================================================
def search_workitems(
    domain: str, org_id: str, token: str,
    project_id: str, category: str,
    user_id: str = "",
) -> List[dict]:
    url = f"https://{domain}/oapi/v1/projex/organizations/{org_id}/workitems:search"

    status_ids = TASK_ACTIVE_STATUS if category == "Task" else BUG_ACTIVE_STATUS
    filters = [
        {
            "fieldIdentifier": "status",
            "operator": "CONTAINS",
            "value": status_ids,
            "toValue": None,
            "className": "status",
            "format": "multiList",
        },
    ]
    if user_id:
        filters.append({
            "fieldIdentifier": "assignedTo",
            "operator": "CONTAINS",
            "value": [user_id],
            "toValue": None,
            "className": "user",
            "format": "list",
        })

    body = {
        "category": category,
        "conditions": json.dumps({"conditionGroups": [filters]}, ensure_ascii=False),
        "orderBy": "gmtCreate",
        "page": 1,
        "perPage": 50,
        "sort": "desc",
        "spaceId": project_id,
        "spaceType": "Project",
    }

    headers = {"Content-Type": "application/json", "x-yunxiao-token": token}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ============================================================================
# 数据处理
# ============================================================================
def clean_title(title: str) -> str:
    if title and title.startswith("\u3010"):
        last = title.rfind("\u3011")
        if last >= 0 and last < len(title) - 1:
            return title[last + 1:].strip()
    return title


def format_item(item: dict, category: str, project_id: str) -> dict:
    status = item.get("status", {}) or {}
    sn = item.get("serialNumber", "")
    item_id = item.get("id", "")
    status_name = status.get("displayName") or status.get("name", "")
    raw_title = item.get("subject", "")
    created = item.get("gmtCreate", 0)

    if created:
        try:
            dt = datetime.fromtimestamp(int(created) / 1000)
            created_str = dt.strftime("%m-%d %H:%M")
        except (ValueError, OSError):
            created_str = str(created)
    else:
        created_str = ""

    url = (f"https://devops.aliyun.com/projex/project/{project_id}"
           f"/{category.lower()}/{item_id}") if project_id else ""

    return {
        "type": category,
        "sn": sn,
        "title": f"[{status_name}] {clean_title(raw_title)}",
        "status": status_name,
        "assignee": (item.get("assignedTo") or {}).get("name", ""),
        "url": url,
        "created_at": created_str,
    }


def sort_key(item: dict) -> tuple:
    type_priority = TYPE_SORT.get(item["type"], 9)
    status = item["status"]
    if status in STATUS_SORT_ORDER:
        status_priority = STATUS_SORT_ORDER.index(status)
    else:
        status_priority = len(STATUS_SORT_ORDER)
    return (type_priority, status_priority)


# ============================================================================
# 输出
# ============================================================================
def print_table(items: List[dict]) -> None:
    if not items:
        print("  (无数据)")
        return

    groups: Dict[str, List[dict]] = {}
    for item in items:
        groups.setdefault(item["type"], []).append(item)

    if _HAS_RICH:
        _print_table_rich(groups)
    else:
        _print_table_plain(groups)


def _print_table_rich(groups: Dict[str, List[dict]]) -> None:
    console = Console()

    for type_name in ["Bug", "Task"]:
        type_items = groups.get(type_name, [])
        if not type_items:
            continue

        type_style = "bold red" if type_name == "Bug" else "bold blue"
        console.print(f"\n  [{type_style}]{type_name} ({len(type_items)})[/]")

        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("Status", no_wrap=True, width=10)
        table.add_column("Title", no_wrap=False, ratio=1)
        table.add_column("Created", no_wrap=True, width=14)

        for item in type_items:
            title = item["title"]
            status = item["status"]
            created = item["created_at"]
            status_style = _status_style(status)
            table.add_row(f"[{status_style}]{status}[/]", title, created)

        console.print(table)


def _print_table_plain(groups: Dict[str, List[dict]]) -> None:
    for type_name in ["Bug", "Task"]:
        type_items = groups.get(type_name, [])
        if not type_items:
            continue

        print(f"\n  {type_name} ({len(type_items)})")
        print(f"  {'Status':<10} {'Title':<60} {'Created'}")
        print(f"  {'-'*10} {'-'*60} {'-'*16}")

        for item in type_items:
            title = item["title"][:74]
            status = item["status"][:10]
            created = item["created_at"]
            print(f"  {status:<10} {title:<74} {created}")


def _status_style(status: str) -> str:
    styles = {
        "待处理": "yellow",
        "待确认": "yellow",
        "已拒绝": "red",
        "重新打开": "red",
        "处理中": "cyan",
        "待测试回归": "magenta",
        "待测试": "magenta",
        "待测试复现": "magenta",
        "重复缺陷": "white",
        "暂不修复": "white",
        "已完成": "green",
        "已关闭": "green",
        "无效缺陷": "green",
    }
    return styles.get(status, "white")


def print_json(items: List[dict]) -> None:
    print(json.dumps({
        "total": len(items),
        "items": items,
    }, ensure_ascii=False, indent=2))


# ============================================================================
# CLI 入口
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="yunxiao-cli",
        description="云效任务大盘 - 通过 OpenAPI 查询个人工作项",
    )
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--all", action="store_true", help="显示全部（不按人过滤）")
    parser.add_argument("--project", help="只查询指定项目（逗号分隔多个 ID）")
    parser.add_argument("--config", help="指定配置文件路径")
    parser.add_argument("--categories", default="Bug,Task",
                        help="查询类型 (默认: Bug,Task)")
    args = parser.parse_args()

    if args.config:
        try:
            with open(args.config, encoding="utf-8") as f:
                config = json.load(f)
                if "yunxiao" in config:
                    config = config["yunxiao"]
        except (json.JSONDecodeError, OSError) as e:
            print(f"配置加载失败: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        config = load_config()

    domain = config.get("domain", "openapi-rdc.aliyuncs.com")
    org_id = config.get("org_id", "")
    pat = config.get("pat", "")
    user_id = "" if args.all else config.get("user_id", "")
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]

    if args.project:
        project_ids = [p.strip() for p in args.project.split(",") if p.strip()]
    else:
        project_ids = [p.strip() for p in config.get("project_id", "").split(",") if p.strip()]

    if not org_id or not pat:
        print("错误: 请配置 org_id 和 pat (配置文件或环境变量)", file=sys.stderr)
        sys.exit(1)

    if not project_ids:
        print("警告: 未配置项目 ID，将无法查询数据", file=sys.stderr)

    sup_tasks = [(pid, cat) for pid in project_ids for cat in categories]
    all_items: List[dict] = []

    def fetch_one(proj_id: str, category: str) -> List[dict]:
        try:
            raw_items = search_workitems(
                domain, org_id, pat, proj_id, category, user_id
            )
            return [format_item(it, category, proj_id) for it in raw_items]
        except urllib.error.HTTPError as e:
            print(f"  [{proj_id[:8]}...] {category}: HTTP {e.code}",
                  file=sys.stderr)
            return []
        except Exception as e:
            print(f"  [{proj_id[:8]}...] {category}: {e}",
                  file=sys.stderr)
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        fut_map = {executor.submit(fetch_one, pid, cat): (pid, cat)
                   for pid, cat in sup_tasks}
        for fut in concurrent.futures.as_completed(fut_map):
            all_items.extend(fut.result())

    all_items.sort(key=sort_key)

    if args.json:
        print_json(all_items)
    elif _HAS_RICH:
        Console().print(f"\n  [bold]云效任务大盘[/] ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print_table(all_items)
        Console().print()
    else:
        print(f"\n  云效任务大盘 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print(f"  {'='*60}")
        print_table(all_items)
        print()


if __name__ == "__main__":
    main()
