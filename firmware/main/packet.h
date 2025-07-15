#pragma once
#include <stddef.h>
#include <stdint.h>
#include "sensing.h"

size_t packet_build_payload(uint8_t *buf, size_t max_len, const creek_reading_t *reading);
uint16_t packet_crc16(const uint8_t *data, size_t len);
