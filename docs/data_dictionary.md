# NADOS Dv1.0 Data Dictionary

## Database Schema

### Table: scenarios
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(64) | PK | Scenario unique identifier |
| schema_version | VARCHAR(16) | NOT NULL | Schema version (v1) |
| name | VARCHAR(256) | NOT NULL | Scenario display name |
| description | TEXT | | Scenario description |
| duration_seconds | REAL | NOT NULL | Simulation duration |
| timestep_seconds | REAL | NOT NULL | Timestep size |
| random_seed | INTEGER | NOT NULL | RNG seed |
| coordinate_system | VARCHAR(16) | NOT NULL | ENU/ECEF/LLA |
| scenario_data | TEXT | NOT NULL | Full JSON serialization |
| created_at | DATETIME | DEFAULT NOW | Creation timestamp |
| updated_at | DATETIME | DEFAULT NOW | Last update |

**Indexes**: `ix_scenarios_name`, `ix_scenarios_created`

### Table: runs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(64) | PK | Run unique identifier |
| scenario_id | VARCHAR(64) | FK → scenarios.id | Parent scenario |
| started_at | DATETIME | DEFAULT NOW | Run start time |
| completed_at | DATETIME | NULLABLE | Run completion time |
| random_seed | INTEGER | NOT NULL | Seed used |
| application_version | VARCHAR(32) | NOT NULL | App version |
| configuration_hash | VARCHAR(64) | | Config hash |
| status | VARCHAR(32) | NOT NULL | pending/running/paused/completed/failed/cancelled |
| summary_metrics | TEXT | | JSON metrics |
| created_at | DATETIME | DEFAULT NOW | |
| updated_at | DATETIME | DEFAULT NOW | |

**Indexes**: `ix_runs_scenario`, `ix_runs_status`, `ix_runs_started`

### Table: observations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(64) | PK | Observation unique ID |
| run_id | VARCHAR(64) | FK → runs.id | Parent run |
| sensor_id | VARCHAR(64) | NOT NULL | Source sensor |
| timestamp | REAL | NOT NULL | Simulation time (s) |
| position_x | REAL | NOT NULL | Measured X (m) |
| position_y | REAL | NOT NULL | Measured Y (m) |
| position_z | REAL | NOT NULL | Measured Z (m) |
| uncertainty_xx | REAL | NOT NULL | Cov[0,0] |
| uncertainty_xy | REAL | NOT NULL | Cov[0,1] |
| uncertainty_xz | REAL | NOT NULL | Cov[0,2] |
| uncertainty_yy | REAL | NOT NULL | Cov[1,1] |
| uncertainty_yz | REAL | NOT NULL | Cov[1,2] |
| uncertainty_zz | REAL | NOT NULL | Cov[2,2] |
| validity_status | VARCHAR(32) | NOT NULL | valid/missing/invalid/out_of_range/etc |
| scenario_id | VARCHAR(64) | NOT NULL | Scenario ID |
| created_at | DATETIME | DEFAULT NOW | |

**Indexes**: `ix_observations_run`, `ix_observations_sensor`, `ix_observations_time`

### Table: tracks
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(64) | PK | Track point unique ID |
| run_id | VARCHAR(64) | FK → runs.id | Parent run |
| timestamp | REAL | NOT NULL | Simulation time (s) |
| position_x | REAL | NOT NULL | Estimated X (m) |
| position_y | REAL | NOT NULL | Estimated Y (m) |
| position_z | REAL | NOT NULL | Estimated Z (m) |
| velocity_x | REAL | NOT NULL | Estimated Vx (m/s) |
| velocity_y | REAL | NOT NULL | Estimated Vy (m/s) |
| velocity_z | REAL | NOT NULL | Estimated Vz (m/s) |
| cov_xx | REAL | NOT NULL | Cov[0,0] |
| cov_xy | REAL | NOT NULL | Cov[0,1] |
| cov_xz | REAL | NOT NULL | Cov[0,2] |
| cov_yy | REAL | NOT NULL | Cov[1,1] |
| cov_yz | REAL | NOT NULL | Cov[1,2] |
| cov_zz | REAL | NOT NULL | Cov[2,2] |
| observation_count | INTEGER | DEFAULT 0 | Measurements used |
| tracking_status | VARCHAR(32) | NOT NULL | initializing/active/coasting/lost/terminated |
| source_sensors | TEXT | | JSON array of sensor IDs |
| created_at | DATETIME | DEFAULT NOW | |

**Indexes**: `ix_tracks_run`, `ix_tracks_time`, `ix_tracks_status`

### Table: events
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(64) | PK | Event unique ID |
| run_id | VARCHAR(64) | FK → runs.id | Parent run |
| event_type | VARCHAR(64) | NOT NULL | Event type enum |
| timestamp | REAL | NOT NULL | Simulation time (s) |
| severity | VARCHAR(16) | NOT NULL | debug/info/warning/error/critical |
| message | TEXT | NOT NULL | Human-readable message |
| source_module | VARCHAR(64) | NOT NULL | Originating module |
| associated_object_id | VARCHAR(64) | NULLABLE | Related object |
| metadata | TEXT | | JSON additional data |
| created_at | DATETIME | DEFAULT NOW | |

**Indexes**: `ix_events_run`, `ix_events_type`, `ix_events_time`, `ix_events_severity`

### Table: settings
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | VARCHAR(128) | PK | Setting key |
| value | TEXT | NOT NULL | JSON value |
| description | TEXT | | Description |
| updated_at | DATETIME | DEFAULT NOW | Last update |

## Domain Model Fields

### SimulationScenario
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| scenario_id | str | Yes | Unique identifier |
| schema_version | str | Yes | "v1" |
| name | str | Yes | Display name |
| description | str | No | Description |
| duration_seconds | float | Yes | > 0 |
| timestep_seconds | float | Yes | > 0 |
| random_seed | int | Yes | >= 0 |
| coordinate_system | Enum | Yes | ENU/ECEF/LLA |
| simulated_sensors | List[SensorDefinition] | Yes | Sensors |
| virtual_objects | List[VirtualObject] | Yes | Objects |
| environmental_conditions | EnvironmentalConditions | Yes | Environment |
| visualization_settings | VisualizationSettings | Yes | View config |
| metadata | Dict | No | Extensions |

### VirtualObject
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| object_id | str | Yes | Unique ID |
| object_type | Enum | Yes | generic/vehicle/projectile/target/decoy/unknown |
| initial_position | Vector3D | Yes | Start position (m) |
| initial_velocity | Vector3D | Yes | Start velocity (m/s) |
| initial_acceleration | Vector3D | Yes | Start accel (m/s²) |
| dimensions | Vector3D | Yes | Size (m) |
| appearance | Dict | No | Visual properties |
| simulation_enabled | bool | Yes | Active flag |
| metadata | Dict | No | Extensions |

### SensorDefinition
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sensor_id | str | Yes | Unique ID |
| sensor_type | Enum | Yes | radar/lidar/optical/irst/acoustic/generic |
| simulated_position | Vector3D | Yes | Position (m) |
| sampling_interval | float | Yes | > 0 (s) |
| measurement_noise | Matrix3x3 | Yes | Covariance (m²) |
| availability_schedule | Dict | No | Time windows |
| metadata | Dict | No | Extensions |

### SensorObservation
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| observation_id | str | Yes | Unique ID |
| sensor_id | str | Yes | Source sensor |
| timestamp | float | Yes | Sim time (s) |
| measured_position | Vector3D | Yes | Noisy position (m) |
| measurement_uncertainty | Matrix3x3 | Yes | Covariance (m²) |
| validity_status | Enum | Yes | valid/missing/invalid/out_of_range/sensor_error |
| scenario_id | str | Yes | Parent scenario |
| metadata | Dict | No | Extensions |

### TrackEstimate
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| track_id | str | Yes | Unique track ID |
| timestamp | float | Yes | Sim time (s) |
| estimated_position | Vector3D | Yes | Filtered position (m) |
| estimated_velocity | Vector3D | Yes | Filtered velocity (m/s) |
| covariance_or_uncertainty | Matrix3x3 | Yes | Position cov (m²) |
| observation_count | int | Yes | >= 0 |
| tracking_status | Enum | Yes | initializing/active/coasting/lost/terminated |
| source_sensor_ids | List[str] | Yes | Contributing sensors |
| metadata | Dict | No | Extensions |

### SimulationEvent
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | str | Yes | Unique ID |
| event_type | Enum | Yes | Type enum |
| timestamp | float | Yes | Sim time (s) |
| severity | Enum | Yes | debug/info/warning/error/critical |
| message | str | Yes | Description |
| source_module | str | Yes | Origin |
| associated_object_id | str | No | Related object |
| metadata | Dict | No | Extensions |

### SimulationRun
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| run_id | str | Yes | Unique ID |
| scenario_id | str | Yes | Parent scenario |
| started_at | datetime | Yes | Wall clock start |
| completed_at | datetime | No | Wall clock end |
| random_seed | int | Yes | Seed used |
| application_version | str | Yes | App version |
| configuration_hash | str | Yes | Config hash |
| status | Enum | Yes | Run status |
| summary_metrics | Dict | Yes | Computed metrics |
| metadata | Dict | No | Extensions |

## JSON Schema References

- Scenario: `schemas/scenario-v1.schema.json`
- Report: `schemas/report-v1.schema.json`

## Export Formats

### CSV Columns (Observations)
```
observation_id,sensor_id,timestamp,position_x,position_y,position_z,
uncertainty_xx,uncertainty_xy,uncertainty_xz,uncertainty_yy,uncertainty_yz,uncertainty_zz,
validity_status,scenario_id
```

### CSV Columns (Tracks)
```
track_id,timestamp,position_x,position_y,position_z,
velocity_x,velocity_y,velocity_z,
cov_xx,cov_xy,cov_xz,cov_yy,cov_yz,cov_zz,
observation_count,tracking_status,source_sensors
```

### CSV Columns (Events)
```
event_id,event_type,timestamp,severity,message,source_module,associated_object_id,metadata
```