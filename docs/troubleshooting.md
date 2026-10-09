# NADOS Dv1.0 Troubleshooting Guide

## Common Issues

### Application Won't Start

#### ImportError: No module named 'nados'
```bash
# Solution: Install in development mode
pip install -e .

# Or add src to PYTHONPATH
export PYTHONPATH=/path/to/nados-dv1/src:$PYTHONPATH
```

#### ModuleNotFoundError: No module named 'PyQt6'
```bash
# Install PyQt6
pip install PyQt6

# Linux: may need system packages
sudo apt install python3-pyqt6 python3-pyqt6.qtsvg
```

#### ModuleNotFoundError: No module named 'panda3d'
```bash
# 3D is optional - disable in config
# config/app.yaml:
visualization:
  enable_3d: false

# Or install Panda3D
pip install panda3d
# Linux: sudo apt install panda3d
```

### Database Issues

#### sqlite3.OperationalError: database is locked
```bash
# Check for other processes
lsof data/nados.db

# Kill other processes, or delete lock files
rm -f data/nados.db-wal data/nados.db-shm
```

#### sqlite3.OperationalError: no such table
```bash
# Reinitialize database
rm data/nados.db
python -m nados.scripts.init_db
```

#### Permission denied: data/nados.db
```bash
# Fix permissions
chmod 644 data/nados.db
chmod 755 data/
```

### Simulation Issues

#### Simulation Runs But No Output
- Check if scenario has objects and sensors
- Verify `simulation_enabled: true` on objects
- Check timestep > 0 and duration > 0
- Look at logs: `logs/nados.log`

#### Tracking Not Working
- Verify sensor sampling_interval > 0
- Check measurement_noise matrix is valid (positive definite)
- Ensure object velocity not zero (for CV model initialization)
- Check gate threshold not too strict

#### Poor Tracking Accuracy
- Reduce sensor noise covariance
- Increase sensor sampling rate
- Verify motion model matches object behavior
- Check for coordinate system mismatch

#### NaN/Inf in Results
- Check initial conditions for valid numbers
- Verify measurement noise matrix not singular
- Look for division by zero in calculations
- Enable debug logging for detailed trace

### UI Issues

#### Arabic Text Not Displaying Correctly
```bash
# Install Arabic fonts
# Windows: Built-in
# Linux:
sudo apt install fonts-noto-arabic fonts-noto-sans-arabic
# macOS:
brew install --cask font-noto-sans-arabic
```

#### RTL Layout Issues
- Ensure `setup_arabic_support(app)` called before window creation
- Check `app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)`
- Verify stylesheet doesn't override direction

#### Window Too Small / Elements Clipped
- Minimum window size: 1200x800
- Check layout constraints
- Verify splitter sizes

#### 3D View Crashes
- Update graphics drivers
- Try software rendering: `export QT_QUICK_BACKEND=software`
- Disable 3D: `NADOS_ENABLE_3D=false`

### Configuration Issues

#### Config File Not Found
```bash
# Use default config or specify path
python -m nados.main --config config/app.yaml
```

#### Environment Variables Not Working
```bash
# Check .env file location (project root)
# Verify variable names match exactly
NADOS_DB_PATH=data/nados.db  # Correct
nadOS_db_path=data/nados.db  # Wrong (case sensitive)
```

#### Theme Not Applied
- Restart application after theme change
- Check stylesheet syntax
- Verify color format: `#RRGGBB`

### Performance Issues

#### Slow Simulation
- Reduce `max_objects` in config
- Increase `timestep_seconds` (less steps)
- Disable 3D visualization
- Close other applications
- Check CPU throttling

#### High Memory Usage
- Reduce `max_observations_per_run`
- Reduce `trail_length` in visualization
- Enable database WAL mode (default)
- Periodic vacuum: `python -c "from nados.persistence import get_database; get_database().vacuum()"`

#### UI Freezing
- Simulation must run in worker thread
- Check for blocking calls in main thread
- Reduce visualization update frequency
- Use `QTimer` for periodic updates, not `sleep`

### Logging Issues

#### No Log Files
```bash
# Create logs directory
mkdir -p logs

# Check config
logging:
  directory: "logs"
```

#### Logs Too Verbose
```yaml
# config/app.yaml
logging:
  level: "WARNING"  # or ERROR
```

#### Log Encoding Issues
- Ensure UTF-8 encoding in logging config
- Check terminal supports UTF-8
- Use `encoding: utf-8` in file handlers

## Error Messages Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `Unsupported schema version` | Scenario schema_version not "v1" | Update scenario or code |
| `Invalid numeric value` | Negative duration/timestep/seed | Fix scenario values |
| `Duplicate object_id` | Two objects with same ID | Make IDs unique |
| `Duplicate sensor_id` | Two sensors with same ID | Make IDs unique |
| `Covariance not positive definite` | Invalid noise matrix | Fix measurement_noise |
| `Simulation not running` | Called step/stop on idle engine | Call start() first |
| `Panda3D not available` | Import failed | Install or disable 3D |

## Debug Mode

### Enable Debug Logging
```bash
export NADOS_LOG_LEVEL=DEBUG
python -m nados.main
```

### Log Locations
- Console: Real-time output
- `logs/nados.log`: All levels
- `logs/nados_errors.log`: Errors only
- `logs/nados_structured.log`: JSON format

### Debug Commands
```bash
# Validate scenario without running
python -m nados.scripts.validate_scenarios

# Check database integrity
python -c "from nados.persistence import get_database; db=get_database(); print('OK')"

# Test imports
python -c "import nados; print('Imports OK')"
```

## Getting Help

### Log Analysis
```bash
# Recent errors
tail -50 logs/nados_errors.log

# Search for specific error
grep "KalmanFilter" logs/nados.log

# Structured log query
jq '.level=="ERROR"' logs/nados_structured.log
```

### Reporting Issues
1. Include OS, Python version
2. Provide full error traceback
3. Include relevant log excerpts
4. Specify scenario/config used
5. Note if 3D enabled/disabled

### Debug Information
```bash
# Collect system info
python -c "
import sys, platform
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
import nados; print(f'NADOS: {nados.__version__}')
import PyQt6; print(f'PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}')
try:
    import panda3d; print('Panda3D: Available')
except: print('Panda3D: Not installed')
"
```

## Recovery Procedures

### Corrupted Database
```bash
# Backup
cp data/nados.db data/nados.db.backup

# Try repair
sqlite3 data/nados.db "PRAGMA integrity_check;"

# If failed, restore from backup or reinitialize
rm data/nados.db
python -m nados.scripts.init_db
```

### Lost Scenario
```bash
# Check scenarios/ directory
# Check database scenarios table
python -c "
from nados.persistence import ScenarioRepository, get_database
repo = ScenarioRepository(get_database())
for s in repo.list_all():
    print(s.scenario_id, s.name)
"
```

### Reset to Clean State
```bash
# Remove all generated data
rm -rf data/ logs/ reports/ coverage/ htmlcov/ .pytest_cache/

# Reinstall
pip install -e . --force-reinstall --no-deps

# Reinitialize
python -m nados.scripts.init_db
```