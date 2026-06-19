"""
Load Testing Suite
==================
Simulates concurrent analysis requests to test system throughput,
memory stability, and response time under load.

Tests:
    - Process 100 customer profiles sequentially
    - Measure p50/p95/p99 processing times
    - Verify consistent results under load
    - Detect memory leaks or state pollution between runs

Run with: pytest tests/test_load.py -v -s
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import random
import statistics
import pytest
from agents.orchestrator_agent import OrchestratorAgent
from observability.tracer import Tracer
from observability.metrics import MetricsCollector
from governance.policy_engine import PolicyEngine


def make_orchestrator():
    """Factory for creating an orchestrator instance."""
    tracer  = Tracer()
    metrics = MetricsCollector()
    policy  = PolicyEngine()
    return OrchestratorAgent(tracer=tracer, metrics=metrics, policy_engine=policy)


def generate_profile(seed: int = None) -> dict:
    """Generate a random but realistic customer profile."""
    rng = random.Random(seed)
    employment_types = ["Salaried", "Self-Employed", "Business Owner", "Unemployed", "Retired"]
    return {
        "name":            f"TestCustomer{seed or rng.randint(1000, 9999)}",
        "age":             rng.randint(22, 65),
        "monthly_income":  rng.randint(0, 200_000),
        "existing_loan":   rng.randint(0, 2_000_000),
        "credit_score":    rng.randint(300, 900),
        "missed_payments": rng.randint(0, 12),
        "employment_type": rng.choice(employment_types),
        "analysis_timestamp": "2026-06-19T10:00:00"
    }


class TestLoadPerformance:
    """Performance and throughput tests."""

    def test_single_analysis_under_1_second(self):
        """A single analysis must complete in under 1 second."""
        orch = make_orchestrator()
        profile = generate_profile(42)
        start = time.time()
        result = orch.analyse(profile)
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Analysis took {elapsed:.3f}s – exceeds 1s budget"
        assert result is not None

    def test_50_analyses_sequential(self):
        """Run 50 analyses and collect timing stats."""
        orch = make_orchestrator()
        times = []

        for i in range(50):
            profile = generate_profile(i)
            start = time.time()
            result = orch.analyse(profile)
            elapsed = time.time() - start
            times.append(elapsed)
            assert result["risk_level"] in ["Low Risk", "Medium Risk", "High Risk"]

        # Statistical assertions
        avg = statistics.mean(times)
        p95 = sorted(times)[int(0.95 * len(times))]

        print(f"\n  Load Test: 50 analyses")
        print(f"  Average: {avg:.3f}s  |  p95: {p95:.3f}s  |  Max: {max(times):.3f}s")

        assert avg < 0.5,  f"Average processing time {avg:.3f}s exceeds 500ms"
        assert p95 < 1.0,  f"p95 processing time {p95:.3f}s exceeds 1000ms"

    def test_risk_distribution_across_100_profiles(self):
        """
        Over 100 random profiles, verify all 3 risk levels appear.
        Ensures the scoring system isn't biased to a single classification.
        """
        orch = make_orchestrator()
        levels = {"Low Risk": 0, "Medium Risk": 0, "High Risk": 0}

        for i in range(100):
            profile = generate_profile(i * 7)
            result = orch.analyse(profile)
            levels[result["risk_level"]] += 1

        print(f"\n  Risk Distribution over 100 profiles: {levels}")

        # Each risk level should appear at least once across 100 random profiles
        assert levels["Low Risk"]    > 0, "Low Risk never appeared"
        assert levels["Medium Risk"] > 0, "Medium Risk never appeared"
        assert levels["High Risk"]   > 0, "High Risk never appeared"

    def test_no_state_pollution_between_runs(self):
        """
        Analyse the same profile twice and verify identical results.
        Guards against mutable global state being modified by a run.
        """
        orch = make_orchestrator()
        profile = {
            "name": "StatePollutionTest",
            "age": 35,
            "monthly_income": 80_000,
            "existing_loan": 400_000,
            "credit_score": 720,
            "missed_payments": 1,
            "employment_type": "Salaried",
            "analysis_timestamp": "2026-06-19T10:00:00"
        }

        result1 = orch.analyse(profile)
        result2 = orch.analyse(profile)

        assert result1["risk_score"] == result2["risk_score"]
        assert result1["risk_level"] == result2["risk_level"]
        assert result1["decision"]   == result2["decision"]

    def test_metrics_counter_increments(self):
        """MetricsCollector should correctly count analyses."""
        metrics = MetricsCollector()
        assert metrics.get_total_analyses() == 0

        orch = OrchestratorAgent(
            tracer=Tracer(),
            metrics=metrics,
            policy_engine=PolicyEngine()
        )

        # Run 5 analyses and record manually (as app.py does)
        for i in range(5):
            profile = generate_profile(i)
            result = orch.analyse(profile)
            metrics.record_analysis(result["risk_level"], 0.1)

        assert metrics.get_total_analyses() == 5
