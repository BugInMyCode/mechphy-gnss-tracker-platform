"""PySide6 command-centre prototype UI."""

from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .storage import TelemetryStore
from .telemetry_protocol import decode_gnss_packet, load_golden_telemetry_packet


TABLE_COLUMNS = [
    "Node ID",
    "UTC Time",
    "Latitude",
    "Longitude",
    "Battery mV",
    "Satellites",
    "HDOP",
    "Last Seen",
]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_database_path() -> Path:
    return Path(__file__).resolve().parents[2] / "mechphy_command_center.sqlite3"


def default_golden_vector_path() -> Path:
    return repository_root() / "test-data" / "telemetry_gnss_v1_golden.json"


class MainWindow(QMainWindow):
    def __init__(
        self,
        store: TelemetryStore | None = None,
        golden_vector_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("MECHPHY Command Centre")
        self.resize(980, 520)

        self.store = store or TelemetryStore(default_database_path())
        self.golden_vector_path = golden_vector_path or default_golden_vector_path()

        self.load_golden_button = QPushButton("Load Golden Vector")
        self.load_golden_button.clicked.connect(self.load_golden_vector)

        self.com_stub_button = QPushButton("COM Live TODO")
        self.com_stub_button.setEnabled(False)

        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.load_golden_button)
        toolbar.addWidget(self.com_stub_button)
        toolbar.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.refresh_table()

    def load_golden_vector(self) -> None:
        try:
            packet = load_golden_telemetry_packet(self.golden_vector_path)
            record = decode_gnss_packet(packet)
            self.store.upsert_telemetry(record)
            self.refresh_table()
        except Exception as exc:  # pragma: no cover - UI error presentation only
            QMessageBox.critical(self, "Load failed", str(exc))

    def refresh_table(self) -> None:
        rows = self.store.list_nodes()
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                str(row["node_id"]),
                self._format_utc(row["utc_time"]),
                f"{row['latitude_degrees']:.7f}",
                f"{row['longitude_degrees']:.7f}",
                str(row["battery_mv"]),
                str(row["satellite_count"]),
                f"{row['hdop']:.1f}",
                row["last_seen"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index in {0, 4, 5, 6}:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_index, column_index, item)

        self.table.resizeColumnsToContents()

    @staticmethod
    def _format_utc(utc_time: int) -> str:
        if utc_time == 0:
            return ""
        from datetime import UTC, datetime

        return datetime.fromtimestamp(utc_time, tz=UTC).isoformat().replace("+00:00", "Z")

    def closeEvent(self, event: object) -> None:  # noqa: N802 - Qt method name
        self.store.close()
        super().closeEvent(event)


def run(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    qt_app = QApplication(args)
    window = MainWindow()
    if "--smoke-test" in args:
        window.load_golden_vector()
        return 0
    window.show()
    return qt_app.exec()
