import unittest
import sys
import types

try:
    from widgets.mihomo_panel import MihomoPanel
except ModuleNotFoundError:
    textual = types.ModuleType("textual")
    containers = types.ModuleType("textual.containers")
    widgets = types.ModuleType("textual.widgets")

    class VerticalScroll:
        pass

    class Static:
        def update(self, _value):
            pass

    containers.VerticalScroll = VerticalScroll
    widgets.Static = Static
    sys.modules["textual"] = textual
    sys.modules["textual.containers"] = containers
    sys.modules["textual.widgets"] = widgets

    from widgets.mihomo_panel import MihomoPanel


class MihomoPanelTest(unittest.TestCase):
    def test_format_prioritizes_delay_list_and_keeps_route(self):
        text = MihomoPanel()._format(
            {
                "route": "白嫖机场 → 区域自动 → 香港自动 → 🇭🇰香港HY🚀",
                "delays": {"香港自动": 42, "日本自动": None, "美国OpenAI": 246},
                "delay_history": {"香港自动": [40, 42, 73], "美国OpenAI": [200, 220, 246]},
                "traffic": {"down": 2048, "up": 1024},
                "traffic_history": {"down": [256, 512, 2048], "up": [128, 256, 1024]},
                "wifi": {"ssid": "192-5G", "signal_dbm": -57, "rx_mbit": 585.0, "tx_mbit": 390.0},
                "router": "192.168.1.1",
                "ping": {"avg_ms": 9.6, "loss_pct": 0.0},
                "quality": "OK",
            }
        )

        lines = text.splitlines()
        self.assertEqual(lines[0], "[bold]Proxy[/bold]  🇭🇰香港HY🚀   [green]OK[/]")
        self.assertEqual(lines[1], "[bold]Route[/bold]  白嫖机场 → 区域自动 → 香港自动")
        self.assertIn("[bold]Speed[/bold]  HK  42ms", lines[3])
        self.assertIn("       US  246ms", lines[4])
        self.assertNotIn("JP", text)
        self.assertRegex(lines[3], r"HK\s+42ms\s+[▁▂▃▄▅▆▇█]+")
        self.assertRegex(lines[4], r"US\s+246ms\s+[▁▂▃▄▅▆▇█]+")
        self.assertRegex(lines[6], r"^\[bold\]Flow\[/bold\]\s+↓ 2\.0 KB/s\s+[▁▂▃▄▅▆▇█]+$")
        self.assertRegex(lines[7], r"^\s+↑ 1\.0 KB/s\s+[▁▂▃▄▅▆▇█]+$")

    def test_format_compacts_layout_and_limits_curves_to_ten_points(self):
        text = MihomoPanel()._format(
            {
                "route": "白嫖机场 → 区域自动 → 香港自动 → 🇭🇰香港HY🚀",
                "delays": {"香港自动": 62, "美国OpenAI": 215},
                "delay_history": {"香港自动": list(range(12)), "美国OpenAI": list(range(20, 32))},
                "traffic": {"down": 5000, "up": 1900},
                "traffic_history": {
                    "down": list(range(20)),
                    "up": list(range(30, 50)),
                },
                "wifi": {"ssid": "192", "signal_dbm": -47, "rx_mbit": 78.0, "tx_mbit": 144.4},
                "router": "192.168.1.1",
                "ping": {"avg_ms": 4.3, "loss_pct": 0.0},
                "quality": "OK",
            }
        )

        lines = text.splitlines()
        self.assertEqual(lines[0], "[bold]Proxy[/bold]  🇭🇰香港HY🚀   [green]OK[/]")
        self.assertIn("[bold]Route[/bold]  白嫖机场 → 区域自动 → 香港自动", lines[1])
        self.assertIn("[bold]Speed[/bold]  HK  62ms", lines[3])
        self.assertTrue(lines[4].startswith("       US  215ms"))
        self.assertTrue(lines[6].startswith("[bold]Flow[/bold]   ↓ 4.9 KB/s  "))
        self.assertTrue(lines[7].startswith("       ↑ 1.9 KB/s  "))
        self.assertTrue(lines[9].startswith("[bold]WiFi[/bold]   192  -47 dBm  RX 78.0M / TX 144.4M"))
        self.assertTrue(lines[10].startswith("[bold]LAN[/bold]    192.168.1.1  4.3ms  loss 0%"))
        self.assertRegex(lines[3], r"[▁▂▃▄▅▆▇█]{10}$")
        self.assertRegex(lines[4], r"[▁▂▃▄▅▆▇█]{10}$")
        self.assertRegex(lines[6], r"[▁▂▃▄▅▆▇█]{10}$")
        self.assertRegex(lines[7], r"[▁▂▃▄▅▆▇█]{10}$")


if __name__ == "__main__":
    unittest.main()
