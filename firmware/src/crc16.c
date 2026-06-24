#include "crc16.h"

uint16_t crc16_ccitt_false_update(uint16_t crc, const uint8_t *data, size_t len)
{
    size_t i;

    if ((data == NULL) && (len > 0u)) {
        return crc;
    }

    for (i = 0u; i < len; ++i) {
        uint8_t bit;

        crc ^= (uint16_t)((uint16_t)data[i] << 8);

        for (bit = 0u; bit < 8u; ++bit) {
            if ((crc & UINT16_C(0x8000)) != 0u) {
                crc = (uint16_t)((uint16_t)(crc << 1) ^ CRC16_CCITT_FALSE_POLY);
            } else {
                crc = (uint16_t)(crc << 1);
            }
        }
    }

    return crc;
}

uint16_t crc16_ccitt_false(const uint8_t *data, size_t len)
{
    return (uint16_t)(crc16_ccitt_false_update(CRC16_CCITT_FALSE_INIT, data, len) ^
                     CRC16_CCITT_FALSE_XOROUT);
}
