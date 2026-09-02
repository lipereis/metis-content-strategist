#!/usr/bin/env python3
"""
License Validator for Content Strategist Agent.

Validates license keys against a GitHub Gist license server.
Zero-cost, serverless license validation using GitHub Gist as database.

Usage:
    from scripts.license import check_license
    license_info = check_license()  # Exits if invalid
    
    # Or with custom key
    from scripts.license import validate_license
    lic = validate_license("YOUR_KEY")
    if not lic:
        print("Invalid license")
    else:
        print(f"Valid: {lic['plan']} until {lic['expires']}")
"""

import os
import sys
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


# =============================================================================
# CONFIGURATION — UPDATE THESE FOR YOUR DEPLOYMENT
# =============================================================================

# GitHub Gist raw URL containing license database
# Create a secret Gist at https://gist.github.com with this structure:
# {
#   "licenses": {
#     "KEY-123": {"email": "user@co.com", "plan": "pro", "expires": "2025-12-31", "max_runs": 1000},
#     "KEY-456": {"email": "agency@co.com", "plan": "agency", "expires": "2025-06-30", "max_runs": -1}
#   },
#   "revoked": ["OLD-KEY-123"]
# }
GIST_RAW_URL = os.getenv(
    "LICENSE_GIST_URL",
    "https://gist.githubusercontent.com/YOUR_GITHUB_USERNAME/GIST_ID/raw/licenses.json"
)

# Cache TTL (seconds) — avoid hitting GitHub rate limits
CACHE_TTL = int(os.getenv("LICENSE_CACHE_TTL", "86400"))  # 24 hours

# Fail open (True) or closed (False) when license server unreachable
FAIL_OPEN = os.getenv("LICENSE_FAIL_OPEN", "false").lower() == "true"

# License key environment variable name
LICENSE_ENV_VAR = "METIS_LICENSE"


# =============================================================================
# CORE VALIDATION LOGIC
# =============================================================================

def get_license_key() -> str:
    """Get license key from environment."""
    key = os.getenv(LICENSE_ENV_VAR)
    if not key:
        print(f"❌ License key not found. Set {LICENSE_ENV_VAR} environment variable.")
        print(f"   Example: export {LICENSE_ENV_VAR}=YOUR_KEY_HERE")
        sys.exit(1)
    return key.strip()


def get_cache_path(key: str) -> Path:
    """Get cache file path for a license key."""
    cache_dir = Path.home() / ".content_strategist" / "license_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key_hash = hashlib.md5(key.encode()).hexdigest()[:12]
    return cache_dir / f"license_{key_hash}.json"


def load_cached_licenses(key: str) -> Optional[Dict]:
    """Load licenses from local cache if fresh."""
    cache_path = get_cache_path(key)
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
        
        cached_at = datetime.fromisoformat(cache["cached_at"])
        if (datetime.now() - cached_at).total_seconds() < CACHE_TTL:
            return cache["data"]
    except Exception:
        pass
    return None


def save_cache(key: str, data: Dict) -> None:
    """Save licenses to local cache."""
    cache_path = get_cache_path(key)
    try:
        with open(cache_path, "w") as f:
            json.dump({"data": data, "cached_at": datetime.now().isoformat()}, f)
    except Exception:
        pass  # Cache failures are non-fatal


def fetch_licenses_from_gist() -> Optional[Dict]:
    """Fetch license database from GitHub Gist."""
    try:
        resp = requests.get(GIST_RAW_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Validate structure
        if "licenses" not in data:
            print("❌ Gist missing 'licenses' field")
            return None
        
        return data
    except requests.exceptions.Timeout:
        print("⚠️ License server timeout")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("❌ License Gist not found. Check GIST_RAW_URL.")
        elif e.response.status_code == 403:
            print("❌ Gist access forbidden. Make Gist public or use token.")
        else:
            print(f"❌ License server error: {e}")
    except Exception as e:
        print(f"⚠️ License fetch failed: {e}")
    
    return None


def validate_license(key: str) -> Optional[Dict[str, Any]]:
    """
    Validate a license key.
    
    Returns:
        License info dict if valid, None if invalid/expired/revoked.
        Keys: email, plan, expires, max_runs
    """
    # Try cache first
    cached = load_cached_licenses(key)
    if cached:
        licenses = cached
    else:
        # Fetch from Gist
        data = fetch_licenses_from_gist()
        if not data:
            if FAIL_OPEN:
                print("⚠️ License server unreachable — failing open (FAIL_OPEN=true)")
                return {"plan": "unknown", "email": "unknown", "expires": "2099-12-31", "max_runs": -1}
            print("❌ Cannot validate license — server unreachable")
            return None
        
        licenses = data["licenses"]
        save_cache(key, licenses)
    
    # Check revoked
    revoked = data.get("revoked", []) if "data" in locals() else []
    if key in revoked:
        print("❌ License revoked")
        return None
    
    # Check license exists
    lic = licenses.get(key)
    if not lic:
        print("❌ License key not found")
        return None
    
    # Check expiration
    try:
        expires = datetime.fromisoformat(lic["expires"])
        if expires < datetime.now():
            print(f"❌ License expired on {lic['expires']}")
            return None
    except Exception:
        print("❌ Invalid expiration date in license")
        return None
    
    # Valid!
    return {
        "email": lic.get("email", "unknown"),
        "plan": lic.get("plan", "unknown"),
        "expires": lic["expires"],
        "max_runs": lic.get("max_runs", -1)
    }


def check_license() -> Dict[str, Any]:
    """
    Main entry point — validates license from env var.
    Exits with error if invalid.
    Returns license info dict.
    """
    key = get_license_key()
    lic = validate_license(key)
    
    if not lic:
        sys.exit(1)
    
    print(f"✅ License valid: {lic['plan']} ({lic['email']}) — expires {lic['expires']}")
    if lic["max_runs"] > 0:
        print(f"   Runs remaining: {lic['max_runs']}")
    
    return lic


def get_remaining_runs(key: str) -> int:
    """Get remaining runs for a license key."""
    lic = validate_license(key)
    if not lic:
        return 0
    return lic.get("max_runs", -1)


def decrement_runs(key: str) -> bool:
    """Decrement run counter (requires Gist update — manual or automated)."""
    # This would require updating the Gist — implement via GitHub API if needed
    # For now, just log usage locally
    log_usage(key, "pipeline", 1)
    return True


# =============================================================================
# USAGE LOGGING (LOCAL CSV)
# =============================================================================

def log_usage(key: str, module: str, runs: int = 1) -> None:
    """Log usage to local CSV for tracking."""
    import csv
    from datetime import datetime
    
    log_file = Path.home() / ".content_strategist" / "usage_log.csv"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    new_file = not log_file.exists()
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "license_hash", "module", "runs"])
        key_hash = hashlib.md5(key.encode()).hexdigest()[:8] + "..."
        writer.writerow([datetime.now().isoformat(), key_hash, module, runs])


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI: python scripts/license.py [key]"""
    if len(sys.argv) > 1:
        key = sys.argv[1]
    else:
        key = get_license_key()
    
    lic = validate_license(key)
    if lic:
        print(json.dumps(lic, indent=2))
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()