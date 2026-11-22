"""
Assemble the finished TikTok video for one product
==================================================
Flow renders three 10s clips (Frame 1->2, 2->3, 3->1) and Suno makes the instrumental. This
script turns them into ONE post-ready 9:16 MP4, so nothing is left for CapCut:

  1. Downloads every rendered clip in the product's own Flow project (through signed-in Brave).
  2. QA: works out which clip is Scene 1/2/3 by matching each clip's first and last frames to the
     keyframes. A clip that matches no keyframe was rendered without its frames (text-to-video:
     a different woman) and is refused. Each clip must also be ~10s long and have her voice.
  3. Joins the clips. Each clip ends on the frame the next one starts with, so hard cuts are
     seamless. Two light zooms add movement: an ease-out on the hook (so the first frame is a
     close-up, not the same full-body shot as every other video) and a punch-in on the Scene 2
     detail beat while she keeps talking.
  4. Lays the Suno instrumental under her voice, ducked while she talks, loudness -14 LUFS.
  5. Burns in Malay subtitles from the spoken lines; the hook sentence shows as a yellow text box
     while she says it (most viewers start muted). Text sits over her legs, never her face.
  6. Writes final/<prefix>_final.mp4 (1080x1920, 30fps, under Gmail's 25 MB), a QA contact sheet
     final/<prefix>/qa_sheet.jpg, and records final_video in generations/<prefix>.json.
     reply_gmail.py --prefix <prefix> attaches that MP4 to the caption reply (Step 7).

Usage:
    python assemble_video.py --prefix <prefix>                # download from Flow and assemble
    python assemble_video.py --prefix <prefix> --wait 900     # wait up to 15 min for renders/QA
    python assemble_video.py --prefix <prefix> --qa-only      # download + match clips, no video
    python assemble_video.py --prefix <prefix> --clips s1.mp4 s2.mp4 s3.mp4 [--bgm song.m4a]
    python assemble_video.py --prefix <prefix> --no-bgm --no-subs --no-motion

Exit codes: 0 = video written, 1 = failed (nothing written), 2 = clips failed QA.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw, ImageStat

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)  # type: ignore[attr-defined]

WORKSPACE = Path(__file__).resolve().parent
FINAL_DIR = WORKSPACE / "final"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

W, H, FPS = 1080, 1920, 30
CLIP_MIN_S, CLIP_MAX_S = 8.0, 10.5
# Mean grayscale difference (0-255) between a clip's first/last frame and a keyframe at 36x64.
# Calibrated 2026-11-21 on jaket_blazer_wanita_elegan: the right keyframe scores 6.9-7.8, the other
# two poses of the same woman and room 12.5-20.8. A clip must match one keyframe under the limit AND
# beat the runner-up by the margin, or it is treated as rendered without its frames.
FRAME_MATCH_MAX = 10.0
FRAME_MATCH_MARGIN = 3.0
GMAIL_MAX_MB = 24.0
PAIR_TO_SCENE = {(0, 1): 1, (1, 2): 2, (2, 0): 3}  # (start keyframe, end keyframe) -> scene
FRAME_NAMES = ("front", "side", "shoulder")

# Suno BGM only through Suno's own Download button: its CDN files are encrypted for the web player,
# and Free-plan songs have no download allowance and no commercial-use rights (checked 2026-11-21).
# Never decrypt the CDN file or record the player to get around that.

# Subtitle look. TikTok covers the bottom ~22% (caption, sound), the right edge (buttons) and the
# top tabs; her face and the garment fill the upper 60%. So all text sits at ~65-71% height.
FONT_FILES = {"Arial": "arialbd.ttf", "Arial Black": "ariblk.ttf"}
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Arial,70,&H00FFFFFF,&H000000FF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,6,3,2,110,150,560,1
Style: Hook,Arial Black,64,&H00141414,&H000000FF,&H0000D4FF,&H00000000,0,0,0,0,100,100,0,0,3,22,0,2,110,150,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


class AssemblyError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------

def ffmpeg(args: list[str], cwd: Path | None = None) -> str:
    """Run ffmpeg, return its stderr log; raise with the tail of the log on failure."""
    out = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-y", *args], cwd=cwd,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        tail = "\n".join(out.stderr.strip().splitlines()[-12:])
        raise AssemblyError(f"ffmpeg failed ({out.returncode}):\n{tail}")
    return out.stderr


def probe(path: Path) -> dict:
    log = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    size = re.search(r"Video:.*?(\d{3,5})x(\d{3,5})", log)
    return {"duration": dur, "has_audio": "Audio:" in log,
            "width": int(size.group(1)) if size else 0, "height": int(size.group(2)) if size else 0}


def grab_frame(path: Path, at: float | None = None, from_end: float | None = None) -> Image.Image:
    seek = ["-sseof", f"-{from_end}"] if from_end is not None else ["-ss", f"{at or 0:.2f}"]
    out = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", *seek, "-i", str(path), "-frames:v", "1",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    if out.returncode != 0 or not out.stdout:
        raise AssemblyError(f"Could not read a frame from {path.name}")
    return Image.open(io.BytesIO(out.stdout)).convert("RGB")


def _thumb(img: Image.Image) -> Image.Image:
    return img.convert("L").resize((36, 64), Image.Resampling.BILINEAR)


def frame_diff(a: Image.Image, b: Image.Image) -> float:
    """Mean grayscale difference after matching overall brightness.

    Flow's video frames come out ~9 levels darker than the keyframes they start from (2026-11-22), which
    added ~9 to every diff and failed correct clips. Matching the means compares pose and layout instead:
    right pose ~4-5.5, other poses 9-20, another product's keyframes 46+.
    """
    ta, tb = _thumb(a), _thumb(b)
    shift = round(ImageStat.Stat(tb).mean[0] - ImageStat.Stat(ta).mean[0])
    ta = ta.point(lambda v: max(0, min(255, v + shift)))
    return ImageStat.Stat(ImageChops.difference(ta, tb)).mean[0]


def speech_span(path: Path, duration: float) -> tuple[float, float, float]:
    """(first speech, last speech, seconds of sound) from silencedetect; spread over the clip if unclear."""
    log = ffmpeg(["-i", str(path), "-vn", "-af", "silencedetect=noise=-32dB:d=0.35", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    silent = sum(e - s for s, e in zip(starts, ends)) + (duration - starts[-1] if len(starts) > len(ends) else 0)
    begin = ends[0] if starts and starts[0] <= 0.05 and ends else 0.0
    finish = starts[-1] if starts and (len(starts) > len(ends) or abs(ends[-1] - duration) < 0.15) else duration
    if finish - begin < 3.0:
        begin, finish = 0.25, duration - 0.3
    return round(begin, 2), round(finish, 2), round(max(0.0, duration - silent), 2)


# ---------------------------------------------------------------------------
# Inputs: record, Flow clips, Suno track
# ---------------------------------------------------------------------------

def load_inputs(prefix: str) -> tuple[dict, list[Path]]:
    from generation_store import find_keyframes, load_record
    record = load_record(prefix)
    if not record:
        raise AssemblyError(f"No generations/{prefix}.json. Run Step 9 first.")
    kf = find_keyframes(prefix)
    if not kf["all_present"]:
        raise AssemblyError(f"Keyframe trio incomplete in keyframes/: {kf['paths']}")
    trio = [Path(kf["frames"][k]["local_path"]) for k in ("frame_1_front", "frame_2_side", "frame_3_shoulder")]
    return record, trio


async def download_flow_clips(project_url: str, dest: Path) -> list[Path]:
    """Every rendered video in the project, newest first (Flow lists newest first)."""
    from automate_flow import _project_root, connect_to_brave
    for old in dest.glob("flow_tile*.mp4"):
        old.unlink()
    p, browser = await connect_to_brave()
    page = None
    try:
        ctx = browser.contexts[0]
        page = await ctx.new_page()
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(_project_root(project_url), wait_until="domcontentloaded")
        tiles = page.locator("flow-video-tile")
        try:
            await tiles.first.wait_for(timeout=25000)
        except Exception:
            return []
        await page.wait_for_timeout(1500)
        paths: list[Path] = []
        for i in range(await tiles.count()):
            tile = tiles.nth(i)
            await tile.scroll_into_view_if_needed()
            await tile.hover()
            src = None
            for _ in range(16):  # the <video> appears on hover
                src = await tile.evaluate("t => { const v = t.querySelector('video'); return v && (v.currentSrc || v.src) }")
                if src:
                    break
                await page.wait_for_timeout(500)
            if not src:
                print(f"  tile {i + 1}: no video yet (still rendering?)")
                continue
            resp = await ctx.request.get(src)
            body = await resp.body()
            if resp.status != 200 or len(body) < 50_000:
                print(f"  tile {i + 1}: download failed (HTTP {resp.status}, {len(body)} bytes)")
                continue
            path = dest / f"flow_tile{i + 1}.mp4"
            path.write_bytes(body)
            paths.append(path)
            await page.mouse.move(5, 450)
        return paths
    finally:
        if page:
            await page.close()  # only the tab this script opened; never the browser
        await p.stop()


def _suno_ids(record: dict) -> list[str]:
    ids = []
    for t in record.get("suno_tracks") or []:
        m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", json.dumps(t))
        if m and m.group(0) not in ids:
            ids.append(m.group(0))
    return ids


async def _suno_download(song_id: str, dest: Path) -> tuple[Path | None, str]:
    """Download a song with Suno's own menu (... > Download > MP3). Returns (file, reason if none)."""
    from automate_flow import connect_to_brave
    p, browser = await connect_to_brave()
    page = None
    try:
        ctx = browser.contexts[0]
        page = await ctx.new_page()
        await page.set_viewport_size({"width": 1400, "height": 900})
        await page.goto(f"https://suno.com/song/{song_id}", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        downloads: list = []
        page.on("download", lambda d: downloads.append(d))
        await page.locator("button[aria-label^='More options for ']:visible").first.click()
        await page.wait_for_timeout(800)
        await page.locator("[role=menuitem]", has_text="Download").first.click()
        await page.wait_for_timeout(2500)
        if await page.get_by_text("Out of Downloads").count():
            return None, ("Suno says 'Out of Downloads' (Free plan: no download allowance and no commercial-use "
                          "rights for its songs)")
        if not downloads:  # a format choice instead of a direct download
            mp3 = page.get_by_text(re.compile(r"^MP3", re.I)).first
            if await mp3.count():
                await mp3.click()
                await page.wait_for_timeout(5000)
        if not downloads:
            return None, "Suno's Download button gave no file (UI changed?)"
        target = dest / f"bgm_{song_id[:8]}{Path(downloads[0].suggested_filename).suffix or '.mp3'}"
        await downloads[0].save_as(str(target))
        return target, ""
    finally:
        if page:
            await page.close()
        await p.stop()


def download_bgm(record: dict, track_no: int, dest: Path) -> tuple[Path | None, str]:
    ids = _suno_ids(record)
    if not ids:
        return None, "the record has no suno_tracks (Step 8 not run, or songs not recorded)"
    for cached in dest.glob(f"bgm_{ids[min(track_no, len(ids)) - 1][:8]}.*"):
        if probe(cached)["duration"] > 10:  # a real, decodable song from an earlier run
            return cached, ""
        cached.unlink()
    return asyncio.run(_suno_download(ids[min(track_no, len(ids)) - 1], dest))


# ---------------------------------------------------------------------------
# QA: which clip is which scene, and is it usable?
# ---------------------------------------------------------------------------

def check_clip(path: Path, trio: list[Path]) -> dict:
    info = probe(path)
    keys = [Image.open(p).convert("RGB") for p in trio]
    first, last = grab_frame(path, at=0.05), grab_frame(path, from_end=0.15)
    d_start = [round(frame_diff(first, k), 2) for k in keys]
    d_end = [round(frame_diff(last, k), 2) for k in keys]
    s, e = d_start.index(min(d_start)), d_end.index(min(d_end))
    scene = PAIR_TO_SCENE.get((s, e))
    problems = []
    margin = min(sorted(d_start)[1] - min(d_start), sorted(d_end)[1] - min(d_end))
    if min(d_start) > FRAME_MATCH_MAX or min(d_end) > FRAME_MATCH_MAX or margin < FRAME_MATCH_MARGIN:
        problems.append(f"first/last frame matches no keyframe clearly (best {min(d_start)}/{min(d_end)}, limit "
                        f"{FRAME_MATCH_MAX}; margin {margin:.1f}, need {FRAME_MATCH_MARGIN}): rendered without "
                        "its frames (text-to-video), or the wrong product's clip?")
    elif scene is None:
        problems.append(f"starts on {FRAME_NAMES[s]} and ends on {FRAME_NAMES[e]}: not a scene pairing")
    if not CLIP_MIN_S <= info["duration"] <= CLIP_MAX_S:
        problems.append(f"duration {info['duration']:.1f}s, expected ~10s")
    if not info["has_audio"]:
        problems.append("no audio track")
    begin, finish, sound = speech_span(path, info["duration"]) if info["has_audio"] else (0, 0, 0)
    if info["has_audio"] and sound < 4.0:
        problems.append(f"only {sound}s of sound: silent or muddled voice")
    return {"file": path.name, "path": str(path), "scene": scene, "start_diff": d_start, "end_diff": d_end,
            "duration": round(info["duration"], 2), "speech": [begin, finish], "sound_s": sound,
            "ok": not problems, "problems": problems}


def pick_scenes(checks: list[dict]) -> dict[int, dict]:
    """Best passing clip per scene; clips are newest first, so a re-render wins over the original."""
    chosen: dict[int, dict] = {}
    for c in checks:
        if c["ok"] and c["scene"] and c["scene"] not in chosen:
            chosen[c["scene"]] = c
    return chosen


def qa_sheet(chosen: dict[int, dict], trio: list[Path], out: Path) -> None:
    """3 rows (scenes) x 6: start keyframe | clip at 0.1s, 3s, 6s, 9.8s | end keyframe."""
    tw, th, pad = 180, 320, 6
    sheet = Image.new("RGB", (6 * (tw + pad) + pad, 3 * (th + pad + 24) + pad), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    pairs = {1: (0, 1), 2: (1, 2), 3: (2, 0)}
    for row, scene in enumerate((1, 2, 3)):
        c = chosen.get(scene)
        if not c:
            continue
        s, e = pairs[scene]
        cells = [Image.open(trio[s])] + [grab_frame(Path(c["path"]), at=t) for t in (0.1, 3.0, 6.0)] \
            + [grab_frame(Path(c["path"]), from_end=0.2), Image.open(trio[e])]
        labels = [f"S{scene} start key", "0.1s", "3s", "6s", "end", "end key"]
        y = pad + row * (th + pad + 24)
        for col, (img, label) in enumerate(zip(cells, labels)):
            x = pad + col * (tw + pad)
            sheet.paste(img.convert("RGB").resize((tw, th)), (x, y + 24))
            draw.text((x + 4, y + 4), label, fill=(255, 212, 0))
    sheet.save(out, quality=88)


# ---------------------------------------------------------------------------
# Subtitles and hook text
# ---------------------------------------------------------------------------

def _ass_time(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _clean(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\\", "/")


def chunk_line(text: str, max_words: int = 5) -> list[str]:
    """Subtitle chunks: split at sentence and comma breaks first, then into even chunks of <= max_words."""
    clauses = [c.strip() for c in re.findall(r"[^.?!,]+[.?!,]*", text) if c.strip()]
    merged: list[list[str]] = []
    for clause in clauses:  # a 1-2 word clause ("Ha," / "Serius,") joins the next one
        words = clause.split()
        if merged and len(merged[-1]) <= 2 and not re.search(r"[.?!]$", merged[-1][-1]):
            merged[-1] += words
        else:
            merged.append(words)
    chunks = []
    for words in merged:
        n = -(-len(words) // max_words)  # ceil
        size = -(-len(words) // n)
        chunks += [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
    return chunks


def hook_sentence(line: str) -> str:
    m = re.match(r"(.+?[.?!])(\s|$)", line.strip())
    return (m.group(1) if m else line).strip()


def build_ass(dialogue: dict[int, str], spans: dict[int, tuple[float, float]], offsets: dict[int, float],
              hook: str | None, subs: bool) -> str:
    """The hook shows as a yellow box while she says the hook sentence (min 2.2s), in the subtitle zone
    so it never covers her face or the garment; normal subtitles carry on from the next sentence."""
    events = []
    for scene in (1, 2, 3):
        line = dialogue[scene]
        units: list[tuple[str, str]] = []
        if scene == 1 and hook and line.startswith(hook):
            units.append(("Hook", hook))
            line = line[len(hook):].strip()
        units += [("Sub", c) for c in chunk_line(line)]
        begin, finish = spans[scene]
        weights = [len(t) + (6 if re.search(r"[.?!]$", t) else 3 if t.endswith(",") else 0) for _, t in units]
        t = offsets[scene] + begin
        unit = (finish - begin) / max(1, sum(weights))
        for (style, text), w in zip(units, weights):
            end = t + w * unit
            if style == "Hook":
                start, end = 0.0, max(end, 2.2)
                events.append(f"Dialogue: 1,{_ass_time(start)},{_ass_time(end)},Hook,,0,0,0,,"
                              f"{{\\fad(100,150)}}{_clean(text)}")
            elif subs:
                events.append(f"Dialogue: 0,{_ass_time(t)},{_ass_time(end - 0.02)},Sub,,0,0,0,,"
                              f"{_clean(re.sub(r'[,.]$', '', text))}")
            t = end
    return ASS_HEADER + "\n".join(events) + "\n"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _zoom_filter(scene: int, motion: bool) -> str:
    """Scale to 1080x1920 (cover), with a time-based zoom for movement, then crop back to 1080x1920."""
    if not motion or scene == 3:
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    if scene == 1:  # hook: start on a close-up of her upper body, ease out to the full outfit in 0.9s
        z, cy = "(1+0.20*pow(max(0,1-t/0.9),2))", "0.34"
    else:  # scene 2: punch in on the garment detail from 2.0s to 4.6s while she keeps talking
        z, cy = "(1+0.30*min(1,max(0,(t-2.0)/0.25))*min(1,max(0,(4.6-t)/0.25)))", "0.46"
    return (f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame:flags=bicubic,"
            f"crop={W}:{H}:x='(iw-{W})/2':y='(ih-{H})*{cy}'")


def render(chosen: dict[int, dict], record: dict, bgm: Path | None, work: Path, out: Path,
           subs: bool, hook_text: bool, motion: bool, crf: int = 20, maxrate: str = "6M") -> dict:
    dialogue = {i: ((record.get("scenes") or {}).get("spoken_dialogue") or {}).get(f"scene_{i}", "") for i in (1, 2, 3)}
    durs = {i: min(chosen[i]["duration"], 10.0) for i in (1, 2, 3)}
    offsets = {1: 0.0, 2: durs[1], 3: durs[1] + durs[2]}
    total = sum(durs.values())
    spans = {i: (min(chosen[i]["speech"][0], durs[i] - 3), min(chosen[i]["speech"][1], durs[i])) for i in (1, 2, 3)}

    fonts = work / "fonts"
    fonts.mkdir(exist_ok=True)
    for name in FONT_FILES.values():
        src = Path("C:/Windows/Fonts") / name
        if src.is_file() and not (fonts / name).is_file():
            shutil.copy(src, fonts / name)
    hook = hook_sentence(dialogue[1]) if hook_text else None
    (work / "subs.ass").write_text(build_ass(dialogue, spans, offsets, hook, subs), encoding="utf-8")

    inputs, parts = [], []
    for i in (1, 2, 3):
        inputs += ["-i", chosen[i]["path"]]
        fade_out = max(0.0, durs[i] - 0.05)
        parts.append(f"[{i - 1}:v]trim=0:{durs[i]},setpts=PTS-STARTPTS,fps={FPS},{_zoom_filter(i, motion)},"
                     f"setsar=1,format=yuv420p[v{i}]")
        parts.append(f"[{i - 1}:a]atrim=0:{durs[i]},asetpts=PTS-STARTPTS,aresample=48000,"
                     f"aformat=channel_layouts=stereo,afade=t=in:d=0.03,afade=t=out:st={fade_out:.2f}:d=0.05[a{i}]")
    parts.append("[v1][a1][v2][a2][v3][a3]concat=n=3:v=1:a=1[vcat][voice]")
    parts.append("[vcat]ass=subs.ass:fontsdir=fonts[vout]" if (subs or hook) else "[vcat]null[vout]")
    if bgm:
        inputs += ["-stream_loop", "-1", "-i", str(bgm)]
        parts.append("[voice]asplit=2[vmain][vkey]")
        parts.append(f"[3:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.2f},asetpts=PTS-STARTPTS,"
                     f"volume=0.22,afade=t=in:d=0.8,afade=t=out:st={total - 1.5:.2f}:d=1.5[bgm]")
        parts.append("[bgm][vkey]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[bgmd]")
        parts.append("[vmain][bgmd]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    else:
        parts.append("[voice]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    (work / "graph.txt").write_text(";\n".join(parts), encoding="utf-8")

    tmp = work / "render.mp4"
    ffmpeg([*inputs, "-filter_complex_script", "graph.txt", "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-maxrate", maxrate, "-bufsize", "12M",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-movflags", "+faststart", "-t", f"{total:.2f}", str(tmp)], cwd=work)
    shutil.move(str(tmp), out)
    return {"duration": round(probe(out)["duration"], 2), "size_mb": round(out.stat().st_size / 1e6, 1),
            "hook_text": hook, "subtitles": subs, "motion": motion}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def gather_clips(args, record: dict, trio: list[Path], work: Path) -> tuple[list[dict], dict[int, dict]]:
    if args.clips:
        checks = [check_clip(Path(c).resolve(), trio) for c in args.clips]
        return checks, pick_scenes(checks)
    from automate_flow import project_url_for
    project_url = record.get("flow_project_url") or project_url_for(args.prefix, None)
    deadline = time.time() + args.wait
    while True:
        print(f"Downloading rendered clips from {project_url} ...")
        clips = asyncio.run(download_flow_clips(project_url, work))
        checks = [check_clip(c, trio) for c in clips]
        chosen = pick_scenes(checks)
        if len(chosen) == 3 or time.time() >= deadline:
            return checks, chosen
        print(f"  {len(chosen)}/3 scenes ready; checking again in 45s "
              f"({int(deadline - time.time())}s left of --wait).")
        time.sleep(45)


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble the finished 9:16 TikTok video for one product.")
    ap.add_argument("--prefix", required=True, help="Product keyframe prefix (generations/<prefix>.json)")
    ap.add_argument("--clips", nargs=3, metavar="MP4", help="Use these 3 clips instead of downloading from Flow")
    ap.add_argument("--bgm", help="Use this audio file instead of the record's Suno track")
    ap.add_argument("--bgm-track", type=int, default=1, help="Which recorded Suno track to use (1 or 2)")
    ap.add_argument("--no-bgm", action="store_true", help="Voice only")
    ap.add_argument("--no-subs", action="store_true", help="No burned-in subtitles")
    ap.add_argument("--no-hook-text", action="store_true", help="No on-screen hook text")
    ap.add_argument("--no-motion", action="store_true", help="No zooms")
    ap.add_argument("--wait", type=int, default=0, help="Seconds to keep checking Flow for finished renders")
    ap.add_argument("--qa-only", action="store_true", help="Download and check the clips, don't render")
    args = ap.parse_args()

    from generation_store import clean_prefix, update_record
    args.prefix = clean_prefix(args.prefix)
    record, trio = load_inputs(args.prefix)
    work = FINAL_DIR / args.prefix
    work.mkdir(parents=True, exist_ok=True)

    checks, chosen = gather_clips(args, record, trio, work)
    print(f"\nClip QA ({len(checks)} clip(s); keyframe diff limit {FRAME_MATCH_MAX}):")
    for c in checks:
        mark = "OK " if c["ok"] else "BAD"
        print(f"  {mark} {c['file']}: scene {c['scene']} | start diffs {c['start_diff']} | end diffs {c['end_diff']}"
              f" | {c['duration']}s | speech {c['speech'][0]}-{c['speech'][1]}s")
        for prob in c["problems"]:
            print(f"      ! {prob}")
    (work / "qa.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    if chosen:
        qa_sheet(chosen, trio, work / "qa_sheet.jpg")
        print(f"QA contact sheet: {(work / 'qa_sheet.jpg').relative_to(WORKSPACE)}  (open it and check every row)")
    missing = [s for s in (1, 2, 3) if s not in chosen]
    if missing:
        print(f"\nNOT ASSEMBLED: no usable clip for scene(s) {missing}. Re-render them "
              f"(python automate_flow.py --scene N --prefix {args.prefix}) or wait (--wait 900).")
        return 2
    if args.qa_only:
        return 0

    bgm, bgm_note = None, "voice only (--no-bgm)"
    if args.bgm:
        bgm = Path(args.bgm).resolve()
        if not bgm.is_file():
            print(f"NOT ASSEMBLED: --bgm file not found: {bgm}")
            return 1
        bgm_note = f"--bgm {bgm.name}"
    elif not args.no_bgm:
        bgm, reason = download_bgm(record, args.bgm_track, work)
        bgm_note = f"Suno track {args.bgm_track}" if bgm else f"voice only: {reason}"
        if not bgm:
            print(f"\nNOTICE: no background music: {reason}.\n  The video is assembled with her voice only. "
                  "When posting, add a sound from TikTok's Commercial Music Library (cleared for business "
                  "use) and turn its volume down under 'Original sound'. Or pass --bgm <licensed file>.")
    out = FINAL_DIR / f"{args.prefix}_final.mp4"
    print(f"\nRendering {out.relative_to(WORKSPACE)} (BGM: {bgm.name if bgm else 'none'}) ...")
    result = render(chosen, record, bgm, work, out, subs=not args.no_subs,
                    hook_text=not args.no_hook_text, motion=not args.no_motion)
    if result["size_mb"] > GMAIL_MAX_MB:
        print(f"  {result['size_mb']} MB is over Gmail's limit; re-encoding smaller.")
        result = render(chosen, record, bgm, work, out, subs=not args.no_subs,
                        hook_text=not args.no_hook_text, motion=not args.no_motion, crf=24, maxrate="4M")
    rel = out.relative_to(WORKSPACE).as_posix()
    update_record(args.prefix, final_video=rel, flow_status="all_scenes_rendered_and_checked", assembly={
        "assembled_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "clips": {f"scene_{s}": {k: chosen[s][k] for k in ("file", "start_diff", "end_diff", "duration", "speech")}
                  for s in (1, 2, 3)},
        "bgm": bgm_note, **result})
    print(f"Done: {rel} ({result['duration']}s, {result['size_mb']} MB). Recorded as final_video in "
          f"generations/{args.prefix}.json; reply_gmail.py --prefix {args.prefix} attaches it.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssemblyError as err:
        print(f"NOT ASSEMBLED: {err}")
        sys.exit(1)
