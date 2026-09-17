#ifndef UUID7_GEN_H
#define UUID7_GEN_H

#include <stdint.h>

int generate_uuid7_bytes(unsigned char uuid[16]);
int generate_uuid7_bytes_for_timestamp(unsigned char uuid[16], uint64_t unix_ts_ms);
/* Independent random UUID: preserves unix_ts_ms, does not advance the counter. */
int generate_uuid7_at_bytes(unsigned char uuid[16], uint64_t unix_ts_ms);
int generate_uuid7_at_words(uint64_t *high, uint64_t *low, uint64_t unix_ts_ms);
int generate_uuid7_words(uint64_t *high, uint64_t *low);
void reset_uuid7_state(void);
int set_uuid7_state_for_tests(uint64_t timestamp_ms, uint64_t counter_value);

#define UUID7_MAX_TIMESTAMP UINT64_C(0xffffffffffff)
#define UUID7_TIMESTAMP_EXHAUSTED (-2)

#endif
