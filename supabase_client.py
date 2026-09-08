"""
Supabase Database Client & Sync Module
======================================
Provides database connectivity, health verification, and cloud synchronization
for Gemini Flow TikTok product promo generations.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")


def get_supabase_client():
    """Instantiate and return Supabase Client if credentials are configured."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as err:
        print(f"Failed to initialize Supabase client: {err}")
        return None


def test_supabase_connection() -> Dict[str, Any]:
    """Test and report connectivity to the configured Supabase database."""
    client = get_supabase_client()
    if not client:
        return {
            "status": "error",
            "message": "Missing SUPABASE_URL or SUPABASE_ANON_KEY/SUPABASE_SERVICE_ROLE_KEY in .env"
        }
    
    try:
        import urllib.request
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Accept": "application/openapi+json"
        }
        req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            available_paths = list(data.get("paths", {}).keys())
            return {
                "status": "connected",
                "url": SUPABASE_URL,
                "http_status": resp.getcode(),
                "available_tables": [p.lstrip("/") for p in available_paths if p != "/" and not p.startswith("/rpc")],
                "rpc_functions": [p.split("/")[-1] for p in available_paths if p.startswith("/rpc")]
            }
    except Exception as err:
        return {
            "status": "failed",
            "url": SUPABASE_URL,
            "error": str(err)
        }


def save_generation_record(product_name: str, opening_line: str, closing_line: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Save or sync a generation record to Supabase if the target table exists.
    Falls back gracefully without throwing errors if the table is not yet provisioned.
    """
    client = get_supabase_client()
    if not client:
        return False

    payload = {
        "product_name": product_name,
        "opening_line": opening_line,
        "closing_line": closing_line,
        "metadata": metadata or {}
    }

    try:
        client.table("gemini_flow_generations").insert(payload).execute()
        print(f"Synced generation record for '{product_name}' to Supabase.")
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("Testing Supabase connectivity...")
    res = test_supabase_connection()
    print(json.dumps(res, indent=2))

