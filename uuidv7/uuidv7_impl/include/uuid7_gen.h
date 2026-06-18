#ifndef UUID7_GEN_H
#define UUID7_GEN_H

#include <stdint.h>

void generate_uuid7_bytes(unsigned char uuid[16]);
void generate_uuid7_bytes_for_timestamp(unsigned char uuid[16], uint64_t unix_ts_ms);
void generate_uuid7_words(uint64_t *high, uint64_t *low);
void reset_uuid7_state(void);

#endif
