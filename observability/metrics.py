"""
Metrics Collector
=================
Collects runtime metrics for the credit risk agent system.
Tracks:
    - Total analyses run
    - Risk distribution (Low/Medium/High counts)
    - Average processing time
    - Error rates
    - Per-agent execution counts

In production this would export to Prometheus / Grafana / CloudWatch.
"""

import datetime
from collections import defaultdict


class MetricsCollector:
    """
    In-memory metrics store for the current session.
    Provides counters, histograms, and distribution stats.
    """

    def __init__(self):
        self._analyses_total  = 0
        self._risk_distribution = defaultdict(int)
        self._processing_times  = []
        self._errors_total      = 0
        self._agent_call_counts = defaultdict(int)
        self._session_start     = datetime.datetime.now()

    def record_analysis(self, risk_level: str, processing_time: float) -> None:
        """
        Record a completed analysis.

        Args:
            risk_level:      "Low Risk", "Medium Risk", or "High Risk"
            processing_time: seconds taken for the full pipeline
        """
        self._analyses_total += 1
        self._risk_distribution[risk_level] += 1
        self._processing_times.append(processing_time)

    def record_agent_call(self, agent_name: str) -> None:
        """Increment the call counter for a specific agent."""
        self._agent_call_counts[agent_name] += 1

    def record_error(self, error_type: str) -> None:
        """Record an error event."""
        self._errors_total += 1

    def get_total_analyses(self) -> int:
        """Return total number of analyses run this session."""
        return self._analyses_total

    def get_risk_distribution(self) -> dict:
        """Return the count of each risk level classification."""
        return dict(self._risk_distribution)

    def get_avg_processing_time(self) -> float:
        """Return the average analysis processing time in seconds."""
        if not self._processing_times:
            return 0.0
        return round(sum(self._processing_times) / len(self._processing_times), 3)

    def get_p95_processing_time(self) -> float:
        """Return 95th percentile processing time."""
        if len(self._processing_times) < 2:
            return 0.0
        sorted_times = sorted(self._processing_times)
        idx = int(0.95 * len(sorted_times))
        return round(sorted_times[idx], 3)

    def get_error_rate(self) -> float:
        """Return error rate as a percentage of total analyses."""
        if self._analyses_total == 0:
            return 0.0
        return round(self._errors_total / self._analyses_total * 100, 2)

    def get_full_report(self) -> dict:
        """Return a complete metrics report for this session."""
        return {
            "session_start":        self._session_start.isoformat(),
            "total_analyses":       self._analyses_total,
            "risk_distribution":    dict(self._risk_distribution),
            "avg_processing_time_s": self.get_avg_processing_time(),
            "p95_processing_time_s": self.get_p95_processing_time(),
            "error_rate_pct":       self.get_error_rate(),
            "agent_call_counts":    dict(self._agent_call_counts),
            "uptime_minutes": round(
                (datetime.datetime.now() - self._session_start).total_seconds() / 60, 1
            )
        }
