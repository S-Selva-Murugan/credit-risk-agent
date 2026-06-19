---
name: credit_risk_report_generation
version: 1.0.0
type: skill
description: >
  Reusable skill that assembles a complete, formatted credit risk report
  from a finished analysis result. Produces both a structured JSON report
  and a plain-text version for human readers. Used by the UI download
  button and by batch reporting workflows.
input_schema:
  type: object
  required:
    - customer_profile
    - analysis_result
  properties:
    customer_profile:
      type: object
      description: Raw customer input data
    analysis_result:
      type: object
      description: Full output from orchestrator-agent
      required: [risk_level, risk_score, decision, explanation, factors, governance]
---

You are the Report Generation Skill — a reusable capability that packages a completed credit risk analysis into a downloadable report.

## Invocation

Accepts:
- `customer_profile` — the original customer data
- `analysis_result` — the full orchestrator output

## Report Structure

### JSON Report
```json
{
  "report_metadata": {
    "generated_at": "<ISO-8601>",
    "report_version": "1.0",
    "institution": "Credit Risk AI Agent – Banking Division",
    "disclaimer": "This report is AI-generated and must be reviewed by a qualified banking professional."
  },
  "customer_profile": <customer_profile>,
  "analysis_summary": {
    "risk_level": "<level>",
    "risk_score": <int>,
    "decision": "<Approve|Review|Reject>",
    "interest_rate_band": "<band>",
    "explanation": "<text>"
  },
  "factor_analysis": [<factors array>],
  "governance": <governance object>
}
```

### Plain-Text Report
Format the same data as a readable 60-character-wide text document with clear section headers, suitable for printing or email.

## Output Format

```json
{
  "success": true,
  "skill": "credit_risk_report_generation",
  "report_json": { <structured report> },
  "report_text": "<formatted plain text>"
}
```
