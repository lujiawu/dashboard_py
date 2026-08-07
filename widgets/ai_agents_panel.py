from textual.widgets import DataTable
from models.types import AgentSession


class AiAgentsPanel(DataTable):
    """Display active opencode sessions in a DataTable."""

    STATUS_ICON = {
        "running": "\u26a1",
        "idle": "[green]\u25cf[/]",
        "waiting": "\u26a1\u2753",
        "error": "\u26a1\u274c",
        "done": "\u2713",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zebra_stripes = True
        self._last_sessions: list[AgentSession] | None = None

    def on_mount(self):
        self.cursor_type = "row"
        self.add_column("Status", width=8)
        self.add_column("Workspace", width=18)
        self.add_column("Session ID", width=24)
        self.add_column("Title", width=None)

    def update_sessions(self, sessions: list[AgentSession]):
        if sessions is self._last_sessions:
            return
        self._last_sessions = sessions
        rows = self._build_rows(sessions)
        self.clear()
        if not rows:
            self.add_rows([("", "", "", "[dim]暂无 Agent 状态[/dim]")])
        else:
            self.add_rows(rows)

    def _build_rows(self, sessions: list[AgentSession]) -> list[tuple]:
        if not sessions:
            return []

        rows = []
        for session in sessions:
            status = (session.status or "").strip().lower() or "unknown"
            icon = self.STATUS_ICON.get(status, "[dim]\u25cb[/]")
            status_str = f"{icon} {status}"
            workspace = session.directory or "?"
            session_id = session.id or "?"
            rows.append((status_str, workspace, session_id, session.title or "?"))

        return rows
