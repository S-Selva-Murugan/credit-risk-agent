"""
Test Suite – Policy Engine (Governance)
========================================
Tests for the governance policy engine.
Verifies that each policy (P1-P6) fires correctly.

Run with: pytest tests/test_governance.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from governance.policy_engine import PolicyEngine


@pytest.fixture
def engine():
    return PolicyEngine()


@pytest.fixture
def clean_profile():
    """A profile that should pass all policies."""
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
        "sub_scores": {
            "credit_score_risk": 0,
            "dti_risk": 0,
            "missed_payment_risk": 0,
            "employment_risk": 0,
            "age_risk": 0
        }
    }


class TestPolicyEngine:

    def test_clean_profile_is_compliant(self, engine, clean_profile, low_risk_result):
        result = engine.check(clean_profile, low_risk_result)
        assert result["policy_compliant"] is True
        assert result["bias_check_passed"] is True
        assert len(result["flags"]) == 0

    def test_p1_minimum_income_fires(self, engine, clean_profile, low_risk_result):
        """P1: Customer with very low income should fail."""
        clean_profile["monthly_income"] = 5_000  # Below ₹10k threshold
        result = engine.check(clean_profile, low_risk_result)
        policy_codes = [f["policy"] for f in result["flags"]]
        assert "P1-MIN-INCOME" in policy_codes

    def test_p2_max_dti_fires(self, engine, clean_profile, low_risk_result):
        """P2: DTI > 80% should trigger a flag."""
        clean_profile["monthly_income"] = 20_000
        clean_profile["existing_loan"] = 2_000_000  # DTI = 2M / 240k = 833%
        result = engine.check(clean_profile, low_risk_result)
        policy_codes = [f["policy"] for f in result["flags"]]
        assert "P2-MAX-DTI" in policy_codes

    def test_p3_delinquency_fires(self, engine, clean_profile, low_risk_result):
        """P3: Many missed payments with Low Risk verdict should flag."""
        clean_profile["missed_payments"] = 8
        result = engine.check(clean_profile, low_risk_result)
        policy_codes = [f["policy"] for f in result["flags"]]
        assert "P3-DELINQUENCY" in policy_codes

    def test_p5_young_borrower_fires(self, engine, clean_profile, low_risk_result):
        """P5: Customer under 21 should require guarantor flag."""
        clean_profile["age"] = 19
        result = engine.check(clean_profile, low_risk_result)
        policy_codes = [f["policy"] for f in result["flags"]]
        assert "P5-YOUNG-BORROWER" in policy_codes

    def test_p6_senior_borrower_fires(self, engine, clean_profile, low_risk_result):
        """P6: Customer over 65 needs restricted tenure."""
        clean_profile["age"] = 70
        result = engine.check(clean_profile, low_risk_result)
        policy_codes = [f["policy"] for f in result["flags"]]
        assert "P6-SENIOR-BORROWER" in policy_codes

    def test_p1_causes_non_compliance(self, engine, clean_profile, low_risk_result):
        """P1 is a hard failure – policy_compliant should be False."""
        clean_profile["monthly_income"] = 3_000
        result = engine.check(clean_profile, low_risk_result)
        assert result["policy_compliant"] is False

    def test_p5_does_not_cause_non_compliance(self, engine, clean_profile, low_risk_result):
        """P5 is advisory – policy_compliant should still be True."""
        clean_profile["age"] = 20
        result = engine.check(clean_profile, low_risk_result)
        assert result["policy_compliant"] is True

    def test_all_policies_checked(self, engine, clean_profile, low_risk_result):
        result = engine.check(clean_profile, low_risk_result)
        assert "policies_checked" in result
        assert len(result["policies_checked"]) >= 6
