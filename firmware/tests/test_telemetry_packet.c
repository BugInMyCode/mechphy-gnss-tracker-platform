#include "telemetry_packet.h"

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

static telemetry_gnss_t sample_input(void)
{
    telemetry_gnss_t input;

    input.node_id = UINT32_C(0x00001234);
    input.sequence_number = UINT32_C(42);
    input.utc_time = UINT32_C(1782282600);
    input.latitude_e7 = INT32_C(129715990);
    input.longitude_e7 = INT32_C(775945660);
    input.altitude_cm = INT32_C(92000);
    input.fix_type = TELEMETRY_FIX_TYPE_3D;
    input.satellite_count = UINT8_C(12);
    input.hdop_x10 = UINT16_C(9);
    input.battery_mv = UINT16_C(3710);
    input.temperature_c_x10 = INT16_C(287);
    input.status_flags = TELEMETRY_STATUS_GNSS_FIX_VALID;

    return input;
}

static int test_encode_example_packet(void)
{
    static const uint8_t expected[TELEMETRY_PACKET_SIZE] = {
        0x4Du, 0x50u, 0x01u, 0x01u, 0x34u, 0x12u, 0x00u, 0x00u,
        0x2Au, 0x00u, 0x00u, 0x00u, 0x68u, 0x79u, 0x3Bu, 0x6Au,
        0x16u, 0x4Fu, 0xBBu, 0x07u, 0xBCu, 0xFDu, 0x3Fu, 0x2Eu,
        0x60u, 0x67u, 0x01u, 0x00u, 0x03u, 0x0Cu, 0x09u, 0x00u,
        0x7Eu, 0x0Eu, 0x1Fu, 0x01u, 0x01u, 0x00u, 0x90u, 0x18u
    };
    telemetry_gnss_t input = sample_input();
    uint8_t packet[TELEMETRY_PACKET_SIZE];
    telemetry_packet_status_t status;

    status = telemetry_packet_encode_gnss(&input, packet, sizeof(packet));
    TEST_ASSERT(status == TELEMETRY_PACKET_OK);
    TEST_ASSERT(sizeof(packet) == 40u);
    TEST_ASSERT(TELEMETRY_PACKET_SIZE == 40u);
    TEST_ASSERT(TELEMETRY_PACKET_CRC_COVERAGE_SIZE == 38u);
    TEST_ASSERT(TELEMETRY_PACKET_CRC_OFFSET == 38u);

    TEST_ASSERT(packet[0] == 0x4Du);
    TEST_ASSERT(packet[1] == 0x50u);
    TEST_ASSERT(packet[2] == TELEMETRY_PROTOCOL_VERSION);
    TEST_ASSERT(packet[3] == TELEMETRY_MESSAGE_TYPE_GNSS);

    TEST_ASSERT(packet[4] == 0x34u);
    TEST_ASSERT(packet[5] == 0x12u);
    TEST_ASSERT(packet[6] == 0x00u);
    TEST_ASSERT(packet[7] == 0x00u);
    TEST_ASSERT(packet[8] == 0x2Au);
    TEST_ASSERT(packet[9] == 0x00u);
    TEST_ASSERT(packet[12] == 0x68u);
    TEST_ASSERT(packet[13] == 0x79u);
    TEST_ASSERT(packet[14] == 0x3Bu);
    TEST_ASSERT(packet[15] == 0x6Au);
    TEST_ASSERT(packet[16] == 0x16u);
    TEST_ASSERT(packet[17] == 0x4Fu);
    TEST_ASSERT(packet[18] == 0xBBu);
    TEST_ASSERT(packet[19] == 0x07u);
    TEST_ASSERT(packet[20] == 0xBCu);
    TEST_ASSERT(packet[21] == 0xFDu);
    TEST_ASSERT(packet[22] == 0x3Fu);
    TEST_ASSERT(packet[23] == 0x2Eu);
    TEST_ASSERT(packet[38] == 0x90u);
    TEST_ASSERT(packet[39] == 0x18u);

    TEST_ASSERT(memcmp(packet, expected, sizeof(expected)) == 0);
    TEST_ASSERT(telemetry_packet_validate_crc(packet, sizeof(packet)) == TELEMETRY_PACKET_OK);

    packet[16] ^= 0x01u;
    TEST_ASSERT(telemetry_packet_validate_crc(packet, sizeof(packet)) ==
                TELEMETRY_PACKET_ERROR_CRC_MISMATCH);

    return 0;
}

static int test_encode_errors(void)
{
    telemetry_gnss_t input = sample_input();
    uint8_t packet[TELEMETRY_PACKET_SIZE];
    uint8_t short_packet[TELEMETRY_PACKET_SIZE - 1u];

    TEST_ASSERT(telemetry_packet_encode_gnss(NULL, packet, sizeof(packet)) ==
                TELEMETRY_PACKET_ERROR_NULL_INPUT);
    TEST_ASSERT(telemetry_packet_encode_gnss(&input, NULL, sizeof(packet)) ==
                TELEMETRY_PACKET_ERROR_NULL_OUTPUT);
    TEST_ASSERT(telemetry_packet_encode_gnss(&input, short_packet, sizeof(short_packet)) ==
                TELEMETRY_PACKET_ERROR_BUFFER_TOO_SMALL);
    TEST_ASSERT(telemetry_packet_validate_crc(NULL, TELEMETRY_PACKET_SIZE) ==
                TELEMETRY_PACKET_ERROR_NULL_INPUT);
    TEST_ASSERT(telemetry_packet_validate_crc(packet, TELEMETRY_PACKET_SIZE - 1u) ==
                TELEMETRY_PACKET_ERROR_INVALID_LENGTH);

    return 0;
}

int main(void)
{
    TEST_ASSERT(test_encode_example_packet() == 0);
    TEST_ASSERT(test_encode_errors() == 0);

    (void)printf("test_telemetry_packet: PASS\n");
    return 0;
}
