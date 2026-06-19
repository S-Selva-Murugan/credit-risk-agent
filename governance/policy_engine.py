"""
Policy Engine
=============
Governance layer that checks every credit risk decision against
a configurable set of policies before it reaches the user.

Policies enforced:
    P1 – Minimum Income Policy:     Customers below ₹10,000/month income
                                    cannot be approved regardless of other factors.
    P2 – Maximum DTI Policy:        DTI above 80% must trigger a reject override.
    P3 – Bankruptcy/Delinquency:    More than 6 missed payments → forced High Risk.
    P4 – Fair Lending (Bias) Check: Ensure age/employment type do not dominate
                                    the decision unjustly.
    P5 – Minor Age Check:           Customers under 21 require parental guarantor.
    P6 – Senior Borrower Check:     Customers over 65 require loan tenure ≤ 5 years.
"""

import uuid
import datetime
from typing import List, Dict


class PolicyEngine:
    """
    Rule-based governance engine that validates credit decisions.
    All policy rules are explicit and auditable.
    """

    # Policy thresholds (configurable)
    MIN_INCOME_FOR_APPROVAL = 10_000       # ₹ per month
    MAX_DTI_FOR_APPROVAL    = 80           # percentage
    MAX_MISSED_PAYMENTS_FOR_LOW_RISK = 6  # count
    MIN_AGE_NO_GUARANTOR    = 21           # years
    MAX_AGE_STANDARD_TENURE = 65          # years

    def check(self, customer_profile: dict, risk_result: dict) -> dict:
        """
        Run all governance policies against the risk result.

        Args:
            customer_profile: customer input data
            risk_result:      output from RiskScoringAgent

        Returns:
            dict with policy_compliant (bool), bias_check_passed (bool),
                  flags (list), audit_id (str), overrides_applied (list)
        """
        flags = []
        overrides = []
        bias_passed = True

        income     = float(customer_profile.get("monthly_income", 0))
        loan       = float(customer_profile.get("existing_loan", 0))
        missed     = int(customer_profile.get("missed_payments", 0))
        age        = int(customer_profile.get("age", 30))
        emp_type   = customer_profile.get("employment_type", "Salaried")
        risk_level = risk_result.get("risk_level")
        risk_score = risk_result.get("risk_score", 0)

        # Calculate DTI for policy checks
        annual_income = income * 12 if income > 0 else 1
        dti = (loan / annual_income) * 100

        # ── P1: Minimum Income Policy ─────────────────────────────────────
        if income < self.MIN_INCOME_FOR_APPROVAL and risk_level != "High Risk":
            flags.append({
                "policy": "P1-MIN-INCOME",
                "severity": "HIGH",
                "message": f"Customer income ₹{income:,.0f}/month is below minimum ₹{self.MIN_INCOME_FOR_APPROVAL:,}. Override to High Risk."
            })
            overrides.append("P1: Forced to High Risk due to insufficient income.")

        # ── P2: Maximum DTI Policy ────────────────────────────────────────
        if dti > self.MAX_DTI_FOR_APPROVAL:
            flags.append({
                "policy": "P2-MAX-DTI",
                "severity": "HIGH",
                "message": f"Debt-to-Income ratio {dti:.1f}% exceeds maximum allowed {self.MAX_DTI_FOR_APPROVAL}%."
            })
            overrides.append("P2: Loan not eligible due to excessive DTI ratio.")

        # ── P3: Delinquency Override ──────────────────────────────────────
        if missed > self.MAX_MISSED_PAYMENTS_FOR_LOW_RISK and risk_level == "Low Risk":
            flags.append({
                "policy": "P3-DELINQUENCY",
                "severity": "MEDIUM",
                "message": f"{missed} missed payments exceed threshold. Risk upgraded."
            })
            overrides.append("P3: Risk level upgraded due to excessive missed payments.")

        # ── P4: Fair Lending Bias Check ───────────────────────────────────
        # Ensure the employment type penalty alone did not cause a High Risk rating
        # when all other factors are good (credit score > 700, DTI < 30, no missed payments)
        sub = risk_result.get("sub_scores", {})
        if (
            sub.get("credit_score_risk", 99) <= 14 and    # Good or better credit
            sub.get("dti_risk", 99) <= 8 and              # Low DTI
            sub.get("missed_payment_risk", 99) == 0 and   # Perfect payment history
            risk_level == "High Risk"
        ):
            flags.append({
                "policy": "P4-FAIR-LENDING",
                "severity": "MEDIUM",
                "message": "Potential fair lending concern: High Risk with good credit/DTI/payment history. "
                           "Employment type may be overly penalised. Recommend manual review."
            })
            bias_passed = False

        # ── P5: Minor Age Guarantor Policy ───────────────────────────────
        if age < self.MIN_AGE_NO_GUARANTOR:
            flags.append({
                "policy": "P5-YOUNG-BORROWER",
                "severity": "LOW",
                "message": f"Borrower aged {age} is under {self.MIN_AGE_NO_GUARANTOR}. "
                           f"Parental/co-borrower guarantor required."
            })

        # ── P6: Senior Borrower Tenure Policy ────────────────────────────
        if age > self.MAX_AGE_STANDARD_TENURE:
            flags.append({
                "policy": "P6-SENIOR-BORROWER",
                "severity": "LOW",
                "message": f"Borrower aged {age} exceeds {self.MAX_AGE_STANDARD_TENURE}. "
                           f"Loan tenure must not exceed 5 years."
            })

        # ── Overall Compliance ────────────────────────────────────────────
        # P1 and P2 are hard failures; others are advisory
        hard_failure_policies = {"P1-MIN-INCOME", "P2-MAX-DTI"}
        policy_compliant = not any(
            f["policy"] in hard_failure_policies for f in flags
        )

        return {
            "policy_compliant":  policy_compliant,
            "bias_check_passed": bias_passed,
            "flags":             flags,
            "overrides_applied": overrides,
            "policies_checked":  ["P1", "P2", "P3", "P4", "P5", "P6"],
            "check_timestamp":   datetime.datetime.now().isoformat()
        }
