#include "uuid7_gen.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

// Function to generate a UUIDv7
void generate_uuid7(char *uuid) {
    static int seeded = 0;
    if (!seeded) {
        srand(time(NULL));
        seeded = 1;
    }
    
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);

    // Get current time in milliseconds
    uint64_t time_ms = ts.tv_sec * 1000 + ts.tv_nsec / 1000000;

    // Random part for the UUID
    uint16_t rand_a = rand() & 0xFFFF;
    uint16_t rand_b = rand() & 0xFFFF;
    uint16_t rand_c = rand() & 0xFFFF;
    uint16_t rand_d = rand() & 0xFFFF;
    uint16_t rand_e = rand() & 0xFFFF;

    // Compile UUIDv7 string (format: 8-4-4-4-12 hex digits)
    snprintf(uuid, 37, "%08llx-%04llx-%04x-%04x-%04x%04x%04x",
            (unsigned long long)(time_ms >> 28), // higher timestamp part
            (unsigned long long)((time_ms >> 12) & 0xFFFF), // lower timestamp part
            (rand_a & 0x0FFF) | 0x7000, // adjust version field to v7
            (rand_b & 0x3FFF) | 0x8000, // adjust variant
            rand_c,
            rand_d,
            rand_e);
}