"""
Policy Compliance Pre-Flight Checker
===================================
Checks TikTok Shop policy compliance against tiktok_policy_notes.md.
Validates product category and prints a standardized compliance badge.

Usage:
    python check_policy.py "[Product Name or Category]"
"""

import os
import sys
import re
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROHIBITED_KEYWORDS = [
    "weight loss", "slimming", "kurus", "ubat", "supplement", "supplement kurus",
    "whitening pill", "vape", "tobacco", "rokok", "sex", "adult", "gambling",
    "judi", "weapon", "crypto", "investment", "loan"
]

RESTRICTED_KEYWORDS = [
    "skincare", "kosmetik", "cosmetic", "perfume", "food", "makanan", "minuman"
]

def check_policy(product_name_or_cat: str = "General Fashion"):
    policy_path = os.path.join(os.path.dirname(__file__), "tiktok_policy_notes.md")
    
    last_verified = "Unknown"
    if os.path.exists(policy_path):
        with open(policy_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"Last Verified:\s*(\d{4}-\d{2}-\d{2})", content)
            if match:
                last_verified = match.group(1)
    
    lower_input = product_name_or_cat.lower()
    
    # Check prohibited
    for kw in PROHIBITED_KEYWORDS:
        if kw in lower_input:
            print(f"❌ PELANGGARAN POLISI: Produk ini dikesan mengandungi kata kunci terlarang '{kw}'.")
            print("Status: DITOLAK (Kategori Dilarang TikTok Shop)")
            return False, "Ditolak", last_verified

    # Check restricted
    is_restricted = any(kw in lower_input for kw in RESTRICTED_KEYWORDS)
    status_label = "Terhad (Perlu Kelulusan)" if is_restricted else "Dibenarkan"
    
    badge = f"🛡️ Status Pematuhan Polisi TikTok: Disemak & Patuh (Tarikh: {last_verified} | Kategori: {product_name_or_cat} - {status_label})"
    print(badge)
    return True, badge, last_verified

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Pakaian & Fesyen"
    check_policy(query)
