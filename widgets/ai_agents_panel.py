from datetime import datetime, timezone, timedelta
from textual.widgets import DataTable
from models.types import AgentSession


def _extract_hhmm(timestamp: str) -> str:
    if not timestamp:
        return "--:--"
    if len(timestamp) >= 16:
        return timestamp[11:16]
    if len(timestamp) >= 5:
        return timestamp[:5]
    return timestamp


def _is_recent(timestamp: str, hours: int = 24) -> bool:
    if not timestamp:
        return False
    ts_clean = timestamp[:16].replace("T", " ")
    now_bj = datetime.now(timezone(timedelta(hours=8)))
    cutoff = (now_bj - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
    return ts_clean >= cutoff


class AiAgentsPanel(DataTable):
    """Display active opencode sessions in a DataTable."""

    STATUS_EMOJI = {
        "running": "\u26a1",
        "idle": "\u2705",
        "waiting": "\u26a1\u2753",
        "error": "\u26a1\u274c",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.zebra_stripes = True

    def on_mount(self):
        self.cursor_type = "row"
        self.add_column("Status", width=4)
        self.add_column("Agent", width=5)
        self.add_column("Model", width=5)
        self.add_column("Time", width=5)
        self.add_column("Title", width=None)

    def update_sessions(self, sessions: list[AgentSession]):
        rows = self._build_rows(sessions)
        self.clear()
        self.add_rows(rows)

    def _build_rows(self, sessions: list[AgentSession]) -> list[tuple]:
        if not sessions:
            return []

        filtered = [s for s in sessions if _is_recent(s.update_time)]
        if not filtered:
            return []

        filtered.sort(key=lambda s: s.update_time or "", reverse=True)
        filtered.sort(key=lambda s: 0 if (s.status or "").strip().lower() == "running" else 1)

        rows = []
        for session in filtered:
            status = (session.status or "").strip().lower() or "unknown"
            emoji = self.STATUS_EMOJI.get(status, "\u26aa")

            agent_str = (session.agent or "—")[:7].ljust(7)

            model_label = session.model_id or "—"
            if "/" in model_label:
                model_label = model_label.rsplit("/", 1)[-1]
            model_str = model_label[:10].ljust(10)

            time_str = _extract_hhmm(session.update_time)

            host_mark = "\U0001f310 " if session.host and session.host != "local" else ""
            name = session.title or session.directory or "?"
            title_str = host_mark + name

            rows.append((emoji, agent_str, model_str, time_str, title_str))

        return rows
