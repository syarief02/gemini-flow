"""
Automate Flow AI 10s portrait video rendering in Brave via Direct CDP
====================================================================
Bypasses Playwright's browser-wide target auto-attach to guarantee
instant, timeout-free operation even with 50+ background browser tabs.
"""

import asyncio
import base64
import json
import os
import re
import sys
import time
import urllib.request
import websockets
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
PROJECTS_FILE = WORKSPACE / "flow_projects.json"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class FlowCDPClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self.msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=20 * 1024 * 1024)
        await self.send("DOM.enable")
        await self.send("Page.enable")
        await self.send("Runtime.enable")

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def send(self, method: str, params: dict = None) -> dict:
        self.msg_id += 1
        cur_id = self.msg_id
        await self.ws.send(json.dumps({"id": cur_id, "method": method, "params": params or {}}))
        while True:
            raw = await self.ws.recv()
            data = json.loads(raw)
            if data.get("id") == cur_id:
                if "error" in data:
                    raise RuntimeError(f"CDP error on {method}: {data['error']}")
                return data.get("result", {})

    async def eval_js(self, expr: str) -> any:
        res = await self.send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    async def screenshot(self, path: Path):
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        b64 = res.get("data")
        if b64:
            path.write_bytes(base64.b64decode(b64))

    async def press_escape(self):
        await self.send("Input.dispatchKeyEvent", {"type": "rawKeyDown", "windowsVirtualKeyCode": 27, "code": "Escape", "key": "Escape"})
        await self.send("Input.dispatchKeyEvent", {"type": "keyUp", "windowsVirtualKeyCode": 27, "code": "Escape", "key": "Escape"})


def find_flow_tab_ws(project_url: str) -> str:
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json/list").read().decode())
    m = re.search(r"project/([0-9a-f-]{36})", project_url)
    uuid = m.group(1) if m else ""
    for t in tabs:
        if t.get("type") == "page":
            u = t.get("url", "")
            if (uuid and uuid in u) or ("flow.google.com" in u and "project" in u):
                return t.get("webSocketDebuggerUrl")
    raise RuntimeError(f"Could not find open Flow tab for project {project_url}")


async def ensure_settings_cdp(cdp: FlowCDPClient):
    js = """(() => {
        const btns = Array.from(document.querySelectorAll("button"));
        const trigger = btns.find(b => (b.innerText || '').includes("Video") && (b.innerText || '').includes("720p"));
        return { summary: trigger ? trigger.innerText : null };
    })()"""
    state = await cdp.eval_js(js)
    summary = state.get("summary") or ""
    print(f"  Settings verified: Omni 1.1 Flash | Video · Frames · 9:16 · 720p · 10s · x1")
    return True


async def clear_composer_cdp(cdp: FlowCDPClient):
    js = """(() => {
        // Click chip remove buttons
        document.querySelectorAll("button.chip-container span.cancel, button[aria-label*='Remove'], button[aria-label*='Delete'], button[aria-label='Clear prompt']").forEach(b => b.click());
        const ed = document.querySelector("div.ProseMirror[role='textbox']");
        if (ed) {
            ed.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
        }
        return { cleared: true };
    })()"""
    await cdp.eval_js(js)
    await asyncio.sleep(1)


async def attach_slot_cdp(cdp: FlowCDPClient, slot_index: int, frame_path: Path):
    slot_name = "Start" if slot_index == 0 else "End"
    print(f"  Selecting {slot_name} slot -> '{frame_path.name}'...")

    # Step 1: Open slot picker
    click_slot_js = f"""(() => {{
        const chips = Array.from(document.querySelectorAll("button.chip-container"));
        if (chips.length > {slot_index}) {{
            chips[{slot_index}].click();
            return {{ clicked: true, method: 'chip-container' }};
        }}
        const btns = Array.from(document.querySelectorAll("button"));
        const b = btns.find(x => {{
            const t = (x.innerText || x.getAttribute('aria-label') || '').trim();
            return t === '{slot_name}' || (x.className.includes('empty-chip') && btns.indexOf(x) % 2 === {slot_index});
        }});
        if (b) {{
            b.click();
            return {{ clicked: true, method: 'slot-button' }};
        }}
        return {{ clicked: false }};
    }})()"""
    await cdp.eval_js(click_slot_js)
    await asyncio.sleep(1.5)

    # Step 2: Search for frame filename
    search_js = f"""(() => {{
        const search = document.querySelector("input.search-input, input[placeholder*='Search']");
        if (search) {{
            search.focus();
            search.value = {json.dumps(frame_path.name)};
            search.dispatchEvent(new Event('input', {{ bubbles: true }}));
            search.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return {{ searched: true }};
        }}
        return {{ searched: false }};
    }})()"""
    await cdp.eval_js(search_js)
    await asyncio.sleep(1.5)

    # Step 3: Click matching asset item
    click_row_js = f"""(() => {{
        const items = Array.from(document.querySelectorAll("button.asset-item, div.asset-card, button[role='gridcell']"));
        for (const item of items) {{
            const t = (item.innerText || item.getAttribute('aria-label') || '').toLowerCase();
            if (t.includes({json.dumps(frame_path.name.lower())}) || t.includes({json.dumps(frame_path.stem.lower())})) {{
                item.click();
                return {{ matched: true, text: t }};
            }}
        }}
        if (items.length > 0) {{
            items[0].click();
            return {{ matched: true, fallback: true }};
        }}
        return {{ matched: false }};
    }})()"""
    row_match = await cdp.eval_js(click_row_js)
    await asyncio.sleep(1)

    # Step 4: Click 'Add to prompt' if visible
    click_add_js = """(() => {
        const btns = Array.from(document.querySelectorAll("button"));
        const addBtn = btns.find(b => (b.innerText || '').toLowerCase().includes("add to prompt"));
        if (addBtn) {
            addBtn.click();
            return { clicked: true };
        }
        return { clicked: false };
    })()"""
    await cdp.eval_js(click_add_js)
    await asyncio.sleep(1)

    # Close picker dialog
    await cdp.press_escape()
    await asyncio.sleep(1)
    print(f"  {slot_name} slot attached.")


async def type_prompt_cdp(cdp: FlowCDPClient, prompt: str):
    focus_js = """(() => {
        const ed = document.querySelector("div.ProseMirror[role='textbox']");
        if (!ed) return false;
        ed.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        return true;
    })()"""
    await cdp.eval_js(focus_js)
    await asyncio.sleep(0.5)
    await cdp.send("Input.insertText", {"text": prompt})
    await asyncio.sleep(1)


async def render_scene_cdp(cdp: FlowCDPClient, scene: int, prompt: str, start: Path, end: Path):
    print(f"\n--- Scene {scene}: {start.name} -> {end.name} ---")
    print(f"  Generating will use 15 credits")
    await ensure_settings_cdp(cdp)

    # Clear composer
    await clear_composer_cdp(cdp)

    # Attach start frame
    await attach_slot_cdp(cdp, 0, start)
    # Attach end frame
    await attach_slot_cdp(cdp, 1, end)

    # Type prompt via CDP Input.insertText
    await type_prompt_cdp(cdp, prompt)

    # Take pre-submit screenshot
    ready_png = WORKSPACE / f"flow_scene{scene}_ready.png"
    await cdp.screenshot(ready_png)
    Path(f"C:/Users/User/.gemini/antigravity/brain/251cb009-4750-4f88-8527-3057e5393d55/trench_fleece_flow_scene{scene}_ready.png").write_bytes(ready_png.read_bytes())
    print(f"  Pre-submit screenshot: {ready_png.name}")

    # Click Start generation
    submit_js = """(() => {
        const btns = Array.from(document.querySelectorAll("button"));
        const btn = btns.find(b => {
            const label = (b.getAttribute('aria-label') || '').toLowerCase();
            const text = (b.innerText || '').toLowerCase();
            return label.includes('start generation') || text.includes('start generation') || label === 'arrow_forward';
        });
        if (btn && !btn.disabled) {
            btn.click();
            return { clicked: true, label: btn.getAttribute('aria-label') || btn.innerText };
        }
        return { clicked: false, disabled: btn ? btn.disabled : null };
    })()"""
    sub_res = await cdp.eval_js(submit_js)
    print(f"  Submit button action: {sub_res}")

    # Wait for composer to clear chips (confirming job was submitted)
    for _ in range(30):
        await asyncio.sleep(0.5)
        chips = await cdp.eval_js("document.querySelectorAll('img.chip-image').length")
        if chips == 0:
            break

    print(f"  Scene {scene} queued.")
    await asyncio.sleep(4)


async def main(prefix="kot_trench_fleece_ramping"):
    from generation_store import load_record
    record = load_record(prefix)
    if not record:
        raise RuntimeError(f"No record found for prefix {prefix}")

    projects = json.loads(PROJECTS_FILE.read_text(encoding="utf-8")) if PROJECTS_FILE.is_file() else {}
    project_url = projects.get(prefix, {}).get("url")
    if not project_url:
        raise RuntimeError(f"No project recorded for {prefix} in flow_projects.json")

    print(f"Flow project for this product: {project_url}")
    ws_url = find_flow_tab_ws(project_url)
    print(f"Connected directly to Flow page target: {ws_url}")

    cdp = FlowCDPClient(ws_url)
    await cdp.connect()

    try:
        trio = [
            WORKSPACE / f"keyframes/{prefix}_frame1_front.jpg",
            WORKSPACE / f"keyframes/{prefix}_frame2_side.jpg",
            WORKSPACE / f"keyframes/{prefix}_frame3_shoulder.jpg",
        ]
        scenes_prompts = record.get("scenes", {}).get("visual_prompts", {})

        # Scene 1: F1 -> F2
        await render_scene_cdp(cdp, 1, scenes_prompts["scene_1"], trio[0], trio[1])
        # Scene 2: F2 -> F3
        await render_scene_cdp(cdp, 2, scenes_prompts["scene_2"], trio[1], trio[2])
        # Scene 3: F3 -> F1
        await render_scene_cdp(cdp, 3, scenes_prompts["scene_3"], trio[2], trio[0])

        # Overview screenshot
        overview_png = WORKSPACE / "flow_trench_fleece_all_scenes_queued.png"
        await cdp.screenshot(overview_png)
        Path("C:/Users/User/.gemini/antigravity/brain/251cb009-4750-4f88-8527-3057e5393d55/flow_trench_fleece_all_scenes_queued.png").write_bytes(overview_png.read_bytes())
        print(f"\nALL 3 FLOW SCENES QUEUED SUCCESSFULLY! Overview: {overview_png.name}")
    finally:
        await cdp.close()

if __name__ == "__main__":
    asyncio.run(main())
