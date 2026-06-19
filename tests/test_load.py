"""
Load Testing Suite (mocked Claude API)
=======================================
Run with: pytest tests/test_load.py -v -s
"""

import sys, os, time, random, statistics, json, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch

_AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")


def make_runner(md_path, json_response):
    with patch("agents.agent_runner.anthropic.Anthropic"):
        from agents.agent_runner import AgentRunner
        r = AgentRunner(md_path)
    r.run_json = MagicMock(return_value=json_response)
    return r


def run_single(profile, risk_score=20, risk_level="Low Risk"):
    from governance.policy_engine import PolicyEngine
    from observability.metrics import MetricsCollector
    from observability.tracer import Tracer

    risk_agent    = make_runner(os.path.join(_AGENTS_DIR, "risk_scoring_agent.md"),
                                {"risk_score": risk_score, "risk_level": risk_level, "sub_scores": {}})
    explain_agent = make_runner(os.path.join(_AGENTS_DIR, "explanation_agent.md"), {
        "summary": "Test.", "factors": [{"name": f"F{i}", "impact": "positive", "detail": "ok"} for i in range(5)]
    })

    scored    = risk_agent.run_json(json.dumps(profile))
    explained = explain_agent.run_json(json.dumps(profile))

    score = scored["risk_score"]
    if score <= 35:   decision, rate = "Approve", "8.5%"
    elif score <= 65: decision, rate = "Review",  "11%"
    else:             decision, rate = "Reject",  "N/A"

    gov = PolicyEngine().check(profile, scored)
    gov["audit_id"] = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    MetricsCollector().record_analysis(scored["risk_level"], 0.01)

    return {"risk_level": scored["risk_level"], "risk_score": score,
            "decision": decision, "interest_rate_band": rate, "governance": gov,
            "explanation": explained["summary"], "factors": explained["factors"]}


def generate_profile(seed=None):
    rng = random.Random(seed)
    return {
        "name": f"Customer{seed}", "age": rng.randint(22, 65),
        "monthly_income": rng.randint(10_000, 200_000),
        "existing_loan":  rng.randint(0, 1_000_000),
        "credit_score":   rng.randint(300, 900),
        "missed_payments": rng.randint(0, 8),
        "employment_type": rng.choice(["Salaried", "Self-Employed", "Business Owner"]),
        "analysis_timestamp": "2026-06-19T10:00:00"
    }


class TestLoadPerformance:

    def test_single_analysis_under_1_second(self):
        start = time.time()
        result = run_single(generate_profile(42))
        assert time.time() - start < 1.0
        assert result is not None

    def test_50_analyses_sequential(self):
        times = []
        for i in range(50):
            t = time.time()
            result = run_single(generate_profile(i))
            times.append(time.time() - t)
            assert result["risk_level"] in ["Low Risk", "Medium Risk", "High Risk"]

        avg = statistics.mean(times)
        p95 = sorted(times)[int(0.95 * len(times))]
        print(f"\n  50 runs — avg:{avg*1000:.1f}ms  p95:{p95*1000:.1f}ms")
        assert avg  < 0.5
        assert p95  < 1.0

    def test_all_risk_levels_reachable(self):
        levels = set()
        for score, level in [(10, "Low Risk"), (50, "Medium Risk"), (80, "High Risk")]:
            r = run_single(generate_profile(1), risk_score=score, risk_level=level)
            levels.add(r["risk_level"])
        assert levels == {"Low Risk", "Medium Risk", "High Risk"}

    def test_no_state_pollution(self):
        p = generate_profile(99)
        r1 = run_single(p)
        r2 = run_single(p)
        assert r1["risk_score"] == r2["risk_score"]
        assert r1["decision"]   == r2["decision"]

    def test_metrics_counter_increments(self):
        from observability.metrics import MetricsCollector
        m = MetricsCollector()
        for _ in range(5):
            m.record_analysis("Low Risk", 0.01)
        assert m.get_total_analyses() == 5
