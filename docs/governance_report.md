# Governance Report
## Credit Risk Analysis AI Agent — Banking System

**Version:** 1.0.0
**Date:** 2026-06-19
**Classification:** Internal Banking Document

---

## 1. Purpose

This report documents the governance framework, fairness controls, and compliance mechanisms built into the Credit Risk Analysis AI Agent. It is intended for:
- Compliance and Risk Management teams
- Internal Audit
- Regulators (RBI, Basel III oversight)
- Model Risk Management

---

## 2. Regulatory Compliance

### 2.1 Applicable Regulations

| Regulation | Requirement | How We Comply |
|-----------|-------------|---------------|
| RBI Fair Lending Guidelines | No discriminatory decisions | P4 Bias Check enforced per decision |
| Basel III Risk Framework | Documented risk scoring methodology | TDD + all rules explicit and versioned |
| IND AS 109 (IFRS 9) | Expected Credit Loss documentation | Audit trail records every decision |
| Data Protection (DPDPA 2023) | PII minimisation | Audit logs store name hash + age band only |
| Internal Credit Policy | Income/DTI thresholds | P1 (min income) + P2 (max DTI) hard-coded |

---

## 3. Governance Policies

### 3.1 Policy Inventory

#### P1 – Minimum Income Policy
- **Type:** Hard failure (overrides AI decision)
- **Rule:** Monthly income < ₹10,000 → cannot approve
- **Rationale:** RBI mandates minimum demonstrated repayment capacity
- **Override:** None – human banker cannot override P1 without escalation

#### P2 – Maximum DTI Policy
- **Type:** Hard failure
- **Rule:** Debt-to-Income ratio > 80% → loan not eligible
- **Rationale:** Industry standard (CFPB/RBI aligned) to prevent debt spirals
- **Override:** None at standard level; credit committee can override with collateral

#### P3 – Delinquency Override
- **Type:** Advisory flag
- **Rule:** > 6 missed payments in 12 months when classified as Low Risk → upgrade flag
- **Rationale:** Prevents gaming the model by structuring a missing payment

#### P4 – Fair Lending (Bias Check)
- **Type:** Advisory + mandatory review
- **Rule:** If risk = High despite credit score > 670, DTI < 30%, and 0 missed payments → potential bias flag
- **Rationale:** Ensures employment type penalty does not disproportionately impact certain communities
- **Action:** Triggers mandatory manual review by credit officer

#### P5 – Young Borrower (Minor/Young Adult) Policy
- **Type:** Advisory
- **Rule:** Age < 21 → co-borrower or parental guarantor required
- **Rationale:** Limits legal and repayment risk for young borrowers

#### P6 – Senior Borrower Policy
- **Type:** Advisory
- **Rule:** Age > 65 → loan tenure max 5 years
- **Rationale:** Ensures loan repayment is within working/pension income horizon

---

## 4. Fairness and Bias Controls

### 4.1 Bias Detection Approach

The system implements **statistical parity monitoring** via Policy P4:

```python
# P4 fires if:
# - Credit score risk is low (< 15 points)
# - DTI risk is low (< 8 points)  
# - No missed payments (= 0)
# BUT the decision is High Risk
# → This indicates employment type is dominating unfairly
```

### 4.2 Protected Attributes
The scoring model does **not** use the following as inputs:
- Gender
- Religion
- Caste
- Nationality
- Marital status
- Residential address

### 4.3 Transparency
All scoring rules are:
- Documented in this report
- Versioned in source control
- Explainable per decision (ExplanationAgent output)
- Reviewable by the customer on request

---

## 5. Audit Trail

### 5.1 What is Logged

Every analysis generates an immutable record in `logs/audit_log.jsonl`:

```json
{
  "audit_id": "AUD-XXXXXXXXXX",
  "session_id": "uuid",
  "timestamp": "2026-06-19T10:30:00",
  "customer": {
    "name_hash":       "CUST-123456",
    "age_band":        "35-44",
    "employment_type": "Salaried"
  },
  "outcome": {
    "risk_score": 15,
    "risk_level": "Low Risk",
    "decision":   "Approve"
  },
  "governance": {
    "policy_compliant":  true,
    "bias_check_passed": true,
    "flags":             []
  },
  "system": {
    "agent_version":  "1.0.0",
    "scoring_model":  "rule-based-v1",
    "agent_id":       "RiskScoringAgent"
  }
}
```

### 5.2 PII Protection in Audit Logs
- **Name**: Stored as a one-way hash (never in plain text)
- **Age**: Stored as an age band (not exact age)
- **Income**: Not stored in audit logs
- **Loan amount**: Not stored in audit logs

### 5.3 Retention
- Audit logs: 7 years (regulatory requirement)
- Trace logs: 90 days
- Event logs: 1 year

---

## 6. Model Risk Management

### 6.1 Model Version Control
- Scoring rules are version-tagged in `RiskScoringAgent.AGENT_VERSION`
- Each audit record includes the model version used
- Rule changes require a new version number and PR review

### 6.2 Model Monitoring
Metrics collected per analysis:
- Risk distribution (Low/Medium/High counts)
- Average processing time
- Error rate
- Policy violation frequency

Alerts are raised when:
- High Risk decisions occur (post-analysis hook)
- Policy violations are detected
- Bias check fails

### 6.3 Model Validation
- 40+ unit and integration tests
- Load tests: 100-profile simulation
- Boundary condition tests for all scoring rules

---

## 7. Escalation Procedures

| Situation | Escalation Path |
|-----------|----------------|
| P1 or P2 policy violation | Loan rejected; customer notified by banker |
| P4 Bias flag | Mandatory credit officer manual review |
| High Risk borderline (score 60-70) | Senior credit analyst review |
| System error during analysis | IT + Risk team notification |

---

## 8. Review and Update Schedule

| Activity | Frequency |
|----------|-----------|
| Scoring thresholds review | Quarterly |
| Policy review | Annually (or when RBI guidelines change) |
| Bias audit | Monthly (automated via P4 flag tracking) |
| Model performance review | Monthly |
| Full governance report update | Annually |
