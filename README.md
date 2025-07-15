# CreekLink – Low-Cost LoRaWAN Flood Node

CreekLink is a low-cost, battery-powered flood monitoring node built on ESP32 and LoRaWAN.  
It reads an ultrasonic water-level sensor and a tipping bucket rain gauge, then periodically
uploads data over The Things Network (TTN) to a Python backend that stores time-series data in
TimescaleDB and sends simple threshold-based email alerts.

## Features

- **Water-level + rainfall sensing**  
  Ultrasonic water-level measurement + tipping bucket pulse input.

- **Low-power design**  
  Deep-sleep duty cycling tuned for long battery life.

- **LoRaWAN connectivity**  
  Uplinks sensor packets to The Things Network.

- **ESP-IDF firmware in C**  
  Separate tasks for sensing, packet construction, and radio send, with CRC for payload integrity.

- **Time-series backend**  
  Python service that ingests data into TimescaleDB and triggers email alerts when thresholds are breached.
