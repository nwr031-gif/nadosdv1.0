"""UI package initialization."""

from .arabic_support import get_all_translations, setup_arabic_support, translate_ui
from .main_window import MainWindow
from .widgets import MonitoringDashboard, ResultsViewer, ScenarioEditor, SimulationView

__all__ = [
    "MainWindow",
    "SimulationView",
    "MonitoringDashboard",
    "ScenarioEditor",
    "ResultsViewer",
    "setup_arabic_support",
    "translate_ui",
    "get_all_translations",
]
