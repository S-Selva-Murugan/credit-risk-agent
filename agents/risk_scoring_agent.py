"""
Risk Scoring Agent
==================
Specialist subagent responsible for computing a credit risk score (0-100)
and classifying the customer as Low / Medium / High risk.

Scoring Rules:
    - Credit Score   → contributes up to 35 points of risk
    - Debt-to-Income → contributes up to 25 points of risk
    - Missed Payments→ contributes up to 20 points of risk
    - Employment Type→ contributes up to 15 points of risk
    - Age Factor     → contributes up to  5 points of risk

Total possible score = 100 (Higher = More Risk)
Low Risk: 0-35 | Medium Risk: 36-65 | High Risk: 66-100
"""


class RiskScoringAgent:
    """
    Rule-based credit risk scoring subagent.
    Each rule is a separate method so rules can be updated independently.
    """

    # Weight constants (must sum to 100)
    WEIGHT_CREDIT_SCORE    = 35
    WEIGHT_DTI             = 25
    WEIGHT_MISSED_PAYMENTS = 20
    WEIGHT_EMPLOYMENT      = 15
    WEIGHT_AGE             =  5

    def __init__(self, tracer):
        self.tracer = tracer

    def compute_risk(self, profile: dict) -> dict:
        """
        Compute the overall risk score by summing all sub-scores.

        Args:
            profile: customer profile dict

        Returns:
            dict with risk_score (int), risk_level (str), sub_scores (dict)
        """
        self.tracer.log(
            agent="RiskScoringAgent",
            message=f"Computing risk for credit_score={profile['credit_score']}, "
                    f"income={profile['monthly_income']}, loan={profile['existing_loan']}"
        )

        # Compute each sub-score (returns a value between 0 and the weight)
        sub_scores = {
            "credit_score_risk":    self._score_credit(profile["credit_score"]),
            "dti_risk":             self._score_dti(profile["monthly_income"], profile["existing_loan"]),
            "missed_payment_risk":  self._score_missed_payments(profile["missed_payments"]),
            "employment_risk":      self._score_employment(profile["employment_type"]),
            "age_risk":             self._score_age(profile["age"])
        }

        # Total risk score is the sum of all sub-scores
        total_score = sum(sub_scores.values())

        # Classify based on thresholds
        risk_level = self._classify(total_score)

        self.tracer.log(
            agent="RiskScoringAgent",
            message=f"Sub-scores: {sub_scores} | Total: {total_score} | Level: {risk_level}"
        )

        return {
            "risk_score":  total_score,
            "risk_level":  risk_level,
            "sub_scores":  sub_scores
        }

    # ── Sub-scoring Rules ─────────────────────────────────────────────────────

    def _score_credit(self, credit_score: int) -> int:
        """
        Rule: Higher CIBIL score = lower credit risk.
        CIBIL ranges: 800-900 Excellent, 740-799 Very Good, 670-739 Good,
                      580-669 Fair, 300-579 Poor
        """
        if credit_score >= 800:
            return 0    # Excellent – zero risk contribution
        elif credit_score >= 740:
            return 7    # Very Good
        elif credit_score >= 670:
            return 14   # Good
        elif credit_score >= 580:
            return 25   # Fair – moderate risk
        else:
            return 35   # Poor – maximum risk contribution

    def _score_dti(self, monthly_income: int, existing_loan: int) -> int:
        """
        Rule: Debt-to-Income Ratio = (annual loan / annual income) * 100
        High DTI means the customer carries too much debt relative to their income.
        """
        if monthly_income <= 0:
            return self.WEIGHT_DTI  # No income = maximum risk

        annual_income = monthly_income * 12
        dti = (existing_loan / annual_income) * 100  # expressed as a percentage

        if dti <= 20:
            return 0    # Minimal debt burden
        elif dti <= 40:
            return 8    # Manageable
        elif dti <= 60:
            return 16   # Elevated
        elif dti <= 80:
            return 22   # High burden
        else:
            return 25   # Dangerously high – maximum contribution

    def _score_missed_payments(self, missed_payments: int) -> int:
        """
        Rule: Missed EMI payments in the last 12 months are a strong delinquency signal.
        Even one missed payment significantly raises risk.
        """
        if missed_payments == 0:
            return 0    # Perfect payment history
        elif missed_payments == 1:
            return 7    # One slip – minor flag
        elif missed_payments <= 3:
            return 13   # Pattern forming – moderate
        elif missed_payments <= 6:
            return 17   # Serious concern
        else:
            return 20   # Maximum – chronic delinquency

    def _score_employment(self, employment_type: str) -> int:
        """
        Rule: Employment stability directly affects repayment capacity.
        Salaried employees have predictable income; unemployed customers cannot repay.
        """
        employment_risk = {
            "Salaried":       0,   # Most stable income source
            "Business Owner": 5,   # Stable but income can vary
            "Self-Employed":  8,   # Variable income – somewhat risky
            "Retired":        10,  # Fixed pension income – limited growth
            "Unemployed":     15   # No income – highest employment risk
        }
        return employment_risk.get(employment_type, 8)

    def _score_age(self, age: int) -> int:
        """
        Rule: Age affects repayment capacity and career longevity.
        Very young (limited history) and very old (near retirement) customers carry more risk.
        """
        if 28 <= age <= 50:
            return 0   # Prime earning years – low age risk
        elif 25 <= age < 28 or 50 < age <= 58:
            return 2   # Good but slightly outside prime range
        elif 18 <= age < 25 or 58 < age <= 65:
            return 4   # Young adult or pre-retirement
        else:
            return 5   # Senior – highest age risk contribution

    def _classify(self, score: int) -> str:
        """
        Classify the customer into a risk category based on total score.
        """
        if score <= 35:
            return "Low Risk"
        elif score <= 65:
            return "Medium Risk"
        else:
            return "High Risk"
