# Stripe Billing MCP Server

> Built by [MEOK AI Labs](https://meok.ai) -- Stripe billing operations for AI agents.

Manage customers, subscriptions, invoices, checkout sessions, and revenue metrics through the Model Context Protocol. Drop this into any AI assistant that speaks MCP and give it full billing superpowers.

## Tools

| Tool | Description | Rate Limited |
|------|-------------|:------------:|
| `create_customer` | Create a Stripe customer (name, email, metadata) | 10/day free |
| `search_customers` | Search customers by email or name | Unlimited |
| `create_subscription` | Subscribe a customer to a price ID with optional trial | 10/day free |
| `cancel_subscription` | Cancel a subscription (immediate or at period end, with proration) | 10/day free |
| `list_invoices` | List recent invoices for a customer, filter by status | Unlimited |
| `create_checkout_session` | Generate a Stripe Checkout URL for a price | 10/day free |
| `get_revenue_metrics` | Calculate MRR, ARR, churn rate, LTV from live data | Unlimited |
| `get_balance` | Account balance and recent payouts | Unlimited |

## Getting Your Stripe API Key

1. Go to [Stripe Dashboard > API Keys](https://dashboard.stripe.com/apikeys)
2. Copy your **Secret key** (starts with `sk_test_` for test mode or `sk_live_` for production)
3. For testing, use test mode keys -- they won't charge real cards

> **Security:** The server never exposes your full API key. Only the last 4 characters are shown in balance responses.

## Installation

```bash
pip install mcp stripe
```

Or install from source:

```bash
git clone https://github.com/meok-ai/stripe-billing-mcp.git
cd stripe-billing-mcp
pip install -e .
```

## Usage

### Run the server

```bash
STRIPE_SECRET_KEY=sk_test_... python server.py
```

### Claude Desktop config

```json
{
  "mcpServers": {
    "stripe-billing": {
      "command": "python",
      "args": ["/path/to/stripe-billing-mcp/server.py"],
      "env": {
        "STRIPE_SECRET_KEY": "sk_test_..."
      }
    }
  }
}
```

### Claude Code config

```json
{
  "mcpServers": {
    "stripe-billing": {
      "command": "python",
      "args": ["/path/to/stripe-billing-mcp/server.py"],
      "env": {
        "STRIPE_SECRET_KEY": "sk_test_..."
      }
    }
  }
}
```

## Examples

**Create a customer:**
```
Tool: create_customer
Input: {"name": "Jane Smith", "email": "jane@example.com", "metadata": {"plan": "pro"}}
Output: {"id": "cus_abc123", "name": "Jane Smith", "email": "jane@example.com", ...}
```

**Search customers:**
```
Tool: search_customers
Input: {"query": "jane@example.com"}
Output: {"customers": [...], "count": 1, "query": "jane@example.com"}
```

**Create a subscription:**
```
Tool: create_subscription
Input: {"customer_id": "cus_abc123", "price_id": "price_xyz789", "trial_days": 14}
Output: {"id": "sub_def456", "status": "trialing", ...}
```

**Get revenue metrics:**
```
Tool: get_revenue_metrics
Input: {}
Output: {"mrr": 4250.00, "arr": 51000.00, "churn_rate_pct": 3.2, "estimated_ltv": 1328.12, ...}
```

**Generate checkout link:**
```
Tool: create_checkout_session
Input: {"price_id": "price_xyz789", "success_url": "https://myapp.com/thanks", "customer_email": "jane@example.com"}
Output: {"url": "https://checkout.stripe.com/c/pay/...", ...}
```

**Check balance:**
```
Tool: get_balance
Input: {}
Output: {"available": [{"amount": 1234.56, "currency": "usd"}], "pending": [...], "recent_payouts": [...]}
```

## Pricing

| Tier | Limit | Price |
|------|-------|-------|
| Free | 10 write ops/day, unlimited reads | $0 |
| Pro | Unlimited everything | $9/mo |
| Enterprise | Custom limits + webhook support | Contact us |

## Safety

- The Stripe secret key is **never** exposed in tool responses
- Destructive operations (create, cancel) are rate limited to 10/day on the free tier
- Read operations (search, list, metrics, balance) are always unlimited
- Use `sk_test_` keys during development -- they never touch real money

## License

MIT
