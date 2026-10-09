#!/usr/bin/env python3
"""
Main entry point for NADOS Dv1.0 desktop application.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from nados.ui.arabic_support import setup_arabic_support
from nados.orchestration import create_application
from nados.ui.main_window import MainWindow


def main() -> int:
    """Main application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("NADOS Dv1.0")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NADOS Research")
    
    # Setup Arabic RTL support
    setup_arabic_support(app)
    
    # Create and initialize NADOS application
    try:
        nados_app = create_application()
    except RuntimeError as e:
        print(f"Failed to initialize NADOS: {e}")
        return 1
    
    # Create main window
    window = MainWindow()
    
    # Connect NADOS app to window (for simulation control)
    window.engine = nados_app.engine
    
    window.show()
    
    # Run Qt event loop
    result = app.exec()
    
    # Cleanup
    nados_app.shutdown()
    
    return result


if __name__ == "__main__":
    sys.exit(main())