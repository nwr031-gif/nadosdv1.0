"""
Reports API endpoints.
"""

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ReportRequest(BaseModel):
    run_id: str
    formats: list[str] = ["json", "csv"]


class RunResponse(BaseModel):
    id: str
    scenario_id: str
    scenario_name: str
    status: str
    started_at: str
    completed_at: str | None = None
    duration: float | None = None
    seed: int


# Mock runs storage
RUNS_DB = {
    "run_001": {
        "id": "run_001",
        "scenario_id": "basic_tracking",
        "scenario_name": "تتبع أساسي",
        "status": "completed",
        "started_at": "2024-01-15T10:30:00Z",
        "completed_at": "2024-01-15T10:31:00Z",
        "duration": 60,
        "seed": 42,
    },
    "run_002": {
        "id": "run_002",
        "scenario_id": "noisy_sensor",
        "scenario_name": "مستشعر ضوضائي",
        "status": "completed",
        "started_at": "2024-01-15T11:00:00Z",
        "completed_at": "2024-01-15T11:02:00Z",
        "duration": 120,
        "seed": 12345,
    },
}

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


@router.get("/runs", response_model=list[dict])
async def list_runs():
    """List all simulation runs."""
    return list(RUNS_DB.values())


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get run details."""
    if run_id not in RUNS_DB:
        raise HTTPException(status_code=404, detail="Run not found")
    return RUNS_DB[run_id]


@router.post("/generate")
async def generate_report(request: dict):
    """Generate a report for a run."""
    run_id = request.get("run_id")

    if run_id not in RUNS_DB:
        raise HTTPException(status_code=404, detail="Run not found")

    run = RUNS_DB[run_id]

    # Generate mock report
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generator_version": "1.0.0",
            "report_format_version": "v1",
        },
        "simulation_info": {
            "application_version": "1.0.0",
            "scenario_name": run["scenario_name"],
            "scenario_schema_version": "v1",
            "configuration_hash": "abc123",
            "random_seed": run["seed"],
            "simulation_duration_seconds": run.get("duration", 0),
        },
        "execution_status": {
            "status": run["status"],
            "started_at": run["started_at"],
            "completed_at": run.get("completed_at"),
            "duration_seconds": run.get("duration"),
        },
        "observation_statistics": {
            "total_generated": 600,
            "valid_count": 580,
            "rejected_count": 20,
            "rejection_rate": 0.033,
            "by_sensor": {"radar_001": {"total": 300, "valid": 290, "missing": 10, "invalid": 0}},
        },
        "tracking_summary": {
            "total_tracks": 1,
            "active_tracks": 1,
            "lost_tracks": 0,
            "average_observations_per_track": 290.0,
        },
        "processing_statistics": {"first_event_time": 0, "last_event_time": 60, "event_count": 650},
        "errors_and_warnings": {"error_count": 0, "warning_count": 2, "critical_count": 0},
        "known_limitations": [
            "محاكاة تستخدم نماذج حركية مبسطة",
            "نماذج المستشعرات افتراضية وغير معاير لأنظمة حقيقية",
            "التتبع يستخدم مرشح كالمّان أساسي مع افتراض سرعة ثابتة",
            "الدمج يفترض أخطاء مستشعرات غير مترابطة",
            "لا توجد تأثيرات انتشار جوي مُحاكاة",
        ],
    }

    # Save report files
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"report_{run_id}_{timestamp}"
    generated_files = {}

    if "json" in ["json", "csv"]:  # Always generate both for demo
        json_path = REPORTS_DIR / f"{base_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        generated_files["json"] = str(json_path)

    if "csv" in ["json", "csv"]:
        csv_path = REPORTS_DIR / f"{base_name}.csv"
        # Simple CSV export
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Section", "Key", "Value"])

        def flatten(obj, prefix=""):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    flatten(v, key)
                else:
                    writer.writerow([key, str(v)])

        flatten(report)

        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())
        generated_files["csv"] = str(csv_path)

    return {"message": "Report generated successfully", "run_id": run_id, "files": generated_files}


@router.get("/{run_id}/download/{format}")
async def download_report(run_id: str, format: str):
    """Download a generated report."""
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{run_id}_{timestamp}.{format}"
    filepath = REPORTS_DIR / filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    from fastapi.responses import FileResponse

    return FileResponse(filepath, filename=filename)
