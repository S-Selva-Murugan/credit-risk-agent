# Deployment Guide
## Credit Risk Analysis AI Agent — Banking System

**Version:** 1.0.0
**Date:** 2026-06-19

---

## 1. Prerequisites

### 1.1 System Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| OS | Ubuntu 20.04 / macOS 12 / Windows 10 | Ubuntu 22.04 LTS |
| Python | 3.10 | 3.11+ |
| RAM | 512 MB | 2 GB |
| CPU | 1 vCPU | 2 vCPU |
| Disk | 500 MB | 2 GB |
| Network | Not required (local mode) | Internet for MCP extensions |

### 1.2 Required Software
- Python 3.10+
- pip 23+
- git (optional, for clone)

---

## 2. Local Development Setup

### Step 1: Navigate to Project Directory

```bash
cd "credit_risk_agent"
```

### Step 2: Create a Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Check Python version
python --version      # Should be 3.10+

# Run tests to verify everything works
pytest tests/ -v
```

Expected output:
```
tests/test_governance.py::TestPolicyEngine::test_clean_profile_is_compliant PASSED
tests/test_hooks.py::TestPreAnalysisHook::test_valid_profile_passes PASSED
... (78 tests should all pass)
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open at: **http://localhost:8501**

---

## 3. Project Structure

```
credit_risk_agent/
├── app.py                          # Main Streamlit application
│
├── agents/                         # Agent pipeline
│   ├── orchestrator_agent.py       # Master coordinator
│   ├── risk_scoring_agent.py       # Risk computation subagent
│   ├── explanation_agent.py        # Explanation generation subagent
│   └── audit_agent.py              # Audit logging subagent
│
├── skills/                         # Reusable skills
│   ├── risk_scoring_skill.py
│   ├── explanation_skill.py
│   └── report_generation_skill.py
│
├── hooks/                          # Lifecycle hooks
│   ├── pre_analysis_hook.py        # Input validation
│   └── post_analysis_hook.py       # Post-processing / alerts
│
├── mcp/                            # MCP server integrations
│   ├── credit_bureau_mcp.py        # CIBIL bureau (mock)
│   └── banking_data_mcp.py         # Internal bank data (mock)
│
├── governance/
│   └── policy_engine.py            # 6-policy governance engine
│
├── observability/
│   ├── tracer.py                   # Distributed tracing
│   └── metrics.py                  # Metrics collector
│
├── data/
│   └── sample_profiles.py          # 6 pre-built test profiles
│
├── tests/                          # Test suites (78 tests)
│   ├── test_risk_scoring.py
│   ├── test_hooks.py
│   ├── test_governance.py
│   ├── test_mcp.py
│   ├── test_orchestrator.py
│   └── test_load.py
│
├── logs/                           # Auto-created at runtime
│   ├── audit_log.jsonl             # Immutable audit trail
│   ├── traces.jsonl                # Agent execution traces
│   └── events.jsonl                # Post-analysis events
│
├── docs/                           # Project documentation
│   ├── technical_design_document.md
│   ├── governance_report.md
│   ├── testing_evaluation_report.md
│   ├── deployment_guide.md
│   ├── architecture_diagram.md
│   └── presentation_deck.md
│
├── requirements.txt
└── README.md
```

---

## 4. Configuration

### 4.1 Environment Variables (Optional)

No environment variables are required for the base deployment.
For production integration with real credit bureaus, set:

```bash
# Credit Bureau API (not used in mock mode)
export CIBIL_API_KEY="your-api-key-here"
export CIBIL_API_URL="https://api.cibil.com/v2"

# Banking Data Warehouse
export BDW_DB_HOST="your-db-host"
export BDW_DB_PORT="5432"
```

### 4.2 Streamlit Configuration

Create `.streamlit/config.toml` for custom settings:

```toml
[server]
port = 8501
headless = true
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1e3a5f"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

---

## 5. Docker Deployment (Production)

### 5.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", \
  "--server.port=8501", \
  "--server.address=0.0.0.0", \
  "--server.headless=true"]
```

### 5.2 Build and Run

```bash
# Build the image
docker build -t credit-risk-agent:1.0.0 .

# Run the container
docker run -p 8501:8501 credit-risk-agent:1.0.0

# Run with volume for persistent logs
docker run -p 8501:8501 \
  -v $(pwd)/logs:/app/logs \
  credit-risk-agent:1.0.0
```

---

## 6. Cloud Deployment (AWS / GCP / Azure)

### 6.1 AWS ECS (Fargate)

```yaml
# task-definition.json (key parts)
{
  "containerDefinitions": [{
    "name": "credit-risk-agent",
    "image": "your-ecr-repo/credit-risk-agent:1.0.0",
    "portMappings": [{"containerPort": 8501}],
    "memory": 512,
    "cpu": 256
  }]
}
```

### 6.2 Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy credit-risk-agent \
  --image gcr.io/PROJECT_ID/credit-risk-agent:1.0.0 \
  --port 8501 \
  --memory 512Mi \
  --platform managed \
  --allow-unauthenticated
```

### 6.3 Streamlit Community Cloud (Quickest)

1. Push code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file as `app.py`
5. Click Deploy

---

## 7. Running Tests in CI/CD

```yaml
# .github/workflows/test.yml
name: Credit Risk Agent Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short
```

---

## 8. Monitoring in Production

### 8.1 Log Files
- `logs/audit_log.jsonl` – All credit decisions (retain 7 years)
- `logs/traces.jsonl` – Agent execution traces
- `logs/events.jsonl` – Post-analysis events and alerts

### 8.2 Alerting
Configure alerts when `events.jsonl` contains `HIGH_RISK_FLAG` or `POLICY_VIOLATION` entries.

### 8.3 Health Check
The app exposes Streamlit's built-in health endpoint at `/_stcore/health`.

---

## 9. Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError: No module named 'streamlit'` | Run `pip install -r requirements.txt` |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| Tests fail with import errors | Ensure you're in the `credit_risk_agent/` directory |
| Logs directory permission error | `mkdir -p logs && chmod 755 logs` |
| App opens to blank page | Hard-refresh browser (Ctrl+Shift+R) |
