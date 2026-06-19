"""
Sample Customer Profiles
========================
Pre-built customer profiles for testing and demonstration.
These appear in the Streamlit sidebar as one-click shortcuts.

Each profile is designed to trigger a different risk classification:
    - Alice Sharma   → Low Risk   (excellent all-round profile)
    - Raj Patel      → Medium Risk (mixed indicators)
    - Kumar Singh    → High Risk   (multiple red flags)
    - Priya Mehta    → Low Risk   (salaried, good score, no debt)
    - Vijay Reddy    → High Risk   (unemployed, poor credit)
"""

SAMPLE_PROFILES = {

    "Alice Sharma (Low Risk)": {
        "name":            "Alice Sharma",
        "age":             34,
        "monthly_income":  120_000,       # ₹1.2 lakh – strong income
        "existing_loan":   300_000,       # ₹3 lakh – low relative to income
        "credit_score":    820,           # Excellent CIBIL score
        "missed_payments": 0,             # Perfect payment history
        "employment_type": "Salaried"     # Most stable employment
    },

    "Raj Patel (Medium Risk)": {
        "name":            "Raj Patel",
        "age":             42,
        "monthly_income":  55_000,        # ₹55k – moderate income
        "existing_loan":   800_000,       # ₹8 lakh – significant existing debt
        "credit_score":    640,           # Fair credit score
        "missed_payments": 2,             # Two missed payments – some concern
        "employment_type": "Self-Employed" # Variable income adds risk
    },

    "Kumar Singh (High Risk)": {
        "name":            "Kumar Singh",
        "age":             28,
        "monthly_income":  18_000,        # ₹18k – low income
        "existing_loan":   500_000,       # ₹5 lakh – high relative to income
        "credit_score":    480,           # Poor CIBIL score
        "missed_payments": 7,             # Chronic delinquency
        "employment_type": "Unemployed"   # No income source
    },

    "Priya Mehta (Low Risk)": {
        "name":            "Priya Mehta",
        "age":             29,
        "monthly_income":  85_000,        # ₹85k – good income
        "existing_loan":   0,             # No existing debt – clean slate
        "credit_score":    775,           # Very good score
        "missed_payments": 0,             # Perfect payment history
        "employment_type": "Salaried"
    },

    "Vijay Reddy (High Risk)": {
        "name":            "Vijay Reddy",
        "age":             52,
        "monthly_income":  0,             # Currently unemployed
        "existing_loan":   1_200_000,     # ₹12 lakh outstanding
        "credit_score":    390,           # Very poor credit
        "missed_payments": 10,            # Severely delinquent
        "employment_type": "Unemployed"
    },

    "Sunita Joshi (Medium Risk)": {
        "name":            "Sunita Joshi",
        "age":             38,
        "monthly_income":  70_000,        # ₹70k – decent income
        "existing_loan":   600_000,       # ₹6 lakh – moderate debt
        "credit_score":    680,           # Good credit score
        "missed_payments": 1,             # One small missed payment
        "employment_type": "Business Owner"
    }
}
