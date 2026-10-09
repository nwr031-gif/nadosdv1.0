"""
NADOS Dv1.0 Web Backend - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sys

# Add parent directory to path for NADOS core modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from nados.config import get_config
from nados.persistence import init_database, get_database
from nados.orchestration import create_application
from nados.simulation import SimulationEngine
from nados.domain import SimulationScenario

# Add backend directory to path for API modules
sys.path.insert(0, os.path.dirname(__file__))

from api import scenarios, simulation, sensors, tracking, reports, health

# Resolve project-relative directories
SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "scenarios")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Global NADOS application instance
nados_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global nados_app
    
    # Initialize configuration
    config = get_config()
    
    # Initialize database (store under project root /data)
    os.makedirs(DATA_DIR, exist_ok=True)
    db_path = os.path.join(DATA_DIR, "nados.db")
    init_database(db_path, config.database.echo)
    
    # Create NADOS application
    nados_app = create_application()
    
    # Load default scenario if available
    if os.path.exists(SCENARIOS_DIR):
        scenario_files = sorted(f for f in os.listdir(SCENARIOS_DIR) if f.endswith('.json'))
        if scenario_files:
            first_scenario = os.path.join(SCENARIOS_DIR, scenario_files[0])
            nados_app.load_scenario(first_scenario)
    
    # Store in app state for access in routes
    app.state.nados_app = nados_app
    app.state.scenarios_dir = SCENARIOS_DIR
    app.state.reports_dir = REPORTS_DIR

    # Background task that advances the simulation while it is running
    import asyncio

    async def simulation_loop():
        while True:
            try:
                engine = getattr(nados_app, "engine", None)
                if engine is not None and engine.state.value == "running":
                    engine.step()
                    timestep = engine.clock.time.timestep
                    speed = max(0.01, engine.clock.time.speed_multiplier)
                    await asyncio.sleep(timestep / speed)
                else:
                    await asyncio.sleep(0.2)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)

    loop_task = asyncio.create_task(simulation_loop())
    app.state.loop_task = loop_task

    yield

    # Shutdown
    loop_task.cancel()
    if nados_app:
        nados_app.shutdown()

# Create FastAPI app
app = FastAPI(
    title="NADOS Dv1.0 API",
    description="NADOS Dv1.0 - Integrated Air Defense Research & Simulation Environment",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(sensors.router, prefix="/api/sensors", tags=["sensors"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["tracking"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "NADOS Dv1.0 API",
        "version": "1.0.0",
        "description": "Integrated Air Defense Research & Simulation Environment",
        "docs": "/docs"
    }

# API info endpoint
@app.get("/api")
async def api_info():
    return {
        "name": "NADOS Dv1.0 API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "scenarios": "/api/scenarios",
            "simulation": "/api/simulation",
            "sensors": "/api/sensors",
            "tracking": "/api/tracking",
            "reports": "/api/reports"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)