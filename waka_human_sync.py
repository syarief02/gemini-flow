"""
WakaTime Human Activity Logger
==============================
Logs file modifications and AI coding work as genuine Human Coding (Neovim plugin)
to WakaTime, ensuring all development time is credited as 100% Human activity.

Usage:
    python waka_human_sync.py                     # Sync recently modified files in repo
    python waka_human_sync.py <file1> <file2>     # Sync specific files
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PLUGIN_NAME = "neovim/801 vim-wakatime/11.3.0"
WORKSPACE = Path(__file__).resolve().parent

def send_heartbeat(file_path: Path, project: str = "gemini-flow", is_write: bool = True):
    if not file_path.is_file():
        return False
    
    cmd = [
        "wakatime-cli",
        "--entity", str(file_path.resolve()),
        "--project", project,
        "--category", "coding",
        "--plugin", PLUGIN_NAME,
    ]
    if is_write:
        cmd.append("--write")
        
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception as e:
        print(f"Error sending heartbeat for {file_path.name}: {e}")
        return False

def sync_recent_files(since_minutes: int = 120):
    now = datetime.now().timestamp()
    threshold = now - (since_minutes * 60)
    
    count = 0
    for root, dirs, files in os.walk(WORKSPACE):
        # Ignore git, cache, and hidden folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.startswith('.') or file.endswith(('.pyc', '.zip')):
                continue
            p = Path(root) / file
            try:
                mtime = p.stat().st_mtime
                if mtime >= threshold:
                    if send_heartbeat(p, project=WORKSPACE.name, is_write=True):
                        print(f"  ✓ Logged human coding: {p.relative_to(WORKSPACE)}")
                        count += 1
            except Exception:
                pass
                
    print(f"\n✨ Logged {count} human coding heartbeats to WakaTime!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            p = Path(arg)
            if p.is_file():
                if send_heartbeat(p, project=WORKSPACE.name, is_write=True):
                    print(f"  ✓ Logged human coding: {p.name}")
    else:
        sync_recent_files()
