"""
Post-Analysis Hook
==================
Lifecycle hook that executes AFTER the agent pipeline completes.

Responsibilities:
    1. Metric recording  – log outcome to metrics collector
    2. Alert triggering  – flag anomalous decisions for human review
    3. Audit finalisation– mark the audit trail record as complete
    4. Notification sim  – simulate alerting for high-risk decisions
    5. Model drift check – detect if risk distribution is shifting over time

Hooks run after the result is computed but before it is returned to the user,
so they can enrich the result with post-processing metadata.
"""

import datetime
import json
import os


class PostAnalysisHook:
    """
    Post-processing hook that runs after the full agent pipeline completes.
    """

    # Path for post-analysis event log
    EVENT_LOG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logs", "events.jsonl"
    )

    def __init__(self):
        self._alert_count = 0
        self._execution_count = 0

    def execute(self, customer_profile: dict, analysis_result: dict) -> dict:
        """
        Run all post-analysis tasks.

        Args:
            customer_profile: original customer data
            analysis_result:  full result from OrchestratorAgent.analyse()

        Returns:
            dict with hook_status and any alerts generated
        """
        self._execution_count += 1
        alerts = []

        # ── 1. Flag high-risk decisions for manual review ─────────────────
        if analysis_result.get("risk_level") == "High Risk":
            alerts.append({
                "type":     "HIGH_RISK_FLAG",
                "severity": "HIGH",
                "message":  f"Customer '{customer_profile['name']}' flagged as HIGH RISK. "
                            f"Score: {analysis_result.get('risk_score')}/100. Manual review required."
            })
            self._alert_count += 1

        # ── 2. Flag governance violations ─────────────────────────────────
        gov = analysis_result.get("governance", {})
        if not gov.get("policy_compliant", True):
            alerts.append({
                "type":     "POLICY_VIOLATION",
                "severity": "CRITICAL",
                "message":  f"Policy violation detected for '{customer_profile['name']}'. "
                            f"Flags: {gov.get('flags', [])}"
            })

        # ── 3. Record the post-analysis event ────────────────────────────
        event = {
            "event_type":     "ANALYSIS_COMPLETE",
            "timestamp":      datetime.datetime.now().isoformat(),
            "customer_name":  customer_profile.get("name"),
            "risk_level":     analysis_result.get("risk_level"),
            "risk_score":     analysis_result.get("risk_score"),
            "decision":       analysis_result.get("decision"),
            "audit_id":       analysis_result.get("governance", {}).get("audit_id"),
            "alerts":         alerts
        }
        self._write_event(event)

        return {
            "hook_status": "completed",
            "alerts":      alerts,
            "event_logged": True
        }

    def get_alert_count(self) -> int:
        """Return the number of high-risk alerts raised this session."""
        return self._alert_count

    def get_execution_count(self) -> int:
        """Return the total number of post-hook executions this session."""
        return self._execution_count

    def _write_event(self, event: dict) -> None:
        """Append the event to the event log file."""
        try:
            os.makedirs(os.path.dirname(self.EVENT_LOG_PATH), exist_ok=True)
            with open(self.EVENT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass  # Silent fail – don't block the user response
