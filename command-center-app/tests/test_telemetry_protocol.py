from __future__ import annotations

import json
from pathlib import Path

import pytest

from mechphy_command_center.telemetry_protocol import (
    PACKET_SIZE_BYTES,
    TelemetryDecodeError,
    crc16_ccitt_false,
    decode_gnss_packet,
    load_golden_telemetry_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_GOLDEN = REPO_ROOT / "test-data" / "telemetry_gnss_v1_golden.json"


def test_decode_telemetry_golden_vector() -> None:
    golden = json.loads(TELEMETRY_GOLDEN.read_text(encoding="utf-8"))
    packet = load_golden_telemetry_packet(TELEMETRY_GOLDEN)
    record = decode_gnss_packet(packet)

    assert len(packet) == PACKET_SIZE_BYTES == 40
    assert record.node_id == golden["input"]["node_id"]
    assert record.sequence_number == golden["input"]["sequence_number"]
    assert record.utc_time == golden["input"]["utc_time"]
    assert record.latitude_e7 == golden["input"]["latitude_e7"]
    assert record.longitude_e7 == golden["input"]["longitude_e7"]
    assert record.latitude_degrees == pytest.approx(golden["input"]["latitude_degrees"])
    assert record.longitude_degrees == pytest.approx(golden["input"]["longitude_degrees"])
    assert record.altitude_cm == golden["input"]["altitude_cm"]
    assert record.fix_type == golden["input"]["fix_type"]
    assert record.satellite_count == golden["input"]["satellite_count"]
    assert record.hdop == pytest.approx(golden["input"]["hdop"])
    assert record.battery_mv == golden["input"]["battery_mv"]
    assert record.temperature_c == pytest.approx(golden["input"]["temperature_c"])
    assert record.status_flags == golden["input"]["status_flags"]
    assert record.crc16 == golden["expected_packet"]["crc16"]
    assert record.crc16 == 0x1890
    assert record.utc_time_iso8601 == golden["input"]["utc_time_iso8601"]


def test_crc16_matches_golden_packet() -> None:
    packet = load_golden_telemetry_packet(TELEMETRY_GOLDEN)
    assert crc16_ccitt_false(packet[:38]) == 0x1890


def test_rejects_corrupted_crc() -> None:
    packet = bytearray(load_golden_telemetry_packet(TELEMETRY_GOLDEN))
    packet[16] ^= 0x01

    with pytest.raises(TelemetryDecodeError, match="crc mismatch"):
        decode_gnss_packet(bytes(packet))


def test_rejects_invalid_magic() -> None:
    packet = bytearray(load_golden_telemetry_packet(TELEMETRY_GOLDEN))
    packet[0] = 0x00

    with pytest.raises(TelemetryDecodeError, match="invalid magic"):
        decode_gnss_packet(bytes(packet))
