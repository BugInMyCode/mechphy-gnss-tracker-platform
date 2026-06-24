#include "telemetry_packet.h"

#include "crc16.h"

static void write_u16_le(uint8_t *buf, size_t offset, uint16_t value)
{
    buf[offset] = (uint8_t)(value & UINT16_C(0x00FF));
    buf[offset + 1u] = (uint8_t)((value >> 8) & UINT16_C(0x00FF));
}

static void write_i16_le(uint8_t *buf, size_t offset, int16_t value)
{
    write_u16_le(buf, offset, (uint16_t)value);
}

static void write_u32_le(uint8_t *buf, size_t offset, uint32_t value)
{
    buf[offset] = (uint8_t)(value & UINT32_C(0x000000FF));
    buf[offset + 1u] = (uint8_t)((value >> 8) & UINT32_C(0x000000FF));
    buf[offset + 2u] = (uint8_t)((value >> 16) & UINT32_C(0x000000FF));
    buf[offset + 3u] = (uint8_t)((value >> 24) & UINT32_C(0x000000FF));
}

static void write_i32_le(uint8_t *buf, size_t offset, int32_t value)
{
    write_u32_le(buf, offset, (uint32_t)value);
}

static uint16_t read_u16_le(const uint8_t *buf, size_t offset)
{
    return (uint16_t)((uint16_t)buf[offset] | ((uint16_t)buf[offset + 1u] << 8));
}

telemetry_packet_status_t telemetry_packet_encode_gnss(const telemetry_gnss_t *input,
                                                       uint8_t *out_buf,
                                                       size_t out_len)
{
    uint16_t crc;

    if (input == NULL) {
        return TELEMETRY_PACKET_ERROR_NULL_INPUT;
    }

    if (out_buf == NULL) {
        return TELEMETRY_PACKET_ERROR_NULL_OUTPUT;
    }

    if (out_len < TELEMETRY_PACKET_SIZE) {
        return TELEMETRY_PACKET_ERROR_BUFFER_TOO_SMALL;
    }

    write_u16_le(out_buf, 0u, TELEMETRY_PACKET_MAGIC);
    out_buf[2u] = TELEMETRY_PROTOCOL_VERSION;
    out_buf[3u] = TELEMETRY_MESSAGE_TYPE_GNSS;
    write_u32_le(out_buf, 4u, input->node_id);
    write_u32_le(out_buf, 8u, input->sequence_number);
    write_u32_le(out_buf, 12u, input->utc_time);
    write_i32_le(out_buf, 16u, input->latitude_e7);
    write_i32_le(out_buf, 20u, input->longitude_e7);
    write_i32_le(out_buf, 24u, input->altitude_cm);
    out_buf[28u] = input->fix_type;
    out_buf[29u] = input->satellite_count;
    write_u16_le(out_buf, 30u, input->hdop_x10);
    write_u16_le(out_buf, 32u, input->battery_mv);
    write_i16_le(out_buf, 34u, input->temperature_c_x10);
    write_u16_le(out_buf, 36u, input->status_flags);

    crc = crc16_ccitt_false(out_buf, TELEMETRY_PACKET_CRC_COVERAGE_SIZE);
    write_u16_le(out_buf, TELEMETRY_PACKET_CRC_OFFSET, crc);

    return TELEMETRY_PACKET_OK;
}

telemetry_packet_status_t telemetry_packet_validate_crc(const uint8_t *packet, size_t len)
{
    uint16_t expected_crc;
    uint16_t actual_crc;

    if (packet == NULL) {
        return TELEMETRY_PACKET_ERROR_NULL_INPUT;
    }

    if (len != TELEMETRY_PACKET_SIZE) {
        return TELEMETRY_PACKET_ERROR_INVALID_LENGTH;
    }

    expected_crc = crc16_ccitt_false(packet, TELEMETRY_PACKET_CRC_COVERAGE_SIZE);
    actual_crc = read_u16_le(packet, TELEMETRY_PACKET_CRC_OFFSET);

    if (expected_crc != actual_crc) {
        return TELEMETRY_PACKET_ERROR_CRC_MISMATCH;
    }

    return TELEMETRY_PACKET_OK;
}
