from __future__ import annotations

import json
from pathlib import Path

import pytest

from mechphy_command_center.telemetry_protocol import PACKET_SIZE_BYTES, decode_gnss_packet
from mechphy_command_center.xbee_api import (
    XBeeApiError,
    calculate_checksum,
    decode_api_frame,
    extract_trailing_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
XBEE_GOLDEN = REPO_ROOT / "test-data" / "xbee_api_escaped_golden.json"


def test_decode_xbee_escaped_golden_vector() -> None:
    golden = json.loads(XBEE_GOLDEN.read_text(encoding="utf-8"))
    escaped_frame = bytes(golden["escaped_api_frame_bytes"])

    frame = decode_api_frame(escaped_frame, escaped=True)

    assert frame.length == golden["frame_data_size_bytes"]
    assert frame.frame_data == bytes(golden["frame_data_bytes"])
    assert frame.checksum == golden["checksum"] == 0xD9
    assert calculate_checksum(frame.frame_data) == frame.checksum

    telemetry_payload = extract_trailing_payload(frame.frame_data, PACKET_SIZE_BYTES)
    assert telemetry_payload == bytes.fromhex(golden["telemetry_payload_hex"])

    record = decode_gnss_packet(telemetry_payload)
    assert record.node_id == 4660
    assert record.latitude_degrees == pytest.approx(12.971599)
    assert record.longitude_degrees == pytest.approx(77.594566)


def test_rejects_bad_xbee_checksum() -> None:
    golden = json.loads(XBEE_GOLDEN.read_text(encoding="utf-8"))
    frame = bytearray(golden["escaped_api_frame_bytes"])
    frame[-1] ^= 0x01

    with pytest.raises(XBeeApiError, match="checksum"):
        decode_api_frame(bytes(frame), escaped=True)


def test_rejects_malformed_escape_sequence() -> None:
    malformed = bytes([0x7E, 0x00, 0x01, 0x7D, 0x00])

    with pytest.raises(XBeeApiError, match="escape"):
        decode_api_frame(malformed, escaped=True)


def test_rejects_length_mismatch() -> None:
    golden = json.loads(XBEE_GOLDEN.read_text(encoding="utf-8"))
    unescaped_frame = bytearray(golden["unescaped_api_frame_bytes"])
    unescaped_frame[2] = 0x01

    with pytest.raises(XBeeApiError, match="length mismatch"):
        decode_api_frame(bytes(unescaped_frame), escaped=False)
