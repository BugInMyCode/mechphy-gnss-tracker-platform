#!/usr/bin/env python3
"""Generate MECHPHY telemetry and XBee API golden test vectors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TELEMETRY_JSON = ROOT / "telemetry_gnss_v1_golden.json"
XBEE_JSON = ROOT / "xbee_api_escaped_golden.json"

ESCAPED_BYTES = {0x7E, 0x7D, 0x11, 0x13}


def hex_string(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def byte_array(data: bytes) -> list[int]:
    return list(data)


def hex_byte(byte: int) -> str:
    return f"0x{byte:02X}"


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def le_u16(value: int) -> bytes:
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def le_u32(value: int) -> bytes:
    return bytes(
        (
            value & 0xFF,
            (value >> 8) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 24) & 0xFF,
        )
    )


def le_i16(value: int) -> bytes:
    return le_u16(value & 0xFFFF)


def le_i32(value: int) -> bytes:
    return le_u32(value & 0xFFFFFFFF)


def build_telemetry_packet() -> tuple[dict[str, Any], bytes, int]:
    fields: dict[str, Any] = {
        "node_id": 4660,
        "node_id_hex": "0x00001234",
        "sequence_number": 42,
        "utc_time": 1782282600,
        "utc_time_iso8601": "2026-06-24T06:30:00Z",
        "latitude_degrees": 12.971599,
        "longitude_degrees": 77.594566,
        "latitude_e7": 129715990,
        "longitude_e7": 775945660,
        "altitude_cm": 92000,
        "fix_type": 3,
        "satellite_count": 12,
        "hdop": 0.9,
        "hdop_x10": 9,
        "battery_mv": 3710,
        "temperature_c": 28.7,
        "temperature_c_x10": 287,
        "status_flags": 1,
        "status_flags_hex": "0x0001",
    }

    packet_without_crc = b"".join(
        (
            le_u16(0x504D),
            bytes((1, 1)),
            le_u32(fields["node_id"]),
            le_u32(fields["sequence_number"]),
            le_u32(fields["utc_time"]),
            le_i32(fields["latitude_e7"]),
            le_i32(fields["longitude_e7"]),
            le_i32(fields["altitude_cm"]),
            bytes((fields["fix_type"], fields["satellite_count"])),
            le_u16(fields["hdop_x10"]),
            le_u16(fields["battery_mv"]),
            le_i16(fields["temperature_c_x10"]),
            le_u16(fields["status_flags"]),
        )
    )
    crc = crc16_ccitt_false(packet_without_crc)
    packet = packet_without_crc + le_u16(crc)

    if len(packet_without_crc) != 38 or len(packet) != 40:
        raise RuntimeError("telemetry packet size calculation failed")

    return fields, packet, crc


def build_telemetry_json() -> tuple[dict[str, Any], bytes]:
    fields, packet, crc = build_telemetry_packet()
    data: dict[str, Any] = {
        "schema": "mechphy.telemetry_gnss_v1.golden",
        "description": "Golden simulated MECHPHY GNSS telemetry packet for protocol v1 decoder tests.",
        "input": fields,
        "expected_packet": {
            "packet_size_bytes": 40,
            "byte_order": "little-endian",
            "crc_algorithm": "CRC-16/CCITT-FALSE",
            "crc_coverage": "bytes 0..37",
            "crc_storage": "little-endian bytes 38..39",
            "crc16": crc,
            "crc16_hex": f"0x{crc:04X}",
            "hex": hex_string(packet),
            "bytes": byte_array(packet),
        },
    }
    return data, packet


def xbee_checksum(frame_data: bytes) -> int:
    return (0xFF - (sum(frame_data) & 0xFF)) & 0xFF


def escape_ap2(unescaped_frame: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    escaped = bytearray((unescaped_frame[0],))
    escaped_positions: list[dict[str, Any]] = []
    frame_data_start_offset = 3

    for unescaped_offset, byte in enumerate(unescaped_frame[1:], start=1):
        if byte in ESCAPED_BYTES:
            escaped_offset = len(escaped)
            entry: dict[str, Any] = {
                "unescaped_frame_offset": unescaped_offset,
                "original_byte": hex_byte(byte),
                "escaped_frame_offset": escaped_offset,
                "escaped_sequence_hex": hex_string(bytes((0x7D, byte ^ 0x20))),
                "escaped_byte_values": [0x7D, byte ^ 0x20],
            }

            if unescaped_offset >= frame_data_start_offset:
                frame_data_offset = unescaped_offset - frame_data_start_offset
                entry["frame_data_offset"] = frame_data_offset
                if frame_data_offset >= 5:
                    entry["telemetry_payload_offset"] = frame_data_offset - 5

            escaped.extend((0x7D, byte ^ 0x20))
            escaped_positions.append(entry)
        else:
            escaped.append(byte)

    return bytes(escaped), escaped_positions


def build_xbee_json(telemetry_packet: bytes) -> dict[str, Any]:
    dummy_prefix = bytes((0xF0, 0x7E, 0x7D, 0x11, 0x13))
    frame_data = dummy_prefix + telemetry_packet
    checksum = xbee_checksum(frame_data)
    length = len(frame_data)
    unescaped_frame = bytes((0x7E, (length >> 8) & 0xFF, length & 0xFF)) + frame_data + bytes(
        (checksum,)
    )
    escaped_frame, escaped_positions = escape_ap2(unescaped_frame)

    return {
        "schema": "mechphy.xbee_api_escaped.golden",
        "description": "Generic XBee API AP=2 escaped-frame vector carrying the telemetry golden packet as payload.",
        "todo_verify_note": (
            "This is not a product-ready XBee-PRO 900HP transmit request. "
            "Transmit request, transmit status, and receive packet frame type IDs remain TODO_VERIFY "
            "until checked against the Digi XBee-PRO 900HP / XBP9B product manual."
        ),
        "xbee_api_rules": {
            "start_delimiter": "0x7E",
            "escape_byte": "0x7D",
            "escape_transform": "escaped_byte = original_byte XOR 0x20",
            "escaped_mode_ap": 2,
            "bytes_to_escape": ["0x7E", "0x7D", "0x11", "0x13"],
            "length_byte_order": "big-endian",
            "length_covers": "frame data only",
            "checksum_rule": "checksum = 0xFF - (sum(frame_data) & 0xFF)",
        },
        "dummy_frame_data_explanation": (
            "The frame data starts with a test-only dummy prefix F0 7E 7D 11 13, followed by "
            "the 40-byte telemetry packet. The prefix deliberately includes 0x7E, 0x7D, "
            "0x11, and 0x13 so AP=2 escaping is covered. 0xF0 is a dummy test byte, not "
            "a verified XBee product frame type."
        ),
        "dummy_prefix_hex": hex_string(dummy_prefix),
        "telemetry_payload_size_bytes": len(telemetry_packet),
        "telemetry_payload_hex": hex_string(telemetry_packet),
        "frame_data_size_bytes": len(frame_data),
        "frame_data_hex": hex_string(frame_data),
        "frame_data_bytes": byte_array(frame_data),
        "checksum": checksum,
        "checksum_hex": hex_byte(checksum),
        "unescaped_api_frame_size_bytes": len(unescaped_frame),
        "unescaped_api_frame_hex": hex_string(unescaped_frame),
        "unescaped_api_frame_bytes": byte_array(unescaped_frame),
        "escaped_api_frame_size_bytes": len(escaped_frame),
        "escaped_api_frame_hex": hex_string(escaped_frame),
        "escaped_api_frame_bytes": byte_array(escaped_frame),
        "escaped_positions": escaped_positions,
        "todo_verify_frame_types": [
            "Transmit Request 64-bit address frame type",
            "Transmit Status frame type",
            "Receive Packet frame type",
        ],
    }


def stable_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2) + "\n"


def write_outputs() -> None:
    telemetry_json, telemetry_packet = build_telemetry_json()
    xbee_json = build_xbee_json(telemetry_packet)
    TELEMETRY_JSON.write_text(stable_json(telemetry_json), encoding="utf-8")
    XBEE_JSON.write_text(stable_json(xbee_json), encoding="utf-8")


def check_outputs() -> int:
    telemetry_json, telemetry_packet = build_telemetry_json()
    xbee_json = build_xbee_json(telemetry_packet)
    expected = {
        TELEMETRY_JSON: stable_json(telemetry_json),
        XBEE_JSON: stable_json(xbee_json),
    }

    for path, content in expected.items():
        if not path.exists():
            print(f"missing: {path}")
            return 1
        actual = path.read_text(encoding="utf-8")
        if actual != content:
            print(f"mismatch: {path}")
            return 1

    print("golden vector JSON files match generator output")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify committed JSON matches output")
    args = parser.parse_args()

    if args.check:
        return check_outputs()

    write_outputs()
    print(f"wrote {TELEMETRY_JSON}")
    print(f"wrote {XBEE_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
