#include "lora_radio.h"
#include "esp_log.h"

static const char *TAG = "lora_radio";

void lora_radio_init(void)
{
    // TODO: init your LoRaWAN stack, join network, etc.
    ESP_LOGI(TAG, "LoRa radio init (stub)");
}

esp_err_t lora_send(const uint8_t *data, size_t len)
{
    // TODO: send via LoRaWAN library
    ESP_LOGI(TAG, "LoRa send (stub), len=%zu", len);
    return ESP_OK;
}