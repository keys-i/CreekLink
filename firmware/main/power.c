#include "power.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_system.h"

static const char *TAG = "power";

void power_print_wakeup_reason(void)
{
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    ESP_LOGI(TAG, "Wakeup cause: %d", cause);
}

void power_deep_sleep_for(uint32_t seconds)
{
    ESP_LOGI(TAG, "Deep sleeping for %u seconds", (unsigned)seconds);
    esp_sleep_enable_timer_wakeup((uint64_t)seconds * 1000000ULL);
    esp_deep_sleep_start();
}
