"""
Risk Scoring Skill
==================
A reusable, standalone skill that encapsulates the core credit risk
scoring logic. Skills in the Claude Agent SDK are self-contained
capabilities that any agent can invoke.

This skill can be called:
    1. Directly from the Orchestrator Agent
    2. From external MCP tool calls
    3. From the Autonomous Planning Agent
    4. In batch from the testing harness

The skill is intentionally stateless – it takes inputs and returns
outputs with no side effects, making it safe to call concurrently.
"""

from agents.risk_scoring_agent import RiskScoringAgent
from observability.tracer import Tracer


class RiskScoringSkill:
    """
    Skill wrapper around RiskScoringAgent for use in multi-agent systems.
    Skills expose a standardised `invoke(input_data)` interface.
    """

    # Skill metadata (used by Agent SDK for discovery / routing)
    SKILL_NAME        = "credit_risk_scoring"
    SKILL_VERSION     = "1.0.0"
    SKILL_DESCRIPTION = "Compute a credit risk score (0-100) and classify a customer as Low/Medium/High risk."

    # JSON Schema for input validation
    INPUT_SCHEMA = {
        "type": "object",
        "required": ["age", "monthly_income", "existing_loan",
                     "credit_score", "missed_payments", "employment_type"],
        "properties": {
            "age":              {"type": "integer", "minimum": 18, "maximum": 80},
            "monthly_income":   {"type": "number",  "minimum": 0},
            "existing_loan":    {"type": "number",  "minimum": 0},
            "credit_score":     {"type": "integer", "minimum": 300, "maximum": 900},
            "missed_payments":  {"type": "integer", "minimum": 0},
            "employment_type":  {"type": "string"}
        }
    }

    def __init__(self):
        # Skills create their own tracer so they work independently
        self._tracer = Tracer()
        self._agent = RiskScoringAgent(tracer=self._tracer)

    def invoke(self, input_data: dict) -> dict:
        """
        Standard skill invocation interface.
        Validates input, runs the scoring agent, returns structured output.

        Args:
            input_data: dict matching INPUT_SCHEMA

        Returns:
            dict with risk_score, risk_level, sub_scores, skill_metadata
        """
        # Validate required fields
        errors = self._validate(input_data)
        if errors:
            return {
                "success": False,
                "error":   f"Input validation failed: {', '.join(errors)}",
                "skill":   self.SKILL_NAME
            }

        # Run the scoring agent
        result = self._agent.compute_risk(input_data)

        return {
            "success":    True,
            "skill":      self.SKILL_NAME,
            "version":    self.SKILL_VERSION,
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "sub_scores": result["sub_scores"]
        }

    def invoke_batch(self, profiles: list) -> list:
        """
        Batch invocation – score multiple customers in one call.
        Useful for portfolio-level risk analysis.

        Args:
            profiles: list of customer profile dicts

        Returns:
            list of result dicts (same order as input)
        """
        return [self.invoke(p) for p in profiles]

    def _validate(self, data: dict) -> list:
        """Returns a list of validation error strings (empty if valid)."""
        errors = []
        required = self.INPUT_SCHEMA["required"]
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        return errors

    def get_schema(self) -> dict:
        """Return the input schema for this skill (used by MCP tool discovery)."""
        return {
            "name":        self.SKILL_NAME,
            "description": self.SKILL_DESCRIPTION,
            "version":     self.SKILL_VERSION,
            "input_schema": self.INPUT_SCHEMA
        }
