#ifndef MECHPHY_TELEMETRY_PACKET_H
#define MECHPHY_TELEMETRY_PACKET_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TELEMETRY_PACKET_SIZE 40u
#define TELEMETRY_PACKET_CRC_SIZE 2u
#define TELEMETRY_PACKET_CRC_OFFSET 38u
#define TELEMETRY_PACKET_CRC_COVERAGE_SIZE 38u

#define TELEMETRY_PACKET_MAGIC UINT16_C(0x504D)
#define TELEMETRY_PROTOCOL_VERSION UINT8_C(1)

#define TELEMETRY_MESSAGE_TYPE_RESERVED_INVALID UINT8_C(0x00)
#define TELEMETRY_MESSAGE_TYPE_GNSS UINT8_C(0x01)
#define TELEMETRY_MESSAGE_TYPE_NODE_HEALTH UINT8_C(0x02)
#define TELEMETRY_MESSAGE_TYPE_RELAY_HEALTH UINT8_C(0x03)
#define TELEMETRY_MESSAGE_TYPE_COMMAND UINT8_C(0x10)
#define TELEMETRY_MESSAGE_TYPE_COMMAND_ACK UINT8_C(0x11)

#define TELEMETRY_UTC_TIME_UNKNOWN UINT32_C(0)
#define TELEMETRY_COORD_E7_UNKNOWN INT32_C(0)
#define TELEMETRY_ALTITUDE_CM_UNKNOWN INT32_C(0)
#define TELEMETRY_HDOP_X10_UNKNOWN UINT16_C(0xFFFF)
#define TELEMETRY_BATTERY_MV_UNKNOWN UINT16_C(0xFFFF)
#define TELEMETRY_TEMPERATURE_C_X10_UNKNOWN ((int16_t)-32768)

#define TELEMETRY_FIX_TYPE_NONE UINT8_C(0)
#define TELEMETRY_FIX_TYPE_2D UINT8_C(2)
#define TELEMETRY_FIX_TYPE_3D UINT8_C(3)

#define TELEMETRY_STATUS_GNSS_FIX_VALID UINT16_C(0x0001)
#define TELEMETRY_STATUS_UTC_TIME_VALID UINT16_C(0x0002)
#define TELEMETRY_STATUS_LOW_BATTERY UINT16_C(0x0004)
#define TELEMETRY_STATUS_EXTERNAL_POWER_PRESENT UINT16_C(0x0008)
#define TELEMETRY_STATUS_QUEUE_OVERFLOW UINT16_C(0x0010)
#define TELEMETRY_STATUS_SENSOR_FAULT UINT16_C(0x0020)
#define TELEMETRY_STATUS_RESERVED_MASK UINT16_C(0xFFC0)

typedef enum {
    TELEMETRY_PACKET_OK = 0,
    TELEMETRY_PACKET_ERROR_NULL_INPUT = -1,
    TELEMETRY_PACKET_ERROR_NULL_OUTPUT = -2,
    TELEMETRY_PACKET_ERROR_BUFFER_TOO_SMALL = -3,
    TELEMETRY_PACKET_ERROR_INVALID_LENGTH = -4,
    TELEMETRY_PACKET_ERROR_CRC_MISMATCH = -5
} telemetry_packet_status_t;

typedef struct {
    uint32_t node_id;
    uint32_t sequence_number;
    uint32_t utc_time;
    int32_t latitude_e7;
    int32_t longitude_e7;
    int32_t altitude_cm;
    uint8_t fix_type;
    uint8_t satellite_count;
    uint16_t hdop_x10;
    uint16_t battery_mv;
    int16_t temperature_c_x10;
    uint16_t status_flags;
} telemetry_gnss_t;

telemetry_packet_status_t telemetry_packet_encode_gnss(const telemetry_gnss_t *input,
                                                       uint8_t *out_buf,
                                                       size_t out_len);

telemetry_packet_status_t telemetry_packet_validate_crc(const uint8_t *packet, size_t len);

#ifdef __cplusplus
}
#endif

#endif
