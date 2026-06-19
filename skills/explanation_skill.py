"""
Explanation Skill
=================
Reusable skill for generating human-readable credit risk explanations.
Wraps ExplanationAgent with the standard Skill interface.
"""

from agents.explanation_agent import ExplanationAgent
from observability.tracer import Tracer


class ExplanationSkill:
    """
    Skill that converts raw risk scores into business-language explanations.
    """

    SKILL_NAME        = "credit_risk_explanation"
    SKILL_VERSION     = "1.0.0"
    SKILL_DESCRIPTION = "Generate a human-readable explanation for a credit risk assessment result."

    def __init__(self):
        self._tracer = Tracer()
        self._agent = ExplanationAgent(tracer=self._tracer)

    def invoke(self, customer_profile: dict, risk_result: dict) -> dict:
        """
        Generate an explanation for a given risk result.

        Args:
            customer_profile: customer data dict
            risk_result:      output from RiskScoringSkill or RiskScoringAgent

        Returns:
            dict with summary and factors list
        """
        result = self._agent.generate(customer_profile, risk_result)
        return {
            "success": True,
            "skill":   self.SKILL_NAME,
            "summary": result["summary"],
            "factors": result["factors"]
        }
