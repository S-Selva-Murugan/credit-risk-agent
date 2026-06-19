"""
Test Suite – Risk Scoring Agent
================================
Unit tests for the RiskScoringAgent.
Tests each scoring rule in isolation and the full classification pipeline.

Run with: pytest tests/test_risk_scoring.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents.risk_scoring_agent import RiskScoringAgent
from observability.tracer import Tracer


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def agent():
    """Create a fresh RiskScoringAgent for each test."""
    tracer = Tracer()
    return RiskScoringAgent(tracer=tracer)


@pytest.fixture
def low_risk_profile():
    """A textbook low-risk customer profile."""
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
def medium_risk_profile():
    """A medium-risk customer with mixed signals (score ~52)."""
    return {
        "name": "Sunita Joshi",
        "age": 38,
        "monthly_income": 70_000,
        "existing_loan": 300_000,         # DTI = 300k / 840k = 35.7% → 8pts
        "credit_score": 640,              # Fair → 25 pts
        "missed_payments": 1,             # 1 missed → 7pts
        "employment_type": "Business Owner"  # 5pts; Age risk 0pts → total 45
    }


@pytest.fixture
def high_risk_profile():
    """A high-risk customer with multiple red flags."""
    return {
        "name": "Kumar Singh",
        "age": 28,
        "monthly_income": 18_000,
        "existing_loan": 500_000,
        "credit_score": 480,
        "missed_payments": 7,
        "employment_type": "Unemployed"
    }


# ── Unit Tests: Individual Scoring Rules ─────────────────────────────────────

class TestCreditScoreRule:
    """Tests for the credit score sub-scoring rule."""

    def test_excellent_credit_zero_risk(self, agent):
        assert agent._score_credit(820) == 0

    def test_very_good_credit_low_risk(self, agent):
        assert agent._score_credit(760) == 7

    def test_good_credit_moderate_risk(self, agent):
        assert agent._score_credit(700) == 14

    def test_fair_credit_elevated_risk(self, agent):
        assert agent._score_credit(620) == 25

    def test_poor_credit_max_risk(self, agent):
        assert agent._score_credit(450) == 35

    def test_boundary_800(self, agent):
        """Test exact boundary between Very Good and Excellent."""
        assert agent._score_credit(800) == 0

    def test_boundary_580(self, agent):
        """Test exact boundary between Poor and Fair."""
        assert agent._score_credit(580) == 25


class TestDTIRule:
    """Tests for the Debt-to-Income ratio sub-scoring rule."""

    def test_zero_debt_zero_risk(self, agent):
        assert agent._score_dti(100_000, 0) == 0

    def test_low_dti(self, agent):
        # Annual income = 1.2M, loan = 240k → DTI = 20% (exactly at boundary)
        assert agent._score_dti(100_000, 240_000) == 0

    def test_moderate_dti(self, agent):
        # Annual income = 600k, loan = 240k → DTI = 40%
        assert agent._score_dti(50_000, 240_000) == 8

    def test_high_dti(self, agent):
        # Annual income = 240k, loan = 240k → DTI = 100%
        assert agent._score_dti(20_000, 240_000) == 25

    def test_zero_income_max_risk(self, agent):
        assert agent._score_dti(0, 100_000) == 25


class TestMissedPaymentsRule:
    """Tests for the missed payments sub-scoring rule."""

    def test_no_missed_zero_risk(self, agent):
        assert agent._score_missed_payments(0) == 0

    def test_one_missed_minor_risk(self, agent):
        assert agent._score_missed_payments(1) == 7

    def test_two_missed_moderate_risk(self, agent):
        assert agent._score_missed_payments(2) == 13

    def test_five_missed_serious_risk(self, agent):
        assert agent._score_missed_payments(5) == 17

    def test_many_missed_max_risk(self, agent):
        assert agent._score_missed_payments(10) == 20


class TestEmploymentRule:
    """Tests for the employment type sub-scoring rule."""

    def test_salaried_zero_risk(self, agent):
        assert agent._score_employment("Salaried") == 0

    def test_business_owner_low_risk(self, agent):
        assert agent._score_employment("Business Owner") == 5

    def test_self_employed_moderate_risk(self, agent):
        assert agent._score_employment("Self-Employed") == 8

    def test_unemployed_max_risk(self, agent):
        assert agent._score_employment("Unemployed") == 15

    def test_unknown_employment_default(self, agent):
        result = agent._score_employment("Freelancer")
        assert 0 <= result <= 15  # Should return a sensible default


class TestAgeRule:
    """Tests for the age sub-scoring rule."""

    def test_prime_age_zero_risk(self, agent):
        assert agent._score_age(35) == 0

    def test_young_adult_low_risk(self, agent):
        assert agent._score_age(22) == 4

    def test_senior_some_risk(self, agent):
        assert agent._score_age(70) == 5


# ── Integration Tests: Full Risk Classification ───────────────────────────────

class TestFullRiskClassification:
    """Integration tests for the complete risk scoring pipeline."""

    def test_low_risk_classification(self, agent, low_risk_profile):
        result = agent.compute_risk(low_risk_profile)
        assert result["risk_level"] == "Low Risk"
        assert result["risk_score"] <= 35

    def test_medium_risk_classification(self, agent, medium_risk_profile):
        result = agent.compute_risk(medium_risk_profile)
        assert result["risk_level"] == "Medium Risk"
        assert 36 <= result["risk_score"] <= 65

    def test_high_risk_classification(self, agent, high_risk_profile):
        result = agent.compute_risk(high_risk_profile)
        assert result["risk_level"] == "High Risk"
        assert result["risk_score"] >= 66

    def test_result_has_sub_scores(self, agent, low_risk_profile):
        result = agent.compute_risk(low_risk_profile)
        assert "sub_scores" in result
        assert "credit_score_risk" in result["sub_scores"]
        assert "dti_risk" in result["sub_scores"]
        assert "missed_payment_risk" in result["sub_scores"]

    def test_score_is_integer(self, agent, low_risk_profile):
        result = agent.compute_risk(low_risk_profile)
        assert isinstance(result["risk_score"], int)

    def test_score_bounded_0_to_100(self, agent, high_risk_profile):
        result = agent.compute_risk(high_risk_profile)
        assert 0 <= result["risk_score"] <= 100

    def test_risk_level_is_valid_string(self, agent, medium_risk_profile):
        result = agent.compute_risk(medium_risk_profile)
        assert result["risk_level"] in ["Low Risk", "Medium Risk", "High Risk"]

    def test_deterministic_output(self, agent, low_risk_profile):
        """Same input must always produce same output (no randomness)."""
        result1 = agent.compute_risk(low_risk_profile)
        result2 = agent.compute_risk(low_risk_profile)
        assert result1["risk_score"] == result2["risk_score"]
        assert result1["risk_level"] == result2["risk_level"]
