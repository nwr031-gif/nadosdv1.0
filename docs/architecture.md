# NADOS Dv1.0 Architecture

## Overview

NADOS Dv1.0 follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Main Window │  │  2D View     │  │  3D View (Opt.)  │   │
│  │  Dashboard   │  │  Scenario    │  │  Results Viewer  │   │
│  │  Editor      │  │              │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Application & Orchestration                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ NADOSApp     │  │ Scenario     │  │ Report Generator │   │
│  │ Orchestrator │  │ Loader       │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Simulation Domain                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Simulation   │  │ Motion       │  │ Event System     │   │
│  │ Engine       │  │ Models       │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Sensor & Tracking                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Sensor       │  │ Kalman       │  │ Data Association │   │
│  │ Simulation   │  │ Filter       │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Data Fusion                                │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ Fusion       │  │ Conflict     │                          │
│  │ Service      │  │ Detection    │                          │
│  └──────────────┘  └──────────────┘                          │
├─────────────────────────────────────────────────────────────┤
│                  Data Persistence                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ SQLite       │  │ Repositories │  │ Migrations       │   │
│  │ Database     │  │              │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Observability                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Structured   │  │ Metrics      │  │ Health Checks    │   │
│  │ Logging      │  │ Collector    │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Explicit Interfaces**: Module contracts defined with protocols/ABCs
3. **Dependency Injection**: Components receive dependencies, don't create them
4. **Deterministic Simulation**: Fixed seeds produce reproducible results
5. **Thread Safety**: Simulation runs off UI thread with proper synchronization
6. **Validation First**: All inputs validated at boundaries

## Module Contracts

### ScenarioRepository
- **Input**: Scenario ID or filter criteria
- **Output**: SimulationScenario objects
- **Validation**: Schema version, required fields, cross-references
- **Threading**: Thread-safe for reads, serialized writes

### SimulationEngine
- **Input**: SimulationScenario, random seed
- **Output**: SimulationStepResult (time, events, observations, tracks)
- **Threading**: Runs in worker thread, communicates via signals
- **State**: IDLE → RUNNING → PAUSED/COMPLETED/ERROR

### SensorModel
- **Input**: True position/velocity, timestamp, object ID
- **Output**: SensorObservation with noise, validity status
- **Determinism**: Seeded RNG per sensor

### Tracker (KalmanFilter)
- **Input**: SensorObservation, dt
- **Output**: TrackEstimate with covariance
- **State**: INITIALIZING → ACTIVE/COASTING → LOST/TERMINATED

### DataFusionService
- **Input**: Multiple SensorObservation or TrackEstimate
- **Output**: Fused position/covariance, conflicts
- **Methods**: Weighted average, Covariance Intersection

### EventBus
- **Input**: SimulationEvent
- **Output**: Delivered to registered handlers
- **Threading**: Thread-safe, async delivery

### SimulationRepository
- **Input**: SimulationRun, Observations, Tracks, Events
- **Output**: Persisted data with run ID
- **Transactions**: Atomic per run

### ReportGenerator
- **Input**: Run ID, format list
- **Output**: Report files (JSON, CSV)
- **Validation**: Against report schema

### VisualizationAdapter
- **Input**: Simulation state snapshots
- **Output**: Rendered frames
- **Threading**: Separate render thread, read-only state access

### MetricsCollector
- **Input**: Counter increments, gauge sets, histogram records
- **Output**: Aggregated metrics, Prometheus format
- **Threading**: Lock-free for counters, locked for histograms

## Data Flow

```
Scenario File → ScenarioLoader → SimulationScenario
                                    ↓
                        SimulationEngine (authoritative state)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
            SensorSimulator   ObjectSimulator   EventEmitter
                    ↓               ↓               ↓
            SensorObservation  KinematicState   SimulationEvent
                    ↓               ↓               ↓
            ┌─────────────────────────────────────┐
            │        ObjectTracker (KF)           │
            └─────────────────────────────────────┘
                            ↓
                    TrackEstimate
                            ↓
            ┌─────────────────────────────────────┐
            │       DataFusionService             │
            └─────────────────────────────────────┘
                            ↓
                    Fused Estimates
                            ↓
            ┌─────────────────────────────────────┐
            │      Persistence Layer              │
            │  (Observations, Tracks, Events)     │
            └─────────────────────────────────────┘
                            ↓
            ┌─────────────────────────────────────┐
            │      ReportGenerator                │
            └─────────────────────────────────────┘
                            ↓
                    JSON/CSV Reports
```

## Threading Model

```
Main Thread (UI)
├── Event Loop
├── Signal/Slot Communication
└── View Updates (30 FPS)

Worker Thread (Simulation)
├── Fixed-timestep Loop
├── Deterministic RNG
├── State Updates
└── Signal Emission (thread-safe)

Render Thread (3D - Optional)
├── Panda3D Task Manager
├── Read-only State Snapshots
└── Frame Rendering (60 FPS)
```

## Safety Boundaries

- All data labeled as `SIMULATED`
- No network listeners by default
- No hardware interfaces
- Input validation at all boundaries
- Resource limits enforced
- Configuration validation on load