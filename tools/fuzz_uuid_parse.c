/* Shared production parser: libFuzzer, or deterministic sanitizer smoke. */
#include <stdint.h>
#include <stdlib.h>
#include "uuid_parse.h"

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    unsigned char raw[16], check[16];
    char text[36];
    static const char hex[] = "0123456789abcdef";
    if (uuid_parse_core((const char *)data, size, raw) == 0) {
        size_t j = 0;
        for (size_t i = 0; i < 16; i++) {
            if (i == 4 || i == 6 || i == 8 || i == 10) text[j++] = '-';
            text[j++] = hex[raw[i] >> 4];
            text[j++] = hex[raw[i] & 15];
        }
        if (uuid_parse_core(text, sizeof(text), check) || memcmp(raw, check, 16)) abort();
    }
    return 0;
}

#ifdef UUID_PARSE_STANDALONE
int main(void) {
    uint32_t state = 9562;
    uint8_t data[80];
    static const char seed[] = "URN:UUID:00112233-4455-6677-8899-aabbccddeeff";
    for (size_t n = 0; n < 200000; n++) {
        size_t size = n % 80;
        for (size_t i = 0; i < size; i++) {
            state ^= state << 13; state ^= state >> 17; state ^= state << 5;
            data[i] = (uint8_t)state;
        }
        if (n % 2 == 0) {
            size = sizeof(seed) - 1;
            memcpy(data, seed, size);
            if (n % 4 == 0) data[n % size] = (uint8_t)state;
        }
        LLVMFuzzerTestOneInput(data, size);
    }
    return 0;
}
#endif
