"""Application configuration and environment settings.

This module defines the Settings class, which centralises configuration for
database connectivity and alerting behaviour. Values are loaded from
environment variables where available, falling back to sane defaults for
local development.
"""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime configuration loaded from environment variables.

    This model defines all configurable parameters for the CreekLink backend,
    including database connectivity and email alert behaviour.

    Attributes:
        database_url: PostgreSQL connection URL for the TimescaleDB instance.
        alert_email_from: Sender address used for outgoing alert emails.
        alert_email_to: Recipient address for high-water-level alerts.
        alert_water_level_mm_threshold: Water level threshold in millimetres
            that triggers an alert when reached or exceeded.
        smtp_host: SMTP server hostname used for sending emails, or None to
            disable email alerts.
        smtp_port: Port number for the SMTP server (typically 587 for TLS).
        smtp_user: Username for SMTP authentication, if required.
        smtp_password: Password for SMTP authentication, if required.
    """

    database_url: str = (
        "postgresql://creeklink:creeklink_password@db:5432/creeklink"
    )

    alert_email_from: str = "creeklink@example.com"
    alert_email_to: str = "you@example.com"
    alert_water_level_mm_threshold: int = 800  # 0.8m

    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


#: Singleton instance of :class:`Settings` used across the application.
settings = Settings()
