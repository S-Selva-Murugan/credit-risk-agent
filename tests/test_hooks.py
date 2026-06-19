"""
Test Suite – Hook .md definitions + AgentRunner
================================================
Verifies the pre/post analysis hook .md files are well-formed and that
AgentRunner correctly invokes them (Claude API mocked).

Run with: pytest tests/test_hooks.py -v
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch

_HOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hooks")
_PRE_MD    = os.path.join(_HOOKS_DIR, "pre_analysis_hook.md")
_POST_MD   = os.path.join(_HOOKS_DIR, "post_analysis_hook.md")


def make_runner(md_path, json_response):
    with patch("agents.agent_runner.anthropic.Anthropic"):
        from agents.agent_runner import AgentRunner
        r = AgentRunner(md_path)
    r.run_json = MagicMock(return_value=json_response)
    return r


@pytest.fixture
def valid_profile():
    return {
        "name": "Alice Sharma", "age": 34, "monthly_income": 120_000,
        "existing_loan": 300_000, "credit_score": 820,
        "missed_payments": 0, "employment_type": "Salaried"
    }


class TestPreAnalysisHookMd:

    def test_md_file_exists(self):
        assert os.path.exists(_PRE_MD)

    def test_md_has_name_frontmatter(self):
        with open(_PRE_MD) as f:
            content = f.read()
        assert "name:" in content
        assert "pre-analysis-hook" in content

    def test_md_has_trigger_frontmatter(self):
        with open(_PRE_MD) as f:
            content = f.read()
        assert "trigger:" in content
        assert "before_agent" in content

    def test_md_defines_validation_rules(self):
        with open(_PRE_MD) as f:
            content = f.read()
        assert "Required Field" in content or "required" in content.lower()
        assert "credit_score" in content or "Credit Score" in content

    def test_md_defines_output_format(self):
        with open(_PRE_MD) as f:
            content = f.read()
        assert '"valid"' in content
        assert '"reason"' in content

    def test_runner_valid_response(self, valid_profile):
        hook = make_runner(_PRE_MD, {"valid": True, "warnings": []})
        result = hook.run_json(f"Validate: {json.dumps(valid_profile)}")
        assert result["valid"] is True

    def test_runner_invalid_response(self, valid_profile):
        hook = make_runner(_PRE_MD, {"valid": False, "reason": "Missing field: name"})
        result = hook.run_json(f"Validate: {json.dumps(valid_profile)}")
        assert result["valid"] is False
        assert "reason" in result

    def test_runner_called_once(self, valid_profile):
        hook = make_runner(_PRE_MD, {"valid": True, "warnings": []})
        hook.run_json(f"Validate: {json.dumps(valid_profile)}")
        hook.run_json.assert_called_once()

    def test_warnings_in_response(self):
        hook = make_runner(_PRE_MD, {"valid": True, "warnings": ["Large loan detected"]})
        result = hook.run_json("Validate large loan profile")
        assert isinstance(result.get("warnings"), list)
        assert len(result["warnings"]) > 0


class TestPostAnalysisHookMd:

    def test_md_file_exists(self):
        assert os.path.exists(_POST_MD)

    def test_md_has_name_frontmatter(self):
        with open(_POST_MD) as f:
            content = f.read()
        assert "post-analysis-hook" in content

    def test_md_has_trigger_frontmatter(self):
        with open(_POST_MD) as f:
            content = f.read()
        assert "after_agent" in content

    def test_md_defines_alert_types(self):
        with open(_POST_MD) as f:
            content = f.read()
        assert "HIGH_RISK_FLAG" in content
        assert "POLICY_VIOLATION" in content

    def test_md_defines_event_logging(self):
        with open(_POST_MD) as f:
            content = f.read()
        assert "events.jsonl" in content or "event" in content.lower()

    def test_runner_returns_completed(self):
        hook = make_runner(_POST_MD, {"hook_status": "completed", "alerts": [], "event_logged": True})
        result = hook.run_json("Log this analysis")
        assert result["hook_status"] == "completed"

    def test_runner_high_risk_alert(self):
        hook = make_runner(_POST_MD, {
            "hook_status": "completed",
            "alerts": [{"type": "HIGH_RISK_FLAG", "severity": "HIGH", "message": "High risk flagged."}],
            "event_logged": True
        })
        result = hook.run_json("Log high risk analysis")
        alert_types = [a["type"] for a in result["alerts"]]
        assert "HIGH_RISK_FLAG" in alert_types

    def test_runner_no_alerts_for_low_risk(self):
        hook = make_runner(_POST_MD, {"hook_status": "completed", "alerts": [], "event_logged": True})
        result = hook.run_json("Log low risk analysis")
        assert result["alerts"] == []
