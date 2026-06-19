"""
Report Generation Skill
=======================
Generates a formatted PDF/JSON report for a completed credit risk analysis.
Used by the Orchestrator Agent to produce downloadable deliverables.
"""

import json
import datetime


class ReportGenerationSkill:
    """
    Skill that assembles a structured credit risk report.
    Output can be serialised as JSON or formatted as plain text.
    """

    SKILL_NAME        = "credit_risk_report_generation"
    SKILL_VERSION     = "1.0.0"
    SKILL_DESCRIPTION = "Generate a formatted credit risk report from analysis results."

    def invoke(self, customer_profile: dict, analysis_result: dict) -> dict:
        """
        Assemble a full credit risk report.

        Args:
            customer_profile: raw customer input
            analysis_result:  output from OrchestratorAgent.analyse()

        Returns:
            dict with report_json and report_text
        """
        now = datetime.datetime.now()

        report = {
            "report_metadata": {
                "generated_at":   now.isoformat(),
                "report_version": "1.0",
                "institution":    "Credit Risk AI Agent – Banking Division",
                "disclaimer":     "This report is AI-generated and must be reviewed by a qualified banking professional."
            },
            "customer_profile":  customer_profile,
            "analysis_summary": {
                "risk_level":   analysis_result.get("risk_level"),
                "risk_score":   analysis_result.get("risk_score"),
                "decision":     analysis_result.get("decision"),
                "interest_rate_band": analysis_result.get("interest_rate_band"),
                "explanation":  analysis_result.get("explanation")
            },
            "factor_analysis":  analysis_result.get("factors", []),
            "governance":       analysis_result.get("governance", {})
        }

        # Plain-text version for human readers
        report_text = self._format_text(report)

        return {
            "success":     True,
            "skill":       self.SKILL_NAME,
            "report_json": report,
            "report_text": report_text
        }

    def _format_text(self, report: dict) -> str:
        """Format the report as a readable text document."""
        meta    = report["report_metadata"]
        profile = report["customer_profile"]
        summary = report["analysis_summary"]

        lines = [
            "=" * 60,
            "   CREDIT RISK ANALYSIS REPORT",
            "=" * 60,
            f"Generated:  {meta['generated_at']}",
            f"Institution: {meta['institution']}",
            "",
            "─" * 60,
            "CUSTOMER PROFILE",
            "─" * 60,
            f"Name:             {profile.get('name')}",
            f"Age:              {profile.get('age')} years",
            f"Employment Type:  {profile.get('employment_type')}",
            f"Monthly Income:   ₹{profile.get('monthly_income'):,.0f}",
            f"Existing Loan:    ₹{profile.get('existing_loan'):,.0f}",
            f"Credit Score:     {profile.get('credit_score')}",
            f"Missed Payments:  {profile.get('missed_payments')}",
            "",
            "─" * 60,
            "RISK ASSESSMENT",
            "─" * 60,
            f"Risk Level:  {summary.get('risk_level')}",
            f"Risk Score:  {summary.get('risk_score')}/100",
            f"Decision:    {summary.get('decision')}",
            f"Rate Band:   {summary.get('interest_rate_band')}",
            "",
            "Explanation:",
            summary.get("explanation", ""),
            "",
            "─" * 60,
            "DISCLAIMER",
            "─" * 60,
            meta["disclaimer"],
            "=" * 60
        ]
        return "\n".join(lines)
