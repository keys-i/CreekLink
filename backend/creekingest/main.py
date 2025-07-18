"""FastAPI application for ingesting CreekLink node readings."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from creekingest.alerts import send_threshold_alert
from creekingest.db import Base, engine, get_db
from creekingest.models import Reading

# Create tables on startup (Simple deployment)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CreekLink Ingest API", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, str]:
    """Return a simple health check status."""
    return {"status": "running"}


@app.post("/uplink")
async def uplink(
    request: Request, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Handle uplink webhooks from the LoRaWAN network server.

    Expects JSON containing a device identifier and a decoded payload. The
    payload is stored as a Reading row, and a simple threshold alert is
    triggered if the water level exceeds the configured limit.
    """
    try:
        payload: Dict[str, Any] = await request.json()
    except (
        Exception
    ) as exc:  # noqa: PERF203 - broad to normalise client errors
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    # Extract device_id (supports TTN-style payloads and a fallback field)
    device_id = (
        payload.get("end_device_ids", {}).get("device_id")
        or payload.get("device_id")
        or "unknown-device"
    )

    # Extract decoded payload (TTN-style structure)
    decoded = payload.get("uplink_message", {}).get("decoded_payload", {})

    water_level_mm = decoded.get("water_level_mm")
    bucket_tips = decoded.get("bucket_tips")

    reading = Reading(
        device_id=device_id,
        water_level_mm=water_level_mm,
        bucket_tips=bucket_tips,
        raw_payload=payload,
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Run simple threshold alert
    send_threshold_alert(device_id, water_level_mm)

    return {"status": "stored", "device_id": device_id}
