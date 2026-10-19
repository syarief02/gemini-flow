"""
Flow AI Automation Script for Brave Browser via Playwright CDP
=============================================================
Connects to Brave running on port 9222 with remote debugging, then for each
scene: clears the composer, enforces Video / Frames / 9:16 / Omni 1.1 Flash /
720p / 10s / x1, attaches the Start and End keyframes by exact filename,
verifies pixel-for-pixel that each slot holds the expected keyframe, types the
visual prompt + Spoken Malay lip-sync line, and only then clicks
'Start generation'. Any failed check aborts that scene WITHOUT submitting.

Every product gets its OWN Flow project. The project for each keyframe prefix is
recorded in flow_projects.json, and renders always go to that product's project.

Usage:
    python automate_flow.py --create-project "OLOME Cropped Denim Jacket" --prefix olome_cropped_denim_jacket
    python automate_flow.py --all --prefix <prefix> --dry-run   # run every check, submit nothing
    python automate_flow.py --all --prefix <prefix>             # render all 3 scenes
    python automate_flow.py --scene 2 --prefix <prefix>
    python automate_flow.py --scene 1 --prompt "..." --start-frame a.jpg --end-frame b.jpg --prefix <prefix>
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).resolve().parent
FLOW_URL = "https://flow.google.com/?pli=1&authuser=5"
KEYFRAMES_DIR = WORKSPACE / "keyframes"
PROJECTS_FILE = WORKSPACE / "flow_projects.json"  # keyframe prefix -> its own Flow project

# Composer settings that every render must use (labels as shown in Flow's settings menu).
REQUIRED_TOGGLES = ("Video", "Frames", "9:16", "720p", "10s", "x1")
REQUIRED_MODEL = "Omni 1.1 Flash"

# Mean grayscale difference (0-255) between a slot thumbnail and a local keyframe at 32x56.
# The same file measures ~0.05; a different pose of the same product measures ~8-10.
CHIP_MATCH_MAX_DIFF = 3.0

# Spoken line length for a 10s clip, in words. Lines of ~40 words (old style) sounded natural but were
# sometimes cut off; lines of 14-21 words (2026-10-19) got stretched and sounded unnatural. Aim 28-32.
MIN_DIALOGUE_WORDS = 24
MAX_DIALOGUE_WORDS = 34
CAMERA_MOTION_WORDS = ("camera glide", "glides", "pan ", "panning", "zoom", "orbit", "dolly", "tracking shot", "circular camera")
# Staging that makes her wait before talking squeezes the speech into part of the clip.
SPEECH_DELAY_PHRASES = ("finishes speaking", "once she faces", "then speaks", "before she speaks", "after turning")

AUDIO_LINE = (
    "For the audio, generate a highly realistic female voice with a standard Malaysian Malay "
    "(Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. No background music, "
    "only her voice and soft ambient sound. Ensure there are no text overlays or watermarks."
)
PACE_LINE = (
    "She speaks continuously in a warm, natural, conversational tone at a relaxed but steady pace, "
    "like chatting with a close friend, from the first second until the clip ends, without long pauses, "
    "and keeps talking naturally while she turns."
)

PAIRINGS = {1: (0, 1), 2: (1, 2), 3: (2, 0)}  # Scene: (start frame idx, end frame idx)

COMPOSER = ".base-prompt-box"
OVERLAY = ".cdk-overlay-container"


class FlowError(RuntimeError):
    """A pre-submit check failed; the scene must not be rendered."""


# ---------------------------------------------------------------------------
# Keyframes and prompt data
# ---------------------------------------------------------------------------

def resolve_keyframes(prefix: str | None) -> tuple[str, list[Path]]:
    """Return (prefix, [frame1, frame2, frame3]) for one product, never mixing products."""
    from supabase_client import get_product_keyframes

    if not prefix:
        newest = sorted(KEYFRAMES_DIR.glob("*_frame1*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not newest:
            raise FlowError(f"No *_frame1*.jpg keyframes found in {KEYFRAMES_DIR}")
        prefix = re.sub(r"_frame1(_front)?$", "", newest[0].stem)

    info = get_product_keyframes(prefix, KEYFRAMES_DIR)
    frames = [info["frames"][k]["local_path"] for k in ("frame_1_front", "frame_2_side", "frame_3_shoulder")]
    if not all(frames):
        raise FlowError(f"Keyframe trio for prefix '{prefix}' is incomplete: {frames}")
    return prefix, [Path(f) for f in frames]


def load_scene_prompts(prefix: str) -> dict:
    """Load the visual prompts + spoken lines from the Supabase record whose keyframes match `prefix`."""
    from supabase_client import get_supabase_client

    client = get_supabase_client()
    if not client:
        raise FlowError("Supabase is not configured; pass --prompt for a single scene instead.")
    rows = (
        client.table("gemini_flow_generations")
        .select("product_name, scenes, keyframe_urls, created_at")
        .order("created_at", desc=True)
        .limit(25)
        .execute()
    ).data or []
    row = next((r for r in rows if any(f"/{prefix}_frame" in (u or "") for u in (r.get("keyframe_urls") or []))), None)
    if not row:
        raise FlowError(f"No Supabase generation record has keyframe_urls for prefix '{prefix}'.")

    scenes = row.get("scenes") or {}
    visual = scenes.get("visual_prompts") or {}
    spoken = scenes.get("spoken_dialogue") or {}
    combined = {1: scenes.get("scene_1_intro"), 2: scenes.get("scene_2_detail"), 3: scenes.get("scene_3_outro")}
    out = {"product": row.get("product_name"), "visual": {}, "dialogue": {}}
    for i in (1, 2, 3):
        vis = visual.get(f"scene_{i}") or (combined[i] or "").split("Spoken Malay (Lip-sync):")[0]
        dia = spoken.get(f"scene_{i}")
        if not dia and combined[i] and "Spoken Malay (Lip-sync):" in combined[i]:
            dia = combined[i].split("Spoken Malay (Lip-sync):", 1)[1]
        out["visual"][i] = (vis or "").strip()
        out["dialogue"][i] = (dia or "").strip().strip('"').strip()
    return out


def build_scene_prompt(visual: str, dialogue: str) -> str:
    """Combine the English visual direction and the verbatim Malay lip-sync line, validating both."""
    visual = visual.strip()
    if "Spoken Malay (Lip-sync):" in visual:
        visual, embedded = visual.split("Spoken Malay (Lip-sync):", 1)
        visual = visual.strip()
        dialogue = dialogue or embedded.strip().strip('"')
    if not visual:
        raise FlowError("Visual prompt is empty.")
    if not dialogue:
        raise FlowError("Spoken Malay dialogue is empty; Flow would render a silent or muddled clip.")

    words = len(re.findall(r"[\w'-]+", dialogue))
    if words > MAX_DIALOGUE_WORDS:
        raise FlowError(
            f"Dialogue has {words} words; over {MAX_DIALOGUE_WORDS} gets cut off before the 10s clip ends. "
            f"Trim it to {MIN_DIALOGUE_WORDS}-{MAX_DIALOGUE_WORDS} words:\n  {dialogue}"
        )
    if words < MIN_DIALOGUE_WORDS:
        raise FlowError(
            f"Dialogue has only {words} words; under {MIN_DIALOGUE_WORDS} the voice gets stretched and sounds "
            f"unnatural. Rewrite it as 2-3 natural spoken sentences ({MIN_DIALOGUE_WORDS}-{MAX_DIALOGUE_WORDS} words):\n  {dialogue}"
        )
    if re.search(r"[:;]", dialogue):
        raise FlowError(
            "Spoken line contains ':' or ';', which reads like a list and causes odd pauses. "
            f"Use commas and full stops, as people actually speak:\n  {dialogue}"
        )
    lowered = visual.lower()
    moving = [w.strip() for w in CAMERA_MOTION_WORDS if w in lowered]
    if moving:
        print(f"WARNING: visual prompt asks for camera motion {moving}; keyframes share one background, "
              "so prefer 'Static locked-off vertical shot' with the subject turning.")
    delayed = [w for w in SPEECH_DELAY_PHRASES if w in lowered]
    if delayed:
        print(f"WARNING: visual prompt delays her speech {delayed}; let her talk through the whole clip, "
              "including while she turns.")

    if "for the audio" not in lowered:
        visual = f"{visual} {AUDIO_LINE}"
    if "conversational tone" not in visual.lower():
        visual = f"{visual} {PACE_LINE}"
    return f'{visual}\n\nSpoken Malay (Lip-sync): "{dialogue}"'


# ---------------------------------------------------------------------------
# Image matching
# ---------------------------------------------------------------------------

def _thumb(img: Image.Image) -> Image.Image:
    return img.convert("L").resize((32, 56), Image.BILINEAR)


def closest_keyframe(image_bytes: bytes, candidates: list[Path]) -> tuple[Path, dict[str, float]]:
    got = _thumb(Image.open(io.BytesIO(image_bytes)))
    scores = {p.name: ImageStat.Stat(ImageChops.difference(got, _thumb(Image.open(p)))).mean[0] for p in candidates}
    best = min(candidates, key=lambda p: scores[p.name])
    return best, scores


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

BRAVE_DEVTOOLS_FILE = Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/User Data/DevToolsActivePort"


async def connect_to_brave(port: int = 9222):
    """Connect to Brave via Chrome DevTools Protocol.

    1) Brave launched with --remote-debugging-port=9222 serves http://127.0.0.1:9222/json/version.
    2) Brave with remote debugging switched on from inside the browser answers 404 there and only
       accepts the websocket path written to its DevToolsActivePort file; the first connection waits
       for the user to approve a prompt in Brave, later ones connect straight away.
    """
    p = await async_playwright().start()
    try:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=6000)
        return p, browser
    except Exception as http_err:
        if BRAVE_DEVTOOLS_FILE.is_file():
            lines = BRAVE_DEVTOOLS_FILE.read_text(encoding="utf-8").split()
            if len(lines) >= 2:
                ws_url = f"ws://127.0.0.1:{lines[0]}{lines[1]}"
                print(f"Connecting to Brave via {ws_url} (approve the remote-debugging prompt in Brave if it appears)...")
                try:
                    return p, await p.chromium.connect_over_cdp(ws_url, timeout=120000)
                except Exception as ws_err:
                    http_err = ws_err
        await p.stop()
        raise RuntimeError(
            f"Could not connect to Brave CDP on port {port}: {str(http_err).splitlines()[0]}\n"
            "Launch Brave with --remote-debugging-port=9222 --remote-allow-origins=*, or switch on remote "
            "debugging in Brave and approve its prompt."
        )


def _project_root(url: str) -> str:
    """https://flow.google.com/u/5/project/<id>[/edit/...][?...] -> https://flow.google.com/u/5/project/<id>"""
    m = re.match(r"(https://[^/]+/(?:u/\d+/)?project/[0-9a-f-]{36})", url)
    if not m:
        raise FlowError(f"Not a Flow project URL: {url}")
    return m.group(1)


def load_projects() -> dict:
    if PROJECTS_FILE.is_file():
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    return {}


def record_project(prefix: str, name: str, url: str):
    projects = load_projects()
    projects[prefix] = {"name": name, "url": url, "created": datetime.now().strftime("%Y-%m-%d %H:%M")}
    PROJECTS_FILE.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def project_url_for(prefix: str, override: str | None) -> str:
    """The product's own project: --project-url if given, else the one recorded for this prefix."""
    if override:
        return _project_root(override)
    entry = load_projects().get(prefix)
    if not entry:
        raise FlowError(
            f"No Flow project recorded for '{prefix}'. Every product needs its own project:\n"
            f'  python automate_flow.py --create-project "<Product name>" --prefix {prefix}'
        )
    return entry["url"]


async def create_flow_project(browser, name: str) -> str:
    """Create a new Flow project in its own tab, rename it to `name`, and return its URL."""
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = await context.new_page()  # never take over the user's own Flow tab
    await page.goto(FLOW_URL, wait_until="domcontentloaded")
    new_btn = page.locator("button").filter(has_text=re.compile(r"New project", re.I)).first
    try:
        await new_btn.wait_for(timeout=20000)
    except Exception:
        raise FlowError("Flow home page has no 'New project' button (signed out, or the UI changed).")
    await new_btn.click()
    try:
        await page.wait_for_url(re.compile(r"/project/[0-9a-f-]{36}"), timeout=30000)
    except Exception:
        raise FlowError("Clicking 'New project' did not open a project.")
    url = _project_root(page.url)

    title = page.locator("input.editable-text-input").first
    await title.wait_for(timeout=15000)
    await title.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.insert_text(name)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(1500)

    # Prove the rename was saved by reloading the project.
    await page.reload(wait_until="domcontentloaded")
    await page.locator("input.editable-text-input").first.wait_for(timeout=15000)
    saved = (await page.locator("input.editable-text-input").first.input_value()).strip()
    if saved != name:
        raise FlowError(f"Project created at {url}, but its title is '{saved}', not '{name}'. Rename it by hand.")
    print(f"Created Flow project '{name}': {url}")
    return url


async def get_flow_page(browser, project_url: str):
    """Use a tab already showing this product's project, or open the project in a new tab."""
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    root = _project_root(project_url)
    match = [pg for pg in context.pages if pg.url.startswith(root)]
    page = match[0] if match else await context.new_page()  # never repurpose another project's tab
    if not match or "/edit/" in page.url:
        await page.goto(root, wait_until="domcontentloaded")
    await page.bring_to_front()
    await page.locator(f"{COMPOSER} [contenteditable='true']").wait_for(timeout=20000)
    print(f"Active Flow project: {page.url}")
    return page


def _slot(page, index: int):
    return page.locator(f"{COMPOSER} .frame-trigger").nth(index)


async def clear_composer(page):
    clear_btn = page.locator(f"{COMPOSER} button[aria-label='Clear prompt']")
    if await clear_btn.count() and await clear_btn.first.is_visible():
        await clear_btn.first.click()
        await page.wait_for_timeout(800)
    filled = await page.locator(f"{COMPOSER} img.chip-image").count()
    if filled:
        raise FlowError(f"Composer still has {filled} attached frame(s) after 'Clear prompt'.")


async def ensure_settings(page):
    """Open the settings menu and force every required toggle and the model, then verify."""
    await page.locator(f"{COMPOSER} button[aria-label='Settings trigger']").click()
    overlay = page.locator(OVERLAY)
    model_btn = overlay.locator("button[aria-label='Select model family']")
    await model_btn.wait_for(timeout=5000)

    radios = overlay.locator("button[role='radio']")
    for label in REQUIRED_TOGGLES:
        # Rendered text is "<icon ligature> <label>", e.g. "crop_9_16 9:16"; match the label word only.
        texts = await radios.evaluate_all("els => els.map(e => e.innerText.trim().split(/\\s+/).pop())")
        matches = [i for i, t in enumerate(texts) if t == label]
        if len(matches) != 1:
            raise FlowError(f"Settings option '{label}' not found (options: {texts}).")
        btn = radios.nth(matches[0])
        if await btn.get_attribute("aria-checked") != "true":
            await btn.click()
            await page.wait_for_timeout(400)
        if await btn.get_attribute("aria-checked") != "true":
            raise FlowError(f"Could not select settings option '{label}'.")

    if REQUIRED_MODEL not in (await model_btn.inner_text()):
        await model_btn.click()
        await overlay.locator("button[role='menuitem']").filter(has_text=REQUIRED_MODEL).first.click()
        await page.wait_for_timeout(500)
        if REQUIRED_MODEL not in (await model_btn.inner_text()):
            raise FlowError(f"Could not select model '{REQUIRED_MODEL}'.")

    cost = overlay.get_by_text(re.compile(r"Generating will use"))
    if await cost.count():
        print(f"  {(await cost.first.inner_text()).strip()}")
    await page.keyboard.press("Escape")
    await model_btn.wait_for(state="detached", timeout=5000)

    summary = await page.locator(f"{COMPOSER} button[aria-label='Settings trigger']").inner_text()
    if not all(s in summary for s in ("Video", "720p", "10s", "9_16", "x1")):
        raise FlowError(f"Settings summary looks wrong after configuring: '{summary}'")
    print(f"  Settings verified: {REQUIRED_MODEL} | {' · '.join(REQUIRED_TOGGLES)}")


async def attach_frame(page, slot_index: int, frame: Path):
    """Open the slot picker, search the exact filename, upload it if missing, and click the exact row."""
    slot_name = ("Start", "End")[slot_index]
    slot = _slot(page, slot_index)
    await slot.locator("button.empty-chip").click()
    overlay = page.locator(OVERLAY)
    search = overlay.locator("input.search-input").first
    await search.wait_for(timeout=5000)

    async def click_exact_row(timeout_ms: int) -> bool:
        await search.fill(frame.name)
        rows = overlay.locator("button.asset-item")
        for _ in range(timeout_ms // 250):
            for i in range(await rows.count()):
                # Row text is "<name>" (narrow layout) or "<name>\nImage" (wide layout).
                if (await rows.nth(i).inner_text()).strip().split("\n")[0].strip() == frame.name:
                    await rows.nth(i).click()
                    # Wide layout previews the asset first and needs an explicit 'Add to prompt'.
                    for _ in range(8):
                        if await slot.locator("img.chip-image").count() or await click_add_to_prompt():
                            break
                        await page.wait_for_timeout(250)
                    return True
            await page.wait_for_timeout(250)
        return False

    async def click_add_to_prompt() -> bool:
        # The button re-renders while an upload finishes, so never wait long on a stale handle.
        add_btn = overlay.locator("button:has-text('Add to prompt')").first
        try:
            if await add_btn.is_visible():
                await add_btn.click(timeout=3000)
                return True
        except Exception:
            pass
        return False

    if not await click_exact_row(4000):
        print(f"  '{frame.name}' is not in this project yet; uploading...")
        async with page.expect_file_chooser(timeout=5000) as chooser:
            await overlay.locator("button[aria-label='Upload media'], button:has-text('Upload media')").first.click()
        await (await chooser.value).set_files(str(frame))
        for _ in range(120):  # up to 60s for the upload to land
            if await slot.locator("img.chip-image").count():
                break
            if not await click_add_to_prompt() and await search.is_visible():
                await click_exact_row(500)
            await page.wait_for_timeout(500)

    try:
        await slot.locator("img.chip-image").wait_for(timeout=15000)
    except Exception:
        raise FlowError(f"{slot_name} slot is still empty after selecting '{frame.name}'.")
    if await search.is_visible():
        await page.keyboard.press("Escape")
    print(f"  {slot_name} slot filled with '{frame.name}'")


async def verify_slot(page, slot_index: int, expected: Path, candidates: list[Path]):
    """Download the slot's image and confirm it is the expected keyframe, not another pose or product."""
    slot_name = ("Start", "End")[slot_index]
    img = _slot(page, slot_index).locator("img.chip-image")
    src = ""
    for _ in range(40):
        src = await img.get_attribute("src") or ""
        if src.startswith("http"):
            break
        await page.wait_for_timeout(250)
    if not src.startswith("http"):
        raise FlowError(f"{slot_name} slot image never finished loading.")

    resp = await page.context.request.get(src)
    if not resp.ok:
        raise FlowError(f"Could not download {slot_name} slot image (HTTP {resp.status}).")
    best, scores = closest_keyframe(await resp.body(), candidates)
    detail = ", ".join(f"{k}={v:.2f}" for k, v in scores.items())
    if best != expected or scores[expected.name] > CHIP_MATCH_MAX_DIFF:
        raise FlowError(f"{slot_name} slot does NOT hold {expected.name} (diffs: {detail}).")
    print(f"  {slot_name} slot verified as {expected.name} (diff {scores[expected.name]:.2f})")


async def type_prompt(page, prompt: str):
    editor = page.locator(f"{COMPOSER} div.ProseMirror[role='textbox']")
    await editor.click()
    await page.keyboard.press("Control+A")
    await page.keyboard.press("Backspace")
    await page.keyboard.insert_text(prompt)
    await page.wait_for_timeout(800)
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    typed = norm(await editor.inner_text())
    visual, spoken = prompt.split("Spoken Malay (Lip-sync):", 1)
    if norm(visual)[:80] not in typed or norm("Spoken Malay (Lip-sync):" + spoken) not in typed:
        raise FlowError("Prompt text in the composer does not match what was typed.")


async def render_scene(page, scene: int, prompt: str, start: Path, end: Path, trio: list[Path], dry_run: bool) -> bool:
    print(f"\n--- Scene {scene}: {start.name} -> {end.name} ---")
    if start == end:
        raise FlowError("Start and End frames are the same file.")
    candidates = list(dict.fromkeys([*trio, start, end]))
    try:
        await page.keyboard.press("Escape")  # close any picker or menu left open
        await clear_composer(page)
        await ensure_settings(page)
        await attach_frame(page, 0, start)
        await attach_frame(page, 1, end)
        await type_prompt(page, prompt)

        # Final gate: re-check both slots after everything else has been touched.
        await verify_slot(page, 0, start, candidates)
        await verify_slot(page, 1, end, candidates)
    except FlowError:
        raise
    except Exception as err:
        raise FlowError(f"Browser step failed before submit: {str(err).splitlines()[0]}") from err
    ready_png = WORKSPACE / f"flow_scene{scene}_ready.png"
    await page.screenshot(path=str(ready_png))
    print(f"  Pre-submit screenshot: {ready_png.name}")

    if dry_run:
        print(f"  DRY RUN: all checks passed; not submitting Scene {scene}.")
        await clear_composer(page)
        return True

    generate_btn = page.locator(f"{COMPOSER} button[aria-label='Start generation']")
    if await generate_btn.is_disabled():
        raise FlowError("'Start generation' is disabled.")
    await generate_btn.click()
    # Flow empties the composer once it accepts the job.
    for _ in range(30):
        if await page.locator(f"{COMPOSER} img.chip-image").count() == 0:
            break
        await page.wait_for_timeout(500)
    else:
        raise FlowError("Composer did not reset after clicking 'Start generation'; the job may not have been queued.")

    await page.wait_for_timeout(3000)
    await page.screenshot(path=str(WORKSPACE / "flow_renders_progress.png"))
    print(f"  Scene {scene} queued.")
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_flow_pipeline(
    scene_num: int = 1,
    render_all: bool = False,
    prefix: str | None = None,
    prompt_override: str | None = None,
    start_frame_override: str | None = None,
    end_frame_override: str | None = None,
    project_url: str | None = None,
    dry_run: bool = False,
) -> bool:
    prefix, trio = resolve_keyframes(prefix)
    print(f"Keyframes ({prefix}): {', '.join(p.name for p in trio)}")
    project_url = project_url_for(prefix, project_url)
    print(f"Flow project for this product: {project_url}")
    scenes_to_run = [1, 2, 3] if render_all else [scene_num]

    # Build and validate every prompt before touching the browser.
    prompts: dict[int, str] = {}
    if prompt_override and not render_all:
        prompts[scene_num] = build_scene_prompt(prompt_override, "")
    else:
        data = load_scene_prompts(prefix)
        print(f"Prompts from record: {data['product']}")
        for s in scenes_to_run:
            prompts[s] = build_scene_prompt(data["visual"][s], data["dialogue"][s])

    print("Connecting to Brave on port 9222...")
    p, browser = await connect_to_brave()
    try:
        page = await get_flow_page(browser, project_url)
        for s in scenes_to_run:
            start, end = trio[PAIRINGS[s][0]], trio[PAIRINGS[s][1]]
            if not render_all:
                start = Path(start_frame_override) if start_frame_override else start
                end = Path(end_frame_override) if end_frame_override else end
            try:
                await render_scene(page, s, prompts[s], start, end, trio, dry_run)
            except FlowError as err:
                print(f"\nABORTED Scene {s} (nothing was submitted): {err}")
                try:
                    await page.screenshot(path=str(WORKSPACE / f"flow_scene{s}_aborted.png"))
                except Exception:
                    pass
                return False
            if s != scenes_to_run[-1]:
                await page.wait_for_timeout(4000)
        return True
    finally:
        # Never close the user's browser
        await p.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Flow AI 10s portrait video rendering in Brave")
    parser.add_argument("--scene", type=int, default=1, choices=[1, 2, 3], help="Scene number to render (1, 2, or 3)")
    parser.add_argument("--all", action="store_true", help="Queue all 3 scenes sequentially (Frame 1->2, 2->3, 3->1)")
    parser.add_argument("--prefix", type=str, help="Keyframe prefix, e.g. striped_split_cuff_blouse (default: newest trio)")
    parser.add_argument("--prompt", type=str, help="Custom scene prompt incl. 'Spoken Malay (Lip-sync): \"...\"' (single scene only)")
    parser.add_argument("--start-frame", type=str, help="Path to start frame image (single scene only)")
    parser.add_argument("--end-frame", type=str, help="Path to end frame image (single scene only)")
    parser.add_argument("--project-url", type=str, help="Override the product's recorded Flow project")
    parser.add_argument("--create-project", type=str, metavar="NAME",
                        help="Create this product's own Flow project named NAME, record it for --prefix, and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run every check and screenshot, but do not submit")
    parser.add_argument("--latest", action="store_true", help="Kept for compatibility; the newest keyframe trio is the default")
    args = parser.parse_args()

    if args.create_project:
        if not args.prefix:
            parser.error("--create-project needs --prefix (the product's keyframe prefix)")
        existing = load_projects().get(args.prefix)
        if existing:
            print(f"'{args.prefix}' already has its Flow project '{existing['name']}': {existing['url']}")
            sys.exit(0)

        async def _create():
            p, browser = await connect_to_brave()
            try:
                url = await create_flow_project(browser, args.create_project.strip())
                record_project(args.prefix, args.create_project.strip(), url)
                print(f"Recorded in {PROJECTS_FILE.name}: {args.prefix} -> {url}")
            finally:
                await p.stop()  # never close the user's browser

        try:
            asyncio.run(_create())
            sys.exit(0)
        except Exception as exc:
            print("Flow project creation error:", exc)
            sys.exit(1)

    try:
        ok = asyncio.run(run_flow_pipeline(
            scene_num=args.scene,
            render_all=args.all,
            prefix=args.prefix,
            prompt_override=args.prompt,
            start_frame_override=args.start_frame,
            end_frame_override=args.end_frame,
            project_url=args.project_url,
            dry_run=args.dry_run,
        ))
        sys.exit(0 if ok else 1)
    except Exception as exc:
        print("Flow automation error:", exc)
        sys.exit(1)
