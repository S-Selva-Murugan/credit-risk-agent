"""
Tracer
======
Distributed tracing utility for the multi-agent credit risk system.
Records every agent action with a timestamp to create a complete audit trail
of every decision from input to output.

In production this would integrate with OpenTelemetry / Jaeger / Datadog.
For this project it provides in-memory and file-based tracing.
"""

import datetime
import json
import os


class Tracer:
    """
    Lightweight tracer for recording the agent pipeline execution.
    One Tracer instance is created per application session and shared
    across all agents via dependency injection.
    """

    # Path to the trace log file
    TRACE_LOG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logs", "traces.jsonl"
    )

    def __init__(self):
        # In-memory trace buffer for the current analysis session
        self._trace: list = []

    def log(self, agent: str, message: str, level: str = "INFO") -> None:
        """
        Record a trace event from an agent.

        Args:
            agent:   Name of the agent generating the trace
            message: Human-readable description of what the agent did
            level:   Log level (INFO, WARNING, ERROR)
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent":     agent,
            "level":     level,
            "message":   message
        }
        self._trace.append(entry)
        self._persist(entry)

    def get_trace(self) -> list:
        """Return all trace entries for the current analysis session."""
        return list(self._trace)

    def clear(self) -> None:
        """Clear the in-memory trace (call before each new analysis)."""
        self._trace.clear()

    def get_agent_steps(self, agent_name: str) -> list:
        """Return trace entries for a specific agent only."""
        return [t for t in self._trace if t["agent"] == agent_name]

    def get_summary(self) -> dict:
        """Return a summary of the trace for display purposes."""
        agents = list({t["agent"] for t in self._trace})
        return {
            "total_steps":    len(self._trace),
            "agents_involved": agents,
            "start_time":     self._trace[0]["timestamp"] if self._trace else None,
            "end_time":       self._trace[-1]["timestamp"] if self._trace else None
        }

    def _persist(self, entry: dict) -> None:
        """Append a trace entry to the persistent trace log file."""
        try:
            os.makedirs(os.path.dirname(self.TRACE_LOG_PATH), exist_ok=True)
            with open(self.TRACE_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Never block the main pipeline for trace failures
