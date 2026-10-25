"""Alert dispatch engine supporting webhooks and emails (B4 Features F16/F17).

Dispatches automated notifications for lake outburst anomalies, flood risk escalations,
and system alerts. Target URLs and email recipients are read from environment settings.
"""

from __future__ import annotations

import datetime
import email.message
import json
import logging
import smtplib
from typing import Any

import httpx

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


class AlertDispatcher:
    """Dispatches webhook notifications and email alerts with robust error handling."""

    def __init__(
        self,
        webhook_url: str | None = None,
        email_to: str | None = None,
        email_from: str | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
    ) -> None:
        self.webhook_url = webhook_url or settings.alert_webhook_url
        self.email_to = email_to or settings.alert_email_to
        self.email_from = email_from or settings.alert_email_from
        self.smtp_host = smtp_host or settings.smtp_host
        self.smtp_port = smtp_port or settings.smtp_port

    async def send_webhook(
        self,
        payload: dict[str, Any],
        url: str | None = None,
    ) -> tuple[bool, int | None, str | None]:
        """Send an HTTP POST webhook alert.

        Returns:
            Tuple of (success, status_code, error_message).
        """
        target_url = url or self.webhook_url
        if not target_url:
            logger.info("No webhook URL configured; skipping webhook dispatch.")
            return False, None, "No webhook URL configured"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    target_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "PravahX-Alerts/1.0",
                    },
                )
                res.raise_for_status()
                return True, res.status_code, None
        except Exception as exc:
            logger.warning("Failed to dispatch alert webhook to %s: %s", target_url, exc)
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            return False, status_code, str(exc)

    def send_email(
        self,
        subject: str,
        body_text: str,
        to_address: str | None = None,
    ) -> tuple[bool, str | None]:
        """Send an alert email via SMTP.

        Returns:
            Tuple of (success, error_message).
        """
        recipient = to_address or self.email_to
        if not recipient:
            logger.info("No email recipient configured; skipping email dispatch.")
            return False, "No email recipient configured"

        msg = email.message.EmailMessage()
        msg["Subject"] = f"[PravahX Alert] {subject}"
        msg["From"] = self.email_from
        msg["To"] = recipient
        msg.set_content(body_text)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.send_message(msg)
            return True, None
        except Exception as exc:
            logger.warning("Failed to dispatch alert email to %s: %s", recipient, exc)
            return False, str(exc)

    async def dispatch(
        self,
        event_type: str,
        title: str,
        details: dict[str, Any],
        webhook_url: str | None = None,
        email_to: str | None = None,
    ) -> dict[str, Any]:
        """Dispatch both webhook and email for an alert event."""
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        payload = {
            "version": "1.0",
            "event_type": event_type,
            "title": title,
            "timestamp": now_iso,
            "details": details,
        }

        webhook_success, status_code, webhook_err = await self.send_webhook(
            payload, url=webhook_url
        )

        email_body = (
            f"PravahX Flood & Outburst Alert Notification\n"
            f"-----------------------------------------\n"
            f"Event: {event_type}\n"
            f"Title: {title}\n"
            f"Timestamp: {now_iso}\n\n"
            f"Details:\n{json.dumps(details, indent=2)}\n"
        )
        email_success, email_err = self.send_email(
            subject=title, body_text=email_body, to_address=email_to
        )

        return {
            "event_type": event_type,
            "title": title,
            "timestamp": now_iso,
            "webhook": {
                "attempted": bool(webhook_url or self.webhook_url),
                "success": webhook_success,
                "status_code": status_code,
                "error": webhook_err,
            },
            "email": {
                "attempted": bool(email_to or self.email_to),
                "success": email_success,
                "error": email_err,
            },
        }
