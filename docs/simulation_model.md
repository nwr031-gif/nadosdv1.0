# NADOS Dv1.0 Simulation Model Documentation

## Coordinate Systems

### ENU (East-North-Up) - Default
Local tangent plane coordinate system:
- **Origin**: Sensor/reference position
- **X (East)**: Positive eastward
- **Y (North)**: Positive northward
- **Z (Up)**: Positive upward (altitude)

### ECEF (Earth-Centered Earth-Fixed)
Global geocentric coordinates:
- **Origin**: Earth center of mass
- **X**: Through prime meridian (0° lon)
- **Y**: Through 90° East longitude
- **Z**: Through North pole

### LLA (Latitude-Longitude-Altitude)
Geodetic coordinates:
- **Latitude**: -90° to +90°
- **Longitude**: -180° to +180°
- **Altitude**: Height above WGS84 ellipsoid

**Internal Convention**: All simulation uses ENU with meters as base unit.

## Motion Models

### Constant Velocity (CV)
State vector: `[x, y, z, vx, vy, vz]` (6D) or `[x, y, z, vx, vy, vz, ax, ay, az]` (9D with zero acceleration)

Dynamics:
```
x_k+1 = x_k + vx_k * dt
y_k+1 = y_k + vy_k * dt
z_k+1 = z_k + vz_k * dt
vx_k+1 = vx_k
vy_k+1 = vy_k
vz_k+1 = vz_k
```

State Transition Matrix (9D):
```
[1 0 0 dt 0  0  0  0  0]
[0 1 0 0  dt 0  0  0  0]
[0 0 1 0  0  dt 0  0  0]
[0 0 0 1  0  0  0  0  0]
[0 0 0 0  1  0  0  0  0]
[0 0 0 0  0  1  0  0  0]
[0 0 0 0  0  0  1  0  0]
[0 0 0 0  0  0  0  1  0]
[0 0 0 0  0  0  0  0  1]
```

Process Noise (White Noise Acceleration):
```
Q = q * [dt^4/4  0       0       dt^3/2  0       0       0       0       0
         0       dt^4/4  0       0       dt^3/2  0       0       0       0
         0       0       dt^4/4  0       0       dt^3/2  0       0       0
         dt^3/2  0       0       dt^2    0       0       0       0       0
         0       dt^3/2  0       0       dt^2    0       0       0       0
         0       0       dt^3/2  0       0       dt^2    0       0       0
         0       0       0       0       0       0       0       0       0
         0       0       0       0       0       0       0       0       0
         0       0       0       0       0       0       0       0       0]
```

### Constant Acceleration (CA)
State vector: `[x, y, z, vx, vy, vz, ax, ay, az]` (9D)

Dynamics:
```
x_k+1 = x_k + vx_k*dt + 0.5*ax_k*dt^2
vx_k+1 = vx_k + ax_k*dt
ax_k+1 = ax_k
```

State Transition Matrix:
```
[1 0 0 dt  0   0   dt^2/2 0      0
 0 1 0 0   dt  0   0      dt^2/2 0
 0 0 1 0   0   dt  0      0      dt^2/2
 0 0 0 1   0   0   dt     0      0
 0 0 0 0   1   0   0      dt     0
 0 0 0 0   0   1   0      0      dt
 0 0 0 0   0   0   1      0      0
 0 0 0 0   0   0   0      1      0
 0 0 0 0   0   0   0      0      1]
```

Process Noise (Jerk-driven):
```
Q_jerk = q_j * [dt^6/36  0        0        dt^5/12  0        0        dt^4/6   0        0
                0        dt^6/36  0        0        dt^5/12  0        0        dt^4/6   0
                0        0        dt^6/36  0        0        dt^5/12  0        0        dt^4/6
                dt^5/12  0        0        dt^4/4   0        0        dt^3/3   0        0
                0        dt^5/12  0        0        dt^4/4   0        0        dt^3/3   0
                0        0        dt^5/12  0        0        dt^4/4   0        0        dt^3/3
                dt^4/6   0        0        dt^3/3   0        0        dt^2     0        0
                0        dt^4/6   0        0        dt^3/3   0        0        dt^2     0
                0        0        dt^4/6   0        0        dt^3/3   0        0        dt^2]
```

## Sensor Models

### Generic Sensor
Cartesian measurement with additive Gaussian noise:
```
z = [x, y, z]^T + N(0, R)
R = diag([σ_x^2, σ_y^2, σ_z^2])
```

### Radar Model
Spherical measurements converted to Cartesian:
- **Range**: `r = sqrt(x^2 + y^2 + z^2) + N(0, σ_r^2)`
- **Azimuth**: `az = atan2(y, x) + N(0, σ_az^2)`
- **Elevation**: `el = atan2(z, sqrt(x^2 + y^2)) + N(0, σ_el^2)`

Cartesian covariance via Jacobian propagation:
```
J = [cos(el)cos(az)  -r*cos(el)sin(az)  -r*sin(el)cos(az)
     cos(el)sin(az)   r*cos(el)cos(az)  -r*sin(el)sin(az)
     sin(el)          0                  r*cos(el)]

R_cart = J * diag(σ_r^2, σ_az^2, σ_el^2) * J^T
```

### LIDAR Model
High-precision Cartesian with range limit:
```
z = [x, y, z]^T + N(0, σ^2 * I)
Range limit: 50 km
```

### Optical/IRST Model
Bearing-only with assumed range:
- Measures azimuth/elevation precisely
- Large range uncertainty (50% of range)
- No Doppler/range rate

## Kalman Filter

### State Vector (9D)
```
x = [px, py, pz, vx, vy, vz, ax, ay, az]^T
```

### Measurement Model
```
z = [px, py, pz]^T + v,  v ~ N(0, R)
H = [I_3x3 | 0_3x6]
```

### Prediction Step
```
x_k|k-1 = F * x_k-1|k-1
P_k|k-1 = F * P_k-1|k-1 * F^T + Q
```

### Update Step
```
y = z - H * x_k|k-1          (innovation)
S = H * P_k|k-1 * H^T + R    (innovation covariance)
K = P_k|k-1 * H^T * S^-1     (Kalman gain)
x_k|k = x_k|k-1 + K * y
P_k|k = (I - K*H) * P_k|k-1 * (I - K*H)^T + K*R*K^T
```

### Gating
Mahalanobis distance:
```
d^2 = y^T * S^-1 * y
```
Reject if `d^2 > χ^2_0.95(3) = 7.815` (default gate: 9.21 for 95% with 3 DOF)

### Track Management
- **INITIALIZING**: First measurement, no prediction
- **ACTIVE**: Regular updates, coast_steps = 0
- **COASTING**: Predicted without measurement, coast_steps > 0
- **LOST**: coast_steps > coast_max (default 10)
- **TERMINATED**: Explicitly removed

## Data Fusion

### Weighted Average Fusion
For N independent observations of same object:
```
w_i = 1 / trace(R_i)
w_i_norm = w_i / Σ w_j

x_fused = Σ w_i_norm * z_i
P_fused = Σ w_i_norm^2 * R_i
```

### Covariance Intersection (CI)
Consistent fusion without correlation knowledge:
```
P_fused^-1 = ω * P_1^-1 + (1-ω) * P_2^-1
x_fused = P_fused * (ω * P_1^-1 * x_1 + (1-ω) * P_2^-1 * x_2)

Optimal ω minimizes trace(P_fused)
```

### Track-to-Track Fusion
Fuse track estimates instead of raw observations:
- Same algorithms applied to track states
- Uses track covariance matrices
- Accounts for track correlation approximately

## Numerical Considerations

### Stability
- Joseph form covariance update for symmetry
- Eigenvalue check for positive definiteness
- Condition number monitoring
- Double precision (float64) throughout

### Units
- **Position**: Meters (m)
- **Velocity**: Meters/second (m/s)
- **Acceleration**: Meters/second² (m/s²)
- **Time**: Seconds (s)
- **Angles**: Radians (rad)
- **Covariance**: Squared units (m², (m/s)²)

### Limits
- Max simulation time: 3600s (configurable)
- Max objects: 1000 (configurable)
- Max sensors: 100 (configurable)
- Max observations/run: 100,000 (configurable)
- Timestep range: 0.01s to 1.0s

## Determinism

### Random Number Generation
- NumPy `default_rng(seed)` per component
- Sensor seeds: `base_seed + hash(sensor_id) % 2^32`
- Object seeds: `base_seed + hash(object_id) % 2^32`
- Reproducible with same seed and scenario

### Floating Point
- IEEE 754 double precision
- Operation order fixed for reproducibility
- No non-deterministic parallel reductions

## Validation

### Scenario Validation
- Schema version check
- Required field presence
- Numeric bounds
- Cross-reference integrity
- Duplicate ID detection

### Runtime Validation
- Finite value checks (no NaN/Inf)
- Covariance positive definiteness
- Gate threshold adherence
- Resource limit enforcement

## Assumptions & Limitations

1. **Flat Earth**: ENU assumes local flat earth (valid for < 100km)
2. **No Atmosphere**: No refraction, attenuation, or ducting
3. **Point Targets**: No RCS fluctuation or glint
4. **Perfect Synchronization**: All sensors share simulation clock
5. **Known Sensor Positions**: No sensor registration errors
6. **Linear Motion**: CV/CA models only
7. **Gaussian Noise**: All noise Gaussian, stationary
8. **Independent Sensors**: No cross-correlation modeled
9. **No Multipath**: Single propagation path
10. **No Countermeasures**: No jamming, decoys, stealth