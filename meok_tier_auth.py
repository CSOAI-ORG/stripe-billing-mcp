"""
MEOK Tier Authentication — Connects Stripe subscriptions to MCP server access.
Drop this into any MCP server directory and import it.

Usage:
    from meok_tier_auth import check_tier_access

    @mcp.tool()
    def my_premium_tool(api_key: str = "", ...) -> str:
        tier = check_tier_access(api_key)
        if tier == "blocked":
            return json.dumps({"error": "Valid API key required. Get one at meok.ai/api-keys"})
        if tier == "free" and is_premium_feature:
            return json.dumps({"error": "Pro tier required. Upgrade at meok.ai/pricing"})
        # ... tool logic
"""

import os
import json
import hashlib
import time
from pathlib import Path

# API key → tier mapping file (populated by webhook or manual)
TIER_DB = Path.home() / ".meok-ai" / "tier_keys.json"
TIER_DB.parent.mkdir(parents=True, exist_ok=True)

# Cache to avoid file reads on every call
_cache = {}
_cache_time = 0

TIERS = {
    "free": {"daily_limit": 10, "tools": "basic", "priority": False},
    "pro": {"daily_limit": 5000, "tools": "all", "priority": False},
    "business": {"daily_limit": 50000, "tools": "all", "priority": True},
    "enterprise": {"daily_limit": -1, "tools": "all", "priority": True},  # unlimited
}

def _load_keys():
    global _cache, _cache_time
    if time.time() - _cache_time < 60:  # Cache for 60s
        return _cache
    if TIER_DB.exists():
        try:
            _cache = json.loads(TIER_DB.read_text())
            _cache_time = time.time()
        except:
            _cache = {}
    return _cache

def register_key(api_key: str, tier: str, customer_email: str = ""):
    """Register an API key with a tier (called by Stripe webhook handler)."""
    keys = _load_keys()
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    keys[key_hash] = {
        "tier": tier,
        "email": customer_email,
        "registered": time.time(),
        "calls_today": 0,
        "last_reset": time.strftime("%Y-%m-%d"),
    }
    TIER_DB.write_text(json.dumps(keys, indent=2))
    return True

def check_tier_access(api_key: str = "") -> str:
    """Check what tier an API key has access to. Returns: free/pro/business/enterprise/blocked."""
    # If no MEOK_API_KEY env var set, allow everything (dev mode)
    master_key = os.environ.get("MEOK_API_KEY", "")
    if not master_key and not api_key:
        return "free"  # No auth configured = free tier
    
    if not api_key:
        return "free"  # No key provided = free tier
    
    # Check master key (full access)
    if master_key and api_key == master_key:
        return "enterprise"
    
    # Check registered keys
    keys = _load_keys()
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    if key_hash in keys:
        entry = keys[key_hash]
        tier = entry.get("tier", "free")
        
        # Reset daily counter
        today = time.strftime("%Y-%m-%d")
        if entry.get("last_reset") != today:
            entry["calls_today"] = 0
            entry["last_reset"] = today
        
        # Check daily limit
        limit = TIERS.get(tier, TIERS["free"])["daily_limit"]
        if limit > 0 and entry["calls_today"] >= limit:
            return "blocked"
        
        entry["calls_today"] = entry.get("calls_today", 0) + 1
        # Save updated count (async would be better, but works)
        try:
            TIER_DB.write_text(json.dumps(keys, indent=2))
        except:
            pass
        
        return tier
    
    return "free"  # Unknown key = free tier

def get_tier_info(tier: str) -> dict:
    """Get tier capabilities."""
    return TIERS.get(tier, TIERS["free"])

# Stripe webhook handler template
STRIPE_WEBHOOK_TEMPLATE = """
# Add to your FastAPI/Flask app to handle Stripe subscription events:
#
# @app.post("/webhook/stripe")
# async def stripe_webhook(request):
#     event = stripe.Webhook.construct_event(...)
#     if event.type == "checkout.session.completed":
#         session = event.data.object
#         api_key = generate_api_key()  # Your key generation
#         tier = "pro" if session.amount_total < 50000 else "business" if session.amount_total < 100000 else "enterprise"
#         register_key(api_key, tier, session.customer_email)
#         # Email the API key to the customer
"""
