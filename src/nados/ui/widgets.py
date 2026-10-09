"""
UI widgets for NADOS Dv1.0.
"""

from PyQt6.QtCharts import QChartView
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from nados.reporting import ReportFormat
from nados.ui.arabic_support import translate_ui


class SimulationView(QWidget):
    """2D schematic map view for simulation."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(800, 600)
        self.objects = {}  # object_id -> (position, velocity, trail)
        self.sensors = {}  # sensor_id -> position
        self.tracks = {}  # track_id -> (position, velocity, covariance)
        self.selected_object = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Canvas for drawing
        self.canvas = SimulationCanvas(self)
        layout.addWidget(self.canvas)

        # Legend
        legend = self._create_legend()
        layout.addWidget(legend)

    def _create_legend(self) -> QWidget:
        legend = QWidget()
        legend.setMaximumHeight(60)
        layout = QHBoxLayout(legend)

        items = [
            ("●", "#00ff00", translate_ui("sensor_locations")),
            ("▲", "#ff0000", translate_ui("object_positions")),
            ("■", "#00ffff", translate_ui("estimated_tracks")),
            ("⋯", "#888888", translate_ui("historical_trails")),
        ]

        for symbol, color, label in items:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 0, 5, 0)

            lbl_symbol = QLabel(symbol)
            lbl_symbol.setStyleSheet(f"color: {color}; font-size: 16px;")
            item_layout.addWidget(lbl_symbol)

            lbl_text = QLabel(label)
            lbl_text.setStyleSheet("color: #aaa;")
            item_layout.addWidget(lbl_text)

            layout.addWidget(item_widget)

        layout.addStretch()
        return legend

    def update_objects(self, objects: dict) -> None:
        """Update object positions."""
        self.objects = objects
        self.canvas.update()

    def update_sensors(self, sensors: dict) -> None:
        """Update sensor positions."""
        self.sensors = sensors
        self.canvas.update()

    def update_tracks(self, tracks: dict) -> None:
        """Update track estimates."""
        self.tracks = tracks
        self.canvas.update()

    def set_selected_object(self, object_id: str) -> None:
        """Set selected object for detail view."""
        self.selected_object = object_id
        self.canvas.update()


class SimulationCanvas(QWidget):
    """Custom canvas for drawing simulation map."""

    def __init__(self, parent_view: SimulationView) -> None:
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)

        # View transform
        self.center_x = 0.0
        self.center_y = 0.0
        self.scale = 0.01  # meters to pixels
        self.dragging = False
        self.last_mouse_pos = None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#0a0a1a"))

        # Grid
        self._draw_grid(painter)

        # Axes
        self._draw_axes(painter)

        # Scale label
        painter.setPen(QColor("#666"))
        painter.drawText(10, 20, f"مقياس: 1px = {1 / self.scale:.0f}m")

        # Draw sensors
        self._draw_sensors(painter)

        # Draw objects
        self._draw_objects(painter)

        # Draw tracks
        self._draw_tracks(painter)

        # Draw selection highlight
        if self.parent_view.selected_object and self.parent_view.selected_object in self.parent_view.objects:
            self._draw_selection(painter, self.parent_view.selected_object)

        # Simulation label
        painter.setPen(QColor("#e94560"))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(self.width() - 120, self.height() - 10, translate_ui("simulation_label"))

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#1a1a3e"), 1))

        # Convert grid spacing to screen coordinates
        grid_spacing = 10000  # 10km grid
        screen_spacing = grid_spacing * self.scale

        if screen_spacing < 20:
            return

        # Vertical lines
        left_world = -self.center_x / self.scale
        right_world = (self.width() - self.center_x) / self.scale

        start_x = int(left_world / grid_spacing) * grid_spacing
        x = start_x
        while x <= right_world:
            screen_x = self._world_to_screen_x(x)
            painter.drawLine(int(screen_x), 0, int(screen_x), self.height())
            x += grid_spacing

        # Horizontal lines
        top_world = -self.center_y / self.scale
        bottom_world = (self.height() - self.center_y) / self.scale

        start_y = int(top_world / grid_spacing) * grid_spacing
        y = start_y
        while y <= bottom_world:
            screen_y = self._world_to_screen_y(y)
            painter.drawLine(0, int(screen_y), self.width(), int(screen_y))
            y += grid_spacing

    def _draw_axes(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#444"), 2))

        # X axis (East)
        screen_y = self._world_to_screen_y(0)
        painter.drawLine(0, int(screen_y), self.width(), int(screen_y))
        painter.drawText(self.width() - 30, int(screen_y) - 5, "شرق (E)")

        # Y axis (North)
        screen_x = self._world_to_screen_x(0)
        painter.drawLine(int(screen_x), 0, int(screen_x), self.height())
        painter.drawText(int(screen_x) + 5, 20, "شمال (N)")

    def _draw_sensors(self, painter: QPainter) -> None:
        painter.setBrush(QBrush(QColor("#00ff00")))
        painter.setPen(QPen(QColor("#00aa00"), 2))

        for sensor_id, pos in self.parent_view.sensors.items():
            screen_x = self._world_to_screen_x(pos.x)
            screen_y = self._world_to_screen_y(pos.y)

            # Sensor symbol (circle)
            painter.drawEllipse(QPointF(screen_x, screen_y), 8, 8)

            # Sensor label
            painter.setPen(QColor("#00ff00"))
            painter.drawText(int(screen_x) + 12, int(screen_y) + 4, sensor_id)
            painter.setPen(QPen(QColor("#00aa00"), 2))

            # Field of view indicator (optional)
            # painter.drawEllipse(QPointF(screen_x, screen_y), 50000 * self.scale, 50000 * self.scale)

    def _draw_objects(self, painter: QPainter) -> None:
        painter.setBrush(QBrush(QColor("#ff0000")))
        painter.setPen(QPen(QColor("#aa0000"), 2))

        for obj_id, (pos, vel, trail) in self.parent_view.objects.items():
            screen_x = self._world_to_screen_x(pos.x)
            screen_y = self._world_to_screen_y(pos.y)

            # Object symbol (triangle pointing in velocity direction)
            if vel.x != 0 or vel.y != 0:
                import math

                angle = math.atan2(vel.y, vel.x)
                size = 10
                points = QPolygonF()
                points.append(QPointF(screen_x + size * math.cos(angle), screen_y + size * math.sin(angle)))
                points.append(QPointF(screen_x + size * math.cos(angle + 2.5), screen_y + size * math.sin(angle + 2.5)))
                points.append(QPointF(screen_x + size * math.cos(angle - 2.5), screen_y + size * math.sin(angle - 2.5)))
                painter.drawPolygon(points)
            else:
                painter.drawEllipse(QPointF(screen_x, screen_y), 8, 8)

            # Trail
            if trail and len(trail) > 1:
                painter.setPen(QPen(QColor("#888888"), 1))
                trail_points = [QPointF(self._world_to_screen_x(p.x), self._world_to_screen_y(p.y)) for p in trail]
                for i in range(len(trail_points) - 1):
                    painter.drawLine(trail_points[i], trail_points[i + 1])
                painter.setPen(QPen(QColor("#aa0000"), 2))

            # Object label
            painter.setPen(QColor("#ffaaaa"))
            painter.drawText(int(screen_x) + 12, int(screen_y) - 12, obj_id)
            painter.setPen(QPen(QColor("#aa0000"), 2))

    def _draw_tracks(self, painter: QPainter) -> None:
        painter.setBrush(QBrush(QColor("#00ffff")))
        painter.setPen(QPen(QColor("#00aaaa"), 2))

        for track_id, (pos, _vel, cov) in self.parent_view.tracks.items():
            screen_x = self._world_to_screen_x(pos.x)
            screen_y = self._world_to_screen_y(pos.y)

            # Track symbol (square)
            painter.drawRect(QRectF(screen_x - 6, screen_y - 6, 12, 12))

            # Uncertainty ellipse (simplified as circle using covariance trace)
            if cov:
                import math

                trace = cov[0][0] + cov[1][1]
                radius = math.sqrt(trace) * self.scale * 2  # 2-sigma
                if radius > 2:
                    painter.setPen(QPen(QColor("#0088aa"), 1, Qt.PenStyle.DashLine))
                    painter.drawEllipse(QPointF(screen_x, screen_y), radius, radius)
                    painter.setPen(QPen(QColor("#00aaaa"), 2))

            # Track label
            painter.setPen(QColor("#aaffff"))
            painter.drawText(int(screen_x) + 12, int(screen_y) + 4, f"T:{track_id}")
            painter.setPen(QPen(QColor("#00aaaa"), 2))

    def _draw_selection(self, painter: QPainter, object_id: str) -> None:
        pos, vel, trail = self.parent_view.objects[object_id]
        screen_x = self._world_to_screen_x(pos.x)
        screen_y = self._world_to_screen_y(pos.y)

        painter.setPen(QPen(QColor("#ffff00"), 3))
        painter.drawEllipse(QPointF(screen_x, screen_y), 15, 15)

    def _world_to_screen_x(self, world_x: float) -> float:
        return self.center_x + world_x * self.scale

    def _world_to_screen_y(self, world_y: float) -> float:
        return self.center_y - world_y * self.scale  # Y inverted for screen

    def _screen_to_world_x(self, screen_x: float) -> float:
        return (screen_x - self.center_x) / self.scale

    def _screen_to_world_y(self, screen_y: float) -> float:
        return (self.center_y - screen_y) / self.scale

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.position()
        elif event.button() == Qt.MouseButton.RightButton:
            # Select object at position
            world_x = self._screen_to_world_x(event.position().x())
            world_y = self._screen_to_world_y(event.position().y())
            self._select_object_at(world_x, world_y)

    def mouseMoveEvent(self, event) -> None:
        if self.dragging and self.last_mouse_pos:
            delta = event.position() - self.last_mouse_pos
            self.center_x += delta.x()
            self.center_y += delta.y()
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def wheelEvent(self, event) -> None:
        # Zoom
        factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.scale *= factor
        self.scale = max(0.0001, min(1.0, self.scale))
        self.update()

    def _select_object_at(self, world_x: float, world_y: float) -> None:
        """Select object near world position."""
        min_dist = float("inf")
        selected = None

        for obj_id, (pos, _vel, _trail) in self.parent_view.objects.items():
            dist = ((pos.x - world_x) ** 2 + (pos.y - world_y) ** 2) ** 0.5
            if dist < min_dist and dist < 50000:  # Within 50km
                min_dist = dist
                selected = obj_id

        self.parent_view.set_selected_object(selected)


class MonitoringDashboard(QWidget):
    """Monitoring dashboard with metrics."""

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Scroll area for metrics
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        # System status group
        status_group = QGroupBox(translate_ui("system_health"))
        status_layout = QGridLayout(status_group)

        self.metrics_labels = {}
        metrics = [
            ("active_objects", translate_ui("active_objects"), "0"),
            ("valid_observations", translate_ui("valid_observations"), "0"),
            ("active_tracks", translate_ui("active_tracks"), "0"),
            ("dropout_rate", translate_ui("dropout_rate"), "0%"),
            ("false_alarms", translate_ui("false_alarms"), "0"),
            ("avg_latency", translate_ui("avg_latency"), "N/A"),
            ("simulation_runtime", translate_ui("simulation_runtime"), "0.0s"),
            ("cpu_usage", translate_ui("cpu_usage"), "N/A"),
            ("memory_usage", translate_ui("memory_usage"), "N/A"),
            ("database_status", translate_ui("database_status"), translate_ui("database_connected")),
        ]

        for i, (key, label, default) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2

            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold;")
            status_layout.addWidget(lbl, row, col)

            val = QLabel(default)
            val.setStyleSheet("color: #00ff00; font-family: monospace;")
            status_layout.addWidget(val, row, col + 1)

            self.metrics_labels[key] = val

        content_layout.addWidget(status_group)

        # Charts placeholder
        charts_group = QGroupBox(translate_ui("time_series_charts"))
        charts_layout = QVBoxLayout(charts_group)

        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(300)
        charts_layout.addWidget(self.chart_view)

        content_layout.addWidget(charts_group)

        # Recent events
        events_group = QGroupBox(translate_ui("event_log"))
        events_layout = QVBoxLayout(events_group)

        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(150)
        events_layout.addWidget(self.events_list)

        content_layout.addWidget(events_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def update_metrics(self, metrics: dict) -> None:
        """Update dashboard metrics."""
        for key, value in metrics.items():
            if key in self.metrics_labels:
                if isinstance(value, float):
                    self.metrics_labels[key].setText(f"{value:.2f}")
                else:
                    self.metrics_labels[key].setText(str(value))

    def add_event(self, event_text: str, severity: str = "info") -> None:
        """Add event to log."""
        color_map = {
            "info": "#00ffff",
            "warning": "#ffaa00",
            "error": "#ff0000",
            "critical": "#ff00ff",
        }
        color = color_map.get(severity, "#ffffff")

        item = QListWidgetItem(event_text)
        item.setForeground(QColor(color))
        self.events_list.insertItem(0, item)

        # Keep only last 100 events
        while self.events_list.count() > 100:
            self.events_list.takeItem(self.events_list.count() - 1)


class ScenarioEditor(QWidget):
    """Scenario editor widget."""

    scenario_saved = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        form_layout = QFormLayout(content)

        # Scenario basic info
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(translate_ui("scenario_name"))
        form_layout.addRow(translate_ui("scenario_name"), self.name_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText(translate_ui("scenario_description"))
        form_layout.addRow(translate_ui("scenario_description"), self.desc_edit)

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" " + "ثواني")
        form_layout.addRow(translate_ui("duration"), self.duration_spin)

        self.timestep_spin = QDoubleSpinBox()
        self.timestep_spin.setRange(0.01, 1.0)
        self.timestep_spin.setValue(0.1)
        self.timestep_spin.setSingleStep(0.01)
        self.timestep_spin.setSuffix(" " + "ثواني")
        form_layout.addRow(translate_ui("timestep"), self.timestep_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2**31 - 1)
        self.seed_spin.setValue(42)
        form_layout.addRow(translate_ui("random_seed"), self.seed_spin)

        # Objects list
        objects_group = QGroupBox("الأجسام الافتراضية")
        objects_layout = QVBoxLayout(objects_group)

        self.objects_list = QListWidget()
        objects_layout.addWidget(self.objects_list)

        obj_buttons = QHBoxLayout()
        add_obj_btn = QPushButton(translate_ui("add_object"))
        add_obj_btn.clicked.connect(self._add_object)
        obj_buttons.addWidget(add_obj_btn)

        remove_obj_btn = QPushButton("إزالة الجسم")
        remove_obj_btn.clicked.connect(self._remove_object)
        obj_buttons.addWidget(remove_obj_btn)

        objects_layout.addLayout(obj_buttons)
        form_layout.addRow(objects_group)

        # Sensors list
        sensors_group = QGroupBox("المستشعرات الافتراضية")
        sensors_layout = QVBoxLayout(sensors_group)

        self.sensors_list = QListWidget()
        sensors_layout.addWidget(self.sensors_list)

        sensor_buttons = QHBoxLayout()
        add_sensor_btn = QPushButton(translate_ui("add_sensor"))
        add_sensor_btn.clicked.connect(self._add_sensor)
        sensor_buttons.addWidget(add_sensor_btn)

        remove_sensor_btn = QPushButton("إزالة المستشعر")
        remove_sensor_btn.clicked.connect(self._remove_sensor)
        sensor_buttons.addWidget(remove_sensor_btn)

        sensors_layout.addLayout(sensor_buttons)
        form_layout.addRow(sensors_group)

        # Buttons
        button_layout = QHBoxLayout()

        validate_btn = QPushButton(translate_ui("validate_scenario"))
        validate_btn.clicked.connect(self._validate_scenario)
        button_layout.addWidget(validate_btn)

        save_btn = QPushButton(translate_ui("save_scenario"))
        save_btn.clicked.connect(self._save_scenario)
        button_layout.addWidget(save_btn)

        load_btn = QPushButton(translate_ui("load_scenario"))
        load_btn.clicked.connect(self._load_scenario)
        button_layout.addWidget(load_btn)

        form_layout.addRow(button_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _add_object(self) -> None:
        """Add a new object to the scenario."""
        item = QListWidgetItem("جسم جديد - اضغط للتعديل")
        item.setData(
            Qt.ItemDataRole.UserRole,
            {
                "object_id": f"obj_{self.objects_list.count() + 1}",
                "object_type": "generic",
                "position": [0, 0, 0],
                "velocity": [100, 0, 0],
            },
        )
        self.objects_list.addItem(item)

    def _remove_object(self) -> None:
        """Remove selected object."""
        row = self.objects_list.currentRow()
        if row >= 0:
            self.objects_list.takeItem(row)

    def _add_sensor(self) -> None:
        """Add a new sensor to the scenario."""
        item = QListWidgetItem("مستشعر جديد - اضغط للتعديل")
        item.setData(
            Qt.ItemDataRole.UserRole,
            {
                "sensor_id": f"sensor_{self.sensors_list.count() + 1}",
                "sensor_type": "radar",
                "position": [0, 0, 0],
                "sampling_interval": 1.0,
            },
        )
        self.sensors_list.addItem(item)

    def _remove_sensor(self) -> None:
        """Remove selected sensor."""
        row = self.sensors_list.currentRow()
        if row >= 0:
            self.sensors_list.takeItem(row)

    def _validate_scenario(self) -> None:
        """Validate the current scenario."""
        errors = []

        if not self.name_edit.text().strip():
            errors.append(translate_ui("missing_required_field") + ": " + translate_ui("scenario_name"))

        if self.duration_spin.value() <= 0:
            errors.append(translate_ui("invalid_numeric_value") + ": " + translate_ui("duration"))

        if self.timestep_spin.value() <= 0:
            errors.append(translate_ui("invalid_numeric_value") + ": " + translate_ui("timestep"))

        if errors:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, translate_ui("validation_failed"), "\n".join(errors))
        else:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, translate_ui("validation_passed"), "السيناريو صالح وجاهز للتشغيل")

    def _save_scenario(self) -> None:
        """Save scenario to file."""
        import json

        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self, translate_ui("save_scenario"), "scenarios", "JSON Files (*json)"
        )
        if file_path:
            scenario_data = self._get_scenario_data()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(scenario_data, f, indent=2, ensure_ascii=False)

            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, "نجاح", f"تم حفظ السيناريو في:\n{file_path}")

    def _load_scenario(self) -> None:
        """Load scenario from file."""
        import json

        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, translate_ui("load_scenario"), "scenarios", "JSON Files (*json)"
        )
        if file_path:
            with open(file_path, encoding="utf-8") as f:
                scenario_data = json.load(f)
            self._set_scenario_data(scenario_data)

    def _get_scenario_data(self) -> dict:
        """Get scenario data from UI."""
        objects = []
        for i in range(self.objects_list.count()):
            item = self.objects_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                objects.append(data)

        sensors = []
        for i in range(self.sensors_list.count()):
            item = self.sensors_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                sensors.append(data)

        return {
            "scenario_id": f"scenario_{int(self.seed_spin.value())}",
            "schema_version": "v1",
            "name": self.name_edit.text(),
            "description": self.desc_edit.toPlainText(),
            "duration_seconds": self.duration_spin.value(),
            "timestep_seconds": self.timestep_spin.value(),
            "random_seed": self.seed_spin.value(),
            "coordinate_system": "ENU",
            "virtual_objects": objects,
            "simulated_sensors": sensors,
        }

    def _set_scenario_data(self, data: dict) -> None:
        """Set scenario data to UI."""
        self.name_edit.setText(data.get("name", ""))
        self.desc_edit.setPlainText(data.get("description", ""))
        self.duration_spin.setValue(data.get("duration_seconds", 60))
        self.timestep_spin.setValue(data.get("timestep_seconds", 0.1))
        self.seed_spin.setValue(data.get("random_seed", 42))

        self.objects_list.clear()
        for obj in data.get("virtual_objects", []):
            item = QListWidgetItem(f"{obj.get('object_id', '')} - {obj.get('object_type', '')}")
            item.setData(Qt.ItemDataRole.UserRole, obj)
            self.objects_list.addItem(item)

        self.sensors_list.clear()
        for sensor in data.get("simulated_sensors", []):
            item = QListWidgetItem(f"{sensor.get('sensor_id', '')} - {sensor.get('sensor_type', '')}")
            item.setData(Qt.ItemDataRole.UserRole, sensor)
            self.sensors_list.addItem(item)


class ResultsViewer(QWidget):
    """Results viewer for simulation runs."""

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Run history
        history_group = QGroupBox(translate_ui("run_history"))
        history_layout = QVBoxLayout(history_group)

        self.runs_table = QTableWidget()
        self.runs_table.setColumnCount(6)
        headers = [
            "معرف التشغيل",
            "السيناريو",
            "الحالة",
            "وقت البدء",
            "المدة",
            "بذرة العشوائية",
        ]
        self.runs_table.setHorizontalHeaderLabels(headers)
        self.runs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.runs_table)

        layout.addWidget(history_group)

        # Comparison charts
        charts_group = QGroupBox(translate_ui("scenario_comparison"))
        charts_layout = QVBoxLayout(charts_group)

        self.comparison_chart = QChartView()
        self.comparison_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.comparison_chart)

        layout.addWidget(charts_group)

        # Export buttons
        export_layout = QHBoxLayout()

        export_json = QPushButton("تصدير JSON")
        export_json.clicked.connect(lambda: self._export(ReportFormat.JSON))
        export_layout.addWidget(export_json)

        export_csv = QPushButton("تصدير CSV")
        export_csv.clicked.connect(lambda: self._export(ReportFormat.CSV))
        export_layout.addWidget(export_csv)

        layout.addLayout(export_layout)

    def _export(self, format_type) -> None:
        """Export report."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        from nados.reporting import ReportGenerator

        # TODO: Get selected run ID
        run_id = "demo_run"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"تصدير {format_type.value.upper()}",
            "reports",
            f"{format_type.value.upper()} Files (*.{format_type.value})",
        )

        if file_path:
            try:
                generator = ReportGenerator()
                generator.generate_report(run_id, [format_type])
                QMessageBox.information(self, "نجاح", f"تم تصدير التقرير إلى:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل تصدير التقرير:\n{str(e)}")
