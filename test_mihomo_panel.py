import unittest

from widgets.mihomo_panel import MihomoPanel


class MihomoPanelTest(unittest.TestCase):
    def test_format_prioritizes_delay_list_and_keeps_route(self):
        text = MihomoPanel()._format(
            {
                "route": "白嫖机场 → 香港自动 → hk-node",
                "delays": {"香港自动": 42, "日本自动": 88, "美国OpenAI": None},
                "traffic": {"down": 2048, "up": 1024},
                "wifi": {"ssid": "192-5G", "signal_dbm": -57, "rx_mbit": 585.0, "tx_mbit": 390.0},
                "router": "192.168.1.1",
                "ping": {"avg_ms": 9.6, "loss_pct": 0.0},
                "quality": "OK",
            }
        )

        self.assertLess(text.index("[bold]Proxy Speed[/bold]"), text.index("[bold]Route[/bold]"))
        self.assertIn("  HK  42ms", text)
        self.assertIn("  JP  88ms", text)
        self.assertIn("  US  --ms", text)
        self.assertIn("[bold]Route[/bold]  白嫖机场 → 香港自动 → hk-node", text)


if __name__ == "__main__":
    unittest.main()
