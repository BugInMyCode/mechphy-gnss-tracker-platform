from __future__ import annotations

from pathlib import Path

from mechphy_command_center.simulator import (
    XBeeGoldenReplaySimulator,
    load_xbee_escaped_frame,
    telemetry_packet_with_sequence,
)
from mechphy_command_center.storage import TelemetryStore
from mechphy_command_center.telemetry_protocol import (
    decode_gnss_packet,
    load_golden_telemetry_packet,
)
from mechphy_command_center.xbee_api import decode_api_frame


REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_GOLDEN = REPO_ROOT / "test-data" / "telemetry_gnss_v1_golden.json"
XBEE_GOLDEN = REPO_ROOT / "test-data" / "xbee_api_escaped_golden.json"


def test_simulator_decodes_xbee_golden_frame() -> None:
    escaped_frame = load_xbee_escaped_frame(XBEE_GOLDEN)
    api_frame = decode_api_frame(escaped_frame, escaped=True)

    assert api_frame.length == 45
    assert api_frame.frame_data[-40:] == load_golden_telemetry_packet(TELEMETRY_GOLDEN)


def test_simulator_packets_increment_sequence_number() -> None:
    simulator = XBeeGoldenReplaySimulator(XBEE_GOLDEN)

    records = [simulator.next_record(), simulator.next_record(), simulator.next_record()]

    assert [record.sequence_number for record in records] == [42, 43, 44]
    assert {record.node_id for record in records} == {4660}


def test_simulator_regenerates_crc_for_incremented_packet() -> None:
    base_packet = load_golden_telemetry_packet(TELEMETRY_GOLDEN)
    packet = telemetry_packet_with_sequence(base_packet, 99)
    record = decode_gnss_packet(packet)

    assert record.sequence_number == 99


def test_sqlite_stores_simulated_packets(tmp_path: Path) -> None:
    simulator = XBeeGoldenReplaySimulator(XBEE_GOLDEN)

    with TelemetryStore(tmp_path / "simulation.sqlite3") as store:
        first = simulator.next_record()
        second = simulator.next_record()
        store.upsert_telemetry(first, last_seen="2026-06-25T00:00:00Z")
        store.upsert_telemetry(second, last_seen="2026-06-25T00:00:02Z")
        rows = store.list_nodes()

    assert len(rows) == 1
    assert rows[0]["node_id"] == 4660
    assert rows[0]["sequence_number"] == 43
    assert rows[0]["last_seen"] == "2026-06-25T00:00:02Z"
