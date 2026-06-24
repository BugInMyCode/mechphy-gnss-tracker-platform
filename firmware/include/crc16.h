#ifndef MECHPHY_CRC16_H
#define MECHPHY_CRC16_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CRC16_CCITT_FALSE_POLY UINT16_C(0x1021)
#define CRC16_CCITT_FALSE_INIT UINT16_C(0xFFFF)
#define CRC16_CCITT_FALSE_XOROUT UINT16_C(0x0000)

uint16_t crc16_ccitt_false(const uint8_t *data, size_t len);
uint16_t crc16_ccitt_false_update(uint16_t crc, const uint8_t *data, size_t len);

#ifdef __cplusplus
}
#endif

#endif
