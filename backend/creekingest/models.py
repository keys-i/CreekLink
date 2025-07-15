"""Database models for sensor readings ingested by the CreekLink backend."""

from __future__ import annotations

from sqlalchemy import JSON, DateTime, BigInteger, Column, Integer, Text, text

from .db import Base


class Reading(Base):
    """A single reading from a CreekLink flood node.

    Represents one payload received from a device, including water level,
    tipping-bucket count, and the raw decoded payload.
    """

    __tablename__ = "readings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    received_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    device_id = Column(Text, nullable=False)
    water_level_mm = Column(Integer, nullable=True)
    bucket_tips = Column(Integer, nullable=True)
    raw_payload = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        """Return a concise string representation of the reading."""
        return (
            f"<Reading id={self.id} device_id={self.device_id!r} "
            f"water_level_mm={self.water_level_mm} bucket_tips={self.bucket_tips}>"
        )
