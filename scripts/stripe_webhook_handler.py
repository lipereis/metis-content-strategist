#!/usr/bin/env python3
"""
Stripe Webhook Handler for License Sync
Run this on your server or as a serverless function to sync Stripe purchases to GitHub Gist.

Usage:
    python stripe_webhook_handler.py

Requirements:
    pip install stripe flask pyyaml requests

Environment Variables:
    STRIPE_SECRET_KEY=sk_live_...
    STRIPE_WEBHOOK_SECRET=whsec_...
    GITHUB_TOKEN=ghp_...
    LICENSE_GIST_ID=abc123...
"""

import os
import json
import hmac
import hashlib
from datetime import datetime
from flask import Flask, request, abort
import requests
import yaml

app = Flask(__name__)

# Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
LICENSE_GIST_ID = os.getenv("LICENSE_GIST_ID")

# Plan configuration
PLANS = {
    "pro": {"max_runs": 1000, "expires_days": 365},
    "agency": {"max_runs": -1, "expires_days": 365},
    "enterprise": {"max_runs": -1, "expires_days": 730},
}

def generate_license_key(email: str, plan: str) -> str:
    """Generate a unique license key."""
    prefix = {"pro": "CS-PRO", "agency": "CS-AGENCY", "enterprise": "CS-ENT"}[plan]
    timestamp = int(datetime.now().timestamp())
    hash_input = f"{email}{plan}{timestamp}"
    suffix = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()
    return f"{prefix}-{timestamp}-{suffix}"

def calculate_expiry(plan: str) -> str:
    """Calculate expiration date based on plan."""
    days = PLANS.get(plan, {}).get("expires_days", 365)
    from datetime import timedelta
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

def get_max_runs(plan: str) -> int:
    """Get max runs for plan."""
    return PLANS.get(plan, {}).get("max_runs", 1000)

def fetch_gist() -> dict:
    """Fetch current license database from Gist."""
    url = f"https://api.github.com/gists/{LICENSE_GIST_ID}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    gist = resp.json()
    content = gist["files"]["licenses.json"]["content"]
    return json.loads(content)

def update_gist(data: dict) -> bool:
    """Update Gist with new license data."""
    url = f"https://api.github.com/gists/{LICENSE_GIST_ID}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            "licenses.json": {
                "content": json.dumps(data, indent=2)
            }
        }
    }
    resp = requests.patch(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    return True

def add_license(email: str, plan: str) -> str:
    """Add a new license to the Gist."""
    # Load current
    data = fetch_gist()
    
    # Generate key
    key = generate_license_key(email, plan)
    expires = calculate_expiry(plan)
    max_runs = get_max_runs(plan)
    
    # Add to licenses
    data["licenses"][key] = {
        "email": email,
        "plan": plan,
        "expires": expires,
        "max_runs": max_runs
    }
    
    # Update Gist
    update_gist(data)
    
    return key

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        abort(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        abort(400, "Invalid signature")
    
    # Handle successful payment
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Extract customer info
        email = session.get("customer_details", {}).get("email")
        metadata = session.get("metadata", {})
        plan = metadata.get("plan", "pro")
        
        if not email:
            print("No email in session")
            return "", 200
        
        # Check if already has license (idempotency)
        # Could check existing licenses here
        
        # Add license
        try:
            license_key = add_license(email, plan)
            print(f"✅ License created: {license_key} for {email} ({plan})")
        except Exception as e:
            print(f"❌ Failed to add license: {e}")
            abort(500)
    
    return "", 200

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)