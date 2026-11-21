"""
Post Performance Tracking
=========================
Until 2026-11-21 nothing recorded how a posted promo did, so hooks were chosen only for being
different from the last 7 (every one scored 100/100). This records each product's post and its
numbers, and ranks hook formats and delivery styles by real results. `generate_prompts.py
--hook-brief` shows the ranking, so the next hook can lean on what actually sold.

Numbers are entered by hand: views/likes/comments/shares from TikTok Studio, orders and GMV from
the TikTok Shop Affiliate dashboard (no public page shows them). Record a snapshot ~48h after
posting, and again at ~7 days if you like; the report uses each product's latest snapshot.

Usage:
    python track_performance.py --prefix <prefix> --post-url https://www.tiktok.com/@you/video/123
    python track_performance.py --prefix <prefix> --views 5400 --likes 210 --comments 12 --shares 9 --orders 4 --gmv 119.60
    python track_performance.py --report        # rank hook formats and delivery styles by results
    python track_performance.py --pending       # assembled/posted products still missing numbers
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

from generation_store import GENERATIONS_DIR, clean_prefix, load_record, update_record

METRICS = ("views", "likes", "comments", "shares", "orders", "gmv")
MIN_POSTS_TO_TRUST = 3


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def clean_post_url(url: str) -> str:
    """https://www.tiktok.com/@handle/video/<id> without query string (shared links carry tracking IDs)."""
    url = url.strip().split("?")[0].split("#")[0]
    if not re.match(r"https://(www\.|vt\.|vm\.)?tiktok\.com/", url):
        raise ValueError(f"Not a TikTok link: {url}")
    return url


def record_post(prefix: str, post_url: str) -> None:
    rec = load_record(prefix) or {}
    perf = dict(rec.get("performance") or {})
    perf["post_url"] = clean_post_url(post_url)
    perf.setdefault("posted_at", _now())
    perf.setdefault("snapshots", [])
    update_record(prefix, performance=perf)
    print(f"Recorded post for {prefix}: {perf['post_url']}")


def record_snapshot(prefix: str, numbers: dict) -> None:
    rec = load_record(prefix) or {}
    perf = dict(rec.get("performance") or {})
    snap = {"at": _now(), **{k: v for k, v in numbers.items() if v is not None}}
    if posted := perf.get("posted_at"):
        hours = (datetime.fromisoformat(snap["at"]) - datetime.fromisoformat(posted)).total_seconds() / 3600
        snap["hours_since_post"] = round(hours, 1)
    perf.setdefault("snapshots", []).append(snap)
    update_record(prefix, performance=perf)
    print(f"Recorded numbers for {prefix}: " + ", ".join(f"{k}={v}" for k, v in snap.items() if k in METRICS))


def _all_records() -> list[dict]:
    out = []
    for path in sorted(GENERATIONS_DIR.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8-sig")))
        except ValueError:
            continue
    return out


def _latest(rec: dict) -> dict | None:
    snaps = (rec.get("performance") or {}).get("snapshots") or []
    return snaps[-1] if snaps else None


def _group_key(rec: dict, field: str) -> str:
    return (rec.get("metadata") or {}).get(field) or rec.get(field) or "(not recorded)"


def rank(field: str) -> list[dict]:
    """Per hook_format or delivery_style: posts, median views, orders, orders per 1k views."""
    groups: dict[str, list[dict]] = {}
    for rec in _all_records():
        snap = _latest(rec)
        if snap and snap.get("views") is not None:
            groups.setdefault(_group_key(rec, field), []).append(snap)
    rows = []
    for key, snaps in groups.items():
        views = [s["views"] for s in snaps]
        orders = sum(s.get("orders") or 0 for s in snaps)
        rows.append({"key": key, "posts": len(snaps), "median_views": int(statistics.median(views)),
                     "orders": orders, "orders_per_1k": round(1000 * orders / max(1, sum(views)), 2),
                     "gmv": round(sum(s.get("gmv") or 0 for s in snaps), 2)})
    return sorted(rows, key=lambda r: (-r["orders_per_1k"], -r["median_views"]))


def performance_brief() -> list[str]:
    """Lines for generate_prompts.py --hook-brief."""
    lines = ["", "📈 RESULTS SO FAR (track_performance.py; latest snapshot per posted product):"]
    fmt, sty = rank("hook_format"), rank("delivery_style")
    if not fmt:
        lines.append("  No results recorded yet. After posting: python track_performance.py --prefix <prefix> "
                     "--post-url <link>, then ~48h later add --views/--orders. Choose by freshness until then.")
        return lines
    for title, rows in (("Hook formats", fmt), ("Delivery styles", sty)):
        lines.append(f"  {title} (best first by orders per 1k views):")
        for r in rows[:6]:
            note = "" if r["posts"] >= MIN_POSTS_TO_TRUST else f"  (only {r['posts']} post(s): not proven yet)"
            lines.append(f"    - {r['key']}: {r['orders_per_1k']} orders/1k views, median {r['median_views']} views, "
                         f"{r['posts']} post(s){note}")
    lines.append(f"  Lean towards proven winners ({MIN_POSTS_TO_TRUST}+ posts), but keep testing unproven formats "
                 "about 1 run in 3 so the data keeps improving.")
    return lines


def pending() -> list[str]:
    out = []
    for rec in _all_records():
        perf = rec.get("performance") or {}
        if rec.get("final_video") and not perf.get("post_url"):
            out.append(f"{rec.get('prefix')}: assembled, post link not recorded")
        elif perf.get("post_url") and not perf.get("snapshots"):
            out.append(f"{rec.get('prefix')}: posted ({perf['post_url']}), no numbers yet")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Record TikTok post results and rank hooks by them.")
    ap.add_argument("--prefix", help="Product prefix (generations/<prefix>.json)")
    ap.add_argument("--post-url", help="The posted TikTok video link")
    for m in METRICS:
        ap.add_argument(f"--{m}", type=float if m == "gmv" else int)
    ap.add_argument("--report", action="store_true", help="Rank hook formats and delivery styles")
    ap.add_argument("--pending", action="store_true", help="List products still missing a post link or numbers")
    args = ap.parse_args()

    if args.report:
        for field in ("hook_format", "delivery_style"):
            rows = rank(field)
            print(f"\n{field} ranking ({len(rows)} group(s)):")
            for r in rows:
                print(f"  {r['key']:<22} posts {r['posts']:>2} | median views {r['median_views']:>7} | "
                      f"orders {r['orders']:>3} | {r['orders_per_1k']:>5} orders/1k views | GMV {r['gmv']}")
            if not rows:
                print("  no results recorded yet")
        return 0
    if args.pending:
        items = pending()
        print("\n".join(items) if items else "Nothing pending.")
        return 0
    if not args.prefix:
        ap.error("--prefix is required (or use --report / --pending)")
    args.prefix = clean_prefix(args.prefix)
    if load_record(args.prefix) is None:
        ap.error(f"No generations/{args.prefix}.json")
    numbers = {m: getattr(args, m) for m in METRICS}
    if not args.post_url and all(v is None for v in numbers.values()):
        ap.error("Give --post-url and/or at least one number (--views, --orders, ...)")
    if args.post_url:
        record_post(args.prefix, args.post_url)
    if any(v is not None for v in numbers.values()):
        record_snapshot(args.prefix, numbers)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)
