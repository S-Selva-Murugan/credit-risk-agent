"""
Test Suite – Orchestrator Agent (Integration)
==============================================
End-to-end integration tests for the full agent pipeline.
Verifies that the Orchestrator coordinates all subagents correctly.

Run with: pytest tests/test_orchestrator.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents.orchestrator_agent import OrchestratorAgent
from observability.tracer import Tracer
from observability.metrics import MetricsCollector
from governance.policy_engine import PolicyEngine


@pytest.fixture
def orchestrator():
    tracer = Tracer()
    metrics = MetricsCollector()
    policy = PolicyEngine()
    return OrchestratorAgent(tracer=tracer, metrics=metrics, policy_engine=policy)


@pytest.fixture
def low_risk_profile():
    return {
        "name": "Alice Sharma",
        "age": 34,
        "monthly_income": 120_000,
        "existing_loan": 300_000,
        "credit_score": 820,
        "missed_payments": 0,
        "employment_type": "Salaried",
        "analysis_timestamp": "2026-06-19T10:00:00"
    }


@pytest.fixture
def high_risk_profile():
    return {
        "name": "Kumar Singh",
        "age": 28,
        "monthly_income": 18_000,
        "existing_loan": 500_000,
        "credit_score": 480,
        "missed_payments": 7,
        "employment_type": "Unemployed",
        "analysis_timestamp": "2026-06-19T10:00:00"
    }


class TestOrchestratorPipeline:

    def test_analyse_returns_dict(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert isinstance(result, dict)

    def test_result_has_required_keys(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        required_keys = ["risk_level", "risk_score", "explanation", "factors",
                         "decision", "interest_rate_band", "governance", "trace"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_low_risk_approved(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert result["risk_level"] == "Low Risk"
        assert result["decision"] == "Approve"

    def test_high_risk_rejected(self, orchestrator, high_risk_profile):
        result = orchestrator.analyse(high_risk_profile)
        assert result["risk_level"] == "High Risk"
        assert result["decision"] == "Reject"

    def test_explanation_is_non_empty_string(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 50

    def test_factors_is_list(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert isinstance(result["factors"], list)
        assert len(result["factors"]) == 5  # One factor per rule

    def test_trace_is_non_empty(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert isinstance(result["trace"], list)
        assert len(result["trace"]) > 0

    def test_governance_block_present(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        gov = result["governance"]
        assert "policy_compliant" in gov
        assert "bias_check_passed" in gov
        assert "audit_id" in gov

    def test_audit_id_is_string(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        audit_id = result["governance"]["audit_id"]
        assert isinstance(audit_id, str)
        assert audit_id.startswith("AUD-")

    def test_risk_score_in_range(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert 0 <= result["risk_score"] <= 100

    def test_interest_rate_band_for_approve(self, orchestrator, low_risk_profile):
        result = orchestrator.analyse(low_risk_profile)
        assert "%" in result["interest_rate_band"]

    def test_interest_rate_na_for_reject(self, orchestrator, high_risk_profile):
        result = orchestrator.analyse(high_risk_profile)
        assert "N/A" in result["interest_rate_band"] or "Reject" in result["decision"]
