#!/usr/bin/env python3
"""
Stripe Billing MCP Server
==========================
Manage Stripe billing operations from AI agents. Create customers, subscriptions,
checkout sessions, search customers, list invoices, and get revenue metrics.

Install: pip install mcp stripe
Run:     STRIPE_SECRET_KEY=sk_... python server.py
"""


import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP


FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None


# ---------------------------------------------------------------------------
# Stripe client setup
# ---------------------------------------------------------------------------
_stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")

try:
    import stripe
except ImportError:
    stripe = None
if _stripe_key and stripe is not None:
    stripe.api_key = _stripe_key

# Safety: never expose the key — only show last 4 chars
_masked_key = f"sk_...{_stripe_key[-4:]}"

# ---------------------------------------------------------------------------
# Rate limiting — destructive operations only
# ---------------------------------------------------------------------------
DESTRUCTIVE_DAILY_LIMIT = 10
_usage: dict[str, list[datetime]] = defaultdict(list)


def _check_destructive_limit(operation: str, caller: str = "anonymous") -> Optional[str]:
    """Rate limit create/cancel operations. Read operations are unlimited."""
    key = f"{caller}:{operation}"
    now = datetime.now()
    cutoff = now - timedelta(days=1)
    _usage[key] = [t for t in _usage[key] if t > cutoff]
    if len(_usage[key]) >= DESTRUCTIVE_DAILY_LIMIT:
        return (
            f"Free tier limit reached ({DESTRUCTIVE_DAILY_LIMIT}/day for {operation}). "
            f"Upgrade to Pro for unlimited: https://mcpize.com/stripe-billing-mcp/pro"
        )
    _usage[key].append(now)
    return None


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP("stripe-billing", instructions="MEOK AI Labs MCP Server")


@mcp.tool()
def create_customer(
    name: str,
    email: str,
    metadata: Optional[dict] = None, api_key: str = "") -> dict:
    """Create a new Stripe customer.

    Args:
        name: Customer full name
        email: Customer email address
        metadata: Optional key-value metadata (e.g. {"plan": "pro", "source": "website"})
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    err = _check_destructive_limit("create_customer")
    if err:
        return {"error": err}

    try:
        params = {"name": name, "email": email}
        if metadata:
            params["metadata"] = metadata
        customer = stripe.Customer.create(**params)
        return {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "created": customer.created,
            "metadata": dict(customer.metadata) if customer.metadata else {},
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def search_customers(
    query: str,
    limit: int = 10, api_key: str = "") -> dict:
    """Search Stripe customers by email or name.

    Args:
        query: Email address or name to search for
        limit: Max results to return (default 10, max 100)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    try:
        limit = min(max(limit, 1), 100)
        # Stripe Search API uses a query language
        # Try email exact match first, fall back to name
        if "@" in query:
            search_query = f'email:"{query}"'
        else:
            search_query = f'name~"{query}"'

        result = stripe.Customer.search(query=search_query, limit=limit)
        customers = []
        for c in result.data:
            customers.append({
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "created": c.created,
                "metadata": dict(c.metadata) if c.metadata else {},
            })
        return {"customers": customers, "count": len(customers), "query": query}
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def create_subscription(
    customer_id: str,
    price_id: str,
    trial_days: Optional[int] = None, api_key: str = "") -> dict:
    """Subscribe a customer to a price/plan.

    Args:
        customer_id: Stripe customer ID (cus_...)
        price_id: Stripe price ID (price_...)
        trial_days: Optional trial period in days
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    err = _check_destructive_limit("create_subscription")
    if err:
        return {"error": err}

    try:
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
        }
        if trial_days and trial_days > 0:
            params["trial_period_days"] = trial_days

        sub = stripe.Subscription.create(**params)
        return {
            "id": sub.id,
            "status": sub.status,
            "customer": sub.customer,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "trial_end": sub.trial_end,
            "items": [
                {
                    "price_id": item.price.id,
                    "product_id": item.price.product,
                    "amount": item.price.unit_amount,
                    "currency": item.price.currency,
                    "interval": item.price.recurring.interval if item.price.recurring else None,
                }
                for item in sub["items"]["data"]
            ],
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def cancel_subscription(
    subscription_id: str,
    at_period_end: bool = True,
    prorate: bool = True, api_key: str = "") -> dict:
    """Cancel a Stripe subscription.

    Args:
        subscription_id: Stripe subscription ID (sub_...)
        at_period_end: If True, cancel at end of billing period (default). If False, cancel immediately.
        prorate: Whether to prorate the final invoice (default True)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    err = _check_destructive_limit("cancel_subscription")
    if err:
        return {"error": err}

    try:
        if at_period_end:
            sub = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
                proration_behavior="create_prorations" if prorate else "none")
        else:
            sub = stripe.Subscription.cancel(
                subscription_id,
                proration_behavior="create_prorations" if prorate else "none")
        return {
            "id": sub.id,
            "status": sub.status,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "canceled_at": sub.canceled_at,
            "current_period_end": sub.current_period_end,
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def list_invoices(
    customer_id: str,
    limit: int = 10,
    status: Optional[str] = None, api_key: str = "") -> dict:
    """List recent invoices for a customer.

    Args:
        customer_id: Stripe customer ID (cus_...)
        limit: Number of invoices to return (default 10, max 100)
        status: Filter by status: draft, open, paid, uncollectible, void (optional)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    try:
        limit = min(max(limit, 1), 100)
        params = {"customer": customer_id, "limit": limit}
        if status:
            params["status"] = status

        invoices = stripe.Invoice.list(**params)
        results = []
        for inv in invoices.data:
            results.append({
                "id": inv.id,
                "number": inv.number,
                "status": inv.status,
                "amount_due": inv.amount_due,
                "amount_paid": inv.amount_paid,
                "currency": inv.currency,
                "created": inv.created,
                "due_date": inv.due_date,
                "hosted_invoice_url": inv.hosted_invoice_url,
                "pdf": inv.invoice_pdf,
            })
        return {
            "invoices": results,
            "count": len(results),
            "customer_id": customer_id,
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def create_checkout_session(
    price_id: str,
    success_url: str = "https://example.com/success",
    cancel_url: str = "https://example.com/cancel",
    mode: str = "subscription",
    customer_email: Optional[str] = None, api_key: str = "") -> dict:
    """Generate a Stripe Checkout URL for a price.

    Args:
        price_id: Stripe price ID (price_...)
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if customer cancels
        mode: Checkout mode — "subscription" or "payment" (one-time)
        customer_email: Pre-fill the customer's email in checkout
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    err = _check_destructive_limit("create_checkout")
    if err:
        return {"error": err}

    try:
        params = {
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if customer_email:
            params["customer_email"] = customer_email

        session = stripe.checkout.Session.create(**params)
        return {
            "id": session.id,
            "url": session.url,
            "mode": session.mode,
            "status": session.status,
            "expires_at": session.expires_at,
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def get_revenue_metrics(api_key: str = "") -> dict:
    """Calculate MRR, ARR, churn rate, and LTV from live Stripe data.

    Fetches active/canceled subscriptions and computes:
    - MRR (Monthly Recurring Revenue)
    - ARR (Annual Recurring Revenue)
    - Churn rate (cancellations in last 30 days / total active)
    - Average revenue per customer
    - Estimated LTV
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    try:
        # Get active subscriptions for MRR
        active_subs = stripe.Subscription.list(status="active", limit=100)
        mrr_cents = 0
        active_count = 0
        for sub in active_subs.auto_paging_iter():
            active_count += 1
            for item in sub["items"]["data"]:
                amount = item["price"]["unit_amount"] or 0
                interval = item["price"].get("recurring", {}).get("interval", "month")
                if interval == "year":
                    mrr_cents += amount / 12
                elif interval == "month":
                    mrr_cents += amount
                elif interval == "week":
                    mrr_cents += amount * 4.33
                elif interval == "day":
                    mrr_cents += amount * 30

        # Get recently canceled subscriptions (last 30 days) for churn
        thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
        canceled_subs = stripe.Subscription.list(
            status="canceled",
            created={"gte": thirty_days_ago},
            limit=100)
        canceled_count = len(canceled_subs.data)

        # Compute metrics
        mrr = mrr_cents / 100  # Convert cents to dollars
        arr = mrr * 12
        total_for_churn = active_count + canceled_count
        churn_rate = (canceled_count / total_for_churn * 100) if total_for_churn > 0 else 0
        avg_revenue = mrr / active_count if active_count > 0 else 0
        # LTV = ARPU / monthly churn rate
        monthly_churn = churn_rate / 100
        ltv = (avg_revenue / monthly_churn) if monthly_churn > 0 else avg_revenue * 24  # Default 24mo if no churn

        return {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "currency": "usd",
            "active_subscriptions": active_count,
            "canceled_last_30d": canceled_count,
            "churn_rate_pct": round(churn_rate, 2),
            "avg_revenue_per_customer": round(avg_revenue, 2),
            "estimated_ltv": round(ltv, 2),
            "note": "Amounts in USD. MRR calculated from all active subscriptions.",
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


@mcp.tool()
def get_balance(api_key: str = "") -> dict:
    """Get current Stripe account balance and recent payouts.

    Returns available and pending balances plus the last 5 payouts.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    try:
        balance = stripe.Balance.retrieve()
        available = [
            {"amount": b.amount / 100, "currency": b.currency}
            for b in balance.available
        ]
        pending = [
            {"amount": b.amount / 100, "currency": b.currency}
            for b in balance.pending
        ]

        # Recent payouts
        payouts = stripe.Payout.list(limit=5)
        payout_list = [
            {
                "id": p.id,
                "amount": p.amount / 100,
                "currency": p.currency,
                "status": p.status,
                "arrival_date": p.arrival_date,
                "created": p.created,
            }
            for p in payouts.data
        ]

        return {
            "available": available,
            "pending": pending,
            "recent_payouts": payout_list,
            "api_key": _masked_key,
        }
    except stripe.error.StripeError as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
