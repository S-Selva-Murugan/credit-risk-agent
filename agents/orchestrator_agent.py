"""
Orchestrator Agent
==================
The central coordinator of the multi-agent credit risk system.
It receives a customer profile, delegates to specialist subagents in order,
collects their outputs, enforces governance policy, and returns a unified result.

Agent Pipeline:
    1. RiskScoringAgent  → computes numeric risk score
    2. ExplanationAgent  → produces human-readable explanation
    3. AuditAgent        → creates immutable audit record
    4. PolicyEngine      → checks governance compliance
"""

import uuid
import datetime
from agents.risk_scoring_agent import RiskScoringAgent
from agents.explanation_agent import ExplanationAgent
from agents.audit_agent import AuditAgent


class OrchestratorAgent:
    """
    The Orchestrator is the master agent.
    It does not compute risk itself – instead it delegates every
    specialised task to the right subagent and combines the results.
    """

    def __init__(self, tracer, metrics, policy_engine):
        # Inject dependencies (tracer, metrics, policy engine)
        self.tracer = tracer
        self.metrics = metrics
        self.policy_engine = policy_engine

        # Instantiate subagents
        self.risk_agent = RiskScoringAgent(tracer=tracer)
        self.explanation_agent = ExplanationAgent(tracer=tracer)
        self.audit_agent = AuditAgent(tracer=tracer)

        # Generate unique ID for this orchestrator session
        self.agent_id = f"ORC-{uuid.uuid4().hex[:8].upper()}"

    def analyse(self, customer_profile: dict) -> dict:
        """
        Main entry point. Orchestrates the full agent pipeline.

        Args:
            customer_profile: dict with keys name, age, monthly_income,
                              existing_loan, credit_score, missed_payments,
                              employment_type, analysis_timestamp

        Returns:
            result: dict containing risk_level, risk_score, explanation,
                    factors, decision, interest_rate_band, governance, trace
        """
        session_id = str(uuid.uuid4())
        audit_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"

        # Begin orchestrator trace
        self.tracer.log(
            agent="OrchestratorAgent",
            message=f"Session {session_id} started for customer '{customer_profile['name']}'"
        )

        # ── Step 1: Risk Scoring ──────────────────────────────────────────────
        self.tracer.log(
            agent="OrchestratorAgent",
            message="Delegating to RiskScoringAgent..."
        )
        risk_result = self.risk_agent.compute_risk(customer_profile)

        # ── Step 2: Explanation ───────────────────────────────────────────────
        self.tracer.log(
            agent="OrchestratorAgent",
            message="Delegating to ExplanationAgent..."
        )
        explanation_result = self.explanation_agent.generate(
            customer_profile, risk_result
        )

        # ── Step 3: Decision & Rate Band ──────────────────────────────────────
        decision, rate_band = self._make_decision(risk_result["risk_score"])
        self.tracer.log(
            agent="OrchestratorAgent",
            message=f"Decision: {decision} | Rate Band: {rate_band}"
        )

        # ── Step 4: Governance / Policy Check ────────────────────────────────
        governance_result = self.policy_engine.check(customer_profile, risk_result)
        governance_result["audit_id"] = audit_id
        self.tracer.log(
            agent="OrchestratorAgent",
            message=f"Policy check: compliant={governance_result['policy_compliant']}"
        )

        # ── Step 5: Audit ─────────────────────────────────────────────────────
        self.audit_agent.record(
            audit_id=audit_id,
            session_id=session_id,
            customer_profile=customer_profile,
            risk_result=risk_result,
            decision=decision,
            governance_result=governance_result
        )
        self.tracer.log(
            agent="OrchestratorAgent",
            message=f"Audit record created: {audit_id}"
        )

        # ── Assemble Final Result ─────────────────────────────────────────────
        result = {
            "risk_level":        risk_result["risk_level"],
            "risk_score":        risk_result["risk_score"],
            "explanation":       explanation_result["summary"],
            "factors":           explanation_result["factors"],
            "decision":          decision,
            "interest_rate_band": rate_band,
            "governance":        governance_result,
            "trace":             self.tracer.get_trace()
        }

        self.tracer.log(
            agent="OrchestratorAgent",
            message=f"Session {session_id} complete. Risk={risk_result['risk_level']} Score={risk_result['risk_score']}"
        )

        return result

    def _make_decision(self, risk_score: int) -> tuple:
        """
        Maps a numeric risk score to a banking decision and interest rate band.

        Args:
            risk_score: Integer 0-100 (higher = riskier)

        Returns:
            (decision, interest_rate_band) tuple
        """
        if risk_score <= 35:
            return "Approve", "8.5% – 10.5% p.a."
        elif risk_score <= 65:
            return "Review", "11.0% – 14.5% p.a."
        else:
            return "Reject", "N/A – Not Eligible"
