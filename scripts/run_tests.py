#!/usr/bin/env python3
"""
Test runner script for NADOS Dv1.0.
"""

import subprocess
import sys
from pathlib import Path


def run_tests(args: list = None) -> int:
    """Run pytest with configured options."""
    if args is None:
        args = sys.argv[1:]

    # Default pytest arguments
    pytest_args = [
        "python",
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "--cov=src/nados",
        "--cov-report=term-missing",
        "--cov-report=xml",
    ]

    # Add user arguments
    pytest_args.extend(args)

    # Run tests
    project_root = Path(__file__).parent.parent
    result = subprocess.run(pytest_args, cwd=project_root)

    return result.returncode


def run_unit_tests() -> int:
    """Run only unit tests."""
    return run_tests(["tests/unit/"])


def run_integration_tests() -> int:
    """Run only integration tests."""
    return run_tests(["tests/integration/"])


def run_with_coverage() -> int:
    """Run tests with coverage report."""
    return run_tests(["--cov=src/nados", "--cov-report=html"])


if __name__ == "__main__":
    sys.exit(run_tests())
