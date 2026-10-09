"""
Main application orchestration class.
"""

import uuid

from nados.config import get_config, load_config
from nados.domain import SimulationScenario
from nados.fusion import DataFusionService
from nados.observability import get_logger, get_metrics_collector, run_health_checks, setup_logging
from nados.persistence import get_database, init_database
from nados.reporting import ReportGenerator
from nados.simulation import SimulationEngine
from nados.tracking import ObjectTracker


class NADOSApplication:
    """Main application orchestrator."""

    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = config_path
        self.logger = get_logger("orchestration.app")
        self.metrics = get_metrics_collector()

        # Core components
        self.scenario: SimulationScenario | None = None
        self.engine: SimulationEngine | None = None
        self.tracker: ObjectTracker | None = None
        self.fusion_service: DataFusionService | None = None
        self.report_generator: ReportGenerator | None = None

        # State
        self.current_run_id: str | None = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the application."""
        try:
            # Load configuration
            if self.config_path:
                load_config(self.config_path)

            config = get_config()

            # Setup logging
            setup_logging()

            # Initialize database
            init_database(config.database.path, config.database.echo)

            # Initialize core services
            self.tracker = ObjectTracker()
            self.fusion_service = DataFusionService()
            self.report_generator = ReportGenerator()

            # Run health checks
            health = run_health_checks()
            for name, check in health.items():
                if check.status.value == "unhealthy":
                    self.logger.warning(f"Health check failed: {name} - {check.message}")

            self._initialized = True
            self.logger.info("NADOS Application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def load_scenario(self, scenario_path: str) -> bool:
        """Load and validate a scenario."""
        try:
            from nados.orchestration.scenario_loader import load_scenario

            self.scenario = load_scenario(scenario_path)

            # Save scenario to database
            from nados.persistence import ScenarioRepository

            scenario_repo = ScenarioRepository()
            scenario_repo.save(self.scenario)

            # Create simulation engine
            self.engine = SimulationEngine(self.scenario)

            # Register event handler for tracking
            self.engine.register_event_handler(self._on_simulation_event)

            self.logger.info(f"Scenario loaded: {self.scenario.name} ({self.scenario.scenario_id})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load scenario: {e}")
            return False

    def _on_simulation_event(self, event) -> None:
        """Handle simulation events."""
        # Forward to tracker for observation processing
        if event.event_type.value == "observation_generated":
            # Extract observation from event metadata
            pass

    def start_simulation(self) -> bool:
        """Start the simulation."""
        if not self.engine:
            self.logger.error("No scenario loaded")
            return False

        try:
            self.current_run_id = str(uuid.uuid4())

            # Create run record
            from nados.domain import RunStatus, SimulationRun
            from nados.persistence import RunRepository

            run = SimulationRun(
                run_id=self.current_run_id,
                scenario_id=self.scenario.scenario_id,
                random_seed=self.scenario.random_seed,
                application_version="1.0.0",
                configuration_hash="",
                status=RunStatus.RUNNING,
            )

            run_repo = RunRepository()
            run_repo.save(run)

            # Start engine
            self.engine.start()

            self.logger.info(f"Simulation started: {self.current_run_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            return False

    def run_simulation_sync(self, max_steps: int | None = None) -> bool:
        """Run simulation synchronously."""
        if not self.engine:
            return False

        try:
            # Create run record if not already created
            if not self.current_run_id:
                self.current_run_id = str(uuid.uuid4())

                from nados.domain import RunStatus, SimulationRun
                from nados.persistence import RunRepository

                run = SimulationRun(
                    run_id=self.current_run_id,
                    scenario_id=self.scenario.scenario_id,
                    random_seed=self.scenario.random_seed,
                    application_version="1.0.0",
                    configuration_hash="",
                    status=RunStatus.RUNNING,
                )

                run_repo = RunRepository()
                run_repo.save(run)

            result = self.engine.run_sync(max_steps)

            # Save results
            self._save_simulation_results()

            return result.success

        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
            return False

    def pause_simulation(self) -> None:
        """Pause simulation."""
        if self.engine:
            self.engine.pause()

    def resume_simulation(self) -> None:
        """Resume simulation."""
        if self.engine:
            self.engine.start()  # Resumes

    def stop_simulation(self) -> None:
        """Stop simulation."""
        if self.engine:
            self.engine.stop()
        self._save_simulation_results()

    def reset_simulation(self) -> None:
        """Reset simulation."""
        if self.engine:
            self.engine.reset()
        self.current_run_id = None

    def step_simulation(self) -> bool:
        """Execute one simulation step."""
        if not self.engine:
            return False

        result = self.engine.step()

        # Process observations for tracking
        if result.success and result.observations:
            for _obs in result.observations:
                # TODO: Process through tracker
                pass

        return result.success

    def _save_simulation_results(self) -> None:
        """Save simulation results to database."""
        if not self.current_run_id or not self.engine:
            return

        try:
            from nados.domain import RunStatus
            from nados.persistence import (
                RunRepository,
            )

            # Get data from engine
            # TODO: Collect observations, tracks, events from engine

            # Update run status
            run_repo = RunRepository()
            run = run_repo.get(self.current_run_id)
            if run:
                run.status = RunStatus.COMPLETED
                run.completed_at = __import__("datetime").datetime.utcnow()
                run_repo.save(run)

            self.logger.info(f"Simulation results saved for run: {self.current_run_id}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    def generate_report(self, run_id: str | None = None, formats: list | None = None) -> dict:
        """Generate report for a run."""
        if not self.report_generator:
            return {}

        target_run_id = run_id or self.current_run_id
        if not target_run_id:
            return {}

        from nados.reporting import ReportFormat

        fmt_list = [ReportFormat(f) for f in (formats or ["json", "csv"])]

        return self.report_generator.generate_report(target_run_id, fmt_list, self.scenario)

    def shutdown(self) -> None:
        """Shutdown the application."""
        self.logger.info("Shutting down NADOS application")

        if self.engine:
            self.engine.stop()

        db = get_database()
        db.close()

        self._initialized = False


def create_application(config_path: str | None = None) -> NADOSApplication:
    """Create and initialize the application."""
    app = NADOSApplication(config_path)
    if not app.initialize():
        raise RuntimeError("Failed to initialize NADOS application")
    return app
