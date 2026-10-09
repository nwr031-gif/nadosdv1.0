# NADOS Dv1.0 User Guide

## Getting Started

### Launch Application
```bash
python -m nados.main
```

### Main Window Overview

The main window consists of:
1. **Sidebar (Right)** - Navigation, simulation controls, status
2. **Main View (Center)** - Tabbed interface for different views
3. **Details Panel (Left)** - Selected object details
4. **Status Bar (Bottom)** - System metrics, database status

### Arabic Interface

The interface uses Arabic as the default language with RTL layout:
- All menus, buttons, and labels are in Arabic
- Numbers remain in Arabic-Indic digits where appropriate
- RTL layout applied to all widgets

## Running a Simulation

### 1. Select Scenario
- Click **"السيناريو الحالي"** in sidebar
- Or use **ملف → تحميل سيناريو**
- Choose from demo scenarios:
  - `basic_tracking.json` - Clean sensor tracking
  - `noisy_sensor.json` - Noisy measurements with filtering
  - `multi_sensor_demo.json` - Multi-sensor fusion

### 2. Start Simulation
- Click **"تشغيل المحاكاة"** (green button)
- Simulation clock starts counting
- Status changes to **"قيد التشغيل"**

### 3. Monitor Progress
- **2D View** - Shows objects, sensors, tracks on map
- **Dashboard** - Real-time metrics and event log
- **Clock** - Shows simulation time vs duration

### 4. Control Simulation
- **إيقاف مؤقت** - Pause simulation
- **استئناف** - Resume from pause
- **إيقاف** - Stop and finalize
- **إعادة ضبط** - Reset to initial state
- **سرعة المحاكاة** - Adjust speed (0.1x to 10x)

### 5. View Results
- Switch to **"التقارير"** tab
- View run history
- Export reports (JSON/CSV)

## Understanding the 2D View

### Map Elements
- **● Green Circles** - Sensor positions
- **▲ Red Triangles** - Virtual objects (targets)
- **■ Cyan Squares** - Track estimates (Kalman filter)
- **⋯ Gray Dots** - Historical trails

### Interaction
- **Pan** - Left-click drag
- **Zoom** - Mouse wheel
- **Select** - Right-click on object
- **Details** - Selected object shown in left panel

### Coordinate System
- **East (X)** - Horizontal axis (positive right)
- **North (Y)** - Vertical axis (positive up)
- **Up (Z)** - Altitude (shown in details)

## Dashboard Metrics

| Metric | Description |
|--------|-------------|
| الأجسام النشطة | Number of simulated objects |
| الملاحظات الصحيحة | Valid sensor observations |
| المسارات النشطة | Active Kalman filter tracks |
| معدل التساقط | Observation dropout percentage |
| الإنذارات الكاذبة | False alarm count |
| زمن الاستجابة | Average processing latency |
| استخدام المعالج | CPU usage percentage |
| استخدام الذاكرة | RAM usage in MB |

## Scenario Editor

### Creating a Scenario
1. Go to **"اختيار سيناريو"** tab
2. Fill in:
   - **اسم السيناريو** - Descriptive name
   - **وصف السيناريو** - Details
   - **المدة** - Simulation time (seconds)
   - **خطوة الوقت** - Timestep (0.01-1.0s)
   - **بذرة العشوائية** - For reproducibility
3. Add objects: **إضافة جسم**
4. Add sensors: **إضافة مستشعر**
5. Click **التحقق من السيناريو**
6. Save: **حفظ السيناريو**

### Object Properties
- **معرف الجسم** - Unique ID
- **النوع** - generic, vehicle, projectile, target, decoy
- **الموقع الابتدائي** - X, Y, Z (meters)
- **السرعة الابتدائية** - Vx, Vy, Vz (m/s)
- **التسارع الابتدائي** - Ax, Ay, Az (m/s²)
- **الأبعاد** - Length, width, height

### Sensor Properties
- **معرف المستشعر** - Unique ID
- **النوع** - radar, lidar, optical, irst, acoustic
- **الموقع** - X, Y, Z (meters)
- **فاصل العينات** - Seconds between measurements
- **ضوضاء القياس** - Covariance matrix

## Reports

### Report Contents
- **Metadata** - Generator version, timestamp
- **Simulation Info** - Scenario, seed, duration
- **Execution Status** - Start/end time, success/failure
- **Observation Statistics** - Counts by sensor, validity
- **Tracking Summary** - Track counts, quality
- **Processing Statistics** - Timing, throughput
- **Errors/Warnings** - Event log summary
- **Known Limitations** - Model assumptions

### Export Formats
- **JSON** - Structured data for analysis
- **CSV** - Flattened for spreadsheets

## 3D Visualization (Optional)

### Enable
1. Install Panda3D: `pip install panda3d`
2. Set `enable_3d: true` in config/app.yaml
3. Or export `NADOS_ENABLE_3D=true`

### Controls
- **Orbit** - Right-click drag
- **Pan** - Middle-click drag
- **Zoom** - Mouse wheel
- **Reset View** - Toolbar button

### Scene Elements
- Ground plane with 10km grid
- Coordinate axes (Red=East, Green=North, Blue=Up)
- Rocket-shaped objects with trails
- Green sensor markers
- "محاكاة - SIMULATION" label

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Start/Pause |
| `R` | Reset |
| `S` | Stop |
| `+/-` | Speed up/down |
| `1` | 2D View |
| `2` | Dashboard |
| `3` | Scenario Editor |
| `4` | Reports |

## Best Practices

### Reproducibility
- Always set a **random seed**
- Use same seed for comparison runs
- Document seed in scenario notes

### Scenario Design
- Keep duration reasonable (< 1 hour)
- Limit objects to < 100 for performance
- Use appropriate timestep (0.1s default)
- Validate before running

### Sensor Configuration
- Place sensors strategically
- Set realistic noise levels
- Configure dropout rates
- Use different sensor types for fusion

### Analysis
- Export reports for offline analysis
- Compare runs with same scenario, different seeds
- Check tracking quality metrics
- Review event log for anomalies

## Troubleshooting

### Simulation Won't Start
- Check scenario validation
- Verify database writable
- Check logs in `logs/nados_errors.log`

### Poor Tracking
- Reduce measurement noise
- Increase sensor sampling rate
- Check motion model matches object
- Verify coordinate system

### UI Issues
- Restart application
- Check theme compatibility
- Verify Arabic font installation

### Performance
- Reduce max objects/sensors in config
- Lower visualization update rate
- Disable 3D if not needed
- Use faster timestep for long runs

## Safety Reminders

⚠️ **This is a research simulator only:**
- All data is synthetic
- No real sensor connections
- No weapon control interfaces
- No operational deployment capability
- Results are not operationally valid