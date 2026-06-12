#include "uuid7_gen.h"

#include <stddef.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <time.h>
#include <unistd.h>
#if !defined(CLOCK_REALTIME)
#include <sys/time.h>
#endif
#endif

#define UUID7_COUNTER_MASK ((UINT64_C(1) << 42) - UINT64_C(1))
#define UUID7_COUNTER_LOW_MASK ((UINT64_C(1) << 30) - UINT64_C(1))

static uint64_t last_ms = 0;
static uint64_t counter = 0;
static uint64_t rng_state = 0;
static int initialized = 0;

static uint64_t current_time_ms(void) {
#ifdef _WIN32
    FILETIME ft;
    ULARGE_INTEGER uli;
    typedef VOID(WINAPI *GetSystemTimePreciseAsFileTimeFn)(LPFILETIME);
    static int resolved_precise_time = 0;
    static GetSystemTimePreciseAsFileTimeFn get_system_time_precise_as_file_time = NULL;

    if (!resolved_precise_time) {
        HMODULE kernel32 = GetModuleHandleA("kernel32.dll");
        if (kernel32 != NULL) {
            get_system_time_precise_as_file_time =
                (GetSystemTimePreciseAsFileTimeFn)GetProcAddress(
                    kernel32, "GetSystemTimePreciseAsFileTime"
                );
        }
        resolved_precise_time = 1;
    }

    if (get_system_time_precise_as_file_time != NULL) {
        get_system_time_precise_as_file_time(&ft);
    } else {
        GetSystemTimeAsFileTime(&ft);
    }

    uli.LowPart = ft.dwLowDateTime;
    uli.HighPart = ft.dwHighDateTime;
    return (uli.QuadPart - UINT64_C(116444736000000000)) / UINT64_C(10000);
#else
#ifdef CLOCK_REALTIME
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (uint64_t)ts.tv_sec * UINT64_C(1000) + (uint64_t)(ts.tv_nsec / 1000000);
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (uint64_t)tv.tv_sec * UINT64_C(1000) + (uint64_t)(tv.tv_usec / 1000);
#endif
#endif
}

static uint64_t seed_value(void) {
    uint64_t seed = current_time_ms();
    seed ^= (uint64_t)(uintptr_t)&seed;
    seed ^= (uint64_t)(uintptr_t)&last_ms << 17;
#ifdef _WIN32
    seed ^= (uint64_t)GetCurrentProcessId() << 32;
#else
    seed ^= (uint64_t)getpid() << 32;
#endif
    return seed ? seed : UINT64_C(0x9e3779b97f4a7c15);
}

static uint64_t random_u64(void) {
    uint64_t x;

    if (rng_state == 0) {
        rng_state = seed_value();
    }

    x = rng_state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    rng_state = x;
    return x * UINT64_C(2685821657736338717);
}

static uint64_t next_counter_start(void) {
    return random_u64() & UUID7_COUNTER_MASK;
}

void reset_uuid7_state(void) {
    last_ms = 0;
    counter = 0;
    rng_state = 0;
    initialized = 0;
}

void generate_uuid7_bytes_for_timestamp(unsigned char uuid[16], uint64_t unix_ts_ms) {
    uint64_t timestamp_ms = unix_ts_ms;
    uint64_t rand_b;
    uint32_t random_tail;
    uint16_t rand_a;

    if (!initialized) {
        rng_state = seed_value();
        counter = next_counter_start();
        initialized = 1;
    }

    if (timestamp_ms > last_ms) {
        last_ms = timestamp_ms;
        counter = next_counter_start();
    } else {
        timestamp_ms = last_ms;
        counter = (counter + 1) & UUID7_COUNTER_MASK;
        if (counter == 0) {
            last_ms += 1;
            timestamp_ms = last_ms;
            counter = next_counter_start();
        }
    }

    random_tail = (uint32_t)random_u64();
    rand_a = (uint16_t)((counter >> 30) & UINT64_C(0x0fff));
    rand_b = ((counter & UUID7_COUNTER_LOW_MASK) << 32) | (uint64_t)random_tail;

    uuid[0] = (unsigned char)(timestamp_ms >> 40);
    uuid[1] = (unsigned char)(timestamp_ms >> 32);
    uuid[2] = (unsigned char)(timestamp_ms >> 24);
    uuid[3] = (unsigned char)(timestamp_ms >> 16);
    uuid[4] = (unsigned char)(timestamp_ms >> 8);
    uuid[5] = (unsigned char)timestamp_ms;
    uuid[6] = (unsigned char)(0x70 | (rand_a >> 8));
    uuid[7] = (unsigned char)rand_a;
    uuid[8] = (unsigned char)(0x80 | ((rand_b >> 56) & 0x3f));
    uuid[9] = (unsigned char)(rand_b >> 48);
    uuid[10] = (unsigned char)(rand_b >> 40);
    uuid[11] = (unsigned char)(rand_b >> 32);
    uuid[12] = (unsigned char)(rand_b >> 24);
    uuid[13] = (unsigned char)(rand_b >> 16);
    uuid[14] = (unsigned char)(rand_b >> 8);
    uuid[15] = (unsigned char)rand_b;
}

void generate_uuid7_bytes(unsigned char uuid[16]) {
    generate_uuid7_bytes_for_timestamp(uuid, current_time_ms());
}
