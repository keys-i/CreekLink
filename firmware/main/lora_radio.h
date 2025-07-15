#pragma once
#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

void lora_radio_init(void);
esp_err_t lora_send(const uint8_t *data, size_t len);