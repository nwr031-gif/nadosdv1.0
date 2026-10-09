"""
Main application window.
"""

import sys
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QListWidget, QListWidgetItem, QTabWidget,
    QStatusBar, QToolBar, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QProgressBar, QDockWidget, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPalette

from nados.ui.arabic_support import translate_ui, setup_arabic_support
from nados.config import get_config
from nados.observability import get_logger


class SimulationWorker(QThread):
    """Worker thread for running simulation."""
    
    step_completed = pyqtSignal(float, list, list, list)  # time, events, observations, tracks
    simulation_finished = pyqtSignal(bool, str)  # success, message
    error_occurred = pyqtSignal(str)
    
    def __init__(self, engine) -> None:
        super().__init__()
        self.engine = engine
        self._running = False
    
    def run(self) -> None:
        self._running = True
        try:
            result = self.engine.run_sync()
            self.simulation_finished.emit(result.success, result.error or "Completed")
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._running = False
    
    def stop(self) -> None:
        self._running = False
        self.engine.stop()


class MainWindow(QMainWindow):
    """Main application window with Arabic RTL support."""
    
    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger("ui.main_window")
        self.config = get_config()
        self.engine = None
        self.worker: Optional[SimulationWorker] = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()
        
        # Update timer for clock display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_clock_display)
        self.update_timer.start(100)  # 10 Hz
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        self.setWindowTitle(translate_ui("main_title"))
        self.resize(1400, 900)
        
        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar
        self.sidebar = self._create_sidebar()
        splitter.addWidget(self.sidebar)
        
        # Center - main view area
        self.view_stack = QTabWidget()
        self.view_stack.setTabPosition(QTabWidget.TabPosition.North)
        splitter.addWidget(self.view_stack)
        
        # Right dock for details
        self.details_dock = QDockWidget(translate_ui("object_details"))
        self.details_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.details_widget = QTextEdit()
        self.details_widget.setReadOnly(True)
        self.details_dock.setWidget(self.details_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.details_dock)
        
        # Create view tabs
        self.simulation_view = self._create_simulation_view()
        self.dashboard_view = self._create_dashboard_view()
        self.scenario_editor = self._create_scenario_editor()
        self.results_viewer = self._create_results_viewer()
        
        self.view_stack.addTab(self.simulation_view, translate_ui("view_2d"))
        self.view_stack.addTab(self.dashboard_view, translate_ui("home"))
        self.view_stack.addTab(self.scenario_editor, translate_ui("select_scenario"))
        self.view_stack.addTab(self.results_viewer, translate_ui("reports"))
        
        # Set splitter sizes
        splitter.setSizes([250, 900])
    
    def _create_sidebar(self) -> QWidget:
        """Create the left sidebar with navigation."""
        sidebar = QWidget()
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(8)
        
        # App title
        title = QLabel(translate_ui("app_name"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Version
        version = QLabel(translate_ui("app_version"))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: gray; padding-bottom: 10px;")
        layout.addWidget(version)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        # Navigation buttons
        nav_items = [
            (translate_ui("home"), "home"),
            (translate_ui("view_2d"), "view_2d"),
            (translate_ui("view_3d"), "view_3d"),
            (translate_ui("virtual_sensors"), "sensors"),
            (translate_ui("object_tracking"), "tracking"),
            (translate_ui("event_log"), "events"),
            (translate_ui("reports"), "reports"),
            (translate_ui("tests"), "tests"),
            (translate_ui("settings"), "settings"),
        ]
        
        self.nav_buttons = {}
        for text, key in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_click(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        # Set first button as active
        self.nav_buttons["home"].setChecked(True)
        
        layout.addStretch()
        
        # Simulation controls at bottom
        controls_group = QFrame()
        controls_group.setFrameShape(QFrame.Shape.StyledPanel)
        controls_layout = QVBoxLayout(controls_group)
        
        controls_title = QLabel(translate_ui("simulation_status"))
        controls_title.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(controls_title)
        
        self.status_label = QLabel(translate_ui("idle"))
        self.status_label.setStyleSheet("padding: 5px; color: green; font-weight: bold;")
        controls_layout.addWidget(self.status_label)
        
        self.scenario_label = QLabel(f"{translate_ui('current_scenario')}: غير محدد")
        self.scenario_label.setWordWrap(True)
        controls_layout.addWidget(self.scenario_label)
        
        self.clock_label = QLabel(f"{translate_ui('simulation_clock')}: 0.00s / 0.00s")
        controls_layout.addWidget(self.clock_label)
        
        # Control buttons
        self.btn_start = QPushButton(translate_ui("start_simulation"))
        self.btn_start.clicked.connect(self._on_start)
        controls_layout.addWidget(self.btn_start)
        
        self.btn_pause = QPushButton(translate_ui("pause_simulation"))
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_pause.setEnabled(False)
        controls_layout.addWidget(self.btn_pause)
        
        self.btn_resume = QPushButton(translate_ui("resume_simulation"))
        self.btn_resume.clicked.connect(self._on_resume)
        self.btn_resume.setEnabled(False)
        controls_layout.addWidget(self.btn_resume)
        
        self.btn_stop = QPushButton(translate_ui("stop_simulation"))
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.setEnabled(False)
        controls_layout.addWidget(self.btn_stop)
        
        self.btn_reset = QPushButton(translate_ui("reset_simulation"))
        self.btn_reset.clicked.connect(self._on_reset)
        controls_layout.addWidget(self.btn_reset)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel(translate_ui("simulation_speed")))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 10.0)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSingleStep(0.5)
        self.speed_spin.valueChanged.connect(self._on_speed_change)
        speed_layout.addWidget(self.speed_spin)
        controls_layout.addLayout(speed_layout)
        
        layout.addWidget(controls_group)
        
        return sidebar
    
    def _create_simulation_view(self) -> QWidget:
        """Create the 2D simulation view."""
        from nados.ui.widgets import SimulationView
        return SimulationView()
    
    def _create_dashboard_view(self) -> QWidget:
        """Create the monitoring dashboard."""
        from nados.ui.widgets import MonitoringDashboard
        return MonitoringDashboard()
    
    def _create_scenario_editor(self) -> QWidget:
        """Create the scenario editor."""
        from nados.ui.widgets import ScenarioEditor
        return ScenarioEditor()
    
    def _create_results_viewer(self) -> QWidget:
        """Create the results viewer."""
        from nados.ui.widgets import ResultsViewer
        return ResultsViewer()
    
    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("ملف")
        
        new_action = QAction(translate_ui("create_scenario"), self)
        new_action.triggered.connect(self._new_scenario)
        file_menu.addAction(new_action)
        
        open_action = QAction(translate_ui("load_scenario"), self)
        open_action.triggered.connect(self._load_scenario)
        file_menu.addAction(open_action)
        
        save_action = QAction(translate_ui("save_scenario"), self)
        save_action.triggered.connect(self._save_scenario)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction(translate_ui("export_report"), self)
        export_action.triggered.connect(self._export_report)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("خروج", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("عرض")
        
        toggle_3d = QAction(translate_ui("toggle_3d"), self)
        toggle_3d.setCheckable(True)
        toggle_3d.triggered.connect(self._toggle_3d_view)
        view_menu.addAction(toggle_3d)
        
        # Help menu
        help_menu = menubar.addMenu("مساعدة")
        
        about_action = QAction("حول", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self) -> None:
        """Set up the toolbar."""
        toolbar = QToolBar("الشريط الرئيسي")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Quick actions
        toolbar.addAction(QAction(translate_ui("start_simulation"), self, triggered=self._on_start))
        toolbar.addAction(QAction(translate_ui("pause_simulation"), self, triggered=self._on_pause))
        toolbar.addAction(QAction(translate_ui("stop_simulation"), self, triggered=self._on_stop))
        toolbar.addSeparator()
        toolbar.addAction(QAction(translate_ui("export_report"), self, triggered=self._export_report))
    
    def _setup_statusbar(self) -> None:
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage(translate_ui("database_connected"))
        
        # Permanent widgets
        self.cpu_label = QLabel("CPU: N/A")
        self.mem_label = QLabel("RAM: N/A")
        self.status_bar.addPermanentWidget(self.cpu_label)
        self.status_bar.addPermanentWidget(self.mem_label)
    
    def _apply_theme(self) -> None:
        """Apply the configured theme."""
        theme = self.config.theme
        
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #1a1a2e;
                    color: #eaeaea;
                }
                QPushButton {
                    background-color: #16213e;
                    border: 1px solid #0f3460;
                    border-radius: 4px;
                    padding: 8px;
                    color: #eaeaea;
                }
                QPushButton:hover {
                    background-color: #0f3460;
                }
                QPushButton:pressed {
                    background-color: #e94560;
                }
                QPushButton:checked {
                    background-color: #e94560;
                    border-color: #e94560;
                }
                QPushButton:disabled {
                    background-color: #0a0a1a;
                    color: #666;
                }
                QTabWidget::pane {
                    border: 1px solid #0f3460;
                    background: #1a1a2e;
                }
                QTabBar::tab {
                    background: #16213e;
                    border: 1px solid #0f3460;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #0f3460;
                    border-bottom-color: #1a1a2e;
                }
                QDockWidget {
                    titlebar-close-icon: url(close.png);
                    titlebar-normal-icon: url(undock.png);
                }
                QDockWidget::title {
                    background: #16213e;
                    padding: 6px;
                }
                QScrollArea {
                    border: none;
                }
                QListWidget {
                    background: #16213e;
                    border: 1px solid #0f3460;
                }
                QTextEdit {
                    background: #16213e;
                    border: 1px solid #0f3460;
                }
                QComboBox, QSpinBox, QDoubleSpinBox {
                    background: #16213e;
                    border: 1px solid #0f3460;
                    padding: 4px;
                }
                QStatusBar {
                    background: #16213e;
                    border-top: 1px solid #0f3460;
                }
                QMenuBar {
                    background: #16213e;
                }
                QMenuBar::item:selected {
                    background: #0f3460;
                }
                QMenu {
                    background: #16213e;
                    border: 1px solid #0f3460;
                }
                QMenu::item:selected {
                    background: #0f3460;
                }
            """)
    
    def _on_nav_click(self, key: str) -> None:
        """Handle navigation button clicks."""
        # Update button states
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        
        # Switch view
        view_map = {
            "home": 1,  # dashboard
            "view_2d": 0,  # simulation
            "view_3d": 0,  # simulation (3D not implemented yet)
            "sensors": 0,
            "tracking": 0,
            "events": 0,
            "reports": 3,  # results
            "tests": 3,
            "settings": 2,  # scenario editor for now
        }
        
        if key in view_map:
            self.view_stack.setCurrentIndex(view_map[key])
        
        self.logger.info(f"Navigation: {key}")
    
    def _on_start(self) -> None:
        """Start simulation."""
        if self.engine and self.engine.state.value == "running":
            return
        
        # TODO: Load scenario and create engine
        self.logger.info("Start simulation requested")
        self._update_simulation_state("running")
    
    def _on_pause(self) -> None:
        """Pause simulation."""
        if self.engine:
            self.engine.pause()
        self._update_simulation_state("paused")
    
    def _on_resume(self) -> None:
        """Resume simulation."""
        if self.engine:
            self.engine.resume()
        self._update_simulation_state("running")
    
    def _on_stop(self) -> None:
        """Stop simulation."""
        if self.engine:
            self.engine.stop()
        if self.worker:
            self.worker.stop()
            self.worker.wait(1000)
        self._update_simulation_state("stopped")
    
    def _on_reset(self) -> None:
        """Reset simulation."""
        if self.engine:
            self.engine.reset()
        self._update_simulation_state("idle")
    
    def _on_speed_change(self, value: float) -> None:
        """Handle simulation speed change."""
        if self.engine:
            self.engine.clock.set_speed(value)
    
    def _update_simulation_state(self, state: str) -> None:
        """Update UI for simulation state."""
        state_map = {
            "idle": (translate_ui("idle"), "green", True, False, False, False, False),
            "running": (translate_ui("running"), "orange", False, True, False, True, True),
            "paused": (translate_ui("paused"), "yellow", False, False, True, True, True),
            "stopped": (translate_ui("stopped"), "red", True, False, False, False, False),
            "completed": (translate_ui("completed"), "green", True, False, False, False, False),
            "error": (translate_ui("error"), "red", True, False, False, False, False),
        }
        
        text, color, start_en, pause_en, resume_en, stop_en, reset_en = state_map.get(state, state_map["idle"])
        
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"padding: 5px; color: {color}; font-weight: bold;")
        
        self.btn_start.setEnabled(start_en)
        self.btn_pause.setEnabled(pause_en)
        self.btn_resume.setEnabled(resume_en)
        self.btn_stop.setEnabled(stop_en)
        self.btn_reset.setEnabled(reset_en)
    
    def _update_clock_display(self) -> None:
        """Update the simulation clock display."""
        if self.engine:
            current = self.engine.current_time
            total = self.engine.clock.time.duration
            progress = self.engine.progress * 100
            self.clock_label.setText(f"{translate_ui('simulation_clock')}: {current:.2f}s / {total:.2f}s ({progress:.1f}%)")
    
    def _new_scenario(self) -> None:
        """Create new scenario."""
        self.view_stack.setCurrentIndex(2)  # Scenario editor
    
    def _load_scenario(self) -> None:
        """Load scenario from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, translate_ui("load_scenario"), "scenarios", "JSON Files (*.json)"
        )
        if file_path:
            self.logger.info(f"Loading scenario: {file_path}")
            # TODO: Load and validate scenario
    
    def _save_scenario(self) -> None:
        """Save current scenario."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, translate_ui("save_scenario"), "scenarios", "JSON Files (*.json)"
        )
        if file_path:
            self.logger.info(f"Saving scenario: {file_path}")
            # TODO: Save scenario
    
    def _export_report(self) -> None:
        """Export simulation report."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, translate_ui("export_report"), "reports", "JSON Files (*.json);;CSV Files (*.csv)"
        )
        if file_path:
            self.logger.info(f"Exporting report: {file_path}")
            # TODO: Generate report
    
    def _toggle_3d_view(self, checked: bool) -> None:
        """Toggle 3D view."""
        self.logger.info(f"3D view toggled: {checked}")
        # TODO: Implement 3D view
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "حول نادوس",
            f"<h3>{translate_ui('app_name')}</h3>"
            f"<p>{translate_ui('app_version')}</p>"
            f"<p>منصة بحث ومحاكاة متكاملة للدفاع الجوي</p>"
            f"<p>نسخة بحثية وتعليمية فقط</p>"
        )
    
    def closeEvent(self, event) -> None:
        """Handle window close."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        
        if self.engine:
            self.engine.stop()
        
        self.logger.info("Application closing")
        event.accept()