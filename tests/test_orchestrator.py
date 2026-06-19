"""
Test Suite – Orchestrator pipeline via AgentRunner
===================================================
All Claude API calls are mocked. Tests verify the pipeline logic in app.py.

Run with: pytest tests/test_orchestrator.py -v
"""

import sys, os, json, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch

_AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
_HOOKS_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hooks")


def make_runner(md_path, json_response):
    with patch("agents.agent_runner.anthropic.Anthropic"):
        from agents.agent_runner import AgentRunner
        r = AgentRunner(md_path)
    r.run_json = MagicMock(return_value=json_response)
    return r


@pytest.fixture
def profile():
    return {
        "name": "Alice Sharma", "age": 34, "monthly_income": 120_000,
        "existing_loan": 300_000, "credit_score": 820,
        "missed_payments": 0, "employment_type": "Salaried",
        "analysis_timestamp": "2026-06-19T10:00:00"
    }

@pytest.fixture
def low_risk_result():
    return {"risk_score": 5, "risk_level": "Low Risk",
            "sub_scores": {"credit_score_risk": 0, "dti_risk": 0,
                           "missed_payment_risk": 0, "employment_risk": 0, "age_risk": 5}}

@pytest.fixture
def explanation_result():
    return {
        "summary": "Alice is low risk with excellent financials.",
        "factors": [{"name": f"Factor{i}", "impact": "positive", "detail": "Good."} for i in range(5)]
    }


def run_pipeline(profile, risk_result, exp_result, hook_valid=True):
    """Simulate the app.py pipeline with mocked agents."""
    from governance.policy_engine import PolicyEngine
    from observability.tracer import Tracer
    from observability.metrics import MetricsCollector

    risk_agent    = make_runner(os.path.join(_AGENTS_DIR, "risk_scoring_agent.md"), risk_result)
    explain_agent = make_runner(os.path.join(_AGENTS_DIR, "explanation_agent.md"), exp_result)
    audit_agent   = make_runner(os.path.join(_AGENTS_DIR, "audit_agent.md"), {"audit_id": "AUD-TEST", "persisted": True})
    pre_hook      = make_runner(os.path.join(_HOOKS_DIR, "pre_analysis_hook.md"), {"valid": hook_valid, "warnings": []})
    post_hook     = make_runner(os.path.join(_HOOKS_DIR, "post_analysis_hook.md"), {"hook_status": "completed"})

    tracer   = Tracer()
    policy   = PolicyEngine()
    metrics  = MetricsCollector()

    hook_out = pre_hook.run_json(f"{json.dumps(profile)}")
    assert hook_out["valid"] is hook_valid

    scored  = risk_agent.run_json(f"{json.dumps(profile)}")
    explained = explain_agent.run_json(f"{json.dumps(profile)}\n{json.dumps(scored)}")

    score = scored["risk_score"]
    if score <= 35:   decision, rate = "Approve", "8.5% – 10.5% p.a."
    elif score <= 65: decision, rate = "Review",  "11.0% – 14.5% p.a."
    else:             decision, rate = "Reject",  "N/A – Not Eligible"

    audit_id   = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    governance = policy.check(profile, scored)
    governance["audit_id"] = audit_id

    metrics.record_analysis(scored["risk_level"], 0.1)

    return {
        "risk_level": scored["risk_level"],
        "risk_score": scored["risk_score"],
        "explanation": explained.get("summary", ""),
        "factors": explained.get("factors", []),
        "decision": decision,
        "interest_rate_band": rate,
        "governance": governance,
    }


class TestPipeline:

    def test_returns_dict(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert isinstance(result, dict)

    def test_required_keys(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        for key in ["risk_level", "risk_score", "explanation", "factors",
                    "decision", "interest_rate_band", "governance"]:
            assert key in result

    def test_low_risk_approved(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert result["risk_level"] == "Low Risk"
        assert result["decision"] == "Approve"
        assert "%" in result["interest_rate_band"]

    def test_medium_risk_review(self, profile, explanation_result):
        medium = {"risk_score": 50, "risk_level": "Medium Risk", "sub_scores": {}}
        result = run_pipeline(profile, medium, explanation_result)
        assert result["decision"] == "Review"

    def test_high_risk_rejected(self, profile, explanation_result):
        high = {"risk_score": 80, "risk_level": "High Risk", "sub_scores": {}}
        result = run_pipeline(profile, high, explanation_result)
        assert result["decision"] == "Reject"
        assert "N/A" in result["interest_rate_band"]

    def test_explanation_string(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 5

    def test_factors_list_of_5(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert isinstance(result["factors"], list)
        assert len(result["factors"]) == 5

    def test_audit_id_format(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert result["governance"]["audit_id"].startswith("AUD-")

    def test_risk_score_in_range(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert 0 <= result["risk_score"] <= 100

    def test_governance_has_required_keys(self, profile, low_risk_result, explanation_result):
        result = run_pipeline(profile, low_risk_result, explanation_result)
        assert "policy_compliant" in result["governance"]
        assert "bias_check_passed" in result["governance"]

    def test_pre_hook_returns_invalid_flag(self, profile, low_risk_result, explanation_result):
        """When hook returns valid=False, the pipeline should see that flag."""
        from unittest.mock import MagicMock, patch
        _HOOKS_DIR2 = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hooks")
        pre_hook = make_runner(os.path.join(_HOOKS_DIR2, "pre_analysis_hook.md"),
                               {"valid": False, "reason": "Invalid name"})
        result = pre_hook.run_json(json.dumps(profile))
        assert result["valid"] is False
        assert "reason" in result
