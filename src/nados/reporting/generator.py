"""
Report generation for simulation runs.
"""

import csv
import json
import hashlib
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from nados.config import get_config
from nados.domain import SimulationRun, SimulationScenario
from nados.persistence import (
    get_database,
    ObservationRepository,
    TrackRepository,
    EventRepository,
    RunRepository,
)


class ReportFormat(str, Enum):
    """Supported report formats."""
    JSON = "json"
    CSV = "csv"


class ReportGenerator:
    """Generates simulation reports in various formats."""
    
    def __init__(self, output_dir: Optional[str] = None) -> None:
        config = get_config()
        self.output_dir = Path(output_dir or config.reports.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.db = get_database()
        self.obs_repo = ObservationRepository(self.db)
        self.track_repo = TrackRepository(self.db)
        self.event_repo = EventRepository(self.db)
        self.run_repo = RunRepository(self.db)
    
    def generate_report(
        self,
        run_id: str,
        formats: Optional[List[ReportFormat]] = None,
        scenario: Optional[SimulationScenario] = None,
    ) -> Dict[ReportFormat, Path]:
        """Generate report for a simulation run."""
        formats = formats or [ReportFormat.JSON, ReportFormat.CSV]
        
        run = self.run_repo.get(run_id)
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        # Load data
        observations = self.obs_repo.get_by_run(run_id)
        tracks = self.track_repo.get_by_run(run_id)
        events = self.event_repo.get_by_run(run_id)
        
        # Get scenario if not provided
        if scenario is None:
            from nados.persistence import ScenarioRepository
            scenario_repo = ScenarioRepository(self.db)
            scenario = scenario_repo.get(run.scenario_id)
        
        # Build report data
        report_data = self._build_report_data(run, scenario, observations, tracks, events)
        
        # Generate files
        output_files = {}
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = f"report_{run_id}_{timestamp}"
        
        for fmt in formats:
            if fmt == ReportFormat.JSON:
                path = self.output_dir / f"{base_name}.json"
                self._write_json(report_data, path)
                output_files[fmt] = path
            elif fmt == ReportFormat.CSV:
                path = self.output_dir / f"{base_name}.csv"
                self._write_csv(report_data, path)
                output_files[fmt] = path
        
        return output_files
    
    def _build_report_data(
        self,
        run: SimulationRun,
        scenario: Optional[SimulationScenario],
        observations: List,
        tracks: List,
        events: List,
    ) -> Dict[str, Any]:
        """Build the report data structure."""
        
        # Calculate metrics
        valid_observations = [o for o in observations if o.validity_status.value == "valid"]
        total_observations = len(observations)
        rejected_observations = total_observations - len(valid_observations)
        
        active_tracks = [t for t in tracks if t.tracking_status.value in ("active", "coasting")]
        
        # Processing time stats
        event_timestamps = [e.timestamp for e in events]
        processing_stats = {}
        if event_timestamps:
            processing_stats = {
                "first_event_time": min(event_timestamps),
                "last_event_time": max(event_timestamps),
                "event_count": len(events),
            }
        
        # Configuration hash
        config_str = f"{run.scenario_id}_{run.random_seed}_{run.application_version}"
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
        
        return {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "generator_version": "1.0.0",
                "report_format_version": "v1",
            },
            "simulation_info": {
                "application_version": run.application_version,
                "scenario_name": scenario.name if scenario else "Unknown",
                "scenario_schema_version": scenario.schema_version if scenario else "Unknown",
                "configuration_hash": config_hash,
                "random_seed": run.random_seed,
                "simulation_duration_seconds": run.duration_seconds() or 0,
            },
            "execution_status": {
                "status": run.status.value,
                "started_at": run.started_at.isoformat() + "Z" if run.started_at else None,
                "completed_at": run.completed_at.isoformat() + "Z" if run.completed_at else None,
                "duration_seconds": run.duration_seconds(),
            },
            "observation_statistics": {
                "total_generated": total_observations,
                "valid_count": len(valid_observations),
                "rejected_count": rejected_observations,
                "rejection_rate": rejected_observations / total_observations if total_observations > 0 else 0,
                "by_sensor": self._group_by_sensor(observations),
            },
            "tracking_summary": {
                "total_tracks": len(tracks),
                "active_tracks": len(active_tracks),
                "lost_tracks": len([t for t in tracks if t.tracking_status.value == "lost"]),
                "average_observations_per_track": (
                    sum(t.observation_count for t in tracks) / len(tracks) if tracks else 0
                ),
            },
            "processing_statistics": processing_stats,
            "errors_and_warnings": {
                "error_count": len([e for e in events if e.severity.value == "error"]),
                "warning_count": len([e for e in events if e.severity.value == "warning"]),
                "critical_count": len([e for e in events if e.severity.value == "critical"]),
            },
            "known_limitations": [
                "Simulation uses simplified kinematic models",
                "Sensor models are synthetic and not calibrated to real systems",
                "Tracking uses basic Kalman filter with constant velocity assumption",
                "Fusion assumes uncorrelated sensor errors",
                "No atmospheric propagation effects modeled",
            ],
        }
    
    def _group_by_sensor(self, observations: List) -> Dict[str, Dict[str, int]]:
        """Group observations by sensor."""
        result = {}
        for obs in observations:
            sensor_id = obs.sensor_id
            if sensor_id not in result:
                result[sensor_id] = {"total": 0, "valid": 0, "missing": 0, "invalid": 0}
            result[sensor_id]["total"] += 1
            result[sensor_id][obs.validity_status.value] = result[sensor_id].get(obs.validity_status.value, 0) + 1
        return result
    
    def _write_json(self, data: Dict[str, Any], path: Path) -> None:
        """Write report as JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _write_csv(self, data: Dict[str, Any], path: Path) -> None:
        """Write report as CSV (flattened)."""
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Section", "Key", "Value"])
            
            def write_section(section: str, obj: Any, prefix: str = "") -> None:
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        write_section(section, value, f"{prefix}{key}.")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        write_section(section, item, f"{prefix}[{i}].")
                else:
                    writer.writerow([section, prefix.rstrip("."), str(obj)])
            
            for section, content in data.items():
                write_section(section, content)


def generate_demo_report(run_id: str, output_dir: Optional[str] = None) -> Dict[ReportFormat, Path]:
    """Convenience function to generate a demo report."""
    generator = ReportGenerator(output_dir)
    return generator.generate_report(run_id)