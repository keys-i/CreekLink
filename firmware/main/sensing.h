#pragma once

typedef struct {
    int water_level_mm;
    int bucket_tips;
} creek_reading_t;

void sensing_init(void);
creek_reading_t sensing_take_reading(void);