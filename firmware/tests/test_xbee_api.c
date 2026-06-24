#include "xbee_api.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define ARRAY_LEN(array) (sizeof(array) / sizeof((array)[0]))

#define TEST_ASSERT(condition)                                                         \
    do {                                                                               \
        if (!(condition)) {                                                            \
            (void)fprintf(stderr, "Assertion failed at %s:%d: %s\n", __FILE__,         \
                          __LINE__, #condition);                                      \
            return 1;                                                                  \
        }                                                                              \
    } while (0)

static int feed_bytes_expect_final(xbee_api_parser_t *parser,
                                   const uint8_t *bytes,
                                   size_t len,
                                   xbee_api_status_t final_status)
{
    size_t i;
    xbee_api_status_t status = XBEE_API_STATUS_IN_PROGRESS;

    for (i = 0u; i < len; ++i) {
        status = xbee_api_parser_feed_byte(parser, bytes[i]);

        if ((i + 1u) < len) {
            TEST_ASSERT(status == XBEE_API_STATUS_IN_PROGRESS);
        }
    }

    TEST_ASSERT(status == final_status);
    return 0;
}

static int test_encode_normal_frame(void)
{
    static const uint8_t frame_data[] = {
        XBEE_API_FRAME_TYPE_LOCAL_AT_COMMAND, 0x01u, 0x4Eu, 0x49u
    };
    static const uint8_t expected[] = {
        0x7Eu, 0x00u, 0x04u, 0x08u, 0x01u, 0x4Eu, 0x49u, 0x5Fu
    };
    uint8_t encoded[16u];
    size_t encoded_len = 0u;
    xbee_api_status_t status;

    TEST_ASSERT(xbee_api_calculate_checksum(frame_data, ARRAY_LEN(frame_data)) == 0x5Fu);
    TEST_ASSERT(xbee_api_validate_checksum(frame_data, ARRAY_LEN(frame_data), 0x5Fu) ==
                XBEE_API_STATUS_OK);

    status = xbee_api_encode_frame(frame_data, ARRAY_LEN(frame_data), encoded, sizeof(encoded),
                                   &encoded_len);
    TEST_ASSERT(status == XBEE_API_STATUS_OK);
    TEST_ASSERT(encoded_len == ARRAY_LEN(expected));
    TEST_ASSERT(memcmp(encoded, expected, ARRAY_LEN(expected)) == 0);

    return 0;
}

static int test_decode_normal_frame(void)
{
    static const uint8_t encoded[] = {
        0x7Eu, 0x00u, 0x04u, 0x08u, 0x01u, 0x4Eu, 0x49u, 0x5Fu
    };
    static const uint8_t expected_frame_data[] = {
        XBEE_API_FRAME_TYPE_LOCAL_AT_COMMAND, 0x01u, 0x4Eu, 0x49u
    };
    xbee_api_parser_t parser;
    uint8_t frame_data[8u];

    TEST_ASSERT(xbee_api_parser_init(&parser, XBEE_API_MODE_NORMAL, frame_data,
                                     sizeof(frame_data)) == XBEE_API_STATUS_OK);
    TEST_ASSERT(feed_bytes_expect_final(&parser, encoded, ARRAY_LEN(encoded),
                                        XBEE_API_STATUS_FRAME_COMPLETE) == 0);
    TEST_ASSERT(parser.frame_data_len == ARRAY_LEN(expected_frame_data));
    TEST_ASSERT(memcmp(parser.frame_data, expected_frame_data, ARRAY_LEN(expected_frame_data)) == 0);

    return 0;
}

static int test_encode_and_decode_escaped_frame(void)
{
    static const uint8_t frame_data[] = {
        XBEE_API_FRAME_TYPE_LOCAL_AT_COMMAND, 0x7Eu, 0x7Du, 0x11u, 0x13u
    };
    static const uint8_t expected[] = {
        0x7Eu, 0x00u, 0x05u, 0x08u, 0x7Du, 0x5Eu, 0x7Du,
        0x5Du, 0x7Du, 0x31u, 0x7Du, 0x33u, 0xD8u
    };
    xbee_api_parser_t parser;
    uint8_t encoded[32u];
    uint8_t decoded[8u];
    size_t encoded_len = 0u;
    xbee_api_status_t status;

    TEST_ASSERT(xbee_api_calculate_checksum(frame_data, ARRAY_LEN(frame_data)) == 0xD8u);

    status = xbee_api_encode_frame_escaped(frame_data, ARRAY_LEN(frame_data), encoded,
                                           sizeof(encoded), &encoded_len);
    TEST_ASSERT(status == XBEE_API_STATUS_OK);
    TEST_ASSERT(encoded_len == ARRAY_LEN(expected));
    TEST_ASSERT(memcmp(encoded, expected, ARRAY_LEN(expected)) == 0);

    TEST_ASSERT(xbee_api_parser_init(&parser, XBEE_API_MODE_ESCAPED, decoded, sizeof(decoded)) ==
                XBEE_API_STATUS_OK);
    TEST_ASSERT(feed_bytes_expect_final(&parser, encoded, encoded_len,
                                        XBEE_API_STATUS_FRAME_COMPLETE) == 0);
    TEST_ASSERT(parser.frame_data_len == ARRAY_LEN(frame_data));
    TEST_ASSERT(memcmp(parser.frame_data, frame_data, ARRAY_LEN(frame_data)) == 0);

    return 0;
}

static int test_reject_corrupted_checksum(void)
{
    uint8_t encoded[] = {
        0x7Eu, 0x00u, 0x04u, 0x08u, 0x01u, 0x4Eu, 0x49u, 0x5Eu
    };
    xbee_api_parser_t parser;
    uint8_t frame_data[8u];

    TEST_ASSERT(xbee_api_parser_init(&parser, XBEE_API_MODE_NORMAL, frame_data,
                                     sizeof(frame_data)) == XBEE_API_STATUS_OK);
    TEST_ASSERT(feed_bytes_expect_final(&parser, encoded, ARRAY_LEN(encoded),
                                        XBEE_API_STATUS_ERROR_CHECKSUM) == 0);

    return 0;
}

static int test_reject_malformed_escape(void)
{
    static const uint8_t malformed[] = {
        0x7Eu, 0x00u, 0x02u, 0x08u, 0x7Du, 0x00u
    };
    xbee_api_parser_t parser;
    uint8_t frame_data[8u];

    TEST_ASSERT(xbee_api_parser_init(&parser, XBEE_API_MODE_ESCAPED, frame_data,
                                     sizeof(frame_data)) == XBEE_API_STATUS_OK);
    TEST_ASSERT(feed_bytes_expect_final(&parser, malformed, ARRAY_LEN(malformed),
                                        XBEE_API_STATUS_ERROR_INVALID_ESCAPE) == 0);

    return 0;
}

static int test_resynchronize_on_start_delimiter(void)
{
    static const uint8_t valid_tail_after_new_start[] = {
        0x00u, 0x01u, 0x08u, 0xF7u
    };
    xbee_api_parser_t parser;
    uint8_t frame_data[8u];
    size_t i;
    xbee_api_status_t status;

    TEST_ASSERT(xbee_api_parser_init(&parser, XBEE_API_MODE_NORMAL, frame_data,
                                     sizeof(frame_data)) == XBEE_API_STATUS_OK);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x7Eu) == XBEE_API_STATUS_IN_PROGRESS);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x00u) == XBEE_API_STATUS_IN_PROGRESS);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x03u) == XBEE_API_STATUS_IN_PROGRESS);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x08u) == XBEE_API_STATUS_IN_PROGRESS);

    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x7Eu) == XBEE_API_STATUS_IN_PROGRESS);

    status = XBEE_API_STATUS_IN_PROGRESS;
    for (i = 0u; i < ARRAY_LEN(valid_tail_after_new_start); ++i) {
        status = xbee_api_parser_feed_byte(&parser, valid_tail_after_new_start[i]);
    }

    TEST_ASSERT(status == XBEE_API_STATUS_FRAME_COMPLETE);
    TEST_ASSERT(parser.frame_data_len == 1u);
    TEST_ASSERT(parser.frame_data[0u] == XBEE_API_FRAME_TYPE_LOCAL_AT_COMMAND);

    return 0;
}

static int test_reject_frame_longer_than_configured_max(void)
{
    xbee_api_parser_t parser;
    uint8_t frame_data[2u];

    TEST_ASSERT(xbee_api_parser_init(&parser, XBEE_API_MODE_NORMAL, frame_data,
                                     sizeof(frame_data)) == XBEE_API_STATUS_OK);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x7Eu) == XBEE_API_STATUS_IN_PROGRESS);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x00u) == XBEE_API_STATUS_IN_PROGRESS);
    TEST_ASSERT(xbee_api_parser_feed_byte(&parser, 0x03u) ==
                XBEE_API_STATUS_ERROR_FRAME_TOO_LONG);

    return 0;
}

static int test_encode_errors(void)
{
    static const uint8_t frame_data[] = {0x08u};
    uint8_t encoded[4u];
    size_t encoded_len = 0u;

    TEST_ASSERT(xbee_api_encode_frame(NULL, ARRAY_LEN(frame_data), encoded, sizeof(encoded),
                                      &encoded_len) == XBEE_API_STATUS_ERROR_NULL_ARGUMENT);
    TEST_ASSERT(xbee_api_encode_frame(frame_data, ARRAY_LEN(frame_data), NULL, sizeof(encoded),
                                      &encoded_len) == XBEE_API_STATUS_ERROR_NULL_ARGUMENT);
    TEST_ASSERT(xbee_api_encode_frame(frame_data, ARRAY_LEN(frame_data), encoded, sizeof(encoded),
                                      NULL) == XBEE_API_STATUS_ERROR_NULL_ARGUMENT);
    TEST_ASSERT(xbee_api_encode_frame(frame_data, ARRAY_LEN(frame_data), encoded, 3u,
                                      &encoded_len) == XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL);
    TEST_ASSERT(xbee_api_encode_frame_escaped(frame_data, ARRAY_LEN(frame_data), encoded, 3u,
                                              &encoded_len) ==
                XBEE_API_STATUS_ERROR_BUFFER_TOO_SMALL);

    return 0;
}

int main(void)
{
    TEST_ASSERT(test_encode_normal_frame() == 0);
    TEST_ASSERT(test_decode_normal_frame() == 0);
    TEST_ASSERT(test_encode_and_decode_escaped_frame() == 0);
    TEST_ASSERT(test_reject_corrupted_checksum() == 0);
    TEST_ASSERT(test_reject_malformed_escape() == 0);
    TEST_ASSERT(test_resynchronize_on_start_delimiter() == 0);
    TEST_ASSERT(test_reject_frame_longer_than_configured_max() == 0);
    TEST_ASSERT(test_encode_errors() == 0);

    (void)printf("test_xbee_api: PASS\n");
    return 0;
}
