"""
Health checks for core modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = None
    timestamp: float = 0.0
    
    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}
        if self.timestamp == 0.0:
            import time
            self.timestamp = time.time()


class HealthChecker:
    """Runs health checks for application components."""
    
    def __init__(self) -> None:
        self._checks: Dict[str, Callable[[], HealthCheck]] = {}
    
    def register_check(self, name: str, check_func: Callable[[], HealthCheck]) -> None:
        """Register a health check function."""
        self._checks[name] = check_func
    
    def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self._checks:
            return HealthCheck(name=name, status=HealthStatus.UNKNOWN, message=f"Check '{name}' not registered")
        try:
            return self._checks[name]()
        except Exception as e:
            return HealthCheck(name=name, status=HealthStatus.UNHEALTHY, message=f"Check failed: {e}")
    
    def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        return {name: self.run_check(name) for name in self._checks}
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall health status."""
        results = self.run_all_checks()
        if not results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in results.values()]
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        return HealthStatus.HEALTHY


_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
        _register_default_checks(_health_checker)
    return _health_checker


def run_health_checks() -> Dict[str, HealthCheck]:
    """Run all health checks and return results."""
    return get_health_checker().run_all_checks()


def _register_default_checks(checker: HealthChecker) -> None:
    """Register default health checks."""
    
    def check_config() -> HealthCheck:
        try:
            from nados.config import get_config
            config = get_config()
            return HealthCheck(name="config", status=HealthStatus.HEALTHY, message="Configuration loaded")
        except Exception as e:
            return HealthCheck(name="config", status=HealthStatus.UNHEALTHY, message=f"Config error: {e}")
    
    def check_database() -> HealthCheck:
        try:
            from nados.persistence import get_database
            from sqlalchemy import text
            db = get_database()
            # Try a simple query
            with db.session() as session:
                session.execute(text("SELECT 1"))
            return HealthCheck(name="database", status=HealthStatus.HEALTHY, message="Database accessible")
        except Exception as e:
            return HealthCheck(name="database", status=HealthStatus.UNHEALTHY, message=f"Database error: {e}")
    
    def check_simulation() -> HealthCheck:
        try:
            from nados.simulation import SimulationEngine
            return HealthCheck(name="simulation", status=HealthStatus.HEALTHY, message="Simulation module available")
        except Exception as e:
            return HealthCheck(name="simulation", status=HealthStatus.UNHEALTHY, message=f"Simulation error: {e}")
    
    checker.register_check("config", check_config)
    checker.register_check("database", check_database)
    checker.register_check("simulation", check_simulation)