#ifndef UUID_LAB_PARSE_CORE_H
#define UUID_LAB_PARSE_CORE_H
#include <stddef.h>
#include <string.h>
static int uuid_nibble(unsigned char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static int uuid_parse_core(const char *s, size_t n, unsigned char out[16]) {
    if (n == 45 && memcmp(s, "urn:uuid:", 9) == 0) { s += 9; n -= 9; }
    else if (n == 38 && s[0] == '{' && s[37] == '}') { s++; n -= 2; }
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
static void uuid_format_core(const unsigned char raw[16], char *out, int hyphens) {
    static const char hex[] = "0123456789abcdef";
    size_t j = 0;
    for (size_t i = 0; i < 16; i++) {
        if (hyphens && (i == 4 || i == 6 || i == 8 || i == 10)) out[j++] = '-';
        out[j++] = hex[raw[i] >> 4]; out[j++] = hex[raw[i] & 15];
    }
}
#endif
