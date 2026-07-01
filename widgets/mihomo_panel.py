from textual.containers import VerticalScroll
from textual.widgets import Static

from store.sources.mihomo_source import GROUPS, format_delay, format_rate, split_route


_LABELS = {"香港自动": "HK", "美国OpenAI": "US"}
_STYLE = {"OK": "green", "WARN": "yellow", "BAD": "red", "DOWN": "red bold"}
_SPARKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[int | float], width: int = 10) -> str:
    if not values:
        return ""
    values = values[-width:]
    low = min(values)
    high = max(values)
    if low == high:
        return _SPARKS[0] * len(values)
    scale = len(_SPARKS) - 1
    return "".join(_SPARKS[round((value - low) * scale / (high - low))] for value in values)


class MihomoPanel(VerticalScroll):
    can_focus = True

    def compose(self):
        self._content = Static()
        yield self._content

    def update_status(self, data: dict):
        self._content.update(self._format(data))

    def _format(self, data: dict) -> str:
        traffic = data.get("traffic") or {}
        traffic_history = data.get("traffic_history") or {}
        wifi = data.get("wifi") or {}
        ping = data.get("ping") or {}
        quality = data.get("quality", "DOWN")
        reason = data.get("quality_reason", "")
        delays = data.get("delays") or {}
        delay_history = data.get("delay_history") or {}
        route_text, current_proxy = split_route(data.get("route", "--"))

        delay_lines = [
            "{prefix}{label}  {delay}{curve}".format(
                prefix="[bold]Speed[/bold]  " if index == 0 else "       ",
                label=_LABELS[name],
                delay=format_delay(delays.get(name)),
                curve=f"  {sparkline(delay_history.get(name) or [])}" if delay_history.get(name) else "",
            )
            for index, name in enumerate(GROUPS)
        ]
        avg = ping.get("avg_ms")
        loss = ping.get("loss_pct")
        router_text = f"{avg:.1f}ms" if avg is not None else "--ms"
        loss_text = f"{loss:.0f}%" if loss is not None else "--%"
        status = f"[{_STYLE.get(quality, 'white')}]{quality}[/]"
        if reason:
            status += f" [dim]{reason}[/dim]"
        down_curve = sparkline(traffic_history.get("down") or [])
        up_curve = sparkline(traffic_history.get("up") or [])

        return "\n".join(
            [
                f"[bold]Proxy[/bold]  {current_proxy}   {status}",
                f"[bold]Route[/bold]  {route_text}",
                "",
                *delay_lines,
                "",
                f"[bold]Flow[/bold]   ↓ {format_rate(traffic.get('down'))}  {down_curve}",
                f"       ↑ {format_rate(traffic.get('up'))}  {up_curve}",
                "",
                f"[bold]WiFi[/bold]   {wifi.get('ssid', '--')}  {wifi.get('signal_dbm', '--')} dBm  RX {wifi.get('rx_mbit', '--')}M / TX {wifi.get('tx_mbit', '--')}M",
                f"[bold]LAN[/bold]    {data.get('router', '--')}  {router_text}  loss {loss_text}",
            ]
        )
