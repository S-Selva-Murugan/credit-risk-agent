"""
Test Suite – MCP Servers
==========================
Tests for the Credit Bureau MCP and Banking Data MCP servers.

Run with: pytest tests/test_mcp.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from mcp.credit_bureau_mcp import CreditBureauMCP
from mcp.banking_data_mcp import BankingDataMCP


@pytest.fixture
def bureau_mcp():
    return CreditBureauMCP()


@pytest.fixture
def banking_mcp():
    return BankingDataMCP()


class TestCreditBureauMCP:

    def test_list_tools_returns_list(self, bureau_mcp):
        tools = bureau_mcp.list_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 4

    def test_get_credit_report_success(self, bureau_mcp):
        result = bureau_mcp.invoke("get_credit_report", {"customer_name": "Alice", "age": 34})
        assert result["isError"] is False

    def test_get_payment_history_success(self, bureau_mcp):
        result = bureau_mcp.invoke("get_payment_history", {"customer_name": "Alice"})
        assert result["isError"] is False

    def test_get_existing_loans_success(self, bureau_mcp):
        result = bureau_mcp.invoke("get_existing_loans", {"customer_name": "Alice"})
        assert result["isError"] is False

    def test_verify_identity_success(self, bureau_mcp):
        result = bureau_mcp.invoke("verify_identity", {"customer_name": "Alice", "age": 34})
        assert result["isError"] is False

    def test_unknown_tool_returns_error(self, bureau_mcp):
        result = bureau_mcp.invoke("nonexistent_tool", {})
        assert result["isError"] is True

    def test_deterministic_for_same_name(self, bureau_mcp):
        r1 = bureau_mcp.invoke("get_credit_report", {"customer_name": "Bob", "age": 30})
        r2 = bureau_mcp.invoke("get_credit_report", {"customer_name": "Bob", "age": 30})
        import json
        d1 = json.loads(r1["content"][0]["text"])
        d2 = json.loads(r2["content"][0]["text"])
        assert d1["cibil_score"] == d2["cibil_score"]


class TestBankingDataMCP:

    def test_list_tools_returns_list(self, banking_mcp):
        tools = banking_mcp.list_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 4

    def test_get_account_summary_success(self, banking_mcp):
        result = banking_mcp.invoke("get_account_summary", {"customer_name": "Alice"})
        assert result["isError"] is False

    def test_get_transaction_history_success(self, banking_mcp):
        result = banking_mcp.invoke("get_transaction_history", {"customer_name": "Alice"})
        assert result["isError"] is False

    def test_get_relationship_score_success(self, banking_mcp):
        result = banking_mcp.invoke("get_relationship_score", {"customer_name": "Alice"})
        assert result["isError"] is False

    def test_get_market_rates_success(self, banking_mcp):
        result = banking_mcp.invoke("get_market_rates", {})
        assert result["isError"] is False

    def test_market_rates_has_repo_rate(self, banking_mcp):
        import json
        result = banking_mcp.invoke("get_market_rates", {})
        data = json.loads(result["content"][0]["text"])
        assert "repo_rate" in data

    def test_unknown_tool_returns_error(self, banking_mcp):
        result = banking_mcp.invoke("bad_tool", {})
        assert result["isError"] is True
