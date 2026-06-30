import asyncio
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

from store.sources.base import DataSource


GROUPS = ("香港自动", "日本自动", "美国OpenAI")


def format_rate(value: float) -> str:
    value = float(value or 0)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if value < 1024 or unit == "GB/s":
            return f"{value:.1f} {unit}"
        value /= 1024


def format_delay(value: int | None) -> str:
    return f"{value}ms" if value is not None else "--ms"


def selected_route(groups: dict[str, dict[str, Any]], start: str = "白嫖机场") -> str:
    route = []
    seen = set()
    current = start
    while current in groups and current not in seen:
        seen.add(current)
        route.append(current)
        next_name = groups[current].get("now")
        if not next_name:
            break
        if next_name in groups:
            current = next_name
        else:
            route.append(next_name)
            break
    return " → ".join(route) if route else "未知"


def latest_delay(group: dict[str, Any]) -> int | None:
    for item in reversed(group.get("history") or []):
        delay = item.get("delay")
        if isinstance(delay, int) and delay > 0:
            return delay
    return None


def parse_iw_link(text: str) -> dict[str, Any]:
    def match(pattern: str):
        found = re.search(pattern, text, re.MULTILINE)
        return found.group(1) if found else None

    signal = match(r"signal:\s*(-?\d+)\s*dBm")
    rx = match(r"rx bitrate:\s*([\d.]+)\s*MBit/s")
    tx = match(r"tx bitrate:\s*([\d.]+)\s*MBit/s")
    return {
        "ssid": match(r"SSID:\s*(.+)") or "--",
        "signal_dbm": int(signal) if signal else None,
        "rx_mbit": float(rx) if rx else None,
        "tx_mbit": float(tx) if tx else None,
    }


def parse_ping(text: str) -> dict[str, Any]:
    loss_match = re.search(r"([\d.]+)%\s*packet loss", text)
    rtt_match = re.search(r"=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+\s*ms", text)
    return {
        "avg_ms": float(rtt_match.group(1)) if rtt_match else None,
        "loss_pct": float(loss_match.group(1)) if loss_match else 100.0,
    }


def assess_network_quality(avg_ms: float | None, loss_pct: float | None, signal_dbm: int | None) -> tuple[str, str]:
    if avg_ms is None or loss_pct == 100:
        return "DOWN", "router unreachable"
    if avg_ms >= 80:
        return "BAD", "high latency"
    if loss_pct is not None and loss_pct >= 50:
        return "BAD", "packet loss"
    if signal_dbm is not None and signal_dbm < -75:
        return "BAD", "weak signal"
    if avg_ms >= 20:
        return "WARN", "latency"
    if loss_pct is not None and loss_pct > 0:
        return "WARN", "packet loss"
    if signal_dbm is not None and signal_dbm < -65:
        return "WARN", "weak signal"
    return "OK", ""


class MihomoSource(DataSource[dict[str, Any]]):
    def __init__(self, config: dict):
        self._api_url = config.get("api_url", "http://127.0.0.1:9090").rstrip("/")
        self._router = config.get("router", "192.168.1.1")
        self._route_start = config.get("route_start", "白嫖机场")
        self._iface = config.get("iface") or self._detect_iface()
        self._traffic_interval = float(config.get("traffic_interval", 2.0))
        self._status_interval = float(config.get("status_interval", 30.0))
        self._group_at = 0.0
        self._wifi_at = 0.0
        self._ping_at = 0.0
        self._groups: dict[str, Any] = {}
        self._wifi: dict[str, Any] = {}
        self._ping: dict[str, Any] = {}
        self._traffic: dict[str, Any] = {}
        self._error = ""

    @property
    def refresh_interval(self) -> float:
        return self._traffic_interval

    async def fetch(self) -> dict[str, Any]:
        now = time.monotonic()
        self._traffic = await asyncio.to_thread(self._read_traffic)
        jobs = []
        if now - self._group_at >= self._status_interval:
            jobs.append(("groups", asyncio.to_thread(self._read_groups)))
        if self._iface and now - self._wifi_at >= self._status_interval:
            jobs.append(("wifi", asyncio.to_thread(self._read_wifi)))
        if now - self._ping_at >= self._status_interval:
            jobs.append(("ping", asyncio.to_thread(self._read_ping)))

        for name, result in zip(
            [name for name, _ in jobs],
            await asyncio.gather(*(job for _, job in jobs)) if jobs else [],
        ):
            if name == "groups":
                self._groups = result
                self._group_at = now
            elif name == "wifi":
                self._wifi = result
                self._wifi_at = now
            elif name == "ping":
                self._ping = result
                self._ping_at = now

        status, reason = assess_network_quality(
            self._ping.get("avg_ms"),
            self._ping.get("loss_pct"),
            self._wifi.get("signal_dbm"),
        )
        groups = self._groups
        return {
            "route": selected_route(groups, self._route_start) if groups else "--",
            "delays": {name: latest_delay(groups.get(name, {})) for name in GROUPS},
            "traffic": self._traffic,
            "wifi": self._wifi,
            "router": self._router,
            "ping": self._ping,
            "quality": status,
            "quality_reason": reason,
            "error": self._error,
        }

    def _request_json(self, path: str, timeout: float = 3.0) -> Any:
        with urllib.request.urlopen(f"{self._api_url}{path}", timeout=timeout) as response:
            return json.loads(response.read())

    def _read_groups(self) -> dict[str, Any]:
        try:
            self._error = ""
            data = self._request_json("/group")
            return {item["name"]: item for item in data.get("proxies") or []}
        except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError) as error:
            self._error = f"Mihomo API: {error}"
            return self._groups

    def _read_traffic(self) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(f"{self._api_url}/traffic", timeout=3) as response:
                line = response.readline()
            return json.loads(line) if line else self._traffic
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            return self._traffic

    def _detect_iface(self) -> str:
        try:
            result = subprocess.run(
                ["ip", "route", "get", self._router],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            parts = result.stdout.split()
            return parts[parts.index("dev") + 1] if "dev" in parts else ""
        except (OSError, subprocess.TimeoutExpired, ValueError, IndexError):
            return ""

    def _read_wifi(self) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["iw", "dev", self._iface, "link"],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            return parse_iw_link(result.stdout) if result.stdout else self._wifi
        except (OSError, subprocess.TimeoutExpired):
            return self._wifi

    def _read_ping(self) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["ping", "-c", "2", "-W", "1", self._router],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            return parse_ping(result.stdout)
        except (OSError, subprocess.TimeoutExpired):
            return {"avg_ms": None, "loss_pct": 100.0}
