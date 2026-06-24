#include "xbee_api.h"

static void parser_reset_frame(xbee_api_parser_t *parser)
{
    parser->state = XBEE_API_PARSER_WAIT_START;
    parser->frame_data_len = 0u;
    parser->bytes_received = 0u;
    parser->expected_frame_data_len = 0u;
    parser->frame_data_sum = 0u;
    parser->escape_pending = 0u;
}

static uint8_t checksum_sum(const uint8_t *frame_data, size_t frame_data_len)
{
    size_t i;
    uint8_t sum = 0u;

    if ((frame_data == NULL) && (frame_data_len > 0u)) {
        return 0u;
    }

    for (i = 0u; i < frame_data_len; ++i) {
        sum = (uint8_t)(sum + frame_data[i]);
    }

    return sum;
}

static size_t escaped_size_for_byte(uint8_t byte)
{
    return xbee_api_byte_requires_escape(byte) ? 2u : 1u;
}

static xbee_api_status_t write_escaped_byte(uint8_t byte,
                                            uint8_t *out_buf,
                                            size_t out_len,
                                            size_t *offset)
{
    if (xbee_api_byte_requires_escape(byte)) {
        if ((*offset + 2u) > out_len) {
            return XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL;
        }

        out_buf[*offset] = XBEE_API_ESCAPE_BYTE;
        *offset += 1u;
        out_buf[*offset] = (uint8_t)(byte ^ XBEE_API_ESCAPE_XOR);
        *offset += 1u;
    } else {
        if ((*offset + 1u) > out_len) {
            return XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL;
        }

        out_buf[*offset] = byte;
        *offset += 1u;
    }

    return XBEE_API_STATUS_OK;
}

static xbee_api_status_t parser_process_unescaped_byte(xbee_api_parser_t *parser,
                                                       uint8_t byte)
{
    switch (parser->state) {
    case XBEE_API_PARSER_WAIT_START:
        if (byte == XBEE_API_START_DELIMITER) {
            parser->state = XBEE_API_PARSER_LENGTH_MSB;
            parser->frame_data_len = 0u;
            parser->bytes_received = 0u;
            parser->expected_frame_data_len = 0u;
            parser->frame_data_sum = 0u;
            parser->escape_pending = 0u;
        }
        return XBEE_API_STATUS_IN_PROGRESS;

    case XBEE_API_PARSER_LENGTH_MSB:
        parser->expected_frame_data_len = (uint16_t)((uint16_t)byte << 8);
        parser->state = XBEE_API_PARSER_LENGTH_LSB;
        return XBEE_API_STATUS_IN_PROGRESS;

    case XBEE_API_PARSER_LENGTH_LSB:
        parser->expected_frame_data_len =
            (uint16_t)(parser->expected_frame_data_len | (uint16_t)byte);

        if ((size_t)parser->expected_frame_data_len > parser->max_frame_data_len) {
            parser_reset_frame(parser);
            return XBEE_API_STATUS_ERROR_FRAME_TOO_LONG;
        }

        parser->frame_data_len = 0u;
        parser->bytes_received = 0u;
        parser->frame_data_sum = 0u;

        if (parser->expected_frame_data_len == 0u) {
            parser->state = XBEE_API_PARSER_CHECKSUM;
        } else {
            parser->state = XBEE_API_PARSER_FRAME_DATA;
        }

        return XBEE_API_STATUS_IN_PROGRESS;

    case XBEE_API_PARSER_FRAME_DATA:
        parser->frame_data[parser->bytes_received] = byte;
        parser->bytes_received += 1u;
        parser->frame_data_len = parser->bytes_received;
        parser->frame_data_sum = (uint8_t)(parser->frame_data_sum + byte);

        if (parser->bytes_received == (size_t)parser->expected_frame_data_len) {
            parser->state = XBEE_API_PARSER_CHECKSUM;
        }

        return XBEE_API_STATUS_IN_PROGRESS;

    case XBEE_API_PARSER_CHECKSUM:
        if ((uint8_t)(parser->frame_data_sum + byte) != UINT8_C(0xFF)) {
            parser_reset_frame(parser);
            return XBEE_API_STATUS_ERROR_CHECKSUM;
        }

        parser->state = XBEE_API_PARSER_WAIT_START;
        parser->escape_pending = 0u;
        return XBEE_API_STATUS_FRAME_COMPLETE;

    default:
        parser_reset_frame(parser);
        return XBEE_API_STATUS_ERROR_INVALID_MODE;
    }
}

uint8_t xbee_api_calculate_checksum(const uint8_t *frame_data, size_t frame_data_len)
{
    return (uint8_t)(UINT8_C(0xFF) - checksum_sum(frame_data, frame_data_len));
}

xbee_api_status_t xbee_api_validate_checksum(const uint8_t *frame_data,
                                             size_t frame_data_len,
                                             uint8_t checksum)
{
    if ((frame_data == NULL) && (frame_data_len > 0u)) {
        return XBEE_API_STATUS_ERROR_NULL_ARGUMENT;
    }

    if ((uint8_t)(checksum_sum(frame_data, frame_data_len) + checksum) != UINT8_C(0xFF)) {
        return XBEE_API_STATUS_ERROR_CHECKSUM;
    }

    return XBEE_API_STATUS_OK;
}

int xbee_api_byte_requires_escape(uint8_t byte)
{
    return (byte == XBEE_API_START_DELIMITER) || (byte == XBEE_API_ESCAPE_BYTE) ||
           (byte == XBEE_API_XON) || (byte == XBEE_API_XOFF);
}

xbee_api_status_t xbee_api_encode_frame(const uint8_t *frame_data,
                                        size_t frame_data_len,
                                        uint8_t *out_buf,
                                        size_t out_len,
                                        size_t *encoded_len)
{
    size_t i;
    size_t required_len;
    uint8_t checksum;

    if (((frame_data == NULL) && (frame_data_len > 0u)) || (out_buf == NULL) ||
        (encoded_len == NULL)) {
        return XBEE_API_STATUS_ERROR_NULL_ARGUMENT;
    }

    if (frame_data_len > (size_t)XBEE_API_MAX_FRAME_DATA_LEN) {
        return XBEE_API_STATUS_ERROR_FRAME_TOO_LONG;
    }

    required_len = 1u + 2u + frame_data_len + 1u;
    if (out_len < required_len) {
        return XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL;
    }

    out_buf[0u] = XBEE_API_START_DELIMITER;
    out_buf[1u] = (uint8_t)((frame_data_len >> 8) & 0xFFu);
    out_buf[2u] = (uint8_t)(frame_data_len & 0xFFu);

    for (i = 0u; i < frame_data_len; ++i) {
        out_buf[3u + i] = frame_data[i];
    }

    checksum = xbee_api_calculate_checksum(frame_data, frame_data_len);
    out_buf[3u + frame_data_len] = checksum;
    *encoded_len = required_len;

    return XBEE_API_STATUS_OK;
}

xbee_api_status_t xbee_api_encode_frame_escaped(const uint8_t *frame_data,
                                                size_t frame_data_len,
                                                uint8_t *out_buf,
                                                size_t out_len,
                                                size_t *encoded_len)
{
    size_t i;
    size_t required_len;
    size_t offset;
    uint8_t length_msb;
    uint8_t length_lsb;
    uint8_t checksum;
    xbee_api_status_t status;

    if (((frame_data == NULL) && (frame_data_len > 0u)) || (out_buf == NULL) ||
        (encoded_len == NULL)) {
        return XBEE_API_STATUS_ERROR_NULL_ARGUMENT;
    }

    if (frame_data_len > (size_t)XBEE_API_MAX_FRAME_DATA_LEN) {
        return XBEE_API_STATUS_ERROR_FRAME_TOO_LONG;
    }

    length_msb = (uint8_t)((frame_data_len >> 8) & 0xFFu);
    length_lsb = (uint8_t)(frame_data_len & 0xFFu);
    checksum = xbee_api_calculate_checksum(frame_data, frame_data_len);

    required_len = 1u;
    required_len += escaped_size_for_byte(length_msb);
    required_len += escaped_size_for_byte(length_lsb);
    for (i = 0u; i < frame_data_len; ++i) {
        required_len += escaped_size_for_byte(frame_data[i]);
    }
    required_len += escaped_size_for_byte(checksum);

    if (out_len < required_len) {
        return XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL;
    }

    offset = 0u;
    out_buf[offset] = XBEE_API_START_DELIMITER;
    offset += 1u;

    status = write_escaped_byte(length_msb, out_buf, out_len, &offset);
    if (status != XBEE_API_STATUS_OK) {
        return status;
    }

    status = write_escaped_byte(length_lsb, out_buf, out_len, &offset);
    if (status != XBEE_API_STATUS_OK) {
        return status;
    }

    for (i = 0u; i < frame_data_len; ++i) {
        status = write_escaped_byte(frame_data[i], out_buf, out_len, &offset);
        if (status != XBEE_API_STATUS_OK) {
            return status;
        }
    }

    status = write_escaped_byte(checksum, out_buf, out_len, &offset);
    if (status != XBEE_API_STATUS_OK) {
        return status;
    }

    *encoded_len = offset;
    return XBEE_API_STATUS_OK;
}

xbee_api_status_t xbee_api_parser_init(xbee_api_parser_t *parser,
                                       xbee_api_mode_t mode,
                                       uint8_t *frame_data_buf,
                                       size_t frame_data_buf_len)
{
    if ((parser == NULL) || (frame_data_buf == NULL)) {
        return XBEE_API_STATUS_ERROR_NULL_ARGUMENT;
    }

    if ((mode != XBEE_API_MODE_NORMAL) && (mode != XBEE_API_MODE_ESCAPED)) {
        return XBEE_API_STATUS_ERROR_INVALID_MODE;
    }

    parser->mode = mode;
    parser->frame_data = frame_data_buf;
    parser->max_frame_data_len = frame_data_buf_len;
    parser_reset_frame(parser);

    return XBEE_API_STATUS_OK;
}

xbee_api_status_t xbee_api_parser_feed_byte(xbee_api_parser_t *parser, uint8_t byte)
{
    uint8_t unescaped_byte;

    if (parser == NULL) {
        return XBEE_API_STATUS_ERROR_NULL_ARGUMENT;
    }

    if ((parser->mode != XBEE_API_MODE_NORMAL) && (parser->mode != XBEE_API_MODE_ESCAPED)) {
        parser_reset_frame(parser);
        return XBEE_API_STATUS_ERROR_INVALID_MODE;
    }

    if (parser->state == XBEE_API_PARSER_WAIT_START) {
        return parser_process_unescaped_byte(parser, byte);
    }

    if ((parser->state != XBEE_API_PARSER_WAIT_START) && (byte == XBEE_API_START_DELIMITER)) {
        parser_reset_frame(parser);
        parser->state = XBEE_API_PARSER_LENGTH_MSB;
        return XBEE_API_STATUS_IN_PROGRESS;
    }

    if (parser->mode == XBEE_API_MODE_ESCAPED) {
        if (parser->escape_pending != 0u) {
            unescaped_byte = (uint8_t)(byte ^ XBEE_API_ESCAPE_XOR);

            if (!xbee_api_byte_requires_escape(unescaped_byte)) {
                parser_reset_frame(parser);
                return XBEE_API_STATUS_ERROR_INVALID_ESCAPE;
            }

            parser->escape_pending = 0u;
            return parser_process_unescaped_byte(parser, unescaped_byte);
        }

        if (byte == XBEE_API_ESCAPE_BYTE) {
            parser->escape_pending = 1u;
            return XBEE_API_STATUS_IN_PROGRESS;
        }

        if ((byte == XBEE_API_XON) || (byte == XBEE_API_XOFF)) {
            parser_reset_frame(parser);
            return XBEE_API_STATUS_ERROR_INVALID_ESCAPE;
        }
    }

    return parser_process_unescaped_byte(parser, byte);
}
