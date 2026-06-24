#ifndef MECHPHY_XBEE_API_H
#define MECHPHY_XBEE_API_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define XBEE_API_START_DELIMITER UINT8_C(0x7E)
#define XBEE_API_ESCAPE_BYTE UINT8_C(0x7D)
#define XBEE_API_ESCAPE_XOR UINT8_C(0x20)
#define XBEE_API_XON UINT8_C(0x11)
#define XBEE_API_XOFF UINT8_C(0x13)
#define XBEE_API_MAX_FRAME_DATA_LEN UINT16_C(0xFFFF)

#define XBEE_API_FRAME_TYPE_LOCAL_AT_COMMAND UINT8_C(0x08)
#define XBEE_API_FRAME_TYPE_AT_COMMAND_RESPONSE UINT8_C(0x88)

/*
 * TODO_VERIFY against the Digi XBee-PRO 900HP / XBP9B product manual before
 * use in product firmware. These placeholder values must not be treated as
 * verified frame types.
 */
#define XBEE_API_FRAME_TYPE_TRANSMIT_REQUEST_64_TODO_VERIFY UINT8_C(0x00)
#define XBEE_API_FRAME_TYPE_TRANSMIT_STATUS_TODO_VERIFY UINT8_C(0x00)
#define XBEE_API_FRAME_TYPE_RECEIVE_PACKET_TODO_VERIFY UINT8_C(0x00)

typedef enum {
    XBEE_API_MODE_NORMAL = 0,
    XBEE_API_MODE_ESCAPED = 1
} xbee_api_mode_t;

typedef enum {
    XBEE_API_STATUS_OK = 0,
    XBEE_API_STATUS_IN_PROGRESS = 1,
    XBEE_API_STATUS_FRAME_COMPLETE = 2,
    XBEE_API_STATUS_ERROR_NULL_ARGUMENT = -1,
    XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL = -2,
    XBEE_API_STATUS_ERROR_FRAME_TOO_LONG = -3,
    XBEE_API_STATUS_ERROR_INVALID_ESCAPE = -4,
    XBEE_API_STATUS_ERROR_CHECKSUM = -5,
    XBEE_API_STATUS_ERROR_INVALID_MODE = -6
} xbee_api_status_t;

typedef enum {
    XBEE_API_PARSER_WAIT_START = 0,
    XBEE_API_PARSER_LENGTH_MSB = 1,
    XBEE_API_PARSER_LENGTH_LSB = 2,
    XBEE_API_PARSER_FRAME_DATA = 3,
    XBEE_API_PARSER_CHECKSUM = 4
} xbee_api_parser_state_t;

typedef struct {
    xbee_api_mode_t mode;
    xbee_api_parser_state_t state;
    uint8_t *frame_data;
    size_t max_frame_data_len;
    size_t frame_data_len;
    size_t bytes_received;
    uint16_t expected_frame_data_len;
    uint8_t frame_data_sum;
    uint8_t escape_pending;
} xbee_api_parser_t;

uint8_t xbee_api_calculate_checksum(const uint8_t *frame_data, size_t frame_data_len);

xbee_api_status_t xbee_api_validate_checksum(const uint8_t *frame_data,
                                             size_t frame_data_len,
                                             uint8_t checksum);

int xbee_api_byte_requires_escape(uint8_t byte);

xbee_api_status_t xbee_api_encode_frame(const uint8_t *frame_data,
                                        size_t frame_data_len,
                                        uint8_t *out_buf,
                                        size_t out_len,
                                        size_t *encoded_len);

xbee_api_status_t xbee_api_encode_frame_escaped(const uint8_t *frame_data,
                                                size_t frame_data_len,
                                                uint8_t *out_buf,
                                                size_t out_len,
                                                size_t *encoded_len);

xbee_api_status_t xbee_api_parser_init(xbee_api_parser_t *parser,
                                       xbee_api_mode_t mode,
                                       uint8_t *frame_data_buf,
                                       size_t frame_data_buf_len);

xbee_api_status_t xbee_api_parser_feed_byte(xbee_api_parser_t *parser, uint8_t byte);

#ifdef __cplusplus
}
#endif

#endif
