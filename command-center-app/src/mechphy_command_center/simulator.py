"""Golden-vector replay helpers for development without live COM hardware."""

from __future__ import annotations

from pathlib import Path
import json

from .telemetry_protocol import (
    CRC_COVERAGE_SIZE,
    CRC_OFFSET,
    PACKET_SIZE_BYTES,
    TelemetryRecord,
    crc16_ccitt_false,
    decode_gnss_packet,
)
from .xbee_api import decode_api_frame, extract_trailing_payload


SEQUENCE_NUMBER_OFFSET = 8
SEQUENCE_NUMBER_SIZE = 4


class SimulationError(ValueError):
    """Raised when a simulated replay source cannot produce telemetry."""


def load_xbee_escaped_frame(path: str | Path) -> bytes:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return bytes(data["escaped_api_frame_bytes"])


def telemetry_packet_with_sequence(packet: bytes, sequence_number: int) -> bytes:
    if len(packet) != PACKET_SIZE_BYTES:
        raise SimulationError(f"expected {PACKET_SIZE_BYTES} telemetry bytes, got {len(packet)}")
    if not 0 <= sequence_number <= 0xFFFFFFFF:
        raise SimulationError("sequence number must fit in uint32")

    output = bytearray(packet)
    output[
        SEQUENCE_NUMBER_OFFSET : SEQUENCE_NUMBER_OFFSET + SEQUENCE_NUMBER_SIZE
    ] = sequence_number.to_bytes(SEQUENCE_NUMBER_SIZE, "little")
    crc = crc16_ccitt_false(bytes(output[:CRC_COVERAGE_SIZE]))
    output[CRC_OFFSET : CRC_OFFSET + 2] = crc.to_bytes(2, "little")
    return bytes(output)


class XBeeGoldenReplaySimulator:
    """Replay the golden XBee AP=2 frame as a stream of valid telemetry packets."""

    def __init__(self, xbee_golden_path: str | Path) -> None:
        self.xbee_golden_path = Path(xbee_golden_path)
        self._base_packet = self._load_base_packet()
        self._base_record = decode_gnss_packet(self._base_packet)
        self._next_sequence = self._base_record.sequence_number

    def _load_base_packet(self) -> bytes:
        escaped_frame = load_xbee_escaped_frame(self.xbee_golden_path)
        api_frame = decode_api_frame(escaped_frame, escaped=True)
        return extract_trailing_payload(api_frame.frame_data, PACKET_SIZE_BYTES)

    @property
    def base_sequence_number(self) -> int:
        return self._base_record.sequence_number

    def next_packet(self) -> bytes:
        packet = telemetry_packet_with_sequence(self._base_packet, self._next_sequence)
        self._next_sequence = (self._next_sequence + 1) & 0xFFFFFFFF
        return packet

    def next_record(self) -> TelemetryRecord:
        return decode_gnss_packet(self.next_packet())
