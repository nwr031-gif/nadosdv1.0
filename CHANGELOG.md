# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-XX

### Added
- Initial project structure and configuration
- Domain models (Scenario, VirtualObject, Sensor, Observation, Track, Event, Run)
- Configuration validation with Pydantic
- Structured logging with rotation
- SQLite persistence layer with migrations
- Deterministic simulation engine with fixed timestep
- Generic kinematics motion models
- Synthetic sensor simulation with noise/dropout
- Kalman filter tracking implementation
- Multi-sensor data fusion (basic weighted average)
- PyQt6 desktop interface with Arabic RTL support
- 2D operational map visualization
- Scenario editor and results viewer
- JSON/CSV report generation
- Unit and integration test suite
- GitHub Actions CI workflow

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- No network listeners by default
- No hard-coded secrets
- Input validation on all external data