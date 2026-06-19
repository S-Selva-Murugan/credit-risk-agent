"""
Test Suite – Hooks (Pre & Post Analysis)
==========================================
Tests for pre-analysis validation/sanitisation and post-analysis event logging.

Run with: pytest tests/test_hooks.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from hooks.pre_analysis_hook import PreAnalysisHook
from hooks.post_analysis_hook import PostAnalysisHook


@pytest.fixture
def pre_hook():
    return PreAnalysisHook()


@pytest.fixture
def post_hook():
    return PostAnalysisHook()


@pytest.fixture
def valid_profile():
    return {
        "name": "Alice Sharma",
        "age": 34,
        "monthly_income": 120_000,
        "existing_loan": 300_000,
        "credit_score": 820,
        "missed_payments": 0,
        "employment_type": "Salaried"
    }


@pytest.fixture
def low_risk_result():
    return {
        "risk_level": "Low Risk",
        "risk_score": 15,
        "decision": "Approve",
        "explanation": "Customer is low risk.",
        "governance": {"audit_id": "AUD-TEST001", "policy_compliant": True}
    }


@pytest.fixture
def high_risk_result():
    return {
        "risk_level": "High Risk",
        "risk_score": 82,
        "decision": "Reject",
        "explanation": "Customer is high risk.",
        "governance": {"audit_id": "AUD-TEST002", "policy_compliant": False}
    }


# ── Pre-Analysis Hook Tests ───────────────────────────────────────────────────

class TestPreAnalysisHook:

    def test_valid_profile_passes(self, pre_hook, valid_profile):
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is True

    def test_missing_name_fails(self, pre_hook, valid_profile):
        del valid_profile["name"]
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False
        assert "name" in result["reason"]

    def test_empty_name_fails(self, pre_hook, valid_profile):
        valid_profile["name"] = "  "
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_invalid_age_low_fails(self, pre_hook, valid_profile):
        valid_profile["age"] = 15
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_invalid_age_high_fails(self, pre_hook, valid_profile):
        valid_profile["age"] = 90
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_negative_income_fails(self, pre_hook, valid_profile):
        valid_profile["monthly_income"] = -1000
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_negative_loan_fails(self, pre_hook, valid_profile):
        valid_profile["existing_loan"] = -500
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_invalid_credit_score_fails(self, pre_hook, valid_profile):
        valid_profile["credit_score"] = 150
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_negative_missed_payments_fails(self, pre_hook, valid_profile):
        valid_profile["missed_payments"] = -1
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_name_with_special_chars_fails(self, pre_hook, valid_profile):
        valid_profile["name"] = "Alice123<script>"
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is False

    def test_sanitisation_strips_whitespace(self, pre_hook, valid_profile):
        valid_profile["name"] = "  Alice Sharma  "
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is True
        assert valid_profile["name"] == "Alice Sharma"

    def test_large_loan_generates_warning(self, pre_hook, valid_profile):
        valid_profile["existing_loan"] = 60_000_000  # ₹6 crore
        result = pre_hook.execute(valid_profile)
        assert result["valid"] is True
        assert len(result.get("warnings", [])) > 0


# ── Post-Analysis Hook Tests ──────────────────────────────────────────────────

class TestPostAnalysisHook:

    def test_post_hook_returns_completed(self, post_hook, valid_profile, low_risk_result):
        result = post_hook.execute(valid_profile, low_risk_result)
        assert result["hook_status"] == "completed"

    def test_post_hook_event_logged(self, post_hook, valid_profile, low_risk_result):
        result = post_hook.execute(valid_profile, low_risk_result)
        assert result["event_logged"] is True

    def test_high_risk_generates_alert(self, post_hook, valid_profile, high_risk_result):
        result = post_hook.execute(valid_profile, high_risk_result)
        assert len(result["alerts"]) > 0
        alert_types = [a["type"] for a in result["alerts"]]
        assert "HIGH_RISK_FLAG" in alert_types

    def test_low_risk_no_high_risk_alert(self, post_hook, valid_profile, low_risk_result):
        result = post_hook.execute(valid_profile, low_risk_result)
        alert_types = [a["type"] for a in result.get("alerts", [])]
        assert "HIGH_RISK_FLAG" not in alert_types

    def test_execution_count_increments(self, post_hook, valid_profile, low_risk_result):
        initial = post_hook.get_execution_count()
        post_hook.execute(valid_profile, low_risk_result)
        assert post_hook.get_execution_count() == initial + 1

    def test_alert_count_increments_on_high_risk(self, post_hook, valid_profile, high_risk_result):
        initial = post_hook.get_alert_count()
        post_hook.execute(valid_profile, high_risk_result)
        assert post_hook.get_alert_count() == initial + 1
