#!/usr/bin/env python3
"""
Validate scenario files for NADOS Dv1.0.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nados.orchestration.scenario_loader import load_scenario, validate_scenario_file


def main() -> int:
    """Validate all scenario files."""
    scenarios_dir = Path(__file__).parent.parent / "scenarios"

    if not scenarios_dir.exists():
        print(f"Scenarios directory not found: {scenarios_dir}")
        return 1

    scenario_files = list(scenarios_dir.glob("*.json"))

    if not scenario_files:
        print("No scenario files found")
        return 0

    all_valid = True

    for scenario_file in scenario_files:
        print(f"\nValidating: {scenario_file.name}")
        errors = validate_scenario_file(str(scenario_file))

        if errors:
            print(f"  [FAIL] INVALID ({len(errors)} errors):")
            for error in errors:
                print(f"    - {error}")
            all_valid = False
        else:
            print("  [OK] VALID")
            # Try loading
            try:
                scenario = load_scenario(str(scenario_file))
                # Encode name for console output
                name = scenario.name.encode("ascii", errors="replace").decode("ascii")
                n_obj = len(scenario.virtual_objects)
                n_sens = len(scenario.simulated_sensors)
                print(f"     Loaded: {name} ({n_obj} objects, {n_sens} sensors)")
            except Exception as e:
                print(f"     Load error: {e}")
                all_valid = False

    print(f"\n{'=' * 50}")
    if all_valid:
        print("All scenarios are valid! [OK]")
        return 0
    else:
        print("Some scenarios have errors! [FAIL]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
