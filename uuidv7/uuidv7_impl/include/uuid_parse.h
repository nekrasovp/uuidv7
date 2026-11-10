#ifndef FASTUUID7_PARSE_H
#define FASTUUID7_PARSE_H
#include <stddef.h>
#include <string.h>

/* 255 marks every non-hex byte, including NUL and non-ASCII. Index only
 * through unsigned char: the standalone fuzzer also supplies arbitrary bytes. */
static const unsigned char uuid_hex_value[256] = {
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 255, 255, 255, 255, 255, 255,
    255, 10, 11, 12, 13, 14, 15, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 10, 11, 12, 13, 14, 15, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
};

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
    unsigned int invalid = 0;
#define UUID_DECODE_PAIR(target, source) do { \
        unsigned int a = uuid_hex_value[(unsigned char)s[(source)]]; \
        unsigned int b = uuid_hex_value[(unsigned char)s[(source) + 1]]; \
        invalid |= a | b; \
        out[(target)] = (unsigned char)((a << 4) | b); \
    } while (0)
    if (n == 36) {
        if (s[8] != '-' || s[13] != '-' || s[18] != '-' || s[23] != '-') return -1;
        UUID_DECODE_PAIR(0, 0);
        UUID_DECODE_PAIR(1, 2);
        UUID_DECODE_PAIR(2, 4);
        UUID_DECODE_PAIR(3, 6);
        UUID_DECODE_PAIR(4, 9);
        UUID_DECODE_PAIR(5, 11);
        UUID_DECODE_PAIR(6, 14);
        UUID_DECODE_PAIR(7, 16);
        UUID_DECODE_PAIR(8, 19);
        UUID_DECODE_PAIR(9, 21);
        UUID_DECODE_PAIR(10, 24);
        UUID_DECODE_PAIR(11, 26);
        UUID_DECODE_PAIR(12, 28);
        UUID_DECODE_PAIR(13, 30);
        UUID_DECODE_PAIR(14, 32);
        UUID_DECODE_PAIR(15, 34);
    } else {
        for (size_t i = 0; i < 16; i++) UUID_DECODE_PAIR(i, 2 * i);
    }
#undef UUID_DECODE_PAIR
    /* The caller must discard out on error, just as for an early rejection. */
    return (invalid & 0xf0) ? -1 : 0;
}
#endif
