from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from alerts.notifier import AlertNotifier


class TestAlertFormatting:
    def test_format_basic_alert(self):
        notifier = AlertNotifier()
        msg = notifier.format_alert_message({
            "src_ip": "10.0.0.1", "src_port": 12345,
            "dst_ip": "192.168.1.1", "dst_port": 80,
            "protocol": "TCP", "anomaly_score": 0.95,
            "packet_count": 100, "total_bytes": 5000,
            "flow_duration_sec": 10.5,
            "syn_count": 0, "rst_count": 0,
        })
        assert "IDS ALERT" in msg
        assert "10.0.0.1" in msg
        assert "192.168.1.1" in msg
        assert "0.9500" in msg

    def test_format_syn_flood_trigger(self):
        notifier = AlertNotifier()
        msg = notifier.format_alert_message({
            "src_ip": "10.0.0.1", "src_port": 80,
            "dst_ip": "10.0.0.2", "dst_port": 443,
            "protocol": "TCP", "anomaly_score": 0.99,
            "packet_count": 500, "total_bytes": 30000,
            "flow_duration_sec": 2.0,
            "syn_count": 400, "rst_count": 0,
        })
        assert "SYN flood" in msg
        assert "400" in msg

    def test_format_port_scan_trigger(self):
        notifier = AlertNotifier()
        msg = notifier.format_alert_message({
            "src_ip": "10.0.0.1", "src_port": 80,
            "dst_ip": "10.0.0.2", "dst_port": 443,
            "protocol": "TCP", "anomaly_score": 0.85,
            "packet_count": 200, "total_bytes": 10000,
            "flow_duration_sec": 5.0,
            "syn_count": 5, "rst_count": 30,
        })
        assert "port scan" in msg or "RST" in msg

    def test_format_missing_fields(self):
        notifier = AlertNotifier()
        msg = notifier.format_alert_message({})
        assert "IDS ALERT" in msg
        assert "?" in msg

    def test_format_minimal_data(self):
        notifier = AlertNotifier()
        msg = notifier.format_alert_message({"anomaly_score": 0.5})
        assert "0.5000" in msg

    def test_format_no_syn_or_rst_triggers(self):
        notifier = AlertNotifier()
        msg = notifier.format_alert_message({
            "src_ip": "1.1.1.1", "src_port": 1,
            "dst_ip": "2.2.2.2", "dst_port": 2,
            "protocol": "TCP", "anomaly_score": 0.5,
            "packet_count": 0, "total_bytes": 0,
            "flow_duration_sec": 0.0,
            "syn_count": 3, "rst_count": 2,
        })
        assert "SYN flood" not in msg
        assert "port scan" not in msg


class TestAlertNotifierChannels:
    def test_send_telegram_no_token(self):
        notifier = AlertNotifier(telegram_token=None, slack_webhook=None)
        result = notifier.send_telegram("123", "test")
        assert result is False

    def test_send_slack_no_webhook(self):
        notifier = AlertNotifier(telegram_token=None, slack_webhook=None)
        result = notifier.send_slack("test")
        assert result is False

    def test_send_alert_no_config(self, capsys):
        notifier = AlertNotifier(telegram_token=None, slack_webhook=None)
        notifier.send_alert({"anomaly_score": 0.5, "src_ip": "1.1.1.1", "src_port": 80, "dst_ip": "2.2.2.2", "dst_port": 443})
        captured = capsys.readouterr()
        assert "0.50" in captured.out
        assert "1.1.1.1" in captured.out
