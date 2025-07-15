#include "sensing.h"
#include "config.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "sensing";

static int tipping_bucket_count = 0;

static void IRAM_ATTR tipping_bucket_isr(void *arg)
{
    tipping_bucket_count++;
}

void sensing_init(void)
{
    // TODO: configure ultrasonic sensor pins
    // configure tipping bucket GPIO as input with interrupt
    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << TIPPING_BUCKET_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .intr_type = GPIO_INTR_POSEDGE,
    };
    gpio_config(&io_conf);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(TIPPING_BUCKET_GPIO, tipping_bucket_isr, NULL);

    ESP_LOGI(TAG, "Sensing init done");
}

static int measure_ultrasonic_water_level_mm(void)
{
    // TODO: replace with real timing code
    // placeholder: 500mm
    return 500;
}

creek_reading_t sensing_take_reading(void)
{
    creek_reading_t r = {
        .water_level_mm = measure_ultrasonic_water_level_mm(),
        .bucket_tips = tipping_bucket_count,
    };
    // reset bucket count after reading
    tipping_bucket_count = 0;
    return r;
}
