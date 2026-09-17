"""
Production Alert Manager for GrowX.
Dispatches critical operational alerts to Slack, Webhooks, or Email with throttling.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional
import urllib.request
import json

logger = logging.getLogger("growx_crawl.ops.alerts")


class AlertManager:
    def __init__(self, webhook_url: Optional[str] = None, min_interval_seconds: int = 300):
        self.webhook_url = webhook_url
        self.min_interval_seconds = min_interval_seconds
        self._last_alert_times: Dict[str, float] = {}
        self.alert_history: List[Dict[str, Any]] = []

    def dispatch(
        self,
        alert_key: str,
        title: str,
        message: str,
        severity: str = "warning",  # "info" | "warning" | "critical"
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Sends an alert if outside the throttling window for the given alert key."""
        now = time.time()
        last_time = self._last_alert_times.get(alert_key, 0.0)
        if (now - last_time) < self.min_interval_seconds:
            logger.debug(f"[ALERT_MANAGER] Throttling alert '{alert_key}' (sent {int(now - last_time)}s ago)")
            return False

        self._last_alert_times[alert_key] = now
        entry = {
            "key": alert_key,
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self.alert_history.append(entry)
        if len(self.alert_history) > 200:
            self.alert_history.pop(0)

        logger.warning(f"[ALERT - {severity.upper()}] {title}: {message}")

        if self.webhook_url:
            try:
                payload = json.dumps({
                    "text": f"*{severity.upper()}: {title}*\n{message}",
                    "severity": severity,
                    "metadata": metadata or {},
                }).encode("utf-8")
                req = urllib.request.Request(
                    self.webhook_url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=5.0):
                    pass
            except Exception as e:
                logger.error(f"[ALERT_MANAGER] Failed to post alert webhook: {e}")

        return True


alert_manager = AlertManager()

__all__ = ["AlertManager", "alert_manager"]
