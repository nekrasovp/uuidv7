#ifndef FASTUUID7_PARSE_H
#define FASTUUID7_PARSE_H
#include <stddef.h>
#include <string.h>

static int uuid_nibble(unsigned char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

/* Strict, length-bounded ASCII grammar. No NUL termination is required. */
static int uuid_parse_core(const char *s, size_t n, unsigned char out[16]) {
    if (n == 45) {
        static const char prefix[] = "urn:uuid:";
        for (size_t i = 0; i < 9; i++) {
            unsigned char c = (unsigned char)s[i];
            if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
            if (c != (unsigned char)prefix[i]) return -1;
        }
        s += 9;
        n -= 9;
    } else if (n == 38 && s[0] == '{' && s[37] == '}') {
        s++;
        n -= 2;
    }
    if (n != 32 && n != 36) return -1;
    size_t j = 0;
    for (size_t i = 0; i < 16; i++) {
        if (n == 36 && (i == 4 || i == 6 || i == 8 || i == 10)) {
            if (s[j++] != '-') return -1;
        }
        int a = uuid_nibble((unsigned char)s[j++]);
        int b = uuid_nibble((unsigned char)s[j++]);
        if (a < 0 || b < 0) return -1;
        out[i] = (unsigned char)((a << 4) | b);
    }
    return 0;
}
#endif
