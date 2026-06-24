"""Decoder for MECHPHY telemetry protocol v1 packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import struct


PACKET_SIZE_BYTES = 40
CRC_COVERAGE_SIZE = 38
CRC_OFFSET = 38
MAGIC = 0x504D
PROTOCOL_VERSION = 1
MESSAGE_TYPE_GNSS = 0x01
CRC16_CCITT_FALSE_POLY = 0x1021
CRC16_CCITT_FALSE_INIT = 0xFFFF


class TelemetryDecodeError(ValueError):
    """Raised when a telemetry packet fails protocol validation."""


@dataclass(frozen=True)
class TelemetryRecord:
    node_id: int
    sequence_number: int
    utc_time: int
    latitude_e7: int
    longitude_e7: int
    altitude_cm: int
    fix_type: int
    satellite_count: int
    hdop_x10: int
    battery_mv: int
    temperature_c_x10: int
    status_flags: int
    crc16: int
    message_type: int = MESSAGE_TYPE_GNSS
    protocol_version: int = PROTOCOL_VERSION

    @property
    def latitude_degrees(self) -> float:
        return self.latitude_e7 / 10_000_000.0

    @property
    def longitude_degrees(self) -> float:
        return self.longitude_e7 / 10_000_000.0

    @property
    def altitude_meters(self) -> float:
        return self.altitude_cm / 100.0

    @property
    def hdop(self) -> float:
        return self.hdop_x10 / 10.0

    @property
    def temperature_c(self) -> float:
        return self.temperature_c_x10 / 10.0

    @property
    def utc_time_iso8601(self) -> str:
        if self.utc_time == 0:
            return ""
        return datetime.fromtimestamp(self.utc_time, tz=UTC).isoformat().replace("+00:00", "Z")


def crc16_ccitt_false(data: bytes) -> int:
    crc = CRC16_CCITT_FALSE_INIT
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ CRC16_CCITT_FALSE_POLY) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def bytes_from_hex_string(hex_string: str) -> bytes:
    return bytes.fromhex(hex_string)


def decode_gnss_packet(packet: bytes) -> TelemetryRecord:
    if len(packet) != PACKET_SIZE_BYTES:
        raise TelemetryDecodeError(f"expected {PACKET_SIZE_BYTES} bytes, got {len(packet)}")

    (
        magic,
        protocol_version,
        message_type,
        node_id,
        sequence_number,
        utc_time,
        latitude_e7,
        longitude_e7,
        altitude_cm,
        fix_type,
        satellite_count,
        hdop_x10,
        battery_mv,
        temperature_c_x10,
        status_flags,
        crc16,
    ) = struct.unpack("<HBBIIIiiiBBHHhHH", packet)

    if magic != MAGIC:
        raise TelemetryDecodeError(f"invalid magic 0x{magic:04X}")
    if protocol_version != PROTOCOL_VERSION:
        raise TelemetryDecodeError(f"unsupported protocol version {protocol_version}")
    if message_type != MESSAGE_TYPE_GNSS:
        raise TelemetryDecodeError(f"unsupported message type 0x{message_type:02X}")

    expected_crc = crc16_ccitt_false(packet[:CRC_COVERAGE_SIZE])
    stored_crc = int.from_bytes(packet[CRC_OFFSET : CRC_OFFSET + 2], "little")
    if expected_crc != stored_crc or crc16 != stored_crc:
        raise TelemetryDecodeError(
            f"crc mismatch expected 0x{expected_crc:04X}, stored 0x{stored_crc:04X}"
        )

    return TelemetryRecord(
        node_id=node_id,
        sequence_number=sequence_number,
        utc_time=utc_time,
        latitude_e7=latitude_e7,
        longitude_e7=longitude_e7,
        altitude_cm=altitude_cm,
        fix_type=fix_type,
        satellite_count=satellite_count,
        hdop_x10=hdop_x10,
        battery_mv=battery_mv,
        temperature_c_x10=temperature_c_x10,
        status_flags=status_flags,
        crc16=stored_crc,
        message_type=message_type,
        protocol_version=protocol_version,
    )


def load_golden_telemetry_packet(path: str | Path) -> bytes:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    packet_bytes = data["expected_packet"]["bytes"]
    return bytes(packet_bytes)
