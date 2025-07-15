#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_sleep.h"

#include "config.h"
#include "sensing.h"
#include "packet.h"
#include "lora_radio.h"
#include "power.h"

static const char *TAG = "creeklink_main";

void app_main(void)
{
    ESP_LOGI(TAG, "Booting CreekLink flood node");

    power_print_wakeup_reason();

    // Init subsystems
    sensing_init();
    lora_radio_init();

    // For a first cut, just do one measurement + send + sleep
    creek_reading_t reading = sensing_take_reading();
    ESP_LOGI(TAG, "Measured water_level_mm=%d, bucket_tips=%d",
             reading.water_level_mm, reading.bucket_tips);

    uint8_t payload[16];
    size_t payload_len = packet_build_payload(payload, sizeof(payload), &reading);
    ESP_LOGI(TAG, "Built payload len=%zu", payload_len);

    if (lora_send(payload, payload_len) == ESP_OK) {
        ESP_LOGI(TAG, "LoRa send OK, going to deep sleep");
    } else {
        ESP_LOGW(TAG, "LoRa send failed, still going to deep sleep");
    }

    power_deep_sleep_for(SLEEP_SECONDS);
}
