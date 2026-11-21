"""
Start Brave with remote debugging (port 9222) for the browser automation scripts,
OUTSIDE the calling agent's process tree, then exit.

Why this exists
---------------
Agents (Antigravity, Claude Code, ...) run every shell command inside a Windows job
object. Anything that command starts with Start-Process, subprocess.Popen or `start`
lands in the same job. When Brave was started that way (test_brave_run.py, 2026-11-19),
the user's whole browser became part of the agent's task:
  * the agent showed a background task that never finished, because the script looped
    forever to "keep Brave alive" (stopping the task would have killed Brave), and
  * Brave runs one process per profile, so every Brave window the user opened joined
    that task; ending the task closed the user's browser.

This script asks WMI to start Brave instead. WMI starts it in the user's desktop
session with WmiPrvSE.exe as its parent, outside every agent job, so this script can
exit as soon as port 9222 answers and Brave stays open on its own.

Usage
-----
    python launch_brave.py              # start Brave with CDP; does nothing if port 9222 already answers
    python launch_brave.py --url URL    # also open URL
    python launch_brave.py --restart    # Brave is open WITHOUT CDP: close it gently, reopen it with CDP
    python launch_brave.py --status     # is CDP up, and is Brave trapped inside a script/agent task?

Exit codes: 0 = CDP ready, 1 = failed, 2 = Brave is open without CDP (rerun with --restart).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

PORT = 9222
BRAVE_FLAGS = (f"--remote-debugging-port={PORT}", "--remote-allow-origins=*")
BRAVE_CANDIDATES = (
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "BraveSoftware/Brave-Browser/Application/brave.exe",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "BraveSoftware/Brave-Browser/Application/brave.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware/Brave-Browser/Application/brave.exe",
)
# A Brave whose parent is one of these was started by a script or an agent shell and is
# inside that command's task: the user's browser dies when the task is stopped.
SCRIPT_PARENTS = {"python.exe", "pythonw.exe", "powershell.exe", "pwsh.exe", "cmd.exe",
                  "node.exe", "agy.exe", "bash.exe", "conhost.exe", "claude.exe"}
# Stop polling the wait loops after this long; nothing in this file waits forever.
START_TIMEOUT_S = 30
CLOSE_TIMEOUT_S = 20


def _powershell(script: str, env: dict[str, str] | None = None) -> str:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, **(env or {})}, timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"powershell exited {out.returncode}")
    return out.stdout.strip()


def cdp_version(port: int = PORT) -> dict | None:
    """The /json/version payload when Brave serves CDP on the port, else None."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def brave_exe() -> Path:
    for path in BRAVE_CANDIDATES:
        if path.is_file():
            return path
    raise RuntimeError("brave.exe not found in Program Files or LocalAppData.")


def brave_browser_processes() -> list[dict]:
    """Brave's browser (main) processes, with their parent's name; renderer/GPU helpers are skipped."""
    raw = _powershell(
        "$all = @{}; Get-CimInstance Win32_Process | ForEach-Object { $all[[int]$_.ProcessId] = $_.Name };"
        "@(Get-CimInstance Win32_Process -Filter \"Name='brave.exe'\" | "
        "Where-Object { $_.CommandLine -notmatch '--type=' } | ForEach-Object { [pscustomobject]@{"
        "pid=[int]$_.ProcessId; ppid=[int]$_.ParentProcessId; parent=$all[[int]$_.ParentProcessId];"
        "cmd=$_.CommandLine } }) | ConvertTo-Json -Compress"
    )
    if not raw:
        return []
    data = json.loads(raw)
    return data if isinstance(data, list) else [data]


def trapped(procs: list[dict]) -> list[dict]:
    """Brave browser processes that a script or agent shell started (and so can take down)."""
    return [p for p in procs if (p.get("parent") or "").lower() in SCRIPT_PARENTS]


def start_detached(args: list[str]) -> int:
    """Start a process through WMI so it is not a child, or job member, of this process. Returns its PID."""
    cmdline = subprocess.list2cmdline(args)
    raw = _powershell(
        "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
        "-Arguments @{CommandLine=$env:LAUNCH_CMDLINE}; "
        "[pscustomobject]@{rc=[int]$r.ReturnValue; pid=[int]$r.ProcessId} | ConvertTo-Json -Compress",
        env={"LAUNCH_CMDLINE": cmdline},
    )
    res = json.loads(raw)
    if res["rc"] != 0:
        raise RuntimeError(f"WMI Win32_Process.Create returned {res['rc']} for: {cmdline}")
    return res["pid"]


def open_tab(url: str, port: int = PORT) -> None:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(url, safe=':/?&=%#')}",
                                 method="PUT")
    with urllib.request.urlopen(req, timeout=5):
        pass


def quit_via_cdp(port: int = PORT) -> None:
    """Ask Brave to quit through CDP (Browser.close), a normal exit that saves the session."""
    import asyncio
    from playwright.async_api import async_playwright

    async def _quit():
        p = await async_playwright().start()
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=10000)
            session = await browser.new_browser_cdp_session()
            try:
                await session.send("Browser.close")
            except Exception:
                pass  # Brave can drop the connection before it answers; the caller polls for the exit.
        finally:
            await p.stop()

    asyncio.run(_quit())


def _wait_for_brave_exit(seconds: float) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if not brave_browser_processes():
            return True
        time.sleep(1)
    return False


def close_brave_gently() -> None:
    """Quit Brave normally (it saves the session); force-close only if it hangs."""
    if cdp_version():
        try:
            quit_via_cdp()
            if _wait_for_brave_exit(CLOSE_TIMEOUT_S):
                return
        except Exception as exc:
            print(f"CDP quit failed ({exc}); asking Brave's windows to close instead.")
    out = subprocess.run(["taskkill", "/IM", "brave.exe"], capture_output=True, text=True)
    if out.returncode != 0:
        print(f"taskkill: {(out.stderr or out.stdout).strip()}")
    if _wait_for_brave_exit(CLOSE_TIMEOUT_S):
        return
    print(f"Brave did not close within {CLOSE_TIMEOUT_S}s; force-closing it.")
    subprocess.run(["taskkill", "/F", "/T", "/IM", "brave.exe"], capture_output=True)
    time.sleep(2)


def warn_if_trapped(procs: list[dict]) -> bool:
    bad = trapped(procs)
    for p in bad:
        print(f"WARNING: Brave (PID {p['pid']}) was started by {p['parent']} (PID {p['ppid']}). It lives inside "
              "that script's or agent's task: the task can't finish cleanly, and stopping it closes Brave.\n"
              "  Fix: stop that task, then run `python launch_brave.py --restart`.")
    return bool(bad)


def main() -> int:
    ap = argparse.ArgumentParser(description="Start Brave with CDP on port 9222, detached from the caller, then exit.")
    ap.add_argument("--url", help="URL to open")
    ap.add_argument("--restart", action="store_true",
                    help="If Brave is open without CDP (or trapped in a script's task), close it gently and reopen it")
    ap.add_argument("--status", action="store_true", help="Report CDP and Brave process state, change nothing")
    args = ap.parse_args()

    procs = brave_browser_processes()
    version = cdp_version()

    if args.status:
        print(f"CDP on port {PORT}: {'UP, ' + version.get('Browser', '') if version else 'not answering'}")
        for p in procs:
            print(f"Brave PID {p['pid']}, parent {p['parent'] or '(exited)'} (PID {p['ppid']})")
        if not procs:
            print("Brave is not running.")
        return 0 if version and not warn_if_trapped(procs) else 1

    if version and not args.restart:
        print(f"Brave CDP already up on port {PORT} ({version.get('Browser', 'Brave')}). Nothing to start.")
        warn_if_trapped(procs)
        if args.url:
            open_tab(args.url)
            print(f"Opened {args.url}")
        return 0

    if procs:
        if not args.restart:
            print("Brave is open but not serving CDP on port 9222 (it was started without the flags).\n"
                  "Run `python launch_brave.py --restart` to close it gently and reopen it with CDP. Tabs come back "
                  "if Brave is set to 'Continue where you left off' (otherwise Ctrl+Shift+T / History).")
            return 2
        print("Closing Brave gently so it can be reopened with remote debugging...")
        close_brave_gently()

    cmd = [str(brave_exe()), *BRAVE_FLAGS] + ([args.url] if args.url else [])
    pid = start_detached(cmd)
    print(f"Started Brave through WMI (PID {pid}, outside this shell's task).")

    deadline = time.time() + START_TIMEOUT_S
    while time.time() < deadline:
        version = cdp_version()
        if version:
            print(f"Brave CDP ready on port {PORT} ({version.get('Browser', 'Brave')}). This script exits now; "
                  "Brave stays open on its own.")
            return 0
        time.sleep(1)
    print(f"Brave started but port {PORT} did not answer within {START_TIMEOUT_S}s. If another Brave window was "
          "already open, close every Brave window and run this again.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"launch_brave error: {exc}")
        sys.exit(1)
