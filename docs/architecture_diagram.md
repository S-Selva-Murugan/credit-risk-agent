# Architecture Diagram
## Credit Risk Analysis AI Agent — Banking System

---

## 1. High-Level System Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║               CREDIT RISK ANALYSIS AI AGENT — SYSTEM OVERVIEW           ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │                   PRESENTATION LAYER (Streamlit)                  │   ║
║  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐  │   ║
║  │  │ Customer     │  │ Risk Score    │  │ Agent Execution      │  │   ║
║  │  │ Input Form   │  │ Results Panel │  │ Trace Viewer         │  │   ║
║  │  └──────┬───────┘  └───────▲───────┘  └──────────────────────┘  │   ║
║  └─────────┼───────────────────┼────────────────────────────────────┘   ║
║            │                   │                                         ║
║  ┌─────────▼───────────────────┼────────────────────────────────────┐   ║
║  │                     LIFECYCLE HOOKS                               │   ║
║  │  ┌────────────────────────┐ │ ┌────────────────────────────────┐ │   ║
║  │  │  Pre-Analysis Hook     │ │ │  Post-Analysis Hook            │ │   ║
║  │  │  • Validate inputs     │ │ │  • Record metrics              │ │   ║
║  │  │  • Sanitise PII        │ │ │  • Raise HIGH_RISK alerts      │ │   ║
║  │  │  • Rate limit check    │ │ │  • Log event stream            │ │   ║
║  │  └───────────┬────────────┘ │ └────────────────────────────────┘ │   ║
║  └─────────────┼───────────────┼────────────────────────────────────┘   ║
║                │               │                                         ║
║  ┌─────────────▼───────────────┼────────────────────────────────────┐   ║
║  │                   AGENT ORCHESTRATION LAYER                       │   ║
║  │                                                                    │   ║
║  │              ┌─────────────────────────┐                          │   ║
║  │              │   ORCHESTRATOR AGENT    │                          │   ║
║  │              │  • Coordinates pipeline  │                          │   ║
║  │              │  • Makes final decision  │                          │   ║
║  │              └──┬──────┬──────┬────────┘                          │   ║
║  │                 │      │      │                                    │   ║
║  │    ┌────────────▼┐  ┌──▼──────▼──────┐  ┌───────────────────┐   │   ║
║  │    │RISK SCORING │  │  EXPLANATION    │  │   AUDIT AGENT     │   │   ║
║  │    │   AGENT     │  │    AGENT        │  │                   │   │   ║
║  │    │             │  │                 │  │ • Creates AUD-xxx │   │   ║
║  │    │ 5 scoring   │  │ 5 factor        │  │ • Hashes PII      │   │   ║
║  │    │ rules       │  │ explanations    │  │ • Persists to     │   │   ║
║  │    │ (0-100)     │  │                 │  │   JSONL file      │   │   ║
║  │    └─────────────┘  └─────────────────┘  └───────────────────┘   │   ║
║  └────────────────────────────────────────────────────────────────────┘  ║
║                                                                          ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │                    GOVERNANCE LAYER                               │   ║
║  │              ┌────────────────────────────┐                      │   ║
║  │              │      POLICY ENGINE          │                      │   ║
║  │              │ P1 Minimum Income           │                      │   ║
║  │              │ P2 Maximum DTI              │                      │   ║
║  │              │ P3 Delinquency Override      │                      │   ║
║  │              │ P4 Fair Lending Check        │                      │   ║
║  │              │ P5 Young Borrower            │                      │   ║
║  │              │ P6 Senior Borrower           │                      │   ║
║  │              └────────────────────────────┘                      │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │               MCP INTEGRATION LAYER (Multi-MCP)                   │   ║
║  │  ┌──────────────────────────┐  ┌───────────────────────────────┐ │   ║
║  │  │   CREDIT BUREAU MCP      │  │   BANKING DATA MCP             │ │   ║
║  │  │  (Mock CIBIL/Experian)   │  │  (Internal Data Warehouse)     │ │   ║
║  │  │                          │  │                                │ │   ║
║  │  │  • get_credit_report     │  │  • get_account_summary         │ │   ║
║  │  │  • get_payment_history   │  │  • get_transaction_history     │ │   ║
║  │  │  • get_existing_loans    │  │  • get_relationship_score      │ │   ║
║  │  │  • verify_identity       │  │  • get_market_rates            │ │   ║
║  │  └──────────────────────────┘  └───────────────────────────────┘ │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │              OBSERVABILITY LAYER                                   │   ║
║  │  ┌─────────────────────┐  ┌───────────────────────────────────┐  │   ║
║  │  │      TRACER          │  │      METRICS COLLECTOR             │  │   ║
║  │  │ • Per-agent logs     │  │ • Total analyses counter           │  │   ║
║  │  │ • Timestamps         │  │ • Risk distribution stats          │  │   ║
║  │  │ • traces.jsonl       │  │ • p50/p95 processing times         │  │   ║
║  │  └─────────────────────┘  └───────────────────────────────────┘  │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Agent Communication Flow

```
Customer Profile Input
        │
        ▼
PreAnalysisHook.execute()
        │ valid? ──NO──► Error to UI
        │ YES
        ▼
OrchestratorAgent.analyse()
        │
        ├──► RiskScoringAgent.compute_risk()
        │         │
        │         ├── _score_credit()      → 0–35 pts
        │         ├── _score_dti()         → 0–25 pts
        │         ├── _score_missed()      → 0–20 pts
        │         ├── _score_employment()  → 0–15 pts
        │         └── _score_age()         → 0–5 pts
        │                   │
        │              risk_score (0–100) + risk_level
        │
        ├──► ExplanationAgent.generate()
        │         │
        │         ├── _explain_credit()
        │         ├── _explain_dti()
        │         ├── _explain_payments()
        │         ├── _explain_employment()
        │         └── _explain_age()
        │                   │
        │              summary + factors[]
        │
        ├──► PolicyEngine.check()
        │         │
        │         ├── P1 Min Income check
        │         ├── P2 Max DTI check
        │         ├── P3 Delinquency check
        │         ├── P4 Bias check
        │         ├── P5 Young Borrower check
        │         └── P6 Senior Borrower check
        │                   │
        │              {policy_compliant, flags[]}
        │
        └──► AuditAgent.record()
                    │
                    └── audit_log.jsonl
        │
        ▼
PostAnalysisHook.execute()
        │
        ├── record metrics
        ├── raise HIGH_RISK alert if needed
        └── events.jsonl
        │
        ▼
Result Display in Streamlit UI
```

---

## 3. Skills Architecture

```
                    ┌──────────────────────┐
                    │  SKILLS LAYER        │
                    │                      │
    ┌───────────────┤  Reusable, stateless │
    │               │  callable units      │
    │               └──────────────────────┘
    │
    ├── RiskScoringSkill.invoke(profile)
    │       └── delegates to RiskScoringAgent
    │       └── returns {success, risk_score, risk_level, sub_scores}
    │
    ├── ExplanationSkill.invoke(profile, risk_result)
    │       └── delegates to ExplanationAgent
    │       └── returns {success, summary, factors[]}
    │
    └── ReportGenerationSkill.invoke(profile, result)
            └── assembles full report
            └── returns {report_json, report_text}
```

---

## 4. Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                  PRODUCTION                      │
│                                                  │
│   ┌───────────────┐     ┌───────────────────┐   │
│   │  Load Balancer│────►│  Streamlit Server  │   │
│   │  (nginx/ALB)  │     │  (Docker container)│   │
│   └───────────────┘     └─────────┬─────────┘   │
│                                   │              │
│                     ┌─────────────▼───────────┐  │
│                     │  Credit Risk AI Agent    │  │
│                     │  (Python in-process)     │  │
│                     └─────────────┬───────────┘  │
│                                   │              │
│          ┌────────────────────────┼──────────┐   │
│          ▼                        ▼          ▼   │
│   ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│   │ audit_log    │  │ traces.jsonl │  │events  ││
│   │ .jsonl       │  │              │  │.jsonl  ││
│   │ (7yr retain) │  │ (90d retain) │  │(1yr)   ││
│   └──────────────┘  └──────────────┘  └────────┘│
└─────────────────────────────────────────────────┘
```
