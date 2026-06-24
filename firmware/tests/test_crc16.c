#include "crc16.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define TEST_ASSERT(condition)                                                         \
    do {                                                                               \
        if (!(condition)) {                                                            \
            (void)fprintf(stderr, "Assertion failed at %s:%d: %s\n", __FILE__,         \
                          __LINE__, #condition);                                      \
            return 1;                                                                  \
        }                                                                              \
    } while (0)

int main(void)
{
    static const uint8_t known_vector[] = "123456789";
    uint16_t crc;

    crc = crc16_ccitt_false(known_vector, strlen((const char *)known_vector));
    TEST_ASSERT(crc == UINT16_C(0x29B1));

    crc = crc16_ccitt_false(NULL, 0u);
    TEST_ASSERT(crc == CRC16_CCITT_FALSE_INIT);

    (void)printf("test_crc16: PASS\n");
    return 0;
}
