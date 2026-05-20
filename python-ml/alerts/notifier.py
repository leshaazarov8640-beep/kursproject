import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AlertNotifier:
    def __init__(self, telegram_token: Optional[str] = None, slack_webhook: Optional[str] = None):
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.slack_webhook = slack_webhook or os.getenv("SLACK_WEBHOOK_URL")

    def send_telegram(self, chat_id: str, message: str) -> bool:
        if not self.telegram_token:
            logger.warning("Telegram token not configured")
            return False
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Telegram alert sent to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def send_slack(self, message: str) -> bool:
        if not self.slack_webhook:
            return False
        try:
            import requests
            payload = {"text": message}
            resp = requests.post(self.slack_webhook, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Slack alert sent")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def format_alert_message(self, alert_data: Dict) -> str:
        lines = [
            "IDS ALERT: ANOMALY DETECTED",
            f"  Flow: {alert_data.get('src_ip', '?')}:{alert_data.get('src_port', '?')} -> "
            f"{alert_data.get('dst_ip', '?')}:{alert_data.get('dst_port', '?')}",
            f"  Protocol: {alert_data.get('protocol', '?')}",
            f"  Anomaly Score: {alert_data.get('anomaly_score', 0):.4f}",
            f"  Packets: {alert_data.get('packet_count', 0)}",
            f"  Total Bytes: {alert_data.get('total_bytes', 0)}",
            f"  Duration: {alert_data.get('flow_duration_sec', 0):.2f}s",
        ]
        if alert_data.get("syn_count", 0) > 10:
            lines.append(f"  High SYN count: {alert_data['syn_count']} (possible SYN flood)")
        if alert_data.get("rst_count", 0) > 5:
            lines.append(f"  High RST count: {alert_data['rst_count']} (possible port scan)")
        return "\n".join(lines)

    def send_alert(self, alert_data: Dict, telegram_chat_id: Optional[str] = None) -> None:
        message = self.format_alert_message(alert_data)
        logger.info(f"Alert: {message}")

        if telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID"):
            chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
            self.send_telegram(chat_id, message)

        self.send_slack(message)
