"""
Generation Records in the Repo
==============================
Every product's full generation record lives in generations/<prefix>.json and its keyframe
images in keyframes/, both committed to GitHub (Step 10). This replaces the old Supabase
table + storage bucket: nothing important lives outside the repo.

    from generation_store import save_record, load_record, find_keyframes
    save_record("bgm_plain_mini_dress", {...})
    record = load_record("bgm_plain_mini_dress")
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

WORKSPACE = Path(__file__).resolve().parent
GENERATIONS_DIR = WORKSPACE / "generations"
KEYFRAMES_DIR = WORKSPACE / "keyframes"

# The repo is public, so committed keyframes have stable raw links (they resolve after `git push`).
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/syarief02/gemini-flow/master"

# Frame key -> accepted filenames (current naming first, legacy short naming second).
FRAME_FILENAMES = {
    "frame_1_front": ("{prefix}_frame1_front.jpg", "{prefix}_frame1.jpg"),
    "frame_2_side": ("{prefix}_frame2_side.jpg", "{prefix}_frame2.jpg"),
    "frame_3_shoulder": ("{prefix}_frame3_shoulder.jpg", "{prefix}_frame3.jpg"),
}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_prefix(prefix: str) -> str:
    return prefix.lower().replace("-", "_").replace(" ", "_").strip("_")


def keyframe_url(filename: str) -> str:
    """Public GitHub raw link for a committed file in keyframes/."""
    return f"{GITHUB_RAW_BASE}/keyframes/{Path(filename).name}"


def find_keyframes(prefix: str, keyframes_dir: Optional[str | Path] = None) -> Dict[str, Any]:
    """Locate the 3 keyframes for a product prefix in keyframes/ (local files only)."""
    target_dir = Path(keyframes_dir) if keyframes_dir else KEYFRAMES_DIR
    prefix = clean_prefix(prefix)
    result: Dict[str, Any] = {"prefix": prefix, "frames": {}, "all_present": True, "paths": [], "urls": []}

    for key, patterns in FRAME_FILENAMES.items():
        names = [p.format(prefix=prefix) for p in patterns]
        chosen = next((n for n in names if (target_dir / n).is_file()), names[0])
        local = target_dir / chosen
        exists = local.is_file()
        if not exists:
            result["all_present"] = False
        result["frames"][key] = {
            "filename": chosen,
            "local_path": str(local) if exists else None,
            "exists_locally": exists,
            "url": keyframe_url(chosen),
        }
        result["paths"].append(f"keyframes/{chosen}")
        result["urls"].append(keyframe_url(chosen))
    return result


def record_path(prefix: str) -> Path:
    return GENERATIONS_DIR / f"{clean_prefix(prefix)}.json"


def load_record(prefix: str) -> Optional[Dict[str, Any]]:
    path = record_path(prefix)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_record(prefix: str, record: Dict[str, Any]) -> Path:
    """Create or update generations/<prefix>.json. Keeps the original created_at on updates."""
    prefix = clean_prefix(prefix)
    existing = load_record(prefix) or {}
    now = _now()
    data = {"prefix": prefix, "created_at": existing.get("created_at", now), **record, "updated_at": now}
    data["prefix"] = prefix

    GENERATIONS_DIR.mkdir(exist_ok=True)
    path = record_path(prefix)
    # Write to a temp file and swap it in, so an interrupted write can't truncate the record.
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def latest_record() -> Optional[Dict[str, Any]]:
    """The most recently updated record in generations/, or None if there are none."""
    records = []
    for path in GENERATIONS_DIR.glob("*.json"):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except ValueError:
            print(f"Notice: skipping unreadable record {path.name}")
    if not records:
        return None
    # Ties on updated_at (same second) go to the product created last.
    return max(records, key=lambda r: (r.get("updated_at") or "", r.get("created_at") or ""))
