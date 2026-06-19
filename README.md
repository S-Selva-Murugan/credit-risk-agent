# Credit Risk Analysis AI Agent 🏦

An AI-powered, multi-agent credit risk assessment system for banking professionals.
Built with Python, Streamlit, and the Claude Agent SDK.

---

## What It Does

Enter a customer's financial profile and get:
- A **risk score** (0–100) with a visual gauge
- A **risk classification**: Low / Medium / High Risk
- A **detailed explanation** of why the customer received that rating
- A **banking decision**: Approve / Review / Reject
- An **interest rate band** recommendation
- A full **governance policy check** (6 policies)
- An **immutable audit record** for every decision

---

## Quick Start

### 1. Navigate into the project folder

```bash
cd credit_risk_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

Open your browser to **http://localhost:8501**

---

## Project Structure

```
credit_risk_agent/
├── app.py                    # Main Streamlit UI
│
├── agents/                   # The 4 AI agents
│   ├── orchestrator_agent.py # Coordinates all agents
│   ├── risk_scoring_agent.py # Computes risk score (rule-based)
│   ├── explanation_agent.py  # Generates explanations
│   └── audit_agent.py        # Logs all decisions
│
├── skills/                   # Reusable capabilities
│   ├── risk_scoring_skill.py
│   ├── explanation_skill.py
│   └── report_generation_skill.py
│
├── hooks/                    # Lifecycle hooks
│   ├── pre_analysis_hook.py  # Validates input before analysis
│   └── post_analysis_hook.py # Records metrics after analysis
│
├── mcp/                      # MCP server integrations
│   ├── credit_bureau_mcp.py  # Mock CIBIL credit bureau
│   └── banking_data_mcp.py   # Mock internal banking data
│
├── governance/
│   └── policy_engine.py      # 6 banking policies enforced
│
├── observability/
│   ├── tracer.py             # Distributed tracing
│   └── metrics.py            # Performance metrics
│
├── data/
│   └── sample_profiles.py    # 6 sample customer profiles
│
├── tests/                    # 78 automated tests
│   ├── test_risk_scoring.py
│   ├── test_hooks.py
│   ├── test_governance.py
│   ├── test_mcp.py
│   ├── test_orchestrator.py
│   └── test_load.py
│
├── docs/                     # Project documentation
│   ├── architecture_diagram.md
│   ├── technical_design_document.md
│   ├── governance_report.md
│   ├── testing_evaluation_report.md
│   ├── deployment_guide.md
│   └── presentation_deck.md
│
├── logs/                     # Auto-created runtime logs
│   ├── audit_log.jsonl       # Immutable audit trail
│   ├── traces.jsonl          # Agent traces
│   └── events.jsonl          # Analysis events
│
├── requirements.txt
└── README.md
```

---

## Customer Input Fields

| Field | Description |
|-------|-------------|
| Customer Name | Full name (letters/spaces only) |
| Age | 18–80 years |
| Monthly Income | In ₹ |
| Existing Loan Amount | Total outstanding balance in ₹ |
| Credit Score | CIBIL score 300–900 |
| Missed Payments | EMIs missed in last 12 months |
| Employment Type | Salaried / Self-Employed / Business Owner / Unemployed / Retired |

---

## Risk Scoring Rules

The system uses **rule-based scoring** (no ML/black-box). Total score = sum of 5 components:

| Component | Max Points | Rule |
|-----------|-----------|------|
| Credit Score | 35 | Higher CIBIL = lower risk |
| Debt-to-Income Ratio | 25 | Lower DTI = lower risk |
| Missed Payments | 20 | Zero missed = zero risk |
| Employment Type | 15 | Salaried = zero, Unemployed = max |
| Age Factor | 5 | Prime earning years = zero |

**Classification:**
- 0–35: Low Risk → Approve
- 36–65: Medium Risk → Review
- 66–100: High Risk → Reject

---

## Sample Profiles

Six pre-built profiles are available in the sidebar:

| Profile | Expected Result |
|---------|----------------|
| Alice Sharma | Low Risk |
| Priya Mehta | Low Risk |
| Raj Patel | Medium Risk |
| Sunita Joshi | Medium Risk |
| Kumar Singh | High Risk |
| Vijay Reddy | High Risk |

---

## Running Tests

```bash
# Run all 78 tests
pytest tests/ -v

# Run specific suite
pytest tests/test_risk_scoring.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run load tests (shows timing stats)
pytest tests/test_load.py -v -s
```

---

## Governance Policies

6 banking policies are automatically enforced:

| Policy | Type | Trigger |
|--------|------|---------|
| P1 – Min Income | Hard Fail | Income < ₹10,000/month |
| P2 – Max DTI | Hard Fail | DTI > 80% |
| P3 – Delinquency | Advisory | > 6 missed payments |
| P4 – Fair Lending | Bias Alert | High Risk despite good credit |
| P5 – Young Borrower | Info | Age < 21 |
| P6 – Senior Borrower | Info | Age > 65 |

---

## Architecture

4 cooperating agents + 2 MCP servers + hooks + governance:

```
Input → PreHook → Orchestrator → [RiskAgent + ExplanationAgent + AuditAgent]
                              → PolicyEngine → PostHook → UI
                    ↕                   ↕
           CreditBureauMCP     BankingDataMCP
```

---

## Documentation

Full project documentation is in the `docs/` folder:

- [Architecture Diagram](docs/architecture_diagram.md)
- [Technical Design Document](docs/technical_design_document.md)
- [Governance Report](docs/governance_report.md)
- [Testing & Evaluation Report](docs/testing_evaluation_report.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Presentation Deck](docs/presentation_deck.md)

---

## Disclaimer

This tool is designed to **support** banking professionals in credit decisions.
It does **not replace** human judgment. All decisions should be reviewed by
a qualified banking professional before acting on them.

---

*Credit Risk Analysis AI Agent v1.0.0 | Built with Claude Agent SDK + Streamlit*
