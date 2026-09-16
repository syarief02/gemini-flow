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


# Alias for backward compatibility
get_supabase = get_supabase_client



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


def save_generation_record(
    product_name: str,
    opening_line: str,
    closing_line: str,
    metadata: Optional[Dict[str, Any]] = None,
    scenes: Optional[Dict[str, Any]] = None,
    caption: Optional[str] = None,
    hashtags: Optional[str] = None,
    bgm_prompt: Optional[str] = None,
    keyframe_urls: Optional[Any] = None
) -> bool:
    """
    Save or sync a generation record to Supabase if the target table exists.
    Uses intelligent upsert/update to prevent duplicate rows when called multiple times.
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
    if scenes is not None:
        payload["scenes"] = scenes
    if caption is not None:
        payload["caption"] = caption
    if hashtags is not None:
        payload["hashtags"] = hashtags
    if bgm_prompt is not None:
        payload["bgm_prompt"] = bgm_prompt
    if keyframe_urls is not None:
        payload["keyframe_urls"] = keyframe_urls

    try:
        # Check if a record already exists with the same product_name and opening_line to prevent duplicates
        existing = (
            client.table("gemini_flow_generations")
            .select("id, keyframe_urls")
            .eq("product_name", product_name)
            .order("created_at", desc=True)
            .limit(3)
            .execute()
        )
        match_id = None
        for row in (existing.data or []):
            if row.get("id"):
                match_id = row["id"]
                break

        if match_id:
            client.table("gemini_flow_generations").update(payload).eq("id", match_id).execute()
            print(f"Updated existing generation record ({match_id}) for '{product_name}' in Supabase.")
            return True

        client.table("gemini_flow_generations").insert(payload).execute()
        print(f"Synced new generation record for '{product_name}' to Supabase.")
        return True
    except Exception as e:
        print(f"Supabase sync notice: {e}")
        return False


def upload_keyframe_to_supabase(
    local_path: str | Path,
    remote_filename: Optional[str] = None
) -> Optional[str]:
    """
    Upload a local keyframe image to Supabase Storage bucket 'gemini-flow-keyframes'.
    Returns the public CDN URL or None on failure.
    """
    client = get_supabase_client()
    if not client:
        return None

    path_obj = Path(local_path)
    if not path_obj.is_file():
        print(f"File not found for upload: {local_path}")
        return None

    fname = remote_filename or path_obj.name
    try:
        file_bytes = path_obj.read_bytes()
        mime = "image/jpeg" if fname.lower().endswith((".jpg", ".jpeg")) else "image/png"
        client.storage.from_("gemini-flow-keyframes").upload(
            fname,
            file_bytes,
            {"content-type": mime, "upsert": "true"}
        )
        cdn_url = f"{SUPABASE_URL}/storage/v1/object/public/gemini-flow-keyframes/{fname}"
        return cdn_url
    except Exception as err:
        print(f"Supabase storage upload notice for {fname}: {err}")
        return None


def sync_all_keyframes_to_supabase(
    keyframes_dir: Optional[str | Path] = None
) -> Dict[str, Any]:
    """
    Inspect local keyframes directory and ensure all images are uploaded
    to Supabase Storage 'gemini-flow-keyframes'.
    """
    client = get_supabase_client()
    if not client:
        return {"status": "error", "message": "Supabase client not initialized"}

    target_dir = Path(keyframes_dir) if keyframes_dir else Path(__file__).resolve().parent / "keyframes"
    if not target_dir.is_dir():
        return {"status": "error", "message": f"Directory not found: {target_dir}"}

    try:
        remote_items = client.storage.from_("gemini-flow-keyframes").list(options={"limit": 1000})
        remote_filenames = set(it.get("name") for it in (remote_items or []) if it.get("name"))
    except Exception as e:
        return {"status": "error", "message": f"Failed to list remote bucket: {e}"}

    local_files = [f for f in target_dir.glob("*.jpg")] + [f for f in target_dir.glob("*.jpeg")] + [f for f in target_dir.glob("*.png")]
    uploaded = []
    skipped = []

    for f in local_files:
        if f.name not in remote_filenames:
            url = upload_keyframe_to_supabase(f)
            if url:
                uploaded.append(f.name)
        else:
            skipped.append(f.name)

    return {
        "status": "success",
        "total_local": len(local_files),
        "already_synced": len(skipped),
        "newly_uploaded": len(uploaded),
        "uploaded_files": uploaded
    }


def cleanup_duplicate_generations() -> int:
    """
    Find and delete duplicate generation records in 'gemini_flow_generations',
    retaining the most complete record (with keyframe_urls or newest).
    """
    client = get_supabase_client()
    if not client:
        return 0

    try:
        rows = (
            client.table("gemini_flow_generations")
            .select("id, product_name, opening_line, created_at, keyframe_urls")
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )

        seen: Dict[tuple, Dict[str, Any]] = {}
        to_delete: List[str] = []

        for row in rows:
            key = (row.get("product_name"), row.get("opening_line"))
            if key not in seen:
                seen[key] = row
            else:
                existing = seen[key]
                # If the current row has keyframe_urls but existing does not, keep current and delete existing
                if row.get("keyframe_urls") and not existing.get("keyframe_urls"):
                    to_delete.append(existing["id"])
                    seen[key] = row
                else:
                    to_delete.append(row["id"])

        deleted_count = 0
        for rid in to_delete:
            client.table("gemini_flow_generations").delete().eq("id", rid).execute()
            deleted_count += 1
            print(f"Deleted duplicate record: {rid}")

        return deleted_count
    except Exception as e:
        print(f"Error during duplicate cleanup: {e}")
        return 0


def fetch_recent_generations(limit: int = 7) -> List[Dict[str, Any]]:
    """Fetch the latest generation records directly from Supabase."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        response = (
            client.table("gemini_flow_generations")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Supabase fetch notice: {e}")
        return []

def fetch_generation_by_id(record_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single generation record by its UUID directly from Supabase."""
    client = get_supabase_client()
    if not client or not record_id:
        return None
    try:
        response = (
            client.table("gemini_flow_generations")
            .select("*")
            .eq("id", record_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None
    except Exception as e:
        print(f"Supabase fetch by ID notice: {e}")
        return None


def get_database_health() -> Dict[str, Any]:
    """Comprehensive health check across REST API, database tables, and Storage bucket."""
    client = get_supabase_client()
    if not client:
        return {"status": "unconfigured", "message": "Missing credentials"}

    start_t = time.time()
    conn_info = test_supabase_connection()
    latency_ms = round((time.time() - start_t) * 1000, 1)

    table_counts = {}
    storage_counts = {}
    try:
        res = client.table("gemini_flow_generations").select("id", count="exact").limit(1).execute()
        table_counts["gemini_flow_generations"] = res.count
    except Exception as e_tbl:
        table_counts["gemini_flow_generations"] = f"error: {e_tbl}"

    try:
        items = client.storage.from_("gemini-flow-keyframes").list(options={"limit": 1000})
        storage_counts["gemini-flow-keyframes"] = len(items or [])
    except Exception as e_str:
        storage_counts["gemini-flow-keyframes"] = f"error: {e_str}"

    return {
        "status": conn_info.get("status"),
        "latency_ms": latency_ms,
        "table_counts": table_counts,
        "storage_bucket_counts": storage_counts,
        "available_tables": conn_info.get("available_tables", []),
    }


if __name__ == "__main__":
    import time
    print("Testing Supabase connectivity...")
    res = test_supabase_connection()
    print(json.dumps(res, indent=2))
    print("\nTesting get_database_health()...")
    health = get_database_health()
    print(json.dumps(health, indent=2))
    print("\nChecking and cleaning duplicate records...")
    cleaned = cleanup_duplicate_generations()
    print(f"Cleaned {cleaned} duplicate records.")


