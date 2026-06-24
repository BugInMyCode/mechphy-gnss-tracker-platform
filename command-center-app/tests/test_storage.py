from __future__ import annotations

from pathlib import Path

import pytest

from mechphy_command_center.storage import TelemetryStore
from mechphy_command_center.telemetry_protocol import decode_gnss_packet, load_golden_telemetry_packet


REPO_ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_GOLDEN = REPO_ROOT / "test-data" / "telemetry_gnss_v1_golden.json"


def test_sqlite_insert_and_read_temp_database(tmp_path: Path) -> None:
    packet = load_golden_telemetry_packet(TELEMETRY_GOLDEN)
    record = decode_gnss_packet(packet)
    database_path = tmp_path / "command_center.sqlite3"

    with TelemetryStore(database_path) as store:
        store.upsert_telemetry(record, last_seen="2026-06-25T00:00:00Z")
        rows = store.list_nodes()

    assert len(rows) == 1
    row = rows[0]
    assert row["node_id"] == record.node_id
    assert row["sequence_number"] == record.sequence_number
    assert row["utc_time"] == record.utc_time
    assert row["latitude_degrees"] == pytest.approx(record.latitude_degrees)
    assert row["longitude_degrees"] == pytest.approx(record.longitude_degrees)
    assert row["battery_mv"] == record.battery_mv
    assert row["satellite_count"] == record.satellite_count
    assert row["hdop"] == pytest.approx(record.hdop)
    assert row["last_seen"] == "2026-06-25T00:00:00Z"


def test_sqlite_upsert_keeps_one_row_for_node(tmp_path: Path) -> None:
    packet = load_golden_telemetry_packet(TELEMETRY_GOLDEN)
    record = decode_gnss_packet(packet)

    with TelemetryStore(tmp_path / "command_center.sqlite3") as store:
        store.upsert_telemetry(record, last_seen="2026-06-25T00:00:00Z")
        store.upsert_telemetry(record, last_seen="2026-06-25T00:01:00Z")
        rows = store.list_nodes()

    assert len(rows) == 1
    assert rows[0]["last_seen"] == "2026-06-25T00:01:00Z"
