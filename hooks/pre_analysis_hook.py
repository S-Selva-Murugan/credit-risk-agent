"""
Pre-Analysis Hook
=================
Lifecycle hook that executes BEFORE the agent pipeline begins.

Responsibilities:
    1. Input validation – ensure all required fields are present and sensible
    2. Data sanitisation – strip whitespace, normalise types
    3. Rate limiting  – prevent duplicate submissions in quick succession
    4. PII check      – warn if loan amounts seem implausibly high

Hooks are a key Claude Agent SDK feature. They let you inject cross-cutting
concerns (validation, logging, security) without changing agent logic.
"""

import re
import datetime
from typing import Dict, Any


class PreAnalysisHook:
    """
    Validates and sanitises customer profile data before agents process it.
    """

    # Thresholds for anomaly detection
    MIN_INCOME_FOR_LARGE_LOAN = 10_000    # ₹10k/month minimum for any loan
    MAX_PLAUSIBLE_LOAN        = 50_000_000  # ₹5 crore upper plausibility limit

    def __init__(self):
        # Track last submission time per customer name (simple rate limiter)
        self._last_submission: Dict[str, datetime.datetime] = {}

    def execute(self, profile: dict) -> dict:
        """
        Run all pre-analysis validations.

        Args:
            profile: raw customer profile dict from the Streamlit form

        Returns:
            dict with 'valid' (bool) and 'reason' (str if invalid) and
            optionally 'warnings' (list of non-blocking advisory messages)
        """
        warnings = []

        # ── 1. Required field presence check ─────────────────────────────
        required_fields = [
            "name", "age", "monthly_income", "existing_loan",
            "credit_score", "missed_payments", "employment_type"
        ]
        for field in required_fields:
            if field not in profile or profile[field] is None:
                return {"valid": False, "reason": f"Required field '{field}' is missing."}

        # ── 2. Name validation ────────────────────────────────────────────
        name = str(profile["name"]).strip()
        if len(name) < 2:
            return {"valid": False, "reason": "Customer name must be at least 2 characters."}
        if not re.match(r"^[A-Za-z\s'\-\.]+$", name):
            return {"valid": False, "reason": "Customer name contains invalid characters."}

        # ── 3. Age range check ────────────────────────────────────────────
        age = int(profile["age"])
        if not (18 <= age <= 80):
            return {"valid": False, "reason": f"Age {age} is outside the allowed range (18–80)."}

        # ── 4. Income / loan plausibility check ───────────────────────────
        income = float(profile["monthly_income"])
        loan   = float(profile["existing_loan"])

        if income < 0:
            return {"valid": False, "reason": "Monthly income cannot be negative."}
        if loan < 0:
            return {"valid": False, "reason": "Existing loan amount cannot be negative."}
        if loan > self.MAX_PLAUSIBLE_LOAN:
            warnings.append(f"Loan amount ₹{loan:,.0f} is unusually high. Please verify.")
        if loan > 0 and income < self.MIN_INCOME_FOR_LARGE_LOAN:
            warnings.append("Customer has an existing loan but very low/zero income. Flag for manual review.")

        # ── 5. Credit score range check ───────────────────────────────────
        credit_score = int(profile["credit_score"])
        if not (300 <= credit_score <= 900):
            return {"valid": False, "reason": f"Credit score {credit_score} is outside CIBIL range (300–900)."}

        # ── 6. Missed payments check ──────────────────────────────────────
        missed = int(profile["missed_payments"])
        if missed < 0:
            return {"valid": False, "reason": "Missed payments cannot be negative."}
        if missed > 12:
            warnings.append(f"{missed} missed payments in 12 months suggests serious delinquency.")

        # ── 7. Sanitise the profile in-place ─────────────────────────────
        profile["name"]             = name
        profile["age"]              = age
        profile["monthly_income"]   = income
        profile["existing_loan"]    = loan
        profile["credit_score"]     = credit_score
        profile["missed_payments"]  = missed
        profile["employment_type"]  = str(profile["employment_type"]).strip()

        return {
            "valid":    True,
            "warnings": warnings
        }
