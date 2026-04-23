from datetime import datetime, timezone, timedelta
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import AgentSession


class AiAgentsPanel(VerticalScroll):
    """Display active opencode sessions with status colors."""

    STATUS_EMOJI = {
        "running": "⚡",
        "idle": "✅",
        "waiting": "⚡❓",
        "error": "⚡❌",
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

        current_time = datetime.now(timezone.utc)
        filtered = []

        for session in sessions:
            try:
                ts = session.update_time or ""
                if not ts:
                    continue
                if ts.endswith("Z"):
                    ts = ts[:-1] + "+00:00"
                update_time = datetime.fromisoformat(ts)

                hours_diff = abs((current_time - update_time).total_seconds()) / 3600
                if hours_diff <= 1:
                    filtered.append((session, update_time))
            except ValueError:
                continue

        if not filtered:
            return "No sessions updated in the past hour"

        # Sort by status priority, then update time descending
        def sort_key(item):
            session, update_time = item
            status = (session.status or "").strip().lower() or "unknown"
            priority = self.STATUS_PRIORITY.get(status, 99)
            return (priority, -update_time.timestamp())

        filtered.sort(key=sort_key)

        lines = []
        for session, update_time in filtered:
            status = (session.status or "").strip().lower() or "unknown"
            if status == "running":
                tag = "bold #00ff00"
            elif status == "idle":
                tag = "bold white"
            elif status == "error":
                tag = "bold #ff5252"
            else:
                tag = "dim white"
            emoji = self.STATUS_EMOJI.get(status, "⚪")

            directory = session.directory or "Unknown"
            if len(directory) > 15:
                directory = directory[:12] + "..."

            # Convert to Beijing time (UTC+8)
            beijing_time = update_time.astimezone(timezone(timedelta(hours=8)))
            time_str = beijing_time.strftime("%H:%M")

            lines.append(f"[{tag}]{emoji} {directory:<15} {time_str}[/{tag}]")

        # Pad to at least 6 lines so the panel maintains minimum height
        while len(lines) < 6:
            lines.append("")

        return "\n".join(lines)
