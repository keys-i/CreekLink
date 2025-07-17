# CreekLink Architecture

CreekLink is a scrappy, low-cost flood monitoring system I’m building as a personal project: a battery-powered ESP32 node on a creek bank, talking over LoRaWAN to a tiny Python backend with TimescaleDB.

The idea is pretty simple: **turn cheap hardware + long-range radio into something that actually helps people see what their local creek is doing**, without needing a full-blown $10k council gauge. There’s a heap of research on low-cost flood sensing and citizen-led monitoring, and CreekLink is my attempt to implement a small, realistic version of that.

---

## Why this exists (motivation + light research)

A few themes that pushed me into building this:

- **Floods are hyper–local.** A lot of official gauges are far apart. Papers on community flood sensors and “citizen hydrology” argue that local data (even if a bit noisy) is better than no data when creeks rise quickly in storms.
- **Low-power wireless is finally usable.** LoRaWAN appears over and over in flood and environmental monitoring case studies because it hits a sweet spot: low power, long range, unlicensed bands, and community networks like The Things Network.
- **Battery + deep sleep + small payloads = months of runtime.** A recurring result in embedded sensor research: if you sleep most of the time, keep payloads tiny, and avoid Wi-Fi, you can run for months or more on a small battery.

CreekLink is designed around those ideas: wake up briefly, measure creek level and rainfall, send a tiny 6-byte packet over LoRaWAN, go back to sleep, and dump everything into a time-series database.

---

## Big Picture

From the creek to the database:

1. **CreekLink Node (ESP32 + Ultrasonic + Tipping Bucket)**  
   - Wakes up from deep sleep.  
   - Measures water level using an ultrasonic sensor.  
   - Counts how many times a tipping bucket has tipped since last wake (rainfall).  
   - Packs that into a **6-byte binary payload with CRC**.  
   - Sends it out over LoRaWAN.  
   - Goes back to deep sleep.

2. **LoRaWAN Network Server (e.g. The Things Network)**  
   - Receives the radio frames.  
   - Runs a small payload decoder to turn bytes into `water_level_mm` and `bucket_tips`.  
   - POSTs a JSON webhook to the CreekLink backend.

3. **Backend (FastAPI + TimescaleDB)**  
   - Exposes `/uplink` as a webhook endpoint.  
   - Normalises the inbound JSON (TTN style), pulls out device ID and readings.  
   - Stores everything in a TimescaleDB hypertable.  
   - Runs a simple **threshold rule** and sends email alerts if water gets too high.

4. **Analysis / Visualisation (future)**  
   - Use Grafana / notebooks / CLI scripts on top of TimescaleDB to explore patterns, storm events, and see how well the ultrasonic sensor tracks real water levels.

---

## Repo Layout

Rough structure of the project:

```text
creeklink/
├── backend/
│   ├── docker-compose.yml      # optional: backend + TimescaleDB in containers
│   ├── requirements.txt
│   ├── creekingest/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app, /uplink, /health
│   │   ├── config.py           # env-based config (DB URL, alert thresholds, SMTP)
│   │   ├── db.py               # SQLAlchemy engine/session wiring
│   │   ├── models.py           # Reading model
│   │   ├── alerts.py           # threshold email alerts
│   │   └── examples/           # example webhook payloads + replay script
│   └── scripts/
│       └── init_db.sql         # TimescaleDB hypertable setup
├── firmware/
│   ├── CMakeLists.txt          # ESP-IDF project config
│   ├── sdkconfig
│   └── main/
│       ├── CMakeLists.txt
│       ├── main.c              # app_main, one-shot read + send + sleep
│       ├── sensing.c/.h        # ultrasonic + tipping bucket logic
│       ├── packet.c/.h         # payload packing + CRC
│       ├── lora_radio.c/.h     # LoRaWAN join/send abstraction
│       ├── power.c/.h          # deep sleep + wake reason
│       └── config.h            # pins, timing, keys
└── docs/
    ├── architecture.md         # this doc
    ├── power_budget.md         # notes on battery/runtime (to come)
    └── field_notes.md          # calibration + “what went wrong at the creek” log
````

---

## Firmware Architecture (ESP32 Node)

### Goals

* Be **boring and reliable**: one loop per wakeup, minimal dynamic state.
* Keep **power use low**: short wake time, deep sleep between readings, small LoRa payload.
* Make decoding trivial with a fixed binary format and CRC.

### Main Flow (`main.c`)

Each time the ESP32 wakes:

1. Log boot + wakeup cause (for debugging).
2. `sensing_init()` – set up ultrasonic pins and tipping bucket GPIO/interrupt.
3. `lora_radio_init()` – set up LoRaWAN stack and join network (stubbed at first).
4. `sensing_take_reading()` – returns a `creek_reading_t` struct.
5. `packet_build_payload()` – turns that into a 6-byte payload + CRC.
6. `lora_send()` – sends uplink.
7. `power_deep_sleep_for(SLEEP_SECONDS)` – goes back to deep sleep.

The idea is that **most complexity lives in separate modules**, so `main.c` reads cleanly as “read → pack → send → sleep”.

### Sensing (`sensing.c/.h`)

Responsible for all hardware sensor logic:

* **Ultrasonic water level**

  * Uses TRIG/ECHO pins to time the echo pulse.
  * Converts time-of-flight to distance.
  * Converts distance to **water level in mm** relative to the sensor mount height.
  * Real-world calibration (distance from sensor to creek bed, offsets, noise handling) will go into `field_notes.md`.

* **Tipping bucket (rainfall)**

  * Configures a GPIO with a rising-edge interrupt.
  * Inside the ISR, increments `tipping_bucket_count`.
  * On `sensing_take_reading()`, we snapshot the count and reset it.

Exports:

```c
typedef struct {
    int water_level_mm;
    int bucket_tips;
} creek_reading_t;
```

This struct is the payload “schema” for the rest of the firmware.

### Payload + CRC (`packet.c/.h`)

To keep LoRa airtime short and retain some robustness, the node sends a **tiny binary payload**:

| Byte(s) | Field          | Type   | Notes                                 |
| ------: | -------------- | ------ | ------------------------------------- |
|     0–1 | water_level_mm | uint16 | water level in mm (big-endian)        |
|     2–3 | bucket_tips    | uint16 | number of bucket tips since last send |
|     4–5 | crc            | uint16 | CRC16-CCITT over bytes 0–3            |

Researchy vibe: a bunch of low-power sensing deployments emphasise **small, fixed payloads** to minimise airtime (duty cycle limits) and power consumption. CreekLink follows that pattern.

The CRC is mainly to catch obvious corruption before acting on bad data.

### LoRaWAN abstraction (`lora_radio.c/.h`)

This module hides all the messy RF / LoRaWAN details:

* Frequency plan (e.g. AU915).
* Join mode (OTAA vs ABP).
* Data rates and spreading factors.

It exposes a super small API:

```c
void lora_radio_init(void);
esp_err_t lora_send(const uint8_t *data, size_t len);
```

Right now it’s stubbed out, but the goal is to plug in a real LoRaWAN stack here (ESP-IDF component, LMIC, or vendor-specific driver).

### Power (`power.c/.h`)

The power module centralises low-power behaviour:

* `power_print_wakeup_reason()` → log why we woke up (timer, reset, etc).
* `power_deep_sleep_for(seconds)` → set timer wake and enter deep sleep.

A lot of papers on battery-powered field nodes show that **duty cycle dominates battery life**: even “light” CPU work burns way more than sleep current. CreekLink’s strategy is basically “be asleep as much as possible”.

### Configuration (`config.h`)

Everything that might change between builds or deployments is kept here initially:

* GPIO pins for ultrasonic and tipping bucket.
* Sample interval and sleep duration.
* LoRaWAN keys and IDs.

Later, the noisy bits (keys, maybe intervals) can move into ESP-IDF Kconfig options.

---

## LoRaWAN & Payload Decoding

On the air, CreekLink sends that 6-byte payload. On the server side (e.g. The Things Network), a small **payload formatter** decodes it to something human-friendly.

Example decode logic (pseudocode):

```js
function decodeUplink(input) {
  const b = input.bytes;

  const water_level_mm = (b[0] << 8) | b[1];
  const bucket_tips    = (b[2] << 8) | b[3];
  const crc_rx         = (b[4] << 8) | b[5];

  // Optional CRC check
  // if (crc16_ccitt(b.slice(0, 4)) !== crc_rx) { ... }

  return {
    data: {
      water_level_mm,
      bucket_tips
    }
  };
}
```

The network server then forwards JSON like this to the backend:

```json
{
  "end_device_ids": { "device_id": "creeklink-node-01" },
  "uplink_message": {
    "decoded_payload": {
      "water_level_mm": 780,
      "bucket_tips": 2
    }
  }
}
```

---

## Backend Architecture (FastAPI + TimescaleDB)

The backend is a **small, opinionated ingest service**: it’s not a full “app”, just a reliable funnel from “webhook JSON” to “time-series DB + simple alerts”.

### API (`main.py`)

Endpoints:

* `GET /health`

  * For health checks: returns `{"status": "ok"}`.

* `POST /uplink`

  * Webhook endpoint for the LoRaWAN network server.
  * Expected JSON:

    * `end_device_ids.device_id` for the node ID.
    * `uplink_message.decoded_payload.water_level_mm`
    * `uplink_message.decoded_payload.bucket_tips`
  * Creates and stores a `Reading` row in the DB.
  * Triggers a threshold alert if the water level crosses the configured limit.

The logic is intentionally straightforward: validate basics, store raw payload too, and do the minimum necessary processing so we don’t lose anything that’s useful for later analysis.

### Config (`config.py`)

Uses Pydantic `BaseSettings` to map environment variables into a config object:

* `DATABASE_URL` – PostgreSQL/TimescaleDB connection string.
* `ALERT_WATER_LEVEL_MM_THRESHOLD` – when to start yelling via email.
* SMTP settings (`SMTP_HOST`, `SMTP_USER`, etc.) to actually send alerts.

Makes it easy to run locally or in Docker without editing code.

### Database (`db.py` + `models.py` + `init_db.sql`)

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS readings (
    id            BIGSERIAL PRIMARY KEY,
    received_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id     TEXT NOT NULL,
    water_level_mm INTEGER,
    bucket_tips    INTEGER,
    raw_payload    JSONB
);

SELECT create_hypertable('readings', 'received_at', if_not_exists => TRUE);
```

Why TimescaleDB?

* It’s basically Postgres with **time-series superpowers**, and there’s decent research + examples on using it for sensor data: hypertables, chunking, simple downsampling, retention policies.
* It plays nicely with tools like Grafana and Jupyter, which is perfect for a student project where you want to explore data as much as build a product.

Typical queries:

* Latest readings per node:

  ```sql
  SELECT DISTINCT ON (device_id)
         device_id, received_at, water_level_mm, bucket_tips
  FROM readings
  ORDER BY device_id, received_at DESC;
  ```

* A quick “storm event” view:

  ```sql
  SELECT time_bucket('5 minutes', received_at) AS bucket,
         avg(water_level_mm) AS avg_level,
         sum(bucket_tips) AS tips
  FROM readings
  WHERE received_at > now() - interval '24 hours'
  GROUP BY bucket
  ORDER BY bucket;
  ```

### Alerts (`alerts.py`)

A small helper that does:

* Check if `water_level_mm` exists and is above threshold.
* If SMTP is configured, send a basic text email with device ID, level, and threshold.

This is deliberately simple – more advanced rules (e.g. “level rising faster than X mm/min” or “notify only once every 30 mins”) can build on top.

### Examples & Testing (`examples/`)

* `ttn_uplink_example.json` – realistic TTN payload.
* `simple_uplink_example.json` – minimal JSON if you just want to poke the API.
* Optional `replay_examples.py` – Python script that POSTs the JSON files to `/uplink`, good for smoke testing before hooking up real LoRa.

---

## Deployment & Dev Workflow

### Local dev

1. Start TimescaleDB (Docker or local).

2. Run DB init script.

3. Start FastAPI with `uvicorn`:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

   export DATABASE_URL="postgresql://creeklink:creeklink_password@localhost:5432/creeklink"
   uvicorn creekingest.main:app --reload
   ```

4. Test:

   ```bash
   curl -s http://localhost:8000/health | jq
   python -m creekingest.examples.replay_examples
   ```

### Firmware dev loop

1. Edit firmware in `firmware/main/*.c`.

2. Build & flash:

   ```bash
   cd firmware
   idf.py build
   idf.py flash monitor
   ```

3. Verify log output (measured level, tips, payload length, deep sleep).

4. When LoRa is wired up, watch network server + backend logs while packets arrive.

---

## Where this is going

This is still a work-in-progress passion project. Some future directions:

* **Better calibration & validation.**
  Compare ultrasonic readings against manual staff gauge readings for a few storm events and log the errors in `field_notes.md`.

* **More nodes, more creeks.**
  Once the stack is solid, cloning nodes is mostly hardware: same firmware, different device IDs.

* **Smarter alerts.**
  Move beyond “above X mm” to “rising fast”, “threshold for Y minutes”, or “compare to typical level for this time of year”.

* **Nice dashboards.**
  Add a Grafana dashboard or small web frontend as the “public face” of the data, so the system isn’t just logs and SQL queries.

Under the hood, CreekLink is very much a **learning playground**: embedded C with ESP-IDF, low-power design, LoRaWAN, time-series databases, and basic backend/API work, all tied together by one simple question:

> “What’s my creek doing right now, and can I see it before it gets dangerous?”