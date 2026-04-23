from datetime import datetime, timezone
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import AgentSession


class AiAgentsPanel(VerticalScroll):
    """Display active opencode sessions with status colors."""

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
                if hours_diff <= 24:
                    filtered.append((session, update_time))
            except ValueError:
                continue

        # Sort descending by update time
        filtered.sort(key=lambda x: x[1], reverse=True)

        if not filtered:
            return "No sessions updated in the past 24 hours"

        lines = []
        for session, _ in filtered:
            status = (session.status or "").strip().lower() or "unknown"
            tag = "bold bright_green" if status == "running" else "blue"

            directory = session.directory or "Unknown"
            if len(directory) > 15:
                directory = directory[:12] + "..."

            title = session.title or ""
            if len(title) > 50:
                title = title[:47] + "..."

            lines.append(f"[{tag}]{directory:<15} | {title}[/{tag}]")

        return "\n".join(lines)
