#include "uuid7_gen.h"

#include <errno.h>
#include <stddef.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#else
#include <fcntl.h>
#include <time.h>
#include <unistd.h>
#if !defined(CLOCK_REALTIME)
#include <sys/time.h>
#endif
#endif

#define UUID7_COUNTER_MASK ((UINT64_C(1) << 42) - UINT64_C(1))
#define UUID7_COUNTER_LOW_MASK ((UINT64_C(1) << 30) - UINT64_C(1))
#define UUID7_ENTROPY_POOL_SIZE 4096

static uint64_t last_ms = 0;
static uint64_t counter = 0;
static uint64_t process_id = 0;
static int initialized = 0;
static unsigned char entropy_pool[UUID7_ENTROPY_POOL_SIZE];
static size_t entropy_offset = UUID7_ENTROPY_POOL_SIZE;
#ifndef _WIN32
static int urandom_fd = -1;
#endif

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

static uint64_t current_process_id(void) {
#ifdef _WIN32
    return (uint64_t)GetCurrentProcessId();
#else
    return (uint64_t)getpid();
#endif
}

static void reset_process_state(uint64_t new_process_id) {
    last_ms = 0;
    counter = 0;
    initialized = 0;
    process_id = new_process_id;
    entropy_offset = UUID7_ENTROPY_POOL_SIZE;
    memset(entropy_pool, 0, sizeof(entropy_pool));
}

static void ensure_current_process(void) {
    uint64_t current_id = current_process_id();

    if (process_id != current_id) {
        reset_process_state(current_id);
    }
}

static int refill_entropy_pool(void) {
#ifdef _WIN32
    NTSTATUS status = BCryptGenRandom(
        NULL,
        entropy_pool,
        (ULONG)sizeof(entropy_pool),
        BCRYPT_USE_SYSTEM_PREFERRED_RNG
    );

    if (status < 0) {
        return -1;
    }
#else
    size_t filled = 0;

    if (urandom_fd < 0) {
        int flags = O_RDONLY;
#ifdef O_CLOEXEC
        flags |= O_CLOEXEC;
#endif
        do {
            urandom_fd = open("/dev/urandom", flags);
        } while (urandom_fd < 0 && errno == EINTR);

        if (urandom_fd < 0) {
            return -1;
        }
    }

    while (filled < sizeof(entropy_pool)) {
        ssize_t result = read(
            urandom_fd,
            entropy_pool + filled,
            sizeof(entropy_pool) - filled
        );

        if (result > 0) {
            filled += (size_t)result;
            continue;
        }
        if (result < 0 && errno == EINTR) {
            continue;
        }
        return -1;
    }
#endif

    entropy_offset = 0;
    return 0;
}

static int secure_random_u64(uint64_t *value) {
    if (entropy_offset + sizeof(*value) > sizeof(entropy_pool)) {
        if (refill_entropy_pool() < 0) {
            return -1;
        }
    }

    memcpy(value, entropy_pool + entropy_offset, sizeof(*value));
    entropy_offset += sizeof(*value);
    return 0;
}

static int next_counter_start(uint64_t *counter_start) {
    uint64_t random_value;

    if (secure_random_u64(&random_value) < 0) {
        return -1;
    }
    *counter_start = random_value & UUID7_COUNTER_MASK;
    return 0;
}

void reset_uuid7_state(void) {
    reset_process_state(current_process_id());
}

static void write_uuid7_words(unsigned char uuid[16], uint64_t high, uint64_t low) {
    uuid[0] = (unsigned char)(high >> 56);
    uuid[1] = (unsigned char)(high >> 48);
    uuid[2] = (unsigned char)(high >> 40);
    uuid[3] = (unsigned char)(high >> 32);
    uuid[4] = (unsigned char)(high >> 24);
    uuid[5] = (unsigned char)(high >> 16);
    uuid[6] = (unsigned char)(high >> 8);
    uuid[7] = (unsigned char)high;
    uuid[8] = (unsigned char)(low >> 56);
    uuid[9] = (unsigned char)(low >> 48);
    uuid[10] = (unsigned char)(low >> 40);
    uuid[11] = (unsigned char)(low >> 32);
    uuid[12] = (unsigned char)(low >> 24);
    uuid[13] = (unsigned char)(low >> 16);
    uuid[14] = (unsigned char)(low >> 8);
    uuid[15] = (unsigned char)low;
}

static int generate_uuid7_words_for_timestamp(
    uint64_t *high,
    uint64_t *low,
    uint64_t unix_ts_ms
) {
    uint64_t timestamp_ms = unix_ts_ms;
    uint64_t rand_b;
    uint64_t random_value;
    uint32_t random_tail;
    uint16_t rand_a;

    ensure_current_process();

    if (!initialized) {
        if (next_counter_start(&counter) < 0) {
            return -1;
        }
        initialized = 1;
    }

    if (timestamp_ms > last_ms) {
        last_ms = timestamp_ms;
        if (next_counter_start(&counter) < 0) {
            return -1;
        }
    } else {
        timestamp_ms = last_ms;
        counter = (counter + 1) & UUID7_COUNTER_MASK;
        if (counter == 0) {
            last_ms += 1;
            timestamp_ms = last_ms;
            if (next_counter_start(&counter) < 0) {
                return -1;
            }
        }
    }

    if (secure_random_u64(&random_value) < 0) {
        return -1;
    }
    random_tail = (uint32_t)random_value;
    rand_a = (uint16_t)((counter >> 30) & UINT64_C(0x0fff));
    rand_b = ((counter & UUID7_COUNTER_LOW_MASK) << 32) | (uint64_t)random_tail;

    *high = (timestamp_ms << 16) | (UINT64_C(0x7000) | (uint64_t)rand_a);
    *low = UINT64_C(0x8000000000000000) | rand_b;
    return 0;
}

int generate_uuid7_bytes_for_timestamp(unsigned char uuid[16], uint64_t unix_ts_ms) {
    uint64_t high;
    uint64_t low;

    if (generate_uuid7_words_for_timestamp(&high, &low, unix_ts_ms) < 0) {
        return -1;
    }
    write_uuid7_words(uuid, high, low);
    return 0;
}

int generate_uuid7_bytes(unsigned char uuid[16]) {
    uint64_t high;
    uint64_t low;

    if (generate_uuid7_words_for_timestamp(&high, &low, current_time_ms()) < 0) {
        return -1;
    }
    write_uuid7_words(uuid, high, low);
    return 0;
}

int generate_uuid7_words(uint64_t *high, uint64_t *low) {
    return generate_uuid7_words_for_timestamp(high, low, current_time_ms());
}
