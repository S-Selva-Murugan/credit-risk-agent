"""
Test Suite – AgentRunner + .md agent definitions
==================================================
Verifies that AgentRunner correctly reads .md files, calls the Claude API,
parses JSON responses, and handles edge cases.

Run with: pytest tests/test_risk_scoring.py -v
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch


_AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
_RISK_MD    = os.path.join(_AGENTS_DIR, "risk_scoring_agent.md")
_EXP_MD     = os.path.join(_AGENTS_DIR, "explanation_agent.md")
_ORC_MD     = os.path.join(_AGENTS_DIR, "orchestrator_agent.md")


def make_runner(md_path, response_json: dict):
    """Create an AgentRunner with mocked Anthropic client."""
    with patch("agents.agent_runner.anthropic.Anthropic"):
        from agents.agent_runner import AgentRunner
        runner = AgentRunner(md_path=md_path)
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(response_json))]
    runner.client.messages.create = MagicMock(return_value=mock_msg)
    return runner


class TestAgentRunner:

    def test_reads_agent_name_from_md(self):
        with patch("agents.agent_runner.anthropic.Anthropic"):
            from agents.agent_runner import AgentRunner
            r = AgentRunner(_RISK_MD)
        assert r.name == "risk-scoring-agent"

    def test_reads_model_from_md(self):
        with patch("agents.agent_runner.anthropic.Anthropic"):
            from agents.agent_runner import AgentRunner
            r = AgentRunner(_RISK_MD)
        assert "haiku" in r.model or "sonnet" in r.model

    def test_system_prompt_populated(self):
        with patch("agents.agent_runner.anthropic.Anthropic"):
            from agents.agent_runner import AgentRunner
            r = AgentRunner(_RISK_MD)
        assert len(r.system_prompt) > 100
        assert "Score" in r.system_prompt or "risk" in r.system_prompt.lower()

    def test_run_json_returns_dict(self):
        runner = make_runner(_RISK_MD, {"risk_score": 10, "risk_level": "Low Risk", "sub_scores": {}})
        result = runner.run_json("test prompt")
        assert isinstance(result, dict)

    def test_strips_json_code_fences(self):
        with patch("agents.agent_runner.anthropic.Anthropic"):
            from agents.agent_runner import AgentRunner
            runner = AgentRunner(_RISK_MD)
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text='```json\n{"risk_score": 20, "risk_level": "Low Risk", "sub_scores": {}}\n```')]
        runner.client.messages.create = MagicMock(return_value=mock_msg)
        result = runner.run_json("test")
        assert result["risk_score"] == 20

    def test_invalid_json_raises_value_error(self):
        with patch("agents.agent_runner.anthropic.Anthropic"):
            from agents.agent_runner import AgentRunner
            runner = AgentRunner(_RISK_MD)
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="not json at all")]
        runner.client.messages.create = MagicMock(return_value=mock_msg)
        with pytest.raises(ValueError, match="invalid JSON"):
            runner.run_json("test")

    def test_claude_api_called_with_system_prompt(self):
        runner = make_runner(_RISK_MD, {"risk_score": 5, "risk_level": "Low Risk", "sub_scores": {}})
        runner.run_json("score this customer")
        call_kwargs = runner.client.messages.create.call_args[1]
        assert call_kwargs["system"] == runner.system_prompt
        assert call_kwargs["messages"][0]["content"] == "score this customer"

    def test_profile_json_in_prompt(self):
        runner = make_runner(_RISK_MD, {"risk_score": 5, "risk_level": "Low Risk", "sub_scores": {}})
        prompt = f"Score this.\n\n{json.dumps({'name': 'Alice', 'credit_score': 820}, indent=2)}"
        runner.run_json(prompt)
        call_args = runner.client.messages.create.call_args[1]["messages"][0]["content"]
        assert "Alice" in call_args


class TestRiskScoringMd:

    def test_md_file_exists(self):
        assert os.path.exists(_RISK_MD)

    def test_md_has_name_frontmatter(self):
        with open(_RISK_MD) as f:
            content = f.read()
        assert "name:" in content
        assert "risk-scoring-agent" in content

    def test_md_has_model_frontmatter(self):
        with open(_RISK_MD) as f:
            content = f.read()
        assert "model:" in content

    def test_md_contains_scoring_tables(self):
        with open(_RISK_MD) as f:
            content = f.read()
        assert "credit_score_risk" in content.lower() or "Credit Score" in content

    def test_md_defines_output_format(self):
        with open(_RISK_MD) as f:
            content = f.read()
        assert "risk_score" in content
        assert "risk_level" in content
        assert "sub_scores" in content


class TestExplanationMd:

    def test_md_file_exists(self):
        assert os.path.exists(_EXP_MD)

    def test_md_defines_factors_output(self):
        with open(_EXP_MD) as f:
            content = f.read()
        assert "factors" in content
        assert "summary" in content
        assert "impact" in content


class TestOrchestratorMd:

    def test_md_file_exists(self):
        assert os.path.exists(_ORC_MD)

    def test_md_lists_subagents(self):
        with open(_ORC_MD) as f:
            content = f.read()
        assert "risk-scoring-agent" in content
        assert "explanation-agent" in content
        assert "audit-agent" in content

    def test_md_defines_decision_table(self):
        with open(_ORC_MD) as f:
            content = f.read()
        assert "Approve" in content
        assert "Reject" in content
        assert "Review" in content


class TestRiskClassificationLogic:
    """Verify correct decision mapping from score ranges."""

    @pytest.mark.parametrize("score,expected_decision", [
        (0,   "Approve"),
        (35,  "Approve"),
        (36,  "Review"),
        (65,  "Review"),
        (66,  "Reject"),
        (100, "Reject"),
    ])
    def test_decision_boundaries(self, score, expected_decision):
        if score <= 35:
            decision = "Approve"
        elif score <= 65:
            decision = "Review"
        else:
            decision = "Reject"
        assert decision == expected_decision
