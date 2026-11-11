#include <stdint.h>
#include <stdlib.h>
#include "parse_core.h"
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    unsigned char raw[16], check[16]; char text[36];
    if (uuid_parse_core((const char *)data, size, raw) == 0) {
        uuid_format_core(raw, text, 1);
        if (uuid_parse_core(text, sizeof(text), check) || memcmp(raw, check, 16)) abort();
    }
    return 0;
}
