"""PySide6 command-centre prototype UI."""

from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QDoubleSpinBox,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .map_model import MapNode, map_node_from_row, project_nodes
from .simulator import XBeeGoldenReplaySimulator
from .storage import TelemetryStore
from .telemetry_protocol import TelemetryRecord, decode_gnss_packet, load_golden_telemetry_packet


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


class MapPanel(QWidget):
    """Offline placeholder map panel using a QGraphicsScene scatter plot."""

    SCENE_WIDTH = 520
    SCENE_HEIGHT = 360

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title = QLabel("Location Panel")
        self.summary = QLabel("No nodes loaded.")
        self.summary.setWordWrap(True)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)

        self.view = QGraphicsView(self.scene)
        self.view.setMinimumHeight(280)
        self.view.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.view)
        layout.addWidget(self.summary)
        self.setLayout(layout)

        self.update_nodes([])

    def update_nodes(self, nodes: list[MapNode]) -> None:
        self.scene.clear()
        self.scene.setSceneRect(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
        self._draw_background()

        projection = project_nodes(nodes, self.SCENE_WIDTH, self.SCENE_HEIGHT)
        marker_brush = QBrush(QColor("#1769aa"))
        marker_pen = QPen(QColor("#0b3558"))

        for projected in projection.nodes:
            radius = 7.0
            self.scene.addEllipse(
                projected.x - radius,
                projected.y - radius,
                radius * 2.0,
                radius * 2.0,
                marker_pen,
                marker_brush,
            )
            self.scene.addText(f"Node {projected.node.node_id}").setPos(
                projected.x + 10.0, projected.y - 12.0
            )

        if nodes:
            latest = nodes[-1]
            self.summary.setText(
                "Node ID: {node_id}\nLatitude: {lat:.7f}\nLongitude: {lon:.7f}\n"
                "Last seen: {last_seen}".format(
                    node_id=latest.node_id,
                    lat=latest.latitude,
                    lon=latest.longitude,
                    last_seen=latest.last_seen,
                )
            )
        else:
            self.summary.setText("No nodes loaded.")

    def _draw_background(self) -> None:
        border_pen = QPen(QColor("#9aa6b2"))
        grid_pen = QPen(QColor("#d8dee6"))
        self.scene.addRect(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT, border_pen)
        for x in range(80, self.SCENE_WIDTH, 80):
            self.scene.addLine(float(x), 0.0, float(x), float(self.SCENE_HEIGHT), grid_pen)
        for y in range(60, self.SCENE_HEIGHT, 60):
            self.scene.addLine(0.0, float(y), float(self.SCENE_WIDTH), float(y), grid_pen)
        self.scene.addText("Offline placeholder map").setPos(10.0, 8.0)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_database_path() -> Path:
    return Path(__file__).resolve().parents[2] / "mechphy_command_center.sqlite3"


def default_golden_vector_path() -> Path:
    return repository_root() / "test-data" / "telemetry_gnss_v1_golden.json"


def default_xbee_vector_path() -> Path:
    return repository_root() / "test-data" / "xbee_api_escaped_golden.json"


class MainWindow(QMainWindow):
    def __init__(
        self,
        store: TelemetryStore | None = None,
        golden_vector_path: Path | None = None,
        xbee_vector_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("MECHPHY Command Centre")
        self.resize(1080, 640)

        self.store = store or TelemetryStore(default_database_path())
        self.golden_vector_path = golden_vector_path or default_golden_vector_path()
        self.xbee_vector_path = xbee_vector_path or default_xbee_vector_path()
        self.simulator: XBeeGoldenReplaySimulator | None = None

        self.load_golden_button = QPushButton("Load Golden Vector")
        self.load_golden_button.clicked.connect(self.load_golden_vector)

        self.start_simulation_button = QPushButton("Start Simulation")
        self.start_simulation_button.clicked.connect(self.start_simulation)

        self.stop_simulation_button = QPushButton("Stop Simulation")
        self.stop_simulation_button.clicked.connect(self.stop_simulation)
        self.stop_simulation_button.setEnabled(False)

        self.interval_seconds = QDoubleSpinBox()
        self.interval_seconds.setRange(0.25, 3600.0)
        self.interval_seconds.setSingleStep(0.5)
        self.interval_seconds.setDecimals(2)
        self.interval_seconds.setValue(2.0)
        self.interval_seconds.setSuffix(" s")

        self.com_stub_button = QPushButton("COM Live TODO")
        self.com_stub_button.setEnabled(False)

        self.simulation_timer = QTimer(self)
        self.simulation_timer.timeout.connect(self.run_simulation_step)

        self.table = QTableWidget(0, len(TABLE_COLUMNS))
        self.table.setHorizontalHeaderLabels(TABLE_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        self.status_log = QPlainTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumBlockCount(500)
        self.status_log.setPlaceholderText("Status")

        self.map_panel = MapPanel()

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.load_golden_button)
        toolbar.addWidget(self.start_simulation_button)
        toolbar.addWidget(self.stop_simulation_button)
        toolbar.addWidget(self.interval_seconds)
        toolbar.addWidget(self.com_stub_button)
        toolbar.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(toolbar)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(self.table)
        content_splitter.addWidget(self.map_panel)
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 2)

        layout.addWidget(content_splitter)
        layout.addWidget(self.status_log)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.refresh_table()
        self.append_status("Ready. COM live reading is not implemented yet.")

    def load_golden_vector(self) -> None:
        try:
            packet = load_golden_telemetry_packet(self.golden_vector_path)
            self.handle_telemetry_packet(packet, source="Golden vector")
        except Exception as exc:  # pragma: no cover - UI error presentation only
            QMessageBox.critical(self, "Load failed", str(exc))

    def start_simulation(self) -> None:
        try:
            self.simulator = XBeeGoldenReplaySimulator(self.xbee_vector_path)
            interval_ms = int(self.interval_seconds.value() * 1000)
            self.simulation_timer.start(interval_ms)
            self.start_simulation_button.setEnabled(False)
            self.stop_simulation_button.setEnabled(True)
            self.interval_seconds.setEnabled(False)
            self.append_status(f"Simulation started at {self.interval_seconds.value():.2f}s interval.")
            self.run_simulation_step()
        except Exception as exc:  # pragma: no cover - UI error presentation only
            self.stop_simulation()
            QMessageBox.critical(self, "Simulation failed", str(exc))

    def stop_simulation(self) -> None:
        self.simulation_timer.stop()
        self.simulator = None
        self.start_simulation_button.setEnabled(True)
        self.stop_simulation_button.setEnabled(False)
        self.interval_seconds.setEnabled(True)
        self.append_status("Simulation stopped.")

    def run_simulation_step(self) -> None:
        if self.simulator is None:
            return

        try:
            record = self.simulator.next_record()
            self.handle_decoded_record(record, source="Simulation")
        except Exception as exc:  # pragma: no cover - UI error presentation only
            self.stop_simulation()
            QMessageBox.critical(self, "Simulation failed", str(exc))

    def handle_telemetry_packet(self, packet: bytes, source: str) -> None:
        record = decode_gnss_packet(packet)
        self.handle_decoded_record(record, source=source)

    def handle_decoded_record(self, record: TelemetryRecord, source: str) -> None:
        self.store.upsert_telemetry(record)
        self.refresh_table()
        self.append_status(
            f"{source}: node {record.node_id} sequence {record.sequence_number} stored."
        )

    def append_status(self, message: str) -> None:
        self.status_log.appendPlainText(message)

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
        self.refresh_map(rows)

    def refresh_map(self, rows: list[object]) -> None:
        nodes = [map_node_from_row(row) for row in rows]
        self.map_panel.update_nodes(nodes)

    @staticmethod
    def _format_utc(utc_time: int) -> str:
        if utc_time == 0:
            return ""
        from datetime import datetime, timezone

        return datetime.fromtimestamp(utc_time, tz=timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )

    def closeEvent(self, event: object) -> None:  # noqa: N802 - Qt method name
        self.simulation_timer.stop()
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
