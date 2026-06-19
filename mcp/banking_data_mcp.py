"""
Banking Data MCP Server (Mock)
================================
Second MCP server that simulates an internal banking data warehouse.
Provides real-time account data, transaction history, and relationship info.

This demonstrates Multi-MCP Integration (bonus criterion).

MCP Tool Definitions:
    - get_account_summary    : Account balance and type overview
    - get_transaction_history: Recent transaction patterns
    - get_relationship_score : Customer relationship value score
    - get_market_rates       : Current interest rate benchmarks
"""

import json
import random
import datetime


class BankingDataMCP:
    """
    Internal banking data MCP server.
    Provides account-level and market data to complement bureau data.
    """

    SERVER_NAME    = "banking-data-mcp"
    SERVER_VERSION = "1.0.0"
    PROVIDER       = "Internal Banking Data Warehouse"

    TOOLS = [
        {
            "name":        "get_account_summary",
            "description": "Get customer account summary including balances and account types.",
            "input_schema": {
                "type": "object",
                "required": ["customer_name"],
                "properties": {
                    "customer_name": {"type": "string"}
                }
            }
        },
        {
            "name":        "get_transaction_history",
            "description": "Get the last 90 days of transaction data for risk pattern analysis.",
            "input_schema": {
                "type": "object",
                "required": ["customer_name"],
                "properties": {
                    "customer_name": {"type": "string"},
                    "days":          {"type": "integer", "default": 90}
                }
            }
        },
        {
            "name":        "get_relationship_score",
            "description": "Get the customer relationship value score (0-100).",
            "input_schema": {
                "type": "object",
                "required": ["customer_name"],
                "properties": {
                    "customer_name": {"type": "string"}
                }
            }
        },
        {
            "name":        "get_market_rates",
            "description": "Get current benchmark interest rates (RBI repo rate, MCLR).",
            "input_schema": {
                "type": "object",
                "properties": {}
            }
        }
    ]

    def __init__(self):
        self._call_count = 0

    def invoke(self, tool_name: str, arguments: dict) -> dict:
        """Standard MCP invocation interface."""
        self._call_count += 1

        methods = {
            "get_account_summary":     self._get_account_summary,
            "get_transaction_history": self._get_transaction_history,
            "get_relationship_score":  self._get_relationship_score,
            "get_market_rates":        self._get_market_rates,
        }

        handler = methods.get(tool_name)
        if not handler:
            return {"content": [{"type": "text", "text": json.dumps({"error": f"Unknown tool: {tool_name}"})}], "isError": True}

        result = handler(**arguments)
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "isError": False,
            "server":  self.SERVER_NAME,
            "tool":    tool_name,
            "call_id": self._call_count
        }

    def list_tools(self) -> list:
        return self.TOOLS

    # ── Mock Implementations ──────────────────────────────────────────────────

    def _get_account_summary(self, customer_name: str) -> dict:
        seed = sum(ord(c) for c in customer_name) * 7
        rng = random.Random(seed)
        return {
            "customer_name":    customer_name,
            "account_types":    rng.sample(["Savings", "Current", "FD", "RD", "Demat"], k=rng.randint(1, 3)),
            "savings_balance":  rng.randint(5_000, 500_000),
            "fd_balance":       rng.randint(0, 1_000_000),
            "avg_monthly_balance": rng.randint(10_000, 200_000),
            "account_vintage_years": rng.randint(1, 20)
        }

    def _get_transaction_history(self, customer_name: str, days: int = 90) -> dict:
        seed = sum(ord(c) for c in customer_name) * 11
        rng = random.Random(seed)
        num_txns = rng.randint(5, 50)
        categories = ["Salary", "EMI", "Utilities", "Shopping", "Food", "Transfer", "Investment"]
        transactions = [
            {
                "date":   (datetime.date.today() - datetime.timedelta(days=rng.randint(0, days))).isoformat(),
                "amount": rng.randint(100, 100_000),
                "type":   rng.choice(["Credit", "Debit"]),
                "category": rng.choice(categories)
            }
            for _ in range(num_txns)
        ]
        return {
            "customer_name":   customer_name,
            "period_days":     days,
            "total_credits":   sum(t["amount"] for t in transactions if t["type"] == "Credit"),
            "total_debits":    sum(t["amount"] for t in transactions if t["type"] == "Debit"),
            "transaction_count": num_txns,
            "transactions":    transactions[:5]  # Return sample only
        }

    def _get_relationship_score(self, customer_name: str) -> dict:
        seed = sum(ord(c) for c in customer_name) * 13
        rng = random.Random(seed)
        score = rng.randint(20, 95)
        return {
            "customer_name":      customer_name,
            "relationship_score": score,
            "tier":               "Gold" if score > 75 else ("Silver" if score > 50 else "Bronze"),
            "years_as_customer":  rng.randint(1, 25),
            "products_held":      rng.randint(1, 8)
        }

    def _get_market_rates(self) -> dict:
        return {
            "source":         "RBI (Mock Data)",
            "as_of":          datetime.date.today().isoformat(),
            "repo_rate":      6.50,
            "reverse_repo":   6.25,
            "mclr_1year":     8.75,
            "base_rate":      9.00,
            "prime_lending":  10.50

        }
