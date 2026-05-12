import asyncio
import re
import logging
import time
from pathlib import Path
from textual.widgets import Static
from config import cfg

logger = logging.getLogger(__name__)

GIT_TIMEOUT = 15


class GitStatusPanel(Static):
    def on_mount(self):
        self.border_title = "Git Status"
        self._repos = [Path(p).expanduser() for p in cfg.get("git", {}).get("repos", [])]
        if not self._repos:
            self.update("No repos configured.\nAdd paths in git.repos config.")
        else:
            self.update("Scanning...")

    async def refresh_status(self):
        if not self._repos:
            logger.info("[GitPanel] refresh_status called but repos list is empty")
            return

        t0 = time.monotonic()
        logger.info(f"[GitPanel] refresh_status start, repos={len(self._repos)}")
        lines = []
        for repo_path in self._repos:
            line = await self._scan_one(repo_path)
            lines.append(line)

        self.update("\n".join(lines) if lines else "No repos")
        logger.info(f"[GitPanel] refresh_status done in {time.monotonic() - t0:.1f}s")

    async def _scan_one(self, repo_path: Path) -> str:
        name = repo_path.name
        logger.info(f"[GitPanel] scanning {repo_path}")

        t0 = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "-C", str(repo_path), "rev-parse", "--is-inside-work-tree",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_TIMEOUT)
            if proc.returncode != 0:
                logger.info(f"[GitPanel] {name} not a repo (returncode={proc.returncode})")
                return "\u274c " + name + " (not a repo)"
        except FileNotFoundError:
            logger.warning(f"[GitPanel] {name} git not found on PATH")
            return "\u26a0\ufe0f " + name + " (git not found)"
        except asyncio.TimeoutError:
            logger.warning(f"[GitPanel] {name} rev-parse timed out after {GIT_TIMEOUT}s")
            return "\u23f0 " + name + " (timeout)"
        except OSError as e:
            logger.warning(f"[GitPanel] {name} OSError: {e}")
            return "\u274c " + name + " (error)"

        logger.info(f"[GitPanel] {name} rev-parse ok ({time.monotonic() - t0:.1f}s)")

        if cfg.get("git", {}).get("fetch", True):
            t1 = time.monotonic()
            logger.info(f"[GitPanel] {name} fetching...")
            try:
                fetch_proc = await asyncio.create_subprocess_exec(
                    "git", "-C", str(repo_path), "fetch", "--prune", "--quiet",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(fetch_proc.communicate(), timeout=GIT_TIMEOUT)
                logger.info(f"[GitPanel] {name} fetch done ({time.monotonic() - t1:.1f}s)")
            except asyncio.TimeoutError:
                logger.warning(f"[GitPanel] {name} fetch timed out after {GIT_TIMEOUT}s")
            except OSError as e:
                logger.warning(f"[GitPanel] {name} fetch OSError: {e}")

        t2 = time.monotonic()
        logger.info(f"[GitPanel] {name} git status...")
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "-C", str(repo_path), "status", "--porcelain", "-b",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"[GitPanel] {name} status timed out after {GIT_TIMEOUT}s")
            return "\u23f0 " + name + " (timeout)"
        except OSError as e:
            logger.warning(f"[GitPanel] {name} status OSError: {e}")
            return "\u274c " + name + " (error)"

        logger.info(f"[GitPanel] {name} status done ({time.monotonic() - t2:.1f}s)")

        output = stdout.decode("utf-8", errors="replace").strip()
        lines_list = output.split("\n") if output else []
        branch_line = lines_list[0] if lines_list else ""

        branch_name = self._parse_branch(branch_line)
        ahead = self._parse_count(branch_line, "ahead")
        behind = self._parse_count(branch_line, "behind")
        dirty = len(lines_list) - 1 if lines_list else 0

        result = self._format_result(name, branch_line, branch_name, dirty, ahead, behind)
        logger.info(f"[GitPanel] {name} result: {result}")
        return result

    def _format_result(self, name: str, branch_line: str, branch_name: str,
                       dirty: int, ahead: int, behind: int) -> str:
        if "..." not in branch_line:
            return "\U0001f4a4 " + name +  "\n  " + branch_name

        if dirty == 0 and ahead == 0 and behind == 0:
            return "\u2705 " + name + "\n  " + branch_name

        parts = []
        if dirty > 0:
            parts.append(f"{dirty} modified")
        if ahead > 0:
            parts.append(f"ahead {ahead}")
        if behind > 0:
            parts.append(f"behind {behind}")

        status_str = ", ".join(parts)
        emoji = self._pick_emoji(dirty, ahead, behind)
        return f"{emoji} ({status_str}) {name}\n  {branch_name} "

    @staticmethod
    def _parse_branch(branch_line: str) -> str:
        m = re.match(r"## (.+?)(?:\.\.\..*)?$", branch_line)
        return m.group(1) if m else "?"

    @staticmethod
    def _parse_count(branch_line: str, label: str) -> int:
        m = re.search(rf"{label} (\d+)", branch_line)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _pick_emoji(dirty: int, ahead: int, behind: int) -> str:
        if dirty > 0 and ahead > 0 and behind > 0:
            return "\U0001f500"
        if dirty > 0 and behind > 0:
            return "\U0001f504"
        if dirty > 0 and ahead > 0:
            return "\U0001f4dd"
        if ahead > 0 and behind > 0:
            return "\U0001f500"
        if dirty > 0:
            return "\U0001f4dd"
        if ahead > 0:
            return "\u2b06\ufe0f"
        if behind > 0:
            return "\u2b07\ufe0f"
        return "\u2705"
