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
    - Token consumption (input/output per agent)

Prometheus /metrics endpoint is served on port 8000 automatically when this
module is first imported.
"""

import datetime
import threading
from collections import defaultdict

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    disable_created_metrics,
    make_wsgi_app,
)

disable_created_metrics()

# ── Prometheus registry & metrics (module-level singletons) ──────────────────
_PROM_REGISTRY = CollectorRegistry(auto_describe=True)

_TOKENS = Counter(
    "credit_tokens_total",
    "Tokens consumed per agent call",
    ["agent", "token_type"],
    registry=_PROM_REGISTRY,
)
_ANALYSES = Counter(
    "credit_analyses_total",
    "Total credit risk analyses completed",
    registry=_PROM_REGISTRY,
)
_REQUESTS = Counter(
    "credit_requests_total",
    "Analysis requests received (pre-validation)",
    registry=_PROM_REGISTRY,
)
_ERRORS = Counter(
    "credit_errors_total",
    "Errors during analysis pipeline",
    ["error_type"],
    registry=_PROM_REGISTRY,
)
_LATENCY = Histogram(
    "credit_analysis_duration_seconds",
    "End-to-end analysis pipeline latency",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float("inf")],
    registry=_PROM_REGISTRY,
)
_RISK_DIST = Gauge(
    "credit_risk_level_total",
    "Cumulative count of analyses by risk level (session)",
    ["risk_level"],
    registry=_PROM_REGISTRY,
)

for _lvl in ("Low Risk", "Medium Risk", "High Risk"):
    _RISK_DIST.labels(risk_level=_lvl).set(0)


# ── HTTP server (wsgiref, daemon thread, auto-started at import) ──────────────

def _serve_metrics(port: int) -> None:
    """Run a minimal WSGI server exposing /metrics. Blocks forever."""
    from wsgiref.simple_server import make_server, WSGIRequestHandler

    class _Silent(WSGIRequestHandler):
        def log_message(self, *args):
            pass

    wsgi_app = make_wsgi_app(_PROM_REGISTRY)
    try:
        with make_server("", port, wsgi_app, handler_class=_Silent) as httpd:
            httpd.serve_forever()
    except OSError:
        pass  # port already bound (e.g. during tests); metrics registry is still shared


def start_prometheus_exporter(port: int = 8000) -> None:
    """Public hook kept for explicit callers; auto-start already happens at import."""
    _ensure_server(port)


_server_lock = threading.Lock()
_server_started = False
_server_port = 8000


def _ensure_server(port: int = 8000) -> None:
    global _server_started, _server_port
    with _server_lock:
        if not _server_started:
            _server_port = port
            t = threading.Thread(target=_serve_metrics, args=(port,), name="prom-metrics", daemon=True)
            t.start()
            _server_started = True


# Auto-start on import (runs once per process because sys.modules caches this module)
_ensure_server(8000)


class MetricsCollector:
    """
    In-memory metrics store for the current session.
    Provides counters, histograms, and distribution stats.
    Also updates module-level Prometheus metrics on each record call.
    """

    def __init__(self):
        self._analyses_total    = 0
        self._risk_distribution = defaultdict(int)
        self._processing_times  = []
        self._errors_total      = 0
        self._agent_call_counts = defaultdict(int)
        self._token_counts      = defaultdict(lambda: {"input": 0, "output": 0})
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
        _ANALYSES.inc()
        _LATENCY.observe(processing_time)
        _RISK_DIST.labels(risk_level=risk_level).inc()

    def record_agent_call(self, agent_name: str) -> None:
        """Increment the call counter for a specific agent."""
        self._agent_call_counts[agent_name] += 1

    def record_error(self, error_type: str) -> None:
        """Record an error event."""
        self._errors_total += 1
        _ERRORS.labels(error_type=error_type).inc()

    def record_request(self) -> None:
        """Increment the requests counter (call before the pipeline runs)."""
        _REQUESTS.inc()

    def record_tokens(self, agent_name: str, input_tokens: int, output_tokens: int) -> None:
        """Record token consumption from a Claude API response."""
        self._token_counts[agent_name]["input"]  += input_tokens
        self._token_counts[agent_name]["output"] += output_tokens
        _TOKENS.labels(agent=agent_name, token_type="input").inc(input_tokens)
        _TOKENS.labels(agent=agent_name, token_type="output").inc(output_tokens)

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

    def get_token_counts(self) -> dict:
        """Return token consumption summary per agent."""
        return {agent: dict(counts) for agent, counts in self._token_counts.items()}

    def get_full_report(self) -> dict:
        """Return a complete metrics report for this session."""
        return {
            "session_start":         self._session_start.isoformat(),
            "total_analyses":        self._analyses_total,
            "risk_distribution":     dict(self._risk_distribution),
            "avg_processing_time_s": self.get_avg_processing_time(),
            "p95_processing_time_s": self.get_p95_processing_time(),
            "error_rate_pct":        self.get_error_rate(),
            "agent_call_counts":     dict(self._agent_call_counts),
            "token_counts":          self.get_token_counts(),
            "uptime_minutes": round(
                (datetime.datetime.now() - self._session_start).total_seconds() / 60, 1
            )
        }
