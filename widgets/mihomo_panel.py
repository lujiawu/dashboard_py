from textual.containers import VerticalScroll
from textual.widgets import Static

from store.sources.mihomo_source import GROUPS, format_delay, format_rate


_LABELS = {"香港自动": "HK", "日本自动": "JP", "美国OpenAI": "US"}
_STYLE = {"OK": "green", "WARN": "yellow", "BAD": "red", "DOWN": "red bold"}


class MihomoPanel(VerticalScroll):
    can_focus = True

    def compose(self):
        self._content = Static()
        yield self._content

    def update_status(self, data: dict):
        self._content.update(self._format(data))

    def _format(self, data: dict) -> str:
        traffic = data.get("traffic") or {}
        wifi = data.get("wifi") or {}
        ping = data.get("ping") or {}
        quality = data.get("quality", "DOWN")
        reason = data.get("quality_reason", "")
        delays = data.get("delays") or {}

        delay_lines = [
            f"  {_LABELS[name]}  {format_delay(delays.get(name))}" for name in GROUPS
        ]
        avg = ping.get("avg_ms")
        loss = ping.get("loss_pct")
        router_text = f"{avg:.1f}ms" if avg is not None else "--ms"
        loss_text = f"{loss:.0f}%" if loss is not None else "--%"
        status = f"[{_STYLE.get(quality, 'white')}]{quality}[/]"
        if reason:
            status += f" [dim]{reason}[/dim]"

        return "\n".join(
            [
                f"[bold]Proxy[/bold]  {data.get('route', '--')}",
                "[bold]Proxy Speed[/bold]",
                *delay_lines,
                "",
                f"[bold]Route[/bold]  {data.get('route', '--')}",
                f"[bold]Flow[/bold]   ↓ {format_rate(traffic.get('down'))}  ↑ {format_rate(traffic.get('up'))}",
                "",
                f"[bold]WiFi[/bold]   {wifi.get('ssid', '--')}  {wifi.get('signal_dbm', '--')} dBm  RX {wifi.get('rx_mbit', '--')}M  TX {wifi.get('tx_mbit', '--')}M",
                f"[bold]LAN[/bold]    {data.get('router', '--')}  {router_text}  loss {loss_text}  {status}",
            ]
        )
