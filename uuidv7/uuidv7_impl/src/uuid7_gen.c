#include "uuid7_gen.h"

// Function to generate a UUIDv7
void generate_uuid7(char *uuid) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);

    // Get current time in milliseconds
    uint64_t time_ms = ts.tv_sec * 1000 + ts.tv_nsec / 1000000;

    // Random part for the UUID
    uint16_t rand_a = rand() & 0xFFFF;
    uint16_t rand_b = rand() & 0xFFFF;
    uint16_t rand_c = rand() & 0xFFFF;

    // Compile UUIDv7 string
    snprintf(uuid, 37, "%08lx-%04lx-%04x-%04x-%08x",
            time_ms >> 28, // higher timestamp part
            (time_ms >> 12) & 0xFFFF, // lower timestamp part
            rand_a & 0x0FFF | 0x7000, // adjust version field to v7
            rand_b & 0x3FFF | 0x8000, // adjust variant
            rand_c);
}