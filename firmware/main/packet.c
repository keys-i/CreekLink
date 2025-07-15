#include "packet.h"

static uint16_t crc16_ccitt(uint16_t crc, uint8_t data)
{
    crc ^= data << 8;
    for (int i = 0; i < 8; i++) {
        if (crc & 0x8000)
            crc = (crc << 1) ^ 0x1021;
        else
            crc <<= 1;
    }
    return crc;
}

uint16_t packet_crc16(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc = crc16_ccitt(crc, data[i]);
    }
    return crc;
}

size_t packet_build_payload(uint8_t *buf, size_t max_len, const creek_reading_t *reading)
{
    if (max_len < 6) return 0;

    // Example payload:
    // [0-1] water_level_mm (uint16)
    // [2-3] bucket_tips    (uint16)
    // [4-5] CRC16 of bytes 0-3
    buf[0] = (reading->water_level_mm >> 8) & 0xFF;
    buf[1] = (reading->water_level_mm) & 0xFF;
    buf[2] = (reading->bucket_tips >> 8) & 0xFF;
    buf[3] = (reading->bucket_tips) & 0xFF;

    uint16_t crc = packet_crc16(buf, 4);
    buf[4] = (crc >> 8) & 0xFF;
    buf[5] = crc & 0xFF;

    return 6;
}
