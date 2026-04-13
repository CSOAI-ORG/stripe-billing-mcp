# Stripe Billing MCP Server

> **By [MEOK AI Labs](https://meok.ai)** — Sovereign AI tools for everyone.

Manage Stripe customers, subscriptions, invoices, checkout sessions, and revenue metrics through MCP. Give any AI assistant full billing superpowers.

[![MCPize](https://img.shields.io/badge/MCPize-Listed-blue)](https://mcpize.com/mcp/stripe-billing)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-255+_servers-purple)](https://meok.ai)

## Tools

| Tool | Description |
|------|-------------|
| `create_customer` | Create a new Stripe customer |
| `search_customers` | Search customers by email or name |
| `create_subscription` | Subscribe a customer to a price/plan |
| `cancel_subscription` | Cancel a subscription |
| `list_invoices` | List recent invoices for a customer |
| `create_checkout_session` | Generate a Stripe Checkout URL |
| `get_revenue_metrics` | Calculate MRR, ARR, churn rate, and LTV |
| `get_balance` | Get current account balance and recent payouts |

## Quick Start

```bash
pip install mcp
git clone https://github.com/CSOAI-ORG/stripe-billing-mcp.git
cd stripe-billing-mcp
python server.py
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "stripe-billing": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/stripe-billing-mcp"
    }
  }
}
```

## Pricing

| Plan | Price | Requests |
|------|-------|----------|
| Free | $0/mo | 10 writes/day, unlimited reads |
| Pro | $12/mo | Unlimited |

[Get on MCPize](https://mcpize.com/mcp/stripe-billing)

## Part of MEOK AI Labs

This is one of 255+ MCP servers by MEOK AI Labs. Browse all at [meok.ai](https://meok.ai) or [GitHub](https://github.com/CSOAI-ORG).

---
**MEOK AI Labs** | [meok.ai](https://meok.ai) | nicholas@meok.ai | United Kingdom
