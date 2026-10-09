# NADOS Dv1.0 - Integrated Air Defense Research & Simulation Environment

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-312/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)]()

NADOS Dv1.0 is a local-first research, simulation, visualization, and software testing platform for generic sensor-monitoring and command-and-control systems. It is designed for educational and research purposes only.

## ⚠️ Safety Notice

**This is a research and educational simulator.** All targets, sensors, launch events, and interceptor-like objects are simulated. No real weapon control, real-world targeting, operational interception guidance, or hardware interfaces for controlling weapons are implemented or supported.

## Features

- **Synthetic Scenario Creation** - Create and run reproducible simulation scenarios
- **Virtual Object Generation** - Generate moving objects with configurable kinematics
- **Sensor Simulation** - Simulate sensor observations with configurable noise and dropout models
- **Object Tracking** - Kalman filter-based tracking with uncertainty estimation
- **Multi-Sensor Fusion** - Combine observations from multiple simulated sensors
- **2D Operational Map** - View simulated situation on a schematic map (PyQt6)
- **3D Visualization** - Optional 3D environment (Panda3D)
- **Data Persistence** - SQLite storage for scenarios, runs, observations, and tracks
- **Reporting** - JSON and CSV export with full metadata
- **Deterministic Execution** - Fixed-seed reproducibility for research validation
- **Arabic-First Interface** - RTL support with Arabic as default language

## Installation

```bash
# Clone the repository
git clone https://github.com/nwr031-gif/nadosdv1.0.git
cd nadosdv1.0

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m nados.scripts.init_db

# Run tests
python -m pytest tests/

# Start application
python -m nados.main
```

## Quick Start

1. Launch the application: `python -m nados.main`
2. Select a demo scenario from the sidebar
3. Click "تشغيل المحاكاة" (Start Simulation)
4. Observe the 2D map and tracking display
5. Export reports from the results viewer

## Project Structure

```
nados-dv1/
├── config/              # Configuration files
├── docs/                # Documentation
├── schemas/             # JSON schemas for validation
├── scenarios/           # Demo scenario definitions
├── src/nados/           # Main source code
│   ├── config/          # Configuration management
│   ├── domain/          # Domain models
│   ├── simulation/      # Simulation engine
│   ├── sensors/         # Sensor simulation
│   ├── tracking/        # Object tracking (Kalman filter)
│   ├── fusion/          # Multi-sensor data fusion
│   ├── orchestration/   # Application orchestration
│   ├── persistence/     # Database layer
│   ├── reporting/       # Report generation
│   ├── observability/   # Logging and monitoring
│   ├── ui/              # PyQt6 desktop interface
│   ├── visualization/   # 2D/3D visualization
│   └── plugins/         # Plugin architecture
├── tests/               # Test suite
├── scripts/             # Utility scripts
└── assets/              # Icons, themes
```

## Demo Scenarios

- **basic_tracking.json** - Single object with clean sensor measurements
- **noisy_sensor.json** - Object tracking with measurement noise
- **multi_sensor_demo.json** - Multiple sensors observing same object

## Configuration

Edit `config/app.yaml` to customize:
- Database location
- Simulation limits
- Visualization settings
- Logging configuration
- Default random seed

## Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/nados

# Run specific test module
python -m pytest tests/unit/test_domain.py -v
```

## Documentation

- [Architecture](docs/architecture.md)
- [Installation Guide](docs/installation.md)
- [User Guide](docs/user_guide.md)
- [Simulation Model](docs/simulation_model.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Testing](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Limitations](docs/limitations.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This software is for research and educational purposes only. It does not represent a real operational air defense system and must not be used for any military or safety-critical applications.