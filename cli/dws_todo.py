#!/usr/bin/env python3
"""
DWS Todo List CLI - 通过本地 dws CLI 查询和操作待办事项

用法:
    dws-todo-list                        # 未完成待办表格
    dws-todo-list --all                  # 全部待办
    dws-todo-list --json                 # JSON 输出
    dws-todo-list done <task-id>         # 标记完成
    dws-todo-list undo <task-id>         # 恢复未完成
    dws-todo-list create <title>         # 新建待办
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

CONFIG_PATH = Path.home() / ".config" / "dashboard" / "config.json"
_BJ_TZ = timezone(timedelta(hours=8))


# ============================================================================
# 配置加载
# ============================================================================
def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("dws", {}).get("todo", {})
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "executor_id": os.environ.get("DWS_EXECUTOR_ID", "01455548515339212734"),
        "page": int(os.environ.get("DWS_PAGE", "1")),
        "page_size": int(os.environ.get("DWS_PAGE_SIZE", "100")),
        "timeout": int(os.environ.get("DWS_TIMEOUT", "60")),
    }


# ============================================================================
# 数据模型
# ============================================================================
class Todo:
    def __init__(self, task_id: str, subject: str, completed: bool = False,
                 description: str = "", priority: int = 0, due_time: int = 0,
                 created_time: int = 0):
        self.id = task_id
        self.subject = subject
        self.description = description
        self.completed = completed
        self.priority = priority
        self.due_time = due_time
        self.created_time = created_time


# ============================================================================
# dws CLI 调用
# ============================================================================
def run_dws(args: list[str], timeout_sec: int = 60) -> Optional[dict]:
    cmd = ["dws", f"--timeout={timeout_sec}"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 5)
        if result.returncode != 0:
            print(f"dws 错误: {result.stderr.strip()}", file=sys.stderr)
            return None
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("错误: 未找到 'dws' 命令，请确认已安装", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"解析 dws 响应失败: {e}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print("dws 请求超时", file=sys.stderr)
        return None


def fetch_todos(page: int = 1, page_size: int = 100, completed: bool = False, timeout_sec: int = 60) -> List[Todo]:
    status = "true" if completed else "false"
    data = run_dws(["todo", "task", "list",
                     "--page", str(page), "--size", str(page_size),
                     "--status", status, "--format", "json"],
                    timeout_sec=timeout_sec)
    if not data:
        return []

    cards = data.get("result", {}).get("todoCards", [])
    descriptions = {}
    for item in cards:
        task_id = item.get("taskId", "")
        detail = run_dws(["todo", "task", "get", "--task-id", task_id, "--format", "json"],
                         timeout_sec=timeout_sec) if task_id else None
        descriptions[task_id] = (detail or {}).get("result", {}).get("todoDetailModel", {}).get("description", "") or ""
    return [
        Todo(
            task_id=item.get("taskId", ""),
            subject=item.get("subject", ""),
            description=descriptions.get(item.get("taskId", ""), ""),
            completed=(status == "true"),
            priority=item.get("priority", 0),
            due_time=item.get("dueTime") or 0,
            created_time=item.get("createdTime") or 0,
        )
        for item in cards
    ]


def set_done_status(task_id: str, completed: bool, timeout_sec: int = 60) -> bool:
    status = "true" if completed else "false"
    data = run_dws(["todo", "task", "done",
                     "--task-id", task_id, "--status", status, "--format", "json"],
                    timeout_sec=timeout_sec)
    return data is not None


def create_todo(title: str, executor_id: str, timeout_sec: int = 60) -> bool:
    data = run_dws(["todo", "task", "create",
                     "--title", title, "--executors", executor_id,
                     "--format", "json", "-y"],
                    timeout_sec=timeout_sec)
    return data is not None


# ============================================================================
# 格式化
# ============================================================================
def format_due(due_time: int) -> str:
    if not due_time:
        return "--"
    try:
        dt = datetime.fromtimestamp(due_time / 1000, tz=_BJ_TZ)
        return dt.strftime("%m-%d")
    except (ValueError, OSError):
        return "--"


def _priority_rich(p: int) -> Text:
    if p >= 30:
        return Text("!!!", style="bold red")
    if p == 20:
        return Text("!!", style="bold yellow")
    return Text("!", style="dim yellow")


def _priority_plain(p: int) -> str:
    if p >= 30:
        return "!!!"
    if p == 20:
        return "!!"
    return "!"


def format_todo(t: Todo) -> dict:
    return {
        "id": t.id,
        "subject": t.subject,
        "description": t.description,
        "completed": t.completed,
        "priority": t.priority,
        "due_time": t.due_time,
        "due": format_due(t.due_time),
        "created_time": t.created_time,
    }


# ============================================================================
# 输出
# ============================================================================
def print_table(todos: List[Todo]) -> None:
    if not todos:
        print("  (无待办)")
        return

    if _HAS_RICH:
        _print_rich(todos)
    else:
        _print_plain(todos)


def _print_rich(todos: List[Todo]) -> None:
    console = Console()
    console.print(f"\n  [bold]Todo ({len(todos)})[/]")

    table = Table(box=box.SIMPLE, padding=(0, 1))
    table.add_column("Prio", no_wrap=True, width=4)
    table.add_column("Due", no_wrap=True, width=6)
    table.add_column("Subject", no_wrap=False, ratio=1)
    table.add_column("Description", no_wrap=False, ratio=1)

    for t in sorted(todos, key=lambda x: (-x.priority, x.due_time or 2**31)):
        prio = _priority_rich(t.priority)
        due = format_due(t.due_time)
        subject = f"✅ {t.subject}" if t.completed else t.subject
        table.add_row(prio, due, subject, t.description)

    console.print(table)


def _print_plain(todos: List[Todo]) -> None:
    print(f"\n  Todo ({len(todos)})")
    print(f"  {'Prio':<4} {'Due':<6} {'Subject':<60} Description")
    print(f"  {'-'*4} {'-'*6} {'-'*60} {'-'*40}")

    for t in sorted(todos, key=lambda x: (-x.priority, x.due_time or 2**31)):
        prio = _priority_plain(t.priority)
        due = format_due(t.due_time)
        subject = f"✅ {t.subject}" if t.completed else t.subject
        print(f"  {prio:<4} {due:<6} {subject[:60]:<60} {t.description[:60]}")


def print_json(todos: List[Todo]) -> None:
    print(json.dumps({
        "total": len(todos),
        "items": [format_todo(t) for t in todos],
    }, ensure_ascii=False, indent=2))


# ============================================================================
# CLI 入口
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="dws-todo-list",
        description="DWS Todo List - 查询和操作待办事项",
    )
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--all", action="store_true", help="包含已完成")
    parser.add_argument("--page", type=int, default=0, help="页码")
    parser.add_argument("--page-size", type=int, default=0, help="每页条数")

    sub = parser.add_subparsers(dest="action")
    sub.add_parser("done", help="标记完成").add_argument("task_id", help="任务 ID")
    sub.add_parser("undo", help="恢复未完成").add_argument("task_id", help="任务 ID")
    create_parser = sub.add_parser("create", help="新建待办")
    create_parser.add_argument("title", help="待办标题")

    args = parser.parse_args()
    config = load_config()

    page = args.page or config.get("page", 1)
    page_size = args.page_size or config.get("page_size", 100)
    timeout_sec = config.get("timeout", 60)

    if args.action == "done":
        ok = set_done_status(args.task_id, True, timeout_sec=timeout_sec)
        print("✅ 标记完成" if ok else "❌ 标记失败")
        return

    if args.action == "undo":
        ok = set_done_status(args.task_id, False, timeout_sec=timeout_sec)
        print("↩️ 已恢复" if ok else "❌ 操作失败")
        return

    if args.action == "create":
        executor_id = config.get("executor_id", "01455548515339212734")
        ok = create_todo(args.title, executor_id, timeout_sec=timeout_sec)
        print("✅ 已创建" if ok else "❌ 创建失败")
        return

    # 默认: 列出待办
    todos = fetch_todos(page, page_size, completed=False, timeout_sec=timeout_sec)

    if args.all:
        done = fetch_todos(page, page_size, completed=True, timeout_sec=timeout_sec)
        todos.extend(done)

    if args.json:
        print_json(todos)
    elif _HAS_RICH:
        Console().print(f"\n  [bold]Todo List[/] ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print_table(todos)
        Console().print()
    else:
        print(f"\n  Todo List ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print(f"  {'='*40}")
        print_table(todos)
        print()


if __name__ == "__main__":
    main()
