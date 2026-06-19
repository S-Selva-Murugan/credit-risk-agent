"""
Credit Bureau MCP Server (Mock)
================================
Model Context Protocol (MCP) server that simulates a connection to an
external Credit Bureau data source (e.g., CIBIL, Experian, CRIF).

In production this would make authenticated API calls to the bureau.
Here we return realistic mock data to demonstrate the MCP integration pattern.

MCP Tool Definitions:
    - get_credit_report    : Fetch detailed credit report for a customer
    - get_payment_history  : Fetch 24-month payment history
    - get_existing_loans   : List all active loans from bureau records
    - verify_identity      : Confirm identity against bureau database
"""

import json
import random
import datetime
from typing import Optional


class CreditBureauMCP:
    """
    MCP server that provides credit bureau data to the agent system.
    Implements the MCP tool protocol with a standardised invoke() method.
    """

    SERVER_NAME    = "credit-bureau-mcp"
    SERVER_VERSION = "1.0.0"
    PROVIDER       = "Mock CIBIL Bureau"

    # ── MCP Tool Definitions ──────────────────────────────────────────────────
    TOOLS = [
        {
            "name":        "get_credit_report",
            "description": "Fetch a detailed credit report for a customer by name and age.",
            "input_schema": {
                "type": "object",
                "required": ["customer_name", "age"],
                "properties": {
                    "customer_name": {"type": "string"},
                    "age":           {"type": "integer"}
                }
            }
        },
        {
            "name":        "get_payment_history",
            "description": "Retrieve the 24-month EMI payment history for a customer.",
            "input_schema": {
                "type": "object",
                "required": ["customer_name"],
                "properties": {
                    "customer_name": {"type": "string"},
                    "months":        {"type": "integer", "default": 24}
                }
            }
        },
        {
            "name":        "get_existing_loans",
            "description": "List all active loans registered under the customer.",
            "input_schema": {
                "type": "object",
                "required": ["customer_name"],
                "properties": {
                    "customer_name": {"type": "string"}
                }
            }
        },
        {
            "name":        "verify_identity",
            "description": "Verify customer identity against bureau records.",
            "input_schema": {
                "type": "object",
                "required": ["customer_name", "age"],
                "properties": {
                    "customer_name": {"type": "string"},
                    "age":           {"type": "integer"}
                }
            }
        }
    ]

    def __init__(self):
        self._call_count = 0

    def invoke(self, tool_name: str, arguments: dict) -> dict:
        """
        Standard MCP tool invocation interface.

        Args:
            tool_name:  Name of the MCP tool to invoke
            arguments:  Tool input arguments

        Returns:
            dict with 'content' key containing the tool result
        """
        self._call_count += 1

        tool_methods = {
            "get_credit_report":  self._get_credit_report,
            "get_payment_history": self._get_payment_history,
            "get_existing_loans": self._get_existing_loans,
            "verify_identity":    self._verify_identity,
        }

        handler = tool_methods.get(tool_name)
        if not handler:
            return {
                "content": [{"type": "text", "text": json.dumps({
                    "error": f"Unknown tool: {tool_name}"
                })}],
                "isError": True
            }

        result = handler(**arguments)
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "isError": False,
            "server":  self.SERVER_NAME,
            "tool":    tool_name,
            "call_id": self._call_count
        }

    def list_tools(self) -> list:
        """Return all available MCP tool definitions."""
        return self.TOOLS

    # ── Mock Tool Implementations ─────────────────────────────────────────────

    def _get_credit_report(self, customer_name: str, age: int) -> dict:
        """Mock credit report from CIBIL bureau."""
        seed = sum(ord(c) for c in customer_name) + age
        rng = random.Random(seed)

        return {
            "source":         self.PROVIDER,
            "customer_name":  customer_name,
            "report_date":    datetime.date.today().isoformat(),
            "cibil_score":    rng.randint(550, 850),
            "credit_accounts": rng.randint(1, 8),
            "active_loans":   rng.randint(0, 4),
            "delinquent_accounts": rng.randint(0, 2),
            "oldest_account_years": rng.randint(1, 15),
            "inquiries_last_6_months": rng.randint(0, 5)
        }

    def _get_payment_history(self, customer_name: str, months: int = 24) -> dict:
        """Mock 24-month payment history."""
        seed = sum(ord(c) for c in customer_name)
        rng = random.Random(seed)

        history = []
        for m in range(months):
            date = (datetime.date.today() - datetime.timedelta(days=30 * m)).isoformat()
            status = rng.choices(
                ["On-Time", "Late", "Missed"],
                weights=[80, 15, 5]
            )[0]
            history.append({"month": date, "status": status})

        missed = sum(1 for h in history[:12] if h["status"] == "Missed")
        return {
            "customer_name":  customer_name,
            "period_months":  months,
            "payment_history": history,
            "missed_last_12_months": missed,
            "on_time_percentage": round(
                sum(1 for h in history if h["status"] == "On-Time") / months * 100, 1
            )
        }

    def _get_existing_loans(self, customer_name: str) -> dict:
        """Mock active loan list."""
        seed = sum(ord(c) for c in customer_name) * 3
        rng = random.Random(seed)

        loan_types = ["Home Loan", "Car Loan", "Personal Loan", "Credit Card", "Education Loan"]
        num_loans = rng.randint(0, 3)
        loans = []
        for i in range(num_loans):
            loans.append({
                "loan_id":      f"LN{rng.randint(10000, 99999)}",
                "type":         rng.choice(loan_types),
                "outstanding":  rng.randint(50_000, 2_000_000),
                "emi":          rng.randint(2_000, 50_000),
                "months_remaining": rng.randint(1, 120)
            })

        return {
            "customer_name": customer_name,
            "total_loans":   num_loans,
            "loans":         loans,
            "total_outstanding": sum(l["outstanding"] for l in loans)
        }

    def _verify_identity(self, customer_name: str, age: int) -> dict:
        """Mock identity verification."""
        verified = len(customer_name) > 3 and 18 <= age <= 80
        return {
            "customer_name": customer_name,
            "verified":      verified,
            "verification_source": self.PROVIDER,
            "confidence":    0.95 if verified else 0.0
        }
