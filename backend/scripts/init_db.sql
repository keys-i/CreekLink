-- setting up the initial database schema
CREATE TABLE IF NOT EXISTS readings (
    id              BIGSERIAL PRIMARY KEY,
    recieved_set    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id       TEXT NOT NULL,
    water_level_mm  INTEGER,                -- from Ultrasonic sensor
    bucket_tips     INTEGER,                -- count per reading
    raw_payload     JSONB                   -- full decoded payload
)

SELECT create_hypertable('readings', 'received_at', if_not_exists => TRUE);

-- run this with:
-- docker exec -it creeklink_db psql -U creeklink -d creeklink -f /scripts/init_db.sql