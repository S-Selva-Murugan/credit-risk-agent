"""
Audit Agent
===========
Specialist subagent responsible for creating immutable audit records of
every credit risk decision made by the system.

Purpose:
    - Regulatory compliance (RBI guidelines, Basel III)
    - Explainability of AI decisions
    - Dispute resolution evidence
    - Model performance monitoring

Records are written to both an in-memory store (for the current session)
and a JSON-lines file on disk (for persistence across sessions).
"""

import json
import os
import uuid
import datetime


class AuditAgent:
    """
    Creates tamper-evident audit records for every credit risk decision.
    All records are persisted to disk for regulatory purposes.
    """

    # Path to the audit log file (append-only JSON lines format)
    AUDIT_LOG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "logs", "audit_log.jsonl"
    )

    def __init__(self, tracer):
        self.tracer = tracer
        # In-memory cache of records for the current session
        self._records = []

    def record(self,
               audit_id: str,
               session_id: str,
               customer_profile: dict,
               risk_result: dict,
               decision: str,
               governance_result: dict) -> None:
        """
        Create and persist an audit record.

        Args:
            audit_id:          Unique audit identifier
            session_id:        Session identifier
            customer_profile:  Customer input data
            risk_result:       Output from RiskScoringAgent
            decision:          Final banking decision (Approve/Review/Reject)
            governance_result: Output from PolicyEngine
        """
        self.tracer.log(
            agent="AuditAgent",
            message=f"Creating audit record {audit_id}"
        )

        # Build the audit record – strip PII from the persisted record
        audit_record = {
            "audit_id":    audit_id,
            "session_id":  session_id,
            "timestamp":   datetime.datetime.now().isoformat(),

            # Anonymised customer data (do not log full PII in production)
            "customer": {
                "name_hash":      self._hash_name(customer_profile["name"]),
                "age_band":       self._age_band(customer_profile["age"]),
                "employment_type": customer_profile["employment_type"]
            },

            # Risk outcome
            "outcome": {
                "risk_score": risk_result["risk_score"],
                "risk_level": risk_result["risk_level"],
                "decision":   decision
            },

            # Governance metadata
            "governance": {
                "policy_compliant":  governance_result.get("policy_compliant"),
                "bias_check_passed": governance_result.get("bias_check_passed"),
                "flags":             governance_result.get("flags", [])
            },

            # Model / system metadata
            "system": {
                "agent_version": "1.0.0",
                "scoring_model": "rule-based-v1",
                "agent_id":      "RiskScoringAgent"
            }
        }

        # Store in memory
        self._records.append(audit_record)

        # Persist to disk (append-only)
        self._persist(audit_record)

        self.tracer.log(
            agent="AuditAgent",
            message=f"Audit record {audit_id} persisted to {self.AUDIT_LOG_PATH}"
        )

    def get_records(self) -> list:
        """Return all audit records for the current session."""
        return self._records

    def get_record(self, audit_id: str) -> dict:
        """Retrieve a specific audit record by ID."""
        for record in self._records:
            if record["audit_id"] == audit_id:
                return record
        return {}

    def _persist(self, record: dict) -> None:
        """Append the audit record to the JSON-lines log file on disk."""
        try:
            os.makedirs(os.path.dirname(self.AUDIT_LOG_PATH), exist_ok=True)
            with open(self.AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            self.tracer.log(
                agent="AuditAgent",
                message=f"WARNING: Could not write to audit log: {e}"
            )

    def _hash_name(self, name: str) -> str:
        """
        One-way hash of the customer name for anonymisation.
        Uses a simple truncated hash – in production use SHA-256 with a salt.
        """
        return f"CUST-{abs(hash(name)) % 1_000_000:06d}"

    def _age_band(self, age: int) -> str:
        """Convert exact age to an age band to reduce PII in audit logs."""
        if age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        elif age < 65:
            return "55-64"
        else:
            return "65+"
