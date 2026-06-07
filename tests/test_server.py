#!/usr/bin/env python3
import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
_shared_auth = os.path.expanduser("~/clawd/meok-labs-engine/shared")
if os.path.isdir(_shared_auth):
    sys.path.insert(0, _shared_auth)

_mock_stripe = MagicMock()
_mock_stripe.error.StripeError = type("StripeError", (Exception,), {})
_mock_stripe.Customer.create.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Customer.search.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Subscription.create.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Subscription.modify.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Subscription.cancel.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Invoice.list.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.checkout.Session.create.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Balance.retrieve.side_effect = _mock_stripe.error.StripeError("Stripe not configured")
_mock_stripe.Payout.list.side_effect = _mock_stripe.error.StripeError("Stripe not configured")

_patcher_mod = patch.dict("sys.modules", {"stripe": _mock_stripe})
_patcher_env = patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_mock_key_12345"})
_patcher_mod.start()
_patcher_env.start()
import server
_patcher_env.stop()
_patcher_mod.stop()


def test_server_module_imports():
    assert server is not None


def test_mcp_object_exists():
    assert hasattr(server, "mcp")


def test_tools_registered():
    expected = [
        "create_customer",
        "search_customers",
        "create_subscription",
        "cancel_subscription",
        "list_invoices",
        "create_checkout_session",
        "get_revenue_metrics",
        "get_balance",
    ]
    for name in expected:
        assert hasattr(server, name), f"Missing tool: {name}"
        assert callable(getattr(server, name))


def test_main_function():
    assert hasattr(server, "main")
    assert callable(server.main)


def test_create_customer_returns_error():
    result = server.create_customer(name="Test User", email="test@example.com")
    assert isinstance(result, dict)
    assert "error" in result


def test_search_customers_returns_error():
    result = server.search_customers(query="test@example.com")
    assert isinstance(result, dict)
    assert "error" in result


def test_create_subscription_returns_error():
    result = server.create_subscription(customer_id="cus_mock", price_id="price_mock")
    assert isinstance(result, dict)
    assert "error" in result


def test_cancel_subscription_returns_error():
    result = server.cancel_subscription(subscription_id="sub_mock")
    assert isinstance(result, dict)
    assert "error" in result


def test_list_invoices_returns_error():
    result = server.list_invoices(customer_id="cus_mock")
    assert isinstance(result, dict)
    assert "error" in result


def test_create_checkout_session_returns_error():
    result = server.create_checkout_session(price_id="price_mock")
    assert isinstance(result, dict)
    assert "error" in result


def test_get_revenue_metrics_returns_error():
    result = server.get_revenue_metrics()
    assert isinstance(result, dict)
    assert "error" in result


def test_get_balance_returns_error():
    result = server.get_balance()
    assert isinstance(result, dict)
    assert "error" in result
