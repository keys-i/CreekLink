"""Email-based alerting utilities for CreekLink."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Optional

from creekingest.config import settings

def send_threshold_alert(device_id: str, water_level_mm: Optional[int]) -> None:
    """
    Send an email alert if the water level exceeds the configured threshold.

    The alert is only sent when a valid water level is provided, it meets or
    exceeds the configured threshold, and SMTP settings are fully configured.
    """
    if water_level_mm is None:
        return

    if water_level_mm < settings.alert_water_level_mm_threshold:
        return

    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        # Alerts disabled / not configured
        return

    msg = EmailMessage()
    msg["Subject"] = f"[CreekLink] High Water Level Alert for Device {device_id}"
    msg["From"] = settings.alert_email_from
    msg["To"] = settings.alert_email_to

    msg.set_content(
        (
            f"High water level detected.\n\n"
            f"Device: {device_id}\n"
            f"Water level: {water_level_mm} mm\n"
            f"Threshold: {settings.alert_water_level_mm_threshold} mm\n"
        )
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
