# NADOS Dv1.0 Testing Guide

## Test Structure

```
tests/
├── unit/           # Unit tests (fast, isolated)
├── integration/    # Integration tests (multi-module)
├── regression/     # Regression tests (fixed outputs)
├── ui/             # GUI tests (require display)
└── fixtures/       # Test data fixtures
```

## Running Tests

### All Tests
```bash
python -m pytest
```

### Specific Categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Regression tests
python -m pytest tests/regression/ -v

# UI tests (requires display)
python -m pytest tests/ui/ -v -m gui
```

### With Coverage
```bash
# Terminal report
python -m pytest --cov=src/nados --cov-report=term-missing

# HTML report
python -m pytest --cov=src/nados --cov-report=html

# XML for CI
python -m pytest --cov=src/nados --cov-report=xml
```

### Specific Test Module
```bash
python -m pytest tests/unit/test_domain.py -v
python -m pytest tests/unit/test_kalman.py -v
python -m pytest tests/integration/test_simulation.py -v
```

## Test Categories

### Unit Tests (`tests/unit/`)

| Module | Tests |
|--------|-------|
| `test_domain.py` | Domain model validation, serialization |
| `test_config.py` | Configuration loading, validation |
| `test_motion.py` | Motion model predictions, matrices |
| `test_sensors.py` | Sensor noise generation, dropout |
| `test_kalman.py` | KF predict/update, gating, initialization |
| `test_fusion.py` | Weighted average, CI, track-to-track |
| `test_persistence.py` | Database CRUD, repositories |
| `test_reporting.py` | Report generation, formats |
| `test_scenario_loader.py` | Scenario validation, loading |

### Integration Tests (`tests/integration/`)

| Test | Description |
|------|-------------|
| `test_scenario_execution.py` | Full scenario run from load to report |
| `test_persistence_roundtrip.py` | Save/load scenario, run, results |
| `test_reproducibility.py` | Same seed → same results |
| `test_multi_sensor.py` | Multi-sensor fusion pipeline |
| `test_without_3d.py` | Core functionality without Panda3D |

### Regression Tests (`tests/regression/`)

| Test | Description |
|------|-------------|
| `test_kalman_numerical.py` | Fixed KF outputs for known inputs |
| `test_motion_numerical.py` | Motion model positions at fixed times |
| `test_fusion_numerical.py` | Fusion outputs for fixed inputs |
| `test_scenario_outputs.py` | Full scenario outputs match fixtures |

### UI Tests (`tests/ui/`)

| Test | Description |
|------|-------------|
| `test_main_window.py` | Window creation, navigation |
| `test_simulation_controls.py` | Start/pause/stop/reset buttons |
| `test_scenario_editor.py` | Form validation, save/load |
| `test_2d_view.py` | Canvas rendering, interaction |

## Writing Tests

### Unit Test Template
```python
"""Test module for X."""

import pytest
import numpy as np
from nados.module import ClassUnderTest


class TestClassUnderTest:
    """Tests for ClassUnderTest."""
    
    def test_basic_functionality(self):
        """Test basic operation."""
        obj = ClassUnderTest()
        result = obj.method()
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge condition."""
        with pytest.raises(ValueError):
            ClassUnderTest(invalid_param)
    
    @pytest.mark.parametrize("input,expected", [
        (0, 0),
        (1, 1),
        (-1, 1),
    ])
    def test_parametrized(self, input, expected):
        """Parametrized test."""
        assert ClassUnderTest.method(input) == expected
```

### Numerical Test Template
```python
def test_kalman_predict_known_values():
    """Test KF prediction with known analytical result."""
    kf = KalmanFilter()
    kf.initialize(Vector3D(0, 0, 0), Vector3D(10, 0, 0), 0.0, "test")
    
    # Predict 1 second with CV model
    kf.predict(1.0)
    
    # Position should be 10m East
    estimate = kf.get_estimate()
    assert abs(estimate.estimated_position.x - 10.0) < 1e-10
    assert abs(estimate.estimated_position.y) < 1e-10
    assert abs(estimate.estimated_position.z) < 1e-10
```

### Integration Test Template
```python
def test_full_simulation_run(tmp_path):
    """Test complete simulation execution."""
    # Create temp scenario
    scenario = create_test_scenario()
    scenario_path = tmp_path / "test_scenario.json"
    scenario_path.write_text(scenario.model_dump_json())
    
    # Run through application
    app = create_application()
    assert app.load_scenario(str(scenario_path))
    assert app.run_simulation_sync()
    
    # Verify results persisted
    run_repo = RunRepository()
    runs = run_repo.list_by_scenario(scenario.scenario_id)
    assert len(runs) == 1
    assert runs[0].status == RunStatus.COMPLETED
```

## Fixtures

### Fixture Structure
```
tests/fixtures/
├── scenarios/
│   ├── basic_tracking.json
│   ├── noisy_sensor.json
│   └── multi_sensor_demo.json
├── expected/
│   ├── kalman_step_1.npy
│   ├── fusion_result_2sensor.npy
│   └── motion_cv_10steps.npy
└── reference_runs/
    └── run_basic_tracking_seed42.json
```

### Using Fixtures
```python
@pytest.fixture
def basic_scenario():
    """Load basic tracking scenario fixture."""
    return load_scenario("tests/fixtures/scenarios/basic_tracking.json")


@pytest.fixture
def expected_kalman_state():
    """Load expected KF state after 1 step."""
    return np.load("tests/fixtures/expected/kalman_step_1.npy")
```

## Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| Domain models | 95% |
| Simulation engine | 90% |
| Sensor models | 90% |
| Kalman filter | 95% |
| Fusion algorithms | 90% |
| Persistence | 85% |
| Reporting | 85% |
| Configuration | 90% |

### Coverage Commands
```bash
# Check coverage
pytest --cov=src/nados --cov-fail-under=85

# Detailed report
pytest --cov=src/nados --cov-report=term-missing --cov-report=html
```

## Continuous Integration

### GitHub Actions Workflow
Located at `.github/workflows/ci.yml`

Runs on:
- Push to main/develop
- Pull requests

Steps:
1. Checkout
2. Setup Python 3.12
3. Cache dependencies
4. Install dependencies
5. Lint (ruff)
6. Type check (mypy)
7. Unit tests
8. Integration tests
9. Coverage upload

### Local CI Simulation
```bash
# Run all CI steps locally
ruff check .
mypy src/nados
pytest tests/unit/ tests/integration/ --cov=src/nados --cov-fail-under=85
```

## Test Data Management

### Generating Fixtures
```python
# tests/scripts/generate_fixtures.py
def generate_kalman_fixture():
    kf = KalmanFilter()
    kf.initialize(Vector3D(0,0,0), Vector3D(10,0,0), 0.0, "test")
    kf.predict(1.0)
    np.save("tests/fixtures/expected/kalman_step_1.npy", kf.get_state_vector())
```

### Updating Fixtures
When intentional model changes occur:
1. Update fixture generation script
2. Run script to regenerate
3. Commit new fixtures
4. Update CHANGELOG

## Performance Benchmarks

### Benchmark Script
```bash
python -m tests.benchmark
```

Measures:
- Simulation steps/second
- Observation generation rate
- KF update latency
- Database write throughput
- Memory usage

### Baseline Targets (Reference)
| Operation | Target |
|-----------|--------|
| Simulation step (10 objects, 3 sensors) | < 5ms |
| KF predict + update | < 0.5ms |
| Sensor observation generation | < 0.1ms per sensor |
| Database batch write (1000 obs) | < 50ms |
| Report generation (1hr sim) | < 2s |

## Debugging Tests

### Verbose Output
```bash
pytest tests/unit/test_kalman.py -v -s --tb=long
```

### Debug Specific Test
```bash
pytest tests/unit/test_kalman.py::TestKalmanFilter::test_predict -v --pdb
```

### Profile Test
```bash
pytest tests/unit/test_kalman.py --profile
```