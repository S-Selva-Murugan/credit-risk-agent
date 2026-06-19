"""
Explanation Agent
=================
Specialist subagent responsible for generating human-readable explanations
of why a customer received a particular risk classification.

This agent transforms raw numeric sub-scores into actionable business language
that banking professionals and customers can understand.

It also produces a structured list of factors (positive/neutral/negative)
that are rendered in the UI as a breakdown of risk drivers.
"""


class ExplanationAgent:
    """
    Generates natural-language explanations for credit risk decisions.
    Each method handles one pillar of the explanation.
    """

    def __init__(self, tracer):
        self.tracer = tracer

    def generate(self, profile: dict, risk_result: dict) -> dict:
        """
        Generate a summary explanation and a structured list of risk factors.

        Args:
            profile:     customer profile dict
            risk_result: output from RiskScoringAgent

        Returns:
            dict with summary (str) and factors (list of dicts)
        """
        self.tracer.log(
            agent="ExplanationAgent",
            message=f"Generating explanation for {risk_result['risk_level']} (score={risk_result['risk_score']})"
        )

        sub_scores = risk_result.get("sub_scores", {})

        # Build individual factor explanations
        factors = [
            self._explain_credit(profile["credit_score"], sub_scores.get("credit_score_risk", 0)),
            self._explain_dti(profile["monthly_income"], profile["existing_loan"], sub_scores.get("dti_risk", 0)),
            self._explain_payments(profile["missed_payments"], sub_scores.get("missed_payment_risk", 0)),
            self._explain_employment(profile["employment_type"], sub_scores.get("employment_risk", 0)),
            self._explain_age(profile["age"], sub_scores.get("age_risk", 0))
        ]

        # Build the summary paragraph
        summary = self._build_summary(profile, risk_result, factors)

        self.tracer.log(
            agent="ExplanationAgent",
            message=f"Explanation generated with {len(factors)} factors"
        )

        return {
            "summary": summary,
            "factors": factors
        }

    # ── Factor Explanations ───────────────────────────────────────────────────

    def _explain_credit(self, score: int, risk_points: int) -> dict:
        """Explains the credit score factor."""
        if risk_points == 0:
            return {
                "name": "Credit Score",
                "impact": "positive",
                "detail": f"Excellent CIBIL score of {score} (800–900 range). "
                          f"Demonstrates strong repayment history and credit discipline."
            }
        elif risk_points <= 14:
            return {
                "name": "Credit Score",
                "impact": "neutral",
                "detail": f"Good CIBIL score of {score}. Acceptable credit history "
                          f"with room for improvement."
            }
        elif risk_points <= 25:
            return {
                "name": "Credit Score",
                "impact": "negative",
                "detail": f"Fair CIBIL score of {score} (580–669 range). "
                          f"Indicates some credit issues in the past. Moderate risk."
            }
        else:
            return {
                "name": "Credit Score",
                "impact": "negative",
                "detail": f"Poor CIBIL score of {score} (below 580). "
                          f"Significant credit history concerns. High default risk."
            }

    def _explain_dti(self, income: int, loan: int, risk_points: int) -> dict:
        """Explains the Debt-to-Income ratio factor."""
        annual_income = income * 12 if income > 0 else 1
        dti = round((loan / annual_income) * 100, 1)

        if risk_points == 0:
            return {
                "name": "Debt-to-Income Ratio",
                "impact": "positive",
                "detail": f"DTI of {dti}% is excellent (below 20%). "
                          f"Customer has minimal debt relative to income."
            }
        elif risk_points <= 8:
            return {
                "name": "Debt-to-Income Ratio",
                "impact": "neutral",
                "detail": f"DTI of {dti}% is manageable (20–40%). "
                          f"Debt level is acceptable but should not increase further."
            }
        elif risk_points <= 16:
            return {
                "name": "Debt-to-Income Ratio",
                "impact": "negative",
                "detail": f"DTI of {dti}% is elevated (40–60%). "
                          f"Customer is carrying significant debt. Repayment may be strained."
            }
        else:
            return {
                "name": "Debt-to-Income Ratio",
                "impact": "negative",
                "detail": f"DTI of {dti}% is very high (above 60%). "
                          f"Existing debt burden is severe. New loans pose high default risk."
            }

    def _explain_payments(self, missed: int, risk_points: int) -> dict:
        """Explains the missed payments factor."""
        if missed == 0:
            return {
                "name": "Payment History",
                "impact": "positive",
                "detail": "Perfect payment history – no missed EMIs in the last 12 months. "
                          "Strong indicator of financial discipline."
            }
        elif missed == 1:
            return {
                "name": "Payment History",
                "impact": "neutral",
                "detail": f"{missed} missed payment in the last 12 months. "
                          f"Minor concern – could be a one-time event."
            }
        elif missed <= 3:
            return {
                "name": "Payment History",
                "impact": "negative",
                "detail": f"{missed} missed payments in the last 12 months. "
                          f"Pattern of payment difficulties beginning to form."
            }
        else:
            return {
                "name": "Payment History",
                "impact": "negative",
                "detail": f"{missed} missed payments in the last 12 months is a serious red flag. "
                          f"Chronic delinquency significantly increases default risk."
            }

    def _explain_employment(self, emp_type: str, risk_points: int) -> dict:
        """Explains the employment type factor."""
        explanations = {
            "Salaried": {
                "impact": "positive",
                "detail": "Salaried employment provides a stable, predictable monthly income. "
                          "Lowest employment risk category."
            },
            "Business Owner": {
                "impact": "neutral",
                "detail": "Business owner with relatively stable income, but subject to "
                          "business cycle variations. Moderate employment stability."
            },
            "Self-Employed": {
                "impact": "neutral",
                "detail": "Self-employed income can be irregular or seasonal. "
                          "Repayment capacity may vary month-to-month."
            },
            "Retired": {
                "impact": "neutral",
                "detail": "Retired with fixed pension or savings income. "
                          "Income is predictable but unlikely to grow."
            },
            "Unemployed": {
                "impact": "negative",
                "detail": "Currently unemployed. No regular income source identified. "
                          "Highest employment risk – repayment capacity is very uncertain."
            }
        }
        info = explanations.get(emp_type, {"impact": "neutral", "detail": f"Employment type: {emp_type}."})
        info["name"] = "Employment Status"
        return info

    def _explain_age(self, age: int, risk_points: int) -> dict:
        """Explains the age factor."""
        if risk_points == 0:
            return {
                "name": "Age Factor",
                "impact": "positive",
                "detail": f"Age {age} is in the prime earning bracket (28–50 years). "
                          f"Optimal career stability and repayment capacity."
            }
        elif risk_points <= 2:
            return {
                "name": "Age Factor",
                "impact": "neutral",
                "detail": f"Age {age} is slightly outside the prime earning bracket. "
                          f"Good earning potential but minor age-related consideration."
            }
        else:
            return {
                "name": "Age Factor",
                "impact": "negative",
                "detail": f"Age {age} presents a slight concern – either early career "
                          f"(limited credit history) or approaching retirement (reduced future income)."
            }

    # ── Summary Builder ───────────────────────────────────────────────────────

    def _build_summary(self, profile: dict, risk_result: dict, factors: list) -> str:
        """
        Builds the headline explanation paragraph shown to the user.
        Combines all factors into a coherent, banking-grade narrative.
        """
        name = profile["name"]
        risk_level = risk_result["risk_level"]
        score = risk_result["risk_score"]

        # Separate factors by impact type
        positives = [f["name"] for f in factors if f["impact"] == "positive"]
        negatives = [f["name"] for f in factors if f["impact"] == "negative"]

        # Build narrative based on risk level
        if risk_level == "Low Risk":
            summary = (
                f"{name} has been assessed as LOW RISK with a score of {score}/100. "
                f"This customer demonstrates strong financial health. "
            )
            if positives:
                summary += f"Key strengths include: {', '.join(positives)}. "
            summary += (
                "The customer exhibits a solid credit history, manageable debt levels, "
                "and stable employment, making them a reliable candidate for credit facilities. "
                "Approval is recommended at standard interest rates."
            )

        elif risk_level == "Medium Risk":
            summary = (
                f"{name} has been assessed as MEDIUM RISK with a score of {score}/100. "
                f"This customer shows a mixed financial profile that warrants careful review. "
            )
            if positives:
                summary += f"Positive indicators: {', '.join(positives)}. "
            if negatives:
                summary += f"Areas of concern: {', '.join(negatives)}. "
            summary += (
                "The bank should conduct additional due diligence, verify income documents, "
                "and consider requiring collateral or a guarantor before approval. "
                "Approval may be granted with elevated interest rates and lower loan limits."
            )

        else:  # High Risk
            summary = (
                f"{name} has been assessed as HIGH RISK with a score of {score}/100. "
                f"This customer presents significant credit risk indicators. "
            )
            if negatives:
                summary += f"Critical risk factors: {', '.join(negatives)}. "
            summary += (
                "The combination of risk factors suggests a high probability of default. "
                "It is recommended to reject the loan application or seek substantial "
                "collateral and guarantees before reconsideration. "
                "Financial counselling may also be advisable for the customer."
            )

        return summary
