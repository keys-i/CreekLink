#pragma once

// GPIO pins
#define ULTRASONIC_TRIG_GPIO   4
#define ULTRASONIC_ECHO_GPIO   5
#define TIPPING_BUCKET_GPIO    18

// Timing (ms)
#define MEASUREMENT_INTERVAL_MS  60000   // measure every 60s before sleep
#define SLEEP_SECONDS            300     // deep sleep for 5 mins

// LoRa / app config (i might move this to Kconfig/menuconfig)
#define LORA_APP_EUI   "0000000000000000"
#define LORA_DEV_EUI   "0011223344556677"
#define LORA_APP_KEY   "00112233445566778899AABBCCDDEEFF"