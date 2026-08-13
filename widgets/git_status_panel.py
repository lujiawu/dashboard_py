import asyncio
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

from textual.widgets import Static

from config import cfg

logger = logging.getLogger(__name__)

GIT_TIMEOUT = 15
CONFLICT_CODES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


@dataclass
class RepoStatus:
    name: str
    branch: str = "?"
    dirty: int = 0
    ahead: int = 0
    behind: int = 0
    conflict: bool = False
    upstream: bool = False
    detached: bool = False
    error: str = ""
    action: str = ""

    def sort_key(self) -> tuple[int, str]:
        if self.conflict:
            priority = 0
        elif self.error or self.detached or not self.upstream:
            priority = 1
        elif self.dirty:
            priority = 2
        elif self.behind:
            priority = 3
        elif self.ahead:
            priority = 4
        else:
            priority = 5
        return priority, self.name.lower()


class GitStatusPanel(Static):
    can_focus = True

    def on_mount(self):
        self.border_title = "Git Status"
        self._repos = [Path(p).expanduser() for p in cfg.get("git", {}).get("repos", [])]
        self._last_output = ""
        self.update("Scanning..." if self._repos else "No repos configured.\nAdd paths in git.repos config.")

    async def refresh_status(self):
        if not self._repos:
            return

        started = time.monotonic()
        statuses = [await self._scan_one(repo_path) for repo_path in self._repos]
        output = "\n\n".join(self._format_result(status) for status in sorted(statuses, key=RepoStatus.sort_key))
        if output != self._last_output:
            self._last_output = output
            self.update(output)
        logger.info("[GitPanel] refreshed %d repos in %.1fs", len(statuses), time.monotonic() - started)

    async def _run(self, repo_path: Path, *args: str) -> tuple[int, str, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "-C", str(repo_path), *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=GIT_TIMEOUT)
            return proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace")
        except FileNotFoundError:
            return 1, "", "git not found"
        except asyncio.TimeoutError:
            return 1, "", "timeout"
        except OSError as error:
            return 1, "", str(error)

    async def _scan_one(self, repo_path: Path) -> RepoStatus:
        name = repo_path.name
        code, _, error = await self._run(repo_path, "rev-parse", "--is-inside-work-tree")
        if code:
            return RepoStatus(name, error=self._short_error(error, "not a repo"))

        fetch_error = ""
        if cfg.get("git", {}).get("fetch", True):
            code, _, error = await self._run(repo_path, "fetch", "--prune", "--quiet")
            if code:
                fetch_error = self._short_error(error, "fetch failed")

        status = await self._read_status(repo_path, name)
        if status.error:
            return status
        if fetch_error:
            status.error = fetch_error
            return status

        if status.upstream and not status.detached and not status.conflict and not status.dirty and status.behind and not status.ahead:
            code, _, error = await self._run(repo_path, "pull", "--ff-only", "--quiet")
            if code:
                status.error = self._short_error(error, "pull failed")
            else:
                status = await self._read_status(repo_path, name)
                status.action = "updated"
        return status

    async def _read_status(self, repo_path: Path, name: str) -> RepoStatus:
        code, output, error = await self._run(repo_path, "status", "--porcelain", "-b")
        if code:
            return RepoStatus(name, error=self._short_error(error, "status failed"))

        lines = output.splitlines()
        branch_line = lines[0] if lines else ""
        branch = self._parse_branch(branch_line)
        changes = lines[1:]
        return RepoStatus(
            name=name,
            branch=branch,
            dirty=len(changes),
            ahead=self._parse_count(branch_line, "ahead"),
            behind=self._parse_count(branch_line, "behind"),
            conflict=any(line[:2] in CONFLICT_CODES for line in changes),
            upstream="..." in branch_line,
            detached=branch_line.startswith("## HEAD "),
        )

    @staticmethod
    def _short_error(error: str, fallback: str) -> str:
        return error.strip().splitlines()[-1] if error.strip() else fallback

    @staticmethod
    def _parse_branch(branch_line: str) -> str:
        match = re.match(r"## (.+?)(?:\.\.\..*)?$", branch_line)
        return match.group(1) if match else "?"

    @staticmethod
    def _parse_count(branch_line: str, label: str) -> int:
        match = re.search(rf"{label} (\d+)", branch_line)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _format_result(status: RepoStatus) -> str:
        if status.conflict:
            icon, color, detail = "!", "red", "merge conflict"
        elif status.error:
            icon, color, detail = "!", "red", status.error
        elif status.detached:
            icon, color, detail = "!", "yellow", "detached HEAD"
        elif not status.upstream:
            icon, color, detail = "!", "yellow", "no upstream"
        elif status.dirty:
            icon, color, detail = "*", "yellow", f"{status.dirty} changed"
        elif status.ahead:
            icon, color, detail = "^", "cyan", f"{status.ahead} ahead"
        else:
            icon, color, detail = "+", "green", "up to date"

        sync = []
        if status.ahead:
            sync.append(f"ahead {status.ahead}")
        if status.behind:
            sync.append(f"behind {status.behind}")
        if status.action:
            sync.append(status.action)
        lines = [f"[{color}]{icon}[/] [bold]{status.name}[/]", f"  {status.branch}" + (f"  [dim]{', '.join(sync)}[/]" if sync else "")]
        if detail != "up to date" or status.action:
            lines.append(f"  [{color}]{detail}[/]")
        return "\n".join(lines)
