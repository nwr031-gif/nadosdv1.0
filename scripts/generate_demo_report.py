#!/usr/bin/env python3
"""
Generate demo report for NADOS Dv1.0.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nados.orchestration import create_application


def main() -> int:
    """Generate demo report."""
    print("Initializing NADOS application...")

    app = create_application()

    # Load demo scenario
    print("Loading basic tracking scenario...")
    if not app.load_scenario("scenarios/basic_tracking.json"):
        print("Failed to load scenario")
        return 1

    # Run simulation
    print("Running simulation...")
    if not app.run_simulation_sync():
        print("Simulation failed")
        return 1

    # Generate report
    print("Generating report...")
    report_files = app.generate_report(formats=["json", "csv"])

    for fmt, path in report_files.items():
        print(f"Generated {fmt.value.upper()} report: {path}")

    app.shutdown()
    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
