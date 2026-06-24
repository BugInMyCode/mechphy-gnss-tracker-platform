"""SQLite storage for decoded MECHPHY telemetry."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sqlite3

from .telemetry_protocol import TelemetryRecord


class TelemetryStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS node_telemetry (
                node_id INTEGER PRIMARY KEY,
                sequence_number INTEGER NOT NULL,
                utc_time INTEGER NOT NULL,
                latitude_e7 INTEGER NOT NULL,
                longitude_e7 INTEGER NOT NULL,
                latitude_degrees REAL NOT NULL,
                longitude_degrees REAL NOT NULL,
                altitude_cm INTEGER NOT NULL,
                fix_type INTEGER NOT NULL,
                satellite_count INTEGER NOT NULL,
                hdop_x10 INTEGER NOT NULL,
                hdop REAL NOT NULL,
                battery_mv INTEGER NOT NULL,
                temperature_c_x10 INTEGER NOT NULL,
                temperature_c REAL NOT NULL,
                status_flags INTEGER NOT NULL,
                crc16 INTEGER NOT NULL,
                last_seen TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def upsert_telemetry(self, record: TelemetryRecord, last_seen: str | None = None) -> None:
        observed_at = last_seen or datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
        self.connection.execute(
            """
            INSERT INTO node_telemetry (
                node_id,
                sequence_number,
                utc_time,
                latitude_e7,
                longitude_e7,
                latitude_degrees,
                longitude_degrees,
                altitude_cm,
                fix_type,
                satellite_count,
                hdop_x10,
                hdop,
                battery_mv,
                temperature_c_x10,
                temperature_c,
                status_flags,
                crc16,
                last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                sequence_number = excluded.sequence_number,
                utc_time = excluded.utc_time,
                latitude_e7 = excluded.latitude_e7,
                longitude_e7 = excluded.longitude_e7,
                latitude_degrees = excluded.latitude_degrees,
                longitude_degrees = excluded.longitude_degrees,
                altitude_cm = excluded.altitude_cm,
                fix_type = excluded.fix_type,
                satellite_count = excluded.satellite_count,
                hdop_x10 = excluded.hdop_x10,
                hdop = excluded.hdop,
                battery_mv = excluded.battery_mv,
                temperature_c_x10 = excluded.temperature_c_x10,
                temperature_c = excluded.temperature_c,
                status_flags = excluded.status_flags,
                crc16 = excluded.crc16,
                last_seen = excluded.last_seen
            """,
            (
                record.node_id,
                record.sequence_number,
                record.utc_time,
                record.latitude_e7,
                record.longitude_e7,
                record.latitude_degrees,
                record.longitude_degrees,
                record.altitude_cm,
                record.fix_type,
                record.satellite_count,
                record.hdop_x10,
                record.hdop,
                record.battery_mv,
                record.temperature_c_x10,
                record.temperature_c,
                record.status_flags,
                record.crc16,
                observed_at,
            ),
        )
        self.connection.commit()

    def list_nodes(self) -> list[sqlite3.Row]:
        rows = self.connection.execute(
            """
            SELECT
                node_id,
                sequence_number,
                utc_time,
                latitude_degrees,
                longitude_degrees,
                battery_mv,
                satellite_count,
                hdop,
                last_seen
            FROM node_telemetry
            ORDER BY node_id ASC
            """
        ).fetchall()
        return list(rows)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "TelemetryStore":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
