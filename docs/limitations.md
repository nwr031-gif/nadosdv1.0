# NADOS Dv1.0 Known Limitations

## Simulation Model Limitations

### Physics & Motion
1. **Simplified Kinematics Only**
   - Constant velocity and constant acceleration models only
   - No aerodynamic forces (drag, lift)
   - No gravity variation with altitude
   - No Coriolis or centrifugal effects
   - No thrust modeling for powered objects

2. **Flat Earth Assumption**
   - ENU coordinates assume local flat earth
   - Valid for ranges < 100km
   - No earth curvature corrections
   - No geoid/ellipsoid modeling

3. **No Environmental Effects**
   - Wind only affects sensor noise (not object motion)
   - No atmospheric refraction
   - No ionospheric effects
   - No multipath propagation
   - No weather impact on sensors

### Sensor Models
4. **Idealized Sensor Characteristics**
   - Gaussian noise only (no non-Gaussian tails)
   - Stationary noise statistics
   - No sensor bias drift over time
   - No scan-to-scan correlation
   - No clutter/false alarm modeling (only rate parameter)
   - No beam shape or sidelobes
   - No Doppler/range-rate measurements
   - No polarization effects

5. **Radar Simplifications**
   - Monostatic only
   - No pulse compression modeling
   - No range/velocity ambiguities
   - No PRF selection effects
   - No waveform optimization

6. **Optical/IRST Simplifications**
   - No background clutter modeling
   - No atmospheric transmission losses
   - No sensor saturation/blooming
   - No pixel/FOV discretization

### Tracking & Fusion
7. **Basic Kalman Filter Only**
   - Linear KF (no EKF/UKF for nonlinear models)
   - Single-model (no IMM/MMAE)
   - No track initiation logic (first measurement initializes)
   - No track confirmation/deletion logic (simple coast counter)
   - No data association ambiguity (NN only, no JPDA/MHT)
   - No track labeling or identity management

8. **Fusion Limitations**
   - Assumes independent sensors (no cross-correlation)
   - Covariance Intersection is conservative
   - No out-of-sequence measurement handling
   - No delayed measurement retrodiction
   - No sensor registration error modeling
   - No time synchronization errors

### Data Association
9. **Nearest Neighbor Only**
   - No probabilistic data association (PDA)
   - No joint probabilistic data association (JPDA)
   - No multiple hypothesis tracking (MHT)
   - Global nearest neighbor (greedy)
   - No track splitting/merging logic

## Software Architecture Limitations

### Performance
10. **Single-threaded Simulation Core**
    - No parallelization across objects/sensors
    - Python GIL limits CPU utilization
    - Not optimized for large scenarios (>100 objects)

11. **Memory Growth**
    - Full trajectory stored in memory
    - No automatic trail truncation in engine
    - Database writes every step (can be batched)

12. **Database Bottleneck**
    - SQLite single-writer limitation
    - No connection pooling for reads
    - Synchronous commits by default

### UI/UX
13. **Limited 3D Visualization**
    - Basic procedural geometry only
    - No model loading (glTF, OBJ, etc.)
    - No advanced shaders/effects
    - No head-up display (HUD) overlays
    - No multi-window support

14. **Scenario Editor Basic**
    - No drag-and-drop map editing
    - No trajectory preview
    - No sensor coverage visualization
    - No validation of physical plausibility

15. **Reporting Basic**
    - No PDF generation
    - No interactive plots
    - No comparative analysis tools
    - Fixed report template

## Configuration & Deployment

16. **No Network/Distributed Support**
    - Single-process only
    - No HLA/DIS integration
    - No remote sensor simulation
    - No cloud deployment

17. **Limited Plugin System**
    - No plugin marketplace
    - No hot-reload
    - No sandboxing
    - Python-only plugins

18. **No Authentication/Authorization**
    - Single-user desktop app
    - No role-based access
    - No audit trail for user actions

## Validation & Verification

19. **No Formal Verification**
    - No model checking
    - No proof of correctness
    - Numerical accuracy not certified

20. **Limited Test Coverage**
    - UI tests require display server
    - No hardware-in-the-loop testing
    - No real sensor data validation
    - No operational scenario validation

## Safety & Compliance

21. **Not Safety-Critical Certified**
    - No DO-178C/DO-254 compliance
    - No IEC 61508 SIL rating
    - No MIL-STD compliance
    - Not for operational use

22. **No Security Hardening**
    - No encryption at rest
    - No secure communication
    - No input sanitization for code execution
    - Debug features accessible

## Domain Scope

23. **Air Defense Research Only**
    - No ground/sea domain models
    - No electronic warfare simulation
    - No command decision support
    - No weapon engagement simulation
    - No kill chain modeling

24. **Educational/Research Focus**
    - Parameters chosen for demonstration
    - Not calibrated to real systems
    - No classified/ITAR data
    - No export-controlled algorithms

## Future Roadmap Items

### High Priority
- [ ] Extended Kalman Filter for nonlinear models
- [ ] IMM (Interacting Multiple Model) tracker
- [ ] JPDA data association
- [ ] Scenario versioning/migration
- [ ] Batch database operations
- [ ] PDF report generation

### Medium Priority
- [ ] 3D model loading (glTF)
- [ ] Sensor coverage visualization
- [ ] Trajectory planning editor
- [ ] Monte Carlo simulation runner
- [ ] Distributed simulation (HLA)
- [ ] Real-time data recording

### Low Priority
- [ ] Web-based dashboard
- [ ] Plugin marketplace
- [ ] Multi-language UI (English)
- [ ] Hardware-in-the-loop interface
- [ ] AI/ML integration for tracking
- [ ] Digital twin integration

## Acceptable Use

This simulator is designed for:
- ✅ Algorithm research and development
- ✅ Educational demonstrations
- ✅ Software architecture prototyping
- ✅ Sensor fusion technique evaluation
- ✅ Tracking algorithm comparison
- ✅ Scenario replay and analysis

This simulator is NOT suitable for:
- ❌ Operational mission planning
- ❌ Real-time weapon control
- ❌ Safety-critical systems
- ❌ Regulatory certification
- ❌ Export-controlled applications
- ❌ Classification-guided decisions

## Version Compatibility

| Version | Scenario Schema | Database Schema | API Stability |
|---------|----------------|-----------------|---------------|
| 1.0.0   | v1             | 1               | Alpha         |

Breaking changes will increment minor version and update schemas.