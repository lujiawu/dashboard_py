#!/usr/bin/env python3
"""云效 CLI - 通过 MCP Server 查询项目工作项（Bug/Task/Req）"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any, Optional

# ============================================================================
# 项目配置 (硬编码，与知识库同步)
# ============================================================================
ORG_ID = "681f24490bd1e62a78d91516"
PROJECT_ID = "c121cbdbe805eb951e4c8cd254"
USER_ID = "6923c55679784350ecb2344f"

# ============================================================================
# 类型 ID 映射
# ============================================================================
BUG_TYPES = [
    "37da3a07df4d08aef2e3b393",  # 缺陷
    "17d33cb4ff7f985dc097626969",  # 现场问题
]
TASK_TYPES = [
    "ba102e46bc6a8483d9b7f25c",  # 任务
]
REQ_TYPES = [
    "9uy29901re573f561d69jn40",  # 产品类需求
    "bca48ee2a0976d38f4802fae",  # 技术类需求
]

# ============================================================================
# 状态映射: 中文名 → ID
# ============================================================================
STATUS_MAP: dict[str, list[str]] = {
    "待确认": ["28"],
    "处理中": ["100010"],
    "待开发自验": ["53e19cb99ba3b295fd38a3667b"],
    "待测试回归": ["3e729203f51f6d60719dd35848"],
    "再次打开": ["30"],
    "待测试复现": ["4e7a6897b94d883f7d716ee854"],
    "待测试确认": ["e9c54fd14bc15561c13039fb7d"],
    "已完成": ["100014"],
    "暂不修复": ["31"],
    "无效缺陷": ["37"],
    "重复缺陷": ["626216"],
    "需求变更": ["2c8fd5a9d9f96f35e247597a3e"],
    "缺陷转需求": ["67c66b41d2a401d33667ac2e6e"],
    "仲裁不解决关闭": ["b7a81c8beed66884e508068192"],
    "未复现关闭": ["c4daec069639a0b818cb8eba76"],
    "重复非问题关闭": ["ac6c1a96f99119b21a91e9fb79"],
    "环境问题关闭": ["ff243a3d6f971c58faa18c65dd"],
    "需求变更关闭": ["85f21dc69913c29b6493446511"],
    "待处理": ["100005"],
    "已选择": ["625489"],
    "设计中": ["156603"],
    "开发中": ["142838"],
    "测试中": ["100012"],
    "分析中": ["154395"],
    "已取消": ["141230"],
    "已关闭": ["100085"],
}

# 默认未解决状态组
ACTIVE_BUG_STATUS = [
    "28",        # 待确认
    "100010",    # 处理中
    "53e19cb99ba3b295fd38a3667b",  # 待开发自验
    "30",        # 再次打开
]
ACTIVE_TASK_STATUS = ["100005", "100010"]
ACTIVE_REQ_STATUS = [
    "100005",  # 待处理
    "625489",  # 已选择
    "156603",  # 设计中
    "142838",  # 开发中
    "100012",  # 测试中
    "154395",  # 分析中
    "100010",  # 处理中
]


def _log(msg: str) -> None:
    """写 stderr 日志，避免污染 stdout JSON 输出"""
    print(f"[log] {msg}", file=sys.stderr, flush=True)


# ============================================================================
# MCP 通信层
# ============================================================================
class McpClient:
    """与 MCP Server 通过 stdio JSON-RPC 通信"""

    def __init__(self, server_cmd: list[str], env: dict[str, str]):
        self.server_cmd = server_cmd
        self.env = env
        self.proc: Optional[subprocess.Popen] = None
        self._request_id = 0

    def start(self) -> None:
        _log(f"启动 MCP Server: {' '.join(self.server_cmd)}")
        self.proc = subprocess.Popen(
            self.server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **self.env},
            text=False,
            shell=True,
        )

        # Initialize
        resp = self._call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "yunxiao-cli", "version": "1.0.0"},
        })
        _log(f"初始化完成: {resp.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")

        # Send initialized notification
        self._notify("notifications/initialized", {})
        time.sleep(0.5)

    def stop(self) -> None:
        if self.proc:
            self.proc.stdin.close()
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
            _log("MCP Server 已停止")

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._call("tools/call", {"name": name, "arguments": arguments})
        if "error" in result:
            raise RuntimeError(f"工具调用失败: {result['error']}")
        return result.get("result", result)

    def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        return self._send(request)

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        self._send(request, is_notification=True)

    def _send(self, payload: dict[str, Any], is_notification: bool = False) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False) + "\n"
        self.proc.stdin.write(body.encode("utf-8"))
        self.proc.stdin.flush()

        if is_notification:
            return {}

        line = self.proc.stdout.readline().decode("utf-8").strip()
        if not line:
            raise RuntimeError("MCP 响应为空")
        return json.loads(line)


# ============================================================================
# 查询逻辑
# ============================================================================
def resolve_status_ids(status_names: Optional[list[str]]) -> Optional[list[str]]:
    """将中文状态名转换为 ID 列表"""
    if not status_names:
        return None
    ids: list[str] = []
    for name in status_names:
        if name in STATUS_MAP:
            ids.extend(STATUS_MAP[name])
        else:
            _log(f"未知状态 '{name}'，已跳过")
    return ids if ids else None


def search_workitems(
    client: McpClient,
    category: str,
    type_ids: list[str],
    status_ids: Optional[list[str]] = None,
    assigned_to: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """搜索工作项"""
    status_filter = ",".join(status_ids) if status_ids else None
    wtype_filter = ",".join(type_ids)

    args: dict[str, Any] = {
        "organizationId": ORG_ID,
        "category": category,
        "spaceId": PROJECT_ID,
        "workitemType": wtype_filter,
        "orderBy": "gmtCreate",
        "sort": "desc",
        "page": page,
        "perPage": per_page,
    }
    if status_filter:
        args["status"] = status_filter
    if assigned_to:
        args["assignedTo"] = assigned_to

    _log(f"查询 {category}: type={wtype_filter}, status={status_filter}, assignedTo={assigned_to}, page={page}")
    return client.call_tool("search_workitems", args)


def format_item(item: dict[str, Any], category: str = "") -> dict[str, Any]:
    """提取关键字段"""
    status = item.get("status", {}) or {}
    assignee = item.get("assignedTo", {}) or {}
    sn = item.get("serialNumber", "")
    url = ""
    if item.get("id") and category:
        url = f"https://devops.aliyun.com/projex/project/{PROJECT_ID}/{category.lower()}/{item['id']}"
    return {
        "id": item.get("id", ""),
        "sn": sn,
        "subject": item.get("subject", ""),
        "status": status.get("displayName") or status.get("name", ""),
        "assignee": assignee.get("name", ""),
        "url": url,
        "created_at": item.get("gmtCreate"),
        "updated_at": item.get("gmtModified"),
    }


# ============================================================================
# CLI 入口
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        prog="yunxiao-cli",
        description="云效项目管理 CLI - 查询 Bug/Task/Req",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bug_parser = sub.add_parser("bug", help="Bug (缺陷) 操作")
    bug_parser.add_argument("action", choices=["list"], help="list - 列出 Bug")
    bug_parser.add_argument("--mine", action="store_true", help="仅显示我的")
    bug_parser.add_argument("--status", nargs="*", help="按状态过滤，支持中文名")
    bug_parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    bug_parser.add_argument("--per-page", type=int, default=20, help="每页条数 (默认 20)")
    bug_parser.add_argument("--json", action="store_true", help="输出原始 JSON")

    task_parser = sub.add_parser("task", help="Task (任务) 操作")
    task_parser.add_argument("action", choices=["list"], help="list - 列出任务")
    task_parser.add_argument("--mine", action="store_true", help="仅显示我的")
    task_parser.add_argument("--status", nargs="*", help="按状态过滤，支持中文名")
    task_parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    task_parser.add_argument("--per-page", type=int, default=20, help="每页条数 (默认 20)")
    task_parser.add_argument("--json", action="store_true", help="输出原始 JSON")

    req_parser = sub.add_parser("req", help="Req (需求) 操作")
    req_parser.add_argument("action", choices=["list"], help="list - 列出需求")
    req_parser.add_argument("--mine", action="store_true", help="仅显示我的")
    req_parser.add_argument("--status", nargs="*", help="按状态过滤，支持中文名")
    req_parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    req_parser.add_argument("--per-page", type=int, default=20, help="每页条数 (默认 20)")
    req_parser.add_argument("--json", action="store_true", help="输出原始 JSON")

    all_parser = sub.add_parser("all", help="聚合查询 Bug/Task/Req")
    all_parser.add_argument("action", choices=["list"], help="list - 一次性列出 Bug + Task + Req")
    all_parser.add_argument("--mine", action="store_true", help="仅显示我的")
    all_parser.add_argument("--status", nargs="*", help="按状态过滤，支持中文名")
    all_parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    all_parser.add_argument("--per-page", type=int, default=20, help="每页条数 (默认 20)")
    all_parser.add_argument("--json", action="store_true", help="输出原始 JSON")

    args = parser.parse_args()

    # 启动 MCP Client
    access_token = os.environ.get("YUNXIAO_ACCESS_TOKEN")
    if not access_token:
        _log("错误: 请设置 YUNXIAO_ACCESS_TOKEN 环境变量")
        sys.exit(1)

    client = McpClient(
        server_cmd=["npx", "-y", "alibabacloud-devops-mcp-server"],
        env={"YUNXIAO_ACCESS_TOKEN": access_token},
    )

    try:
        client.start()

        if args.command == "all":
            # 聚合查询 bug + task + req
            CATEGORY_CONFIGS = [
                ("Bug", BUG_TYPES, ACTIVE_BUG_STATUS),
                ("Task", TASK_TYPES, ACTIVE_TASK_STATUS),
                ("Req", REQ_TYPES, ACTIVE_REQ_STATUS),
            ]
            output: dict[str, Any] = {}
            for cat, tids, default_st in CATEGORY_CONFIGS:
                st_ids = resolve_status_ids(args.status) if args.status else default_st
                assigned = "self" if args.mine else None
                _log(f"查询 {cat} ...")
                result = search_workitems(
                    client, cat, tids,
                    status_ids=st_ids,
                    assigned_to=assigned,
                    page=args.page,
                    per_page=args.per_page,
                )
                if args.json:
                    output[cat.lower()] = result
                    continue

                content = result.get("content", [])
                text = content[0].get("text", "{}") if content else "{}"
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    output[cat.lower()] = {"error": "parse failed", "raw": text}
                    continue

                items = data.get("items", [])
                pagination = data.get("pagination", {}) or {}
                total = pagination.get("total", len(items))
                output[cat.lower()] = {
                    "total": total,
                    "page": args.page,
                    "per_page": args.per_page,
                    "items": [format_item(it, cat) for it in items],
                }
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return

        # 单一 category 查询
        if args.command == "bug":
            category = "Bug"
            type_ids = BUG_TYPES
            default_status = ACTIVE_BUG_STATUS
        elif args.command == "task":
            category = "Task"
            type_ids = TASK_TYPES
            default_status = ACTIVE_TASK_STATUS
        else:
            category = "Req"
            type_ids = REQ_TYPES
            default_status = ACTIVE_REQ_STATUS

        status_ids = resolve_status_ids(args.status) if args.status else default_status
        assigned_to = "self" if args.mine else None

        result = search_workitems(
            client, category, type_ids,
            status_ids=status_ids,
            assigned_to=assigned_to,
            page=args.page,
            per_page=args.per_page,
        )
    finally:
        client.stop()

    # 输出
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    content = result.get("content", [])
    if not content:
        print(json.dumps({"items": [], "total": 0}, ensure_ascii=False, indent=2))
        return

    text = content[0].get("text", "{}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(text)
        return

    items = data.get("items", [])
    pagination = data.get("pagination", {}) or {}
    total = pagination.get("total", len(items))

    output = {
        "total": total,
        "page": args.page,
        "per_page": args.per_page,
        "items": [format_item(it, category) for it in items],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
