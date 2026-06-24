"""XBee API and API Escaped Mode frame decoding helpers."""

from __future__ import annotations

from dataclasses import dataclass


START_DELIMITER = 0x7E
ESCAPE_BYTE = 0x7D
ESCAPE_XOR = 0x20
ESCAPED_VALUES = {0x7E, 0x7D, 0x11, 0x13}


class XBeeApiError(ValueError):
    """Raised when an XBee API frame fails validation."""


@dataclass(frozen=True)
class XBeeApiFrame:
    frame_data: bytes
    checksum: int
    length: int


def calculate_checksum(frame_data: bytes) -> int:
    return (0xFF - (sum(frame_data) & 0xFF)) & 0xFF


def validate_checksum(frame_data: bytes, checksum: int) -> None:
    if ((sum(frame_data) + checksum) & 0xFF) != 0xFF:
        raise XBeeApiError("xbee checksum validation failed")


def unescape_ap2_frame(frame: bytes) -> bytes:
    if not frame:
        raise XBeeApiError("empty xbee frame")
    if frame[0] != START_DELIMITER:
        raise XBeeApiError("missing xbee start delimiter")

    unescaped = bytearray((START_DELIMITER,))
    index = 1
    while index < len(frame):
        byte = frame[index]
        if byte == ESCAPE_BYTE:
            index += 1
            if index >= len(frame):
                raise XBeeApiError("trailing xbee escape byte")
            original = frame[index] ^ ESCAPE_XOR
            if original not in ESCAPED_VALUES:
                raise XBeeApiError("invalid xbee escape sequence")
            unescaped.append(original)
        else:
            if byte in (START_DELIMITER, 0x11, 0x13):
                raise XBeeApiError("unescaped reserved byte in AP=2 frame")
            unescaped.append(byte)
        index += 1
    return bytes(unescaped)


def decode_api_frame(frame: bytes, *, escaped: bool = False) -> XBeeApiFrame:
    raw = unescape_ap2_frame(frame) if escaped else frame
    if len(raw) < 4:
        raise XBeeApiError("xbee frame too short")
    if raw[0] != START_DELIMITER:
        raise XBeeApiError("missing xbee start delimiter")

    length = int.from_bytes(raw[1:3], "big")
    expected_size = 1 + 2 + length + 1
    if len(raw) != expected_size:
        raise XBeeApiError(f"xbee length mismatch expected {expected_size} bytes, got {len(raw)}")

    frame_data = raw[3 : 3 + length]
    checksum = raw[3 + length]
    validate_checksum(frame_data, checksum)
    return XBeeApiFrame(frame_data=frame_data, checksum=checksum, length=length)


def extract_trailing_payload(frame_data: bytes, payload_size: int) -> bytes:
    if payload_size < 0:
        raise XBeeApiError("payload size must be non-negative")
    if len(frame_data) < payload_size:
        raise XBeeApiError("frame data shorter than requested payload")
    return frame_data[-payload_size:]
