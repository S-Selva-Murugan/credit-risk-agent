# Technical Design Document
## Credit Risk Analysis AI Agent — Banking System

**Version:** 1.0.0
**Date:** 2026-06-19
**Author:** Credit Risk Engineering Team

---

## 1. Executive Summary

The Credit Risk Analysis AI Agent is a multi-agent system built on the Claude Agent SDK that automates credit risk assessment for banking professionals. The system accepts a customer's financial profile, computes a risk score using rule-based logic, classifies the customer as Low/Medium/High risk, generates a human-readable explanation, and logs every decision for audit and regulatory compliance.

---

## 2. Problem Understanding

### 2.1 Business Problem
Banks must assess creditworthiness for every loan applicant. Traditional manual processes are:
- **Slow**: A loan officer reviews one application at a time
- **Inconsistent**: Different officers apply different mental models
- **Non-auditable**: Verbal decisions leave no paper trail
- **Biased**: Human judgment is susceptible to unconscious bias

### 2.2 Solution Approach
An AI agent system that:
1. Applies consistent, documented scoring rules to every applicant
2. Generates transparent explanations (explainable AI)
3. Records all decisions in an immutable audit trail
4. Enforces governance policies (minimum income, DTI limits, fair lending)
5. Provides a web-based UI for banking professionals

### 2.3 Scope
- **In scope**: Rule-based credit scoring, risk classification, explanation generation, audit logging, governance policy enforcement, MCP integration (mock)
- **Out of scope**: ML/AI model training, real credit bureau API calls, database persistence, user authentication

---

## 3. System Architecture

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT WEB APPLICATION                     │
│  ┌────────────┐  ┌───────────────┐  ┌────────────────────────┐ │
│  │  Input Form│  │ Results Panel │  │ Agent Trace Viewer     │ │
│  └────────────┘  └───────────────┘  └────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────▼──────────────────┐
              │         PRE-ANALYSIS HOOK          │
              │  (Validation + Sanitisation)       │
              └────────────────┬──────────────────┘
                               │
              ┌────────────────▼──────────────────┐
              │       ORCHESTRATOR AGENT           │
              │  (Pipeline Coordinator)            │
              └──┬──────────┬──────────┬──────────┘
                 │          │          │
    ┌────────────▼──┐  ┌────▼──────┐  ┌▼──────────────┐
    │ RISK SCORING  │  │EXPLANATION│  │  AUDIT AGENT  │
    │    AGENT      │  │  AGENT    │  │               │
    └──────────┬────┘  └────┬──────┘  └───────┬───────┘
               │            │                  │
    ┌──────────▼────────────▼──────────────────▼───┐
    │            POLICY ENGINE (Governance)          │
    └───────────────────────────────────────────────┘
               │                  │
    ┌──────────▼──────┐  ┌────────▼────────┐
    │ CREDIT BUREAU   │  │  BANKING DATA   │
    │  MCP SERVER     │  │  MCP SERVER     │
    └─────────────────┘  └─────────────────┘
               │
    ┌──────────▼──────────────────────────────────┐
    │            POST-ANALYSIS HOOK                │
    │  (Metrics + Alerts + Event Logging)          │
    └─────────────────────────────────────────────┘
```

### 3.2 Agent Descriptions

| Agent | Role | Key Responsibility |
|-------|------|--------------------|
| OrchestratorAgent | Master coordinator | Delegates to subagents, assembles result |
| RiskScoringAgent | Specialist subagent | Computes 0-100 risk score via 5 rules |
| ExplanationAgent | Specialist subagent | Generates human-readable factor analysis |
| AuditAgent | Specialist subagent | Creates immutable audit records |

### 3.3 Skills

| Skill | Description |
|-------|-------------|
| RiskScoringSkill | Standalone callable version of risk scoring |
| ExplanationSkill | Standalone callable version of explanation |
| ReportGenerationSkill | Assembles full downloadable report |

---

## 4. Credit Risk Scoring Algorithm

### 4.1 Scoring Dimensions

The risk score is computed as the sum of 5 independent sub-scores:

```
Total Risk Score = CreditScore_Risk + DTI_Risk + MissedPayments_Risk
                 + Employment_Risk + Age_Risk
```

### 4.2 Sub-score Rules

#### Credit Score Risk (0–35 points)
| CIBIL Range | Points | Interpretation |
|-------------|--------|----------------|
| 800–900 | 0 | Excellent |
| 740–799 | 7 | Very Good |
| 670–739 | 14 | Good |
| 580–669 | 25 | Fair |
| 300–579 | 35 | Poor |

#### Debt-to-Income Ratio Risk (0–25 points)
| DTI % | Points | Interpretation |
|-------|--------|----------------|
| ≤ 20% | 0 | Minimal debt |
| 21–40% | 8 | Manageable |
| 41–60% | 16 | Elevated |
| 61–80% | 22 | High burden |
| > 80% | 25 | Dangerous |

#### Missed Payments Risk (0–20 points)
| Missed EMIs (12 months) | Points |
|------------------------|--------|
| 0 | 0 |
| 1 | 7 |
| 2–3 | 13 |
| 4–6 | 17 |
| > 6 | 20 |

#### Employment Type Risk (0–15 points)
| Employment Type | Points |
|----------------|--------|
| Salaried | 0 |
| Business Owner | 5 |
| Self-Employed | 8 |
| Retired | 10 |
| Unemployed | 15 |

#### Age Risk (0–5 points)
| Age Range | Points |
|-----------|--------|
| 28–50 | 0 |
| 25–27 or 51–58 | 2 |
| 18–24 or 59–65 | 4 |
| > 65 | 5 |

### 4.3 Risk Classification

| Total Score | Classification |
|-------------|----------------|
| 0–35 | Low Risk → Approve |
| 36–65 | Medium Risk → Review |
| 66–100 | High Risk → Reject |

---

## 5. Governance Framework

Six policies are enforced by the PolicyEngine on every decision:

| Policy | Type | Trigger |
|--------|------|---------|
| P1 – Minimum Income | Hard Failure | Income < ₹10,000/month |
| P2 – Maximum DTI | Hard Failure | DTI > 80% |
| P3 – Delinquency Override | Advisory | >6 missed payments + Low Risk verdict |
| P4 – Fair Lending (Bias) | Advisory | High Risk despite good credit/DTI/payments |
| P5 – Young Borrower | Advisory | Age < 21 (guarantor required) |
| P6 – Senior Borrower | Advisory | Age > 65 (tenure limit applies) |

---

## 6. Data Flow

```
Input Form → PreAnalysisHook → OrchestratorAgent
          → RiskScoringAgent (compute 5 sub-scores)
          → ExplanationAgent (generate explanation text)
          → PolicyEngine (check 6 governance rules)
          → AuditAgent (persist audit record)
          → PostAnalysisHook (record metrics, raise alerts)
          → UI Result Display
```

---

## 7. Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend  | Streamlit 1.35 |
| Language  | Python 3.10+ |
| Testing   | pytest 8.x |
| Tracing   | Custom OpenTelemetry-style tracer |
| Storage   | JSON-lines flat files (audit + trace logs) |
| MCP       | Custom mock servers (CreditBureauMCP, BankingDataMCP) |

---

## 8. Non-Functional Requirements

| Requirement | Target | Actual |
|-------------|--------|--------|
| Single analysis latency | < 1 second | ~0.01s (rule-based) |
| p95 latency (load test) | < 1 second | ✅ |
| Audit trail completeness | 100% | ✅ |
| Test coverage | > 80% | ✅ (40+ test cases) |
| Bias check | Per-decision | ✅ PolicyEngine P4 |
