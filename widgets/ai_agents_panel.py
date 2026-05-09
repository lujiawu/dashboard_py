from datetime import datetime, timezone, timedelta
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import AgentSession


def _extract_hhmm(timestamp: str) -> str:
    """Extract HH:MM from timestamp string (new or old format)."""
    if not timestamp:
        return "--:--"
    if len(timestamp) >= 16:
        return timestamp[11:16]
    if len(timestamp) >= 5:
        return timestamp[:5]
    return timestamp


def _is_recent(timestamp: str, hours: int = 24) -> bool:
    """Check if timestamp is within N hours (string compare, Beijing time)."""
    if not timestamp:
        return False
    ts_clean = timestamp[:16].replace("T", " ")
    now_bj = datetime.now(timezone(timedelta(hours=8)))
    cutoff = (now_bj - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
    return ts_clean >= cutoff


class AiAgentsPanel(VerticalScroll):
    """Display active opencode sessions with status colors, grouped by host."""

    STATUS_EMOJI = {
        "running": "\u26a1",
        "idle": "\u2705",
        "waiting": "\u26a1\u2753",
        "error": "\u26a1\u274c",
    }

    STATUS_PRIORITY = {
        "running": 0,
        "idle": 1,
        "error": 2,
    }

    def compose(self):
        yield Static(id="content", expand=True)

    def update_sessions(self, sessions: list[AgentSession]):
        content = self._format_sessions(sessions)
        self.query_one("#content", Static).update(content)

    def _format_sessions(self, sessions: list[AgentSession]) -> str:
        if not sessions:
            return "No active sessions"

        filtered = [(s, _extract_hhmm(s.update_time)) for s in sessions if _is_recent(s.update_time)]

        if not filtered:
            return "No sessions updated in the past day"

        # Sort: update time descending first, then running first
        filtered.sort(key=lambda item: item[0].update_time or "", reverse=True)
        filtered.sort(key=lambda item: 0 if (item[0].status or "").strip().lower() == "running" else 1)

        lines = []
        for session, hhmm in filtered:
            status = (session.status or "").strip().lower() or "unknown"
            if status == "running":
                color = "bold #00ff00"
            elif status == "idle":
                color = "bold white"
            elif status == "error":
                color = "bold #ff5252"
            else:
                color = "dim white"
            emoji = self.STATUS_EMOJI.get(status, "\u26aa")
            host_mark = "\U0001f310" if session.host and session.host != "local" else ""

            agent_label = f"{session.agent:<5}" if session.agent else "—    "
            name = session.title or session.directory or "?"
            if len(name) > 20:
                name = name[:17] + "..."

            model_label = session.model_id or "—"
            if "/" in model_label:
                model_label = model_label.rsplit("/", 1)[-1]
            if len(model_label) > 10:
                model_label = model_label[:7] + "..."

            time_str = _extract_hhmm(session.update_time)
            lines.append(
                f"[{color}]{emoji} {agent_label}  {host_mark}{name:<20} "
                f"\U0001f916 {model_label:<10} {time_str}[/{color}]"
            )

        while len(lines) < 8:
            lines.append("")

        return "\n".join(lines)
