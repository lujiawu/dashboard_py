import unittest

from store.sources.mihomo_source import (
    MihomoSource,
    append_history,
    assess_network_quality,
    format_delay,
    latest_delay,
    parse_ping,
    parse_iw_link,
    split_route,
    selected_route,
)


class MihomoSourceTest(unittest.TestCase):
    def test_selected_route_follows_nested_groups_to_node(self):
        groups = {
            "白嫖机场": {"now": "区域自动"},
            "区域自动": {"now": "香港自动"},
            "香港自动": {"now": "🇭🇰香港HY"},
        }

        self.assertEqual(selected_route(groups), "白嫖机场 → 区域自动 → 香港自动 → 🇭🇰香港HY")

    def test_split_route_separates_current_proxy_from_parent_route(self):
        self.assertEqual(
            split_route("白嫖机场 → 区域自动 → 香港自动 → 🇭🇰香港HY🚀"),
            ("白嫖机场 → 区域自动 → 香港自动", "🇭🇰香港HY🚀"),
        )

    def test_append_history_keeps_recent_samples_only(self):
        history = [1, 2]

        self.assertEqual(append_history(history, 3, limit=2), [2, 3])

    def test_latest_delay_uses_last_non_zero_delay(self):
        group = {"history": [{"delay": 71}, {"delay": 0}, {"delay": 195}]}

        self.assertEqual(latest_delay(group), 195)

    def test_parse_iw_link_extracts_wifi_status(self):
        text = """Connected to 8c:83:c0:32:e4:34 (on wlp0s20f3)
\tSSID: 192-5G
\tsignal: -57 dBm
\trx bitrate: 585.0 MBit/s VHT-MCS 7 80MHz VHT-NSS 2
\ttx bitrate: 390.0 MBit/s VHT-MCS 9 80MHz VHT-NSS 1
"""

        self.assertEqual(
            parse_iw_link(text),
            {"ssid": "192-5G", "signal_dbm": -57, "rx_mbit": 585.0, "tx_mbit": 390.0},
        )

    def test_assess_network_quality_reports_bad_latency_and_weak_signal(self):
        self.assertEqual(assess_network_quality(95.0, 0.0, -57), ("BAD", "high latency"))
        self.assertEqual(assess_network_quality(9.6, 0.0, -78), ("BAD", "weak signal"))
        self.assertEqual(assess_network_quality(25.0, 0.0, -57), ("WARN", "latency"))
        self.assertEqual(assess_network_quality(None, 100.0, -57), ("DOWN", "router unreachable"))
        self.assertEqual(assess_network_quality(9.6, 0.0, -57), ("OK", ""))

    def test_parse_ping_extracts_avg_and_loss(self):
        text = """2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 3.322/9.636/13.511/4.503 ms
"""

        self.assertEqual(parse_ping(text), {"avg_ms": 9.636, "loss_pct": 0.0})

    def test_read_groups_treats_null_proxies_as_empty(self):
        source = MihomoSource({})
        source._request_json = lambda path: {"proxies": None}

        self.assertEqual(source._read_groups(), {})

    def test_format_delay_keeps_zero_visible(self):
        self.assertEqual(format_delay(0), "0ms")
        self.assertEqual(format_delay(None), "--ms")


if __name__ == "__main__":
    unittest.main()
