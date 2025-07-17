# CreekLink Power Budget (Rough + Honest)

This is a working power budget for the CreekLink flood node. It’s not meant to be perfect lab-grade data — it’s a “back of the notebook” estimate to check if the design is vaguely sane.

The main question:

> If I run an ESP32 + ultrasonic sensor + LoRa radio on a small battery, **do I get weeks, months, or just sadness?**

Short answer: with deep sleep and short wake times, months is realistic. This doc shows the assumptions and maths.

---

## Hardware Assumptions (v1)

These are ballpark numbers pulled from common ESP32 + LoRa + ultrasonic setups and datasheets. When I get real measurements (USB power meter, multimeter), I’ll replace them.

**Core bits:**

- MCU: ESP32 (Wi-Fi/BLE SoC, using ESP-IDF).
- Radio: LoRa transceiver (integrated module or external like SX127x).
- Level sensor: 5V or 3.3V ultrasonic HC-SR04-style, or low-power equivalent.
- Rain sensor: tipping bucket with reed switch (basically no power).
- Battery: 1 × 18650 Li-ion, say **2500 mAh** usable.

**Current estimates:**

| Mode                            | Current (approx) |
|---------------------------------|------------------|
| Deep sleep (ESP32 only)         | 20–100 µA        |
| Active, no radio TX             | ~80 mA           |
| Radio TX (LoRa uplink)          | 120–150 mA       |
| Ultrasonic measuring (short)    | 10–20 mA         |

I’ll use **conservative-ish** numbers so estimates aren’t over-optimistic.

---

## Operating Pattern

CreekLink is designed to be asleep most of the time.

### Basic duty cycle

For first version:

- **Wake every 5 minutes** (`SLEEP_SECONDS = 300`).
- On each wake:
  - Boot, log wakeup (ESP32 start-up).
  - Take one ultrasonic reading.
  - Read tipping bucket count.
  - Build a 6-byte payload.
  - Send one LoRa uplink.
  - Go back to deep sleep.

The whole **awake time per cycle** is roughly:

- Sensor measure + logic + radio join (if already joined) + TX: **~2 seconds**  
  (Later I’ll measure this properly from boot to `esp_deep_sleep_start()`.)

So per 5-minute cycle:

- Deep sleep: ~298 seconds  
- Awake: ~2 seconds

This gives a **duty cycle** of:  
`awake_fraction ≈ 2 / 300 ≈ 0.0067` → 0.67% awake, 99.33% asleep.

---

## Energy Math: One 5-Minute Cycle

Let’s split the 2 seconds of “awake” into sub-phases:

- 0.5 s MCU active + ultrasonic measurement (no TX): **80 mA**
- 0.5 s radio TX: **150 mA**
- 1.0 s general logic/overhead: **80 mA**

(This is rough; it just gives a shape for power distribution.)

### mAh per phase

Convert seconds → hours: divide by 3600.

#### Ultrasonic + active (no TX)

- Time: 1.5 s total at 80 mA (0.5 + 1.0)
- Time in hours: `1.5 / 3600 ≈ 0.000417 h`
- Charge: `80 mA × 0.000417 h ≈ 0.033 mAh`

#### Radio TX

- Time: 0.5 s at 150 mA
- Time in hours: `0.5 / 3600 ≈ 0.000139 h`
- Charge: `150 mA × 0.000139 h ≈ 0.0208 mAh`

#### Total awake per cycle

`0.033 mAh + 0.0208 mAh ≈ 0.054 mAh` per 5-minute cycle while awake.

### Deep sleep per cycle

Assume **60 µA = 0.06 mA** deep sleep current (ESP32 + board overhead).

- Time in sleep per cycle: 298 s  
  `298 / 3600 ≈ 0.0828 h`
- Charge: `0.06 mA × 0.0828 h ≈ 0.0050 mAh`

### Grand total per 5-minute cycle

- Awake: ~0.054 mAh  
- Deep sleep: ~0.005 mAh  
- **Total ≈ 0.059 mAh per 5-minute cycle**

---

## Daily Consumption

There are **12 cycles per hour × 24 hours = 288 cycles per day**.

- Per cycle: ~0.059 mAh  
- Per day: `0.059 mAh × 288 ≈ 17.0 mAh/day`

So at this duty cycle, the node uses **~17 mAh per day** (on these assumptions).

---

## Battery Life Estimate (Single 18650)

Assume:

- 1 × 18650 Li-ion cell
- Rated capacity: 2500 mAh
- Realistic usable capacity (derating for cold, age, etc): say 2000 mAh

### Runtime estimate

`runtime_days ≈ usable_mAh / daily_mAh`

- `runtime_days ≈ 2000 mAh / 17 mAh/day ≈ 117.6 days`

So **roughly ~4 months** of runtime on one 18650 cell at a 5-minute interval, if assumptions hold.

If everything is more efficient than these conservative numbers, 5+ months is plausible. If there’s more overhead (e.g. bad deep sleep current, Wi-Fi accidentally left on), it’ll be less.

---

## How It Changes With Sample Interval

The biggest knob we have is **how often we wake up**.

Assume awake energy per cycle stays ~0.054 mAh and sleep current is negligible compared to that (which is increasingly true as interval shrinks).

### 1-minute interval (storm mode)

- Interval: 60 s  
- Cycles per day: `24 × 60 = 1440`
- Daily consumption: `0.054 mAh × 1440 ≈ 77.8 mAh/day` (plus a bit of sleep)

Battery life:

- `2000 mAh / 78 mAh/day ≈ 25.6 days`

So at **1-minute resolution**, we’re talking roughly **3–4 weeks** runtime on a single 18650.

### 10-minute interval

- Interval: 600 s  
- Cycles per day: `24 × 6 = 144`
- Daily: `0.054 mAh × 144 ≈ 7.8 mAh/day` (+ sleep)

Battery life:

- `2000 / 7.8 ≈ 256 days` → **~8.5 months**

### Summary table

Using the same assumptions:

| Interval | Cycles/day | Approx daily draw | Approx runtime (2000 mAh) |
|----------|-----------:|------------------:|---------------------------:|
| 1 min    | 1440       | ~78 mAh/day       | ~25 days                   |
| 5 min    | 288        | ~17 mAh/day       | ~118 days                  |
| 10 min   | 144        | ~8 mAh/day        | ~256 days                  |

This is why a lot of field sensor deployments choose **5–15 minute intervals** for “normal operation”, and only go faster during events.

---

## Research-ish Takeaways

These rough numbers line up with what low-power sensing papers keep saying:

- **Sleep dominates.** If you can keep your **awake time short and predictable**, most of your energy budget is just a tiny sleep current times a long duration.
- **Radio TX is expensive but short.** LoRa TX is “spiky” — high current but very short airtime. Keeping payloads small and avoiding re-transmissions matters.
- **Sampling rate is a policy choice.** There’s always a trade-off between resolution (1-minute samples are nice for hydro nerds) and battery life. A lot of deployments compromise at 5–15 minutes.

CreekLink aims for a **“default 5-minute interval”**, which is a decent balance for a hobby node: enough resolution to see storm behaviour but still giving months of runtime.

---

## What I Still Need to Measure

Right now, these numbers are educated guesses. To tighten them up, I want to:

- Measure **real deep sleep current**  
  Using a USB power meter or current-sense resistor to see what the ESP32 + LoRa module + regulator actually pull in deep sleep.

- Measure **boot-to-sleep time**  
  Time from wake to `esp_deep_sleep_start()` with real LoRa TX included. Log this and combine with current to get more accurate awake mAh per cycle.

- Log **battery voltage over time**  
  If I add a voltage divider to an ADC pin, I can see how quickly the battery drains in the field and compare it to the estimates here.

Once I have real measurements, I’ll update this doc with “measured” vs “estimated” and maybe add graphs.

---

## TL;DR

- With a 5-minute wake interval, CreekLink should be able to run on a single 18650 cell for roughly **4 months** (ballpark).
- If I want more resolution during storms, I can temporarily drop to 1-minute intervals and still get a few weeks.
- As long as the firmware sticks to **“wake → read → send → sleep”** and LoRaWAN works without lots of retries, the power story looks good enough to deploy a prototype at an actual creek without babying it every week.
