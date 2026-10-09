"""
Metrics collection for monitoring and observability.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MetricValue:
    """A single metric measurement."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates application metrics."""
    
    def __init__(self) -> None:
        self._metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        self._lock = threading.RLock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            self._metrics[name].append(MetricValue(name=name, value=self._counters[key], labels=labels or {}))
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._metrics[name].append(MetricValue(name=name, value=value, labels=labels or {}))
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            self._metrics[name].append(MetricValue(name=name, value=value, labels=labels or {}))
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        with self._lock:
            key = self._make_key(name, labels)
            values = self._histograms.get(key, [])
            if not values:
                return {"count": 0, "min": 0, "max": 0, "mean": 0, "sum": 0}
            
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "sum": sum(values),
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self.get_histogram_stats(k.split("|")[0], self._parse_labels(k)) for k in self._histograms},
            }
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a key from name and labels."""
        if not labels:
            return name
        label_str = "|".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}|{label_str}"
    
    def _parse_labels(self, key: str) -> Dict[str, str]:
        """Parse labels from key."""
        parts = key.split("|")
        if len(parts) < 2:
            return {}
        labels = {}
        for part in parts[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                labels[k] = v
        return labels


_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector