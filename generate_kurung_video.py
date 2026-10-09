"""
30-Second Motion Graphics Video Generator — Kurung Pahang Riau Ibu & Anak
=========================================================================
Generates a broadcast-quality 9:16 vertical motion graphics video (1080x1920, 30fps)
for KURUNG PAHANG RIAU IBU & ANAK PREMIUM COTTON LINEN on TikTok Shop.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import scipy.io.wavfile as wavfile
import imageio_ffmpeg

WORKSPACE = Path(__file__).resolve().parent
KEYFRAME_DIR = WORKSPACE / "keyframes"
OUTPUT_DIR = WORKSPACE / "output" / "20261009_220647"

VIDEO_PATH = WORKSPACE / "kurung_pahang_riau_motion_30s.mp4"
AUDIO_PATH = WORKSPACE / "kurung_motion_audio.wav"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SEC = 30.0
TOTAL_FRAMES = int(FPS * DURATION_SEC)

# Dusty Mauve / Anggun Palette
C_BG_TOP = (250, 242, 238)
C_BG_BOT = (235, 220, 215)
C_DARK = (38, 28, 32)
C_MAUVE = (168, 120, 140)
C_MAUVE_LIGHT = (215, 175, 190)
C_ROSE_GOLD = (205, 165, 135)
C_WHITE = (255, 255, 255)
C_YELLOW = (255, 208, 0)
C_CREAM = (250, 240, 228)
C_WARM_PINK = (220, 145, 155)
C_GRAY = (110, 105, 115)
C_LIGHT_GRAY = (242, 235, 232)


def get_font(size: int, bold: bool = True):
    font_file = "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
    if not os.path.exists(font_file):
        font_file = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    try:
        return ImageFont.truetype(font_file, size)
    except Exception:
        return ImageFont.load_default()


# ==========================================
# 1. AUDIO SYNTHESIS ENGINE (BGM + SFX)
# ==========================================

def synthesize_audio(output_path: Path):
    print("🎵 Synthesizing 30.0s Nusantara-inspired BGM & synchronized SFX...", flush=True)
    sr = 44100
    n_samples = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, n_samples, endpoint=False)

    bpm = 105.0
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4

    music_l = np.zeros(n_samples, dtype=np.float32)
    music_r = np.zeros(n_samples, dtype=np.float32)
    sfx_l = np.zeros(n_samples, dtype=np.float32)
    sfx_r = np.zeros(n_samples, dtype=np.float32)

    # Drum Synth (lighter, more delicate for traditional wear)
    def add_kick(start_time: float, gain: float = 0.70):
        idx = int(start_time * sr)
        dur = int(0.22 * sr)
        if idx >= n_samples: return
        length = min(dur, n_samples - idx)
        kt = np.linspace(0, 0.22, length, endpoint=False)
        freq = 120.0 * np.exp(-kt * 20.0) + 38.0
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.exp(-kt * 15.0)
        kick = np.sin(phase) * env * gain
        music_l[idx:idx+length] += kick
        music_r[idx:idx+length] += kick

    def add_snare(start_time: float, gain: float = 0.45):
        idx = int(start_time * sr)
        dur = int(0.18 * sr)
        if idx >= n_samples: return
        length = min(dur, n_samples - idx)
        st = np.linspace(0, 0.18, length, endpoint=False)
        tone = np.sin(2 * np.pi * 180.0 * st) * np.exp(-st * 28.0) * 0.35
        noise = (np.random.rand(length) * 2 - 1) * np.exp(-st * 20.0) * 0.5
        snare = (tone + noise) * gain
        music_l[idx:idx+length] += snare
        music_r[idx:idx+length] += snare

    def add_hat(start_time: float, gain: float = 0.20):
        idx = int(start_time * sr)
        dur = int(0.04 * sr)
        if idx >= n_samples: return
        length = min(dur, n_samples - idx)
        ht = np.linspace(0, 0.04, length, endpoint=False)
        noise = (np.random.rand(length) * 2 - 1) * np.exp(-ht * 85.0) * gain
        music_l[idx:idx+length] += noise * 0.85
        music_r[idx:idx+length] += noise * 1.15

    cur_t = 0.0
    while cur_t < DURATION_SEC - 0.2:
        b0, b1, b2, b3 = cur_t, cur_t + beat_dur, cur_t + beat_dur * 2, cur_t + beat_dur * 3
        add_kick(b0, 0.72)
        add_kick(b1 + beat_dur * 0.5, 0.55)
        add_kick(b2, 0.65)
        add_snare(b1, 0.50)
        add_snare(b3, 0.55)
        for step in range(16):
            ht_time = cur_t + step * (beat_dur / 4)
            h_gain = 0.28 if step % 4 == 0 else (0.18 if step % 2 == 0 else 0.11)
            add_hat(ht_time, h_gain)
        cur_t += bar_dur

    # Warm Acoustic Bass
    bass_notes = [43.65, 48.99, 41.20, 55.0]
    bar_count = int(DURATION_SEC / bar_dur) + 2
    for b in range(bar_count):
        b_time = b * bar_dur
        root_f = bass_notes[b % len(bass_notes)]
        for beat in [0.0, 1.5, 2.5, 3.25]:
            note_t = b_time + beat * beat_dur
            if note_t >= DURATION_SEC: break
            idx = int(note_t * sr)
            dur = int(beat_dur * 0.85 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            bt = np.linspace(0, dur / sr, length, endpoint=False)
            env = np.exp(-bt * 3.8)
            bass = (np.sin(2 * np.pi * root_f * bt) + 0.3 * np.sin(2 * np.pi * root_f * 2 * bt)) * env * 0.50
            music_l[idx:idx+length] += bass
            music_r[idx:idx+length] += bass

    # Warm Acoustic Guitar Chords (fingerpicked feel)
    chords = [
        [174.61, 220.00, 261.63, 329.63],
        [196.00, 246.94, 293.66, 349.23],
        [164.81, 196.00, 246.94, 293.66],
        [220.00, 261.63, 329.63, 392.00]
    ]
    for b in range(bar_count):
        b_time = b * bar_dur
        chord = chords[b % len(chords)]
        for beat in [0.0, 1.75, 2.75]:
            note_t = b_time + beat * beat_dur
            if note_t >= DURATION_SEC: break
            idx = int(note_t * sr)
            dur = int(beat_dur * 1.1 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            ct = np.linspace(0, dur / sr, length, endpoint=False)
            env = np.exp(-ct * 3.2)
            chord_sig = np.zeros(length, dtype=np.float32)
            for f in chord:
                tone = (np.sin(2 * np.pi * f * ct) +
                        0.35 * np.sin(2 * np.pi * f * 2 * ct) +
                        0.12 * np.sin(2 * np.pi * f * 3 * ct))
                chord_sig += tone
            chord_sig = chord_sig * env * 0.10
            music_l[idx:idx+length] += chord_sig * 1.1
            music_r[idx:idx+length] += chord_sig * 0.9

    # Marimba / Gamelan-style Melodic Lead
    lead_notes = [
        (0.0, 523.25), (0.5, 587.33), (1.0, 659.25), (1.5, 783.99),
        (2.0, 659.25), (2.5, 587.33), (3.0, 523.25), (3.5, 440.00),
    ]
    cur_t = 0.0
    while cur_t < DURATION_SEC - 1.0:
        for offset_beat, freq in lead_notes:
            note_t = cur_t + offset_beat * beat_dur
            if note_t >= DURATION_SEC: break
            idx = int(note_t * sr)
            dur = int(0.35 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            lt = np.linspace(0, 0.35, length, endpoint=False)
            env = np.exp(-lt * 9.0)
            mod = np.sin(2 * np.pi * freq * 1.5 * lt) * 1.8
            bell = np.sin(2 * np.pi * freq * lt + mod) * env * 0.16
            music_l[idx:idx+length] += bell * 0.85
            music_r[idx:idx+length] += bell * 1.15
        cur_t += bar_dur

    # SFX
    def add_sub_drop(start_time):
        idx = int(start_time * sr)
        dur = int(1.2 * sr)
        length = min(dur, n_samples - idx)
        if length <= 0: return
        st = np.linspace(0, 1.2, length, endpoint=False)
        freq = 65.0 * np.exp(-st * 2.5) + 24.0
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.exp(-st * 2.2)
        sig = np.sin(phase) * env * 0.65
        sfx_l[idx:idx+length] += sig
        sfx_r[idx:idx+length] += sig

    def add_whoosh(start_time, reverse=False, gain=0.40):
        idx = int(start_time * sr)
        dur = int(0.6 * sr)
        length = min(dur, n_samples - idx)
        if length <= 0: return
        wt = np.linspace(0, 0.6, length, endpoint=False)
        noise = (np.random.rand(length) * 2 - 1)
        env = np.exp((wt - 0.6) * 5.0) if reverse else np.sin(np.pi * wt / 0.6)
        sig = noise * env * gain
        pan_l = np.linspace(1.0, 0.2, length) if not reverse else np.linspace(0.2, 1.0, length)
        pan_r = 1.2 - pan_l
        sfx_l[idx:idx+length] += sig * pan_l
        sfx_r[idx:idx+length] += sig * pan_r

    def add_pop(start_time, freq=880.0):
        idx = int(start_time * sr)
        dur = int(0.08 * sr)
        length = min(dur, n_samples - idx)
        if length <= 0: return
        pt = np.linspace(0, 0.08, length, endpoint=False)
        pop = np.sin(2 * np.pi * (freq * np.exp(-pt * 35.0)) * pt) * np.exp(-pt * 42.0) * 0.40
        sfx_l[idx:idx+length] += pop
        sfx_r[idx:idx+length] += pop

    def add_glock_chime(start_time):
        chimes = [1046.50, 1318.51, 1567.98, 2093.00]
        for i, f in enumerate(chimes):
            idx = int((start_time + i * 0.06) * sr)
            dur = int(0.7 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            gt = np.linspace(0, 0.7, length, endpoint=False)
            env = np.exp(-gt * 6.5)
            tone = (np.sin(2 * np.pi * f * gt) + 0.25 * np.sin(2 * np.pi * f * 2.7 * gt)) * env * 0.25
            sfx_l[idx:idx+length] += tone * (0.8 + 0.4 * (i % 2))
            sfx_r[idx:idx+length] += tone * (1.2 - 0.4 * (i % 2))

    def add_celebration_bell(start_time):
        notes = [587.33, 880.0, 1174.66, 1760.0]
        for i, f in enumerate(notes):
            idx = int((start_time + i * 0.07) * sr)
            dur = int(1.0 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            bt = np.linspace(0, 1.0, length, endpoint=False)
            bell = np.sin(2 * np.pi * f * bt) * np.exp(-bt * 4.2) * 0.30
            sfx_l[idx:idx+length] += bell
            sfx_r[idx:idx+length] += bell

    add_sub_drop(0.0)
    add_whoosh(0.1, reverse=True, gain=0.30)
    add_whoosh(2.2, reverse=False, gain=0.35)
    add_pop(5.0, 950.0)
    add_pop(6.5, 1100.0)
    add_pop(8.0, 1250.0)
    add_whoosh(11.4, reverse=False, gain=0.40)
    add_glock_chime(11.8)
    add_pop(14.5, 1400.0)
    add_whoosh(17.8, reverse=True, gain=0.45)
    for k in range(6):
        add_pop(19.0 + k * 0.28, 700.0 + k * 130.0)
    add_celebration_bell(24.5)
    add_whoosh(24.8, reverse=False, gain=0.35)
    add_pop(27.0, 1050.0)

    # Master Mixing
    mix_l = music_l * 0.80 + sfx_l * 0.70
    mix_r = music_r * 0.80 + sfx_r * 0.70
    fade_len = int(1.5 * sr)
    fade_env = np.linspace(1.0, 0.0, fade_len)
    mix_l[-fade_len:] *= fade_env
    mix_r[-fade_len:] *= fade_env
    max_peak = max(np.max(np.abs(mix_l)), np.max(np.abs(mix_r)), 0.01)
    mix_l = (mix_l / max_peak) * 0.90
    mix_r = (mix_r / max_peak) * 0.90
    stereo = np.vstack(((mix_l * 32767).astype(np.int16), (mix_r * 32767).astype(np.int16))).T
    wavfile.write(str(output_path), sr, stereo)
    print(f"✅ Generated audio track: {output_path} ({DURATION_SEC}s, 44.1kHz stereo)", flush=True)


# ==========================================
# 2. MOTION GRAPHICS VISUAL ENGINE
# ==========================================

def ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, x)), 3)

def ease_in_out_quad(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 2 * x * x if x < 0.5 else 1 - math.pow(-2 * x + 2, 2) / 2

def draw_rounded_card(draw, box, fill, outline=None, width=2, radius=24):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def draw_badge(draw, text, cx, cy, font, bg_color, text_color, padding=(32, 14), radius=30):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    px, py = padding
    x0 = cx - tw // 2 - px
    y0 = cy - th // 2 - py
    x1 = cx + tw // 2 + px
    y1 = cy + th // 2 + py
    draw_rounded_card(draw, (x0, y0, x1, y1), fill=bg_color, outline=C_ROSE_GOLD, width=2, radius=radius)
    draw.text((cx - tw // 2, cy - th // 2 - 2), text, font=font, fill=text_color)


def create_gradient_bg(w, h):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    y_r = np.linspace(C_BG_TOP[0], C_BG_BOT[0], h)
    y_g = np.linspace(C_BG_TOP[1], C_BG_BOT[1], h)
    y_b = np.linspace(C_BG_TOP[2], C_BG_BOT[2], h)
    for c in range(3):
        col_vals = [y_r, y_g, y_b][c]
        arr[:, :, c] = col_vals[:, None]
    return Image.fromarray(arr, "RGB")


def render_all_frames():
    print("🎬 Rendering 900 motion graphics frames (1080x1920 @ 30fps)...", flush=True)

    # Load Keyframe assets
    img_f1 = Image.open(KEYFRAME_DIR / "kurung_pahang_riau_frame1_front.jpg").convert("RGB")
    img_f2 = Image.open(KEYFRAME_DIR / "kurung_pahang_riau_frame2_side.jpg").convert("RGB")
    img_f3 = Image.open(KEYFRAME_DIR / "kurung_pahang_riau_frame3_shoulder.jpg").convert("RGB")
    img_orig = Image.open(OUTPUT_DIR / "product_1.jpg").convert("RGB")

    # Particle field
    np.random.seed(88)
    n_particles = 50
    px_arr = np.random.uniform(50, WIDTH - 50, n_particles)
    py_arr = np.random.uniform(100, HEIGHT - 100, n_particles)
    ps = np.random.uniform(2.0, 6.0, n_particles)
    pspeed = np.random.uniform(20.0, 55.0, n_particles)

    # FFmpeg pipe
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-",
        "-i", str(AUDIO_PATH),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(VIDEO_PATH)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    f_title = get_font(68, bold=True)
    f_huge = get_font(78, bold=True)
    f_sub = get_font(40, bold=True)
    f_card = get_font(34, bold=True)
    f_badge = get_font(30, bold=True)
    f_small = get_font(26, bold=False)

    start_time = time.time()

    for frame_idx in range(TOTAL_FRAMES):
        t_sec = frame_idx / FPS
        progress = frame_idx / TOTAL_FRAMES

        frame = create_gradient_bg(WIDTH, HEIGHT)
        draw = ImageDraw.Draw(frame)

        # Floating rose gold embers
        for p in range(n_particles):
            cur_py = (py_arr[p] - pspeed[p] * t_sec) % (HEIGHT - 120) + 60
            cur_px = px_arr[p] + math.sin(t_sec * 1.3 + p) * 12.0
            r = ps[p]
            draw.ellipse([cur_px - r, cur_py - r, cur_px + r, cur_py + r],
                         fill=(C_ROSE_GOLD[0], C_ROSE_GOLD[1], C_ROSE_GOLD[2]))

        # Top Brand Bar
        draw.rectangle([0, 0, WIDTH, 115], fill=(38, 28, 32))
        draw.text((70, 40), "NOOR FASHION", font=f_badge, fill=C_MAUVE_LIGHT)
        draw.text((WIDTH - 380, 42), "TIKTOK SHOP MALAYSIA", font=get_font(26, bold=True), fill=C_WHITE)
        draw.line([0, 115, WIDTH, 115], fill=C_ROSE_GOLD, width=2)

        # =================================================================
        # ACT 1: SCROLL-STOPPING HOOK (0.0s - 5.0s)
        # =================================================================
        if t_sec < 5.0:
            act_progress = t_sec / 5.0
            draw.rectangle([40, 155, WIDTH - 40, HEIGHT - 155], fill=(38, 28, 32))
            draw_rounded_card(draw, (40, 155, WIDTH - 40, HEIGHT - 155), fill=(38, 28, 32), outline=C_ROSE_GOLD, width=3, radius=32)

            draw_badge(draw, "KURUNG PAHANG RIAU 2026", WIDTH // 2, 255, f_badge, C_MAUVE, C_WHITE)

            p1 = ease_out_cubic(min(1.0, t_sec / 1.0))
            scale_y = int(470 - (1.0 - p1) * 80)
            draw.text((WIDTH // 2 - 420, scale_y), "KENDURI PANAS", font=f_huge, fill=C_YELLOW)
            draw.text((WIDTH // 2 - 420, scale_y + 100), "TERIK SAMPAI BAJU", font=f_title, fill=C_WHITE)
            draw.text((WIDTH // 2 - 420, scale_y + 180), "MELEKAP BASAH?", font=f_huge, fill=C_WARM_PINK)

            if t_sec >= 2.0:
                p2 = ease_out_cubic(min(1.0, (t_sec - 2.0) / 0.8))
                card_y = int(850 - (1.0 - p2) * 60)
                draw_rounded_card(draw, (80, card_y, WIDTH - 80, card_y + 340), fill=(50, 38, 44), outline=C_MAUVE_LIGHT, width=3, radius=24)
                draw.text((120, card_y + 40), "COTTON LINEN SEJUK", font=f_title, fill=C_MAUVE_LIGHT)
                draw.text((120, card_y + 130), "BERNAFAS GILA! 🌸", font=f_huge, fill=C_WHITE)
                draw.text((120, card_y + 240), "Potongan pesak beralun auto sorok pinggul", font=f_sub, fill=(200, 185, 195))

            if t_sec >= 3.4:
                p3 = ease_out_cubic(min(1.0, (t_sec - 3.4) / 0.6))
                bounce_y = int(1440 - (1.0 - p3) * 40)
                draw_badge(draw, "✨ SEDONDON IBU & ANAK TERSEDIA ✨", WIDTH // 2, bounce_y, f_sub, C_MAUVE, C_WHITE, padding=(40, 20))

        # =================================================================
        # ACT 2: HERO PRODUCT REVEAL (5.0s - 11.5s)
        # =================================================================
        elif t_sec < 11.5:
            act_progress = (t_sec - 5.0) / 6.5
            zoom = 1.0 + 0.07 * ease_out_cubic(act_progress)
            target_w = int(720 * zoom)
            target_h = int(1290 * zoom)
            resized_f1 = img_f1.resize((target_w, target_h), Image.Resampling.LANCZOS)

            win_w, win_h = 700, 1100
            win_x = (WIDTH - win_w) // 2
            win_y = 215

            cx, cy = target_w // 2, target_h // 2
            cropped_f1 = resized_f1.crop((cx - win_w // 2, cy - win_h // 2, cx + win_w // 2, cy + win_h // 2))

            draw_rounded_card(draw, (win_x - 12, win_y - 12, win_x + win_w + 12, win_y + win_h + 12), fill=(230, 218, 210), outline=C_ROSE_GOLD, width=3, radius=28)
            frame.paste(cropped_f1, (win_x, win_y))
            draw = ImageDraw.Draw(frame)

            draw_badge(draw, "KURUNG PAHANG RIAU COTTON LINEN", WIDTH // 2, 175, f_sub, C_DARK, C_MAUVE_LIGHT, padding=(36, 16))

            if t_sec >= 6.0:
                draw_rounded_card(draw, (70, 1365, WIDTH - 70, 1460), fill=(38, 28, 32), outline=C_ROSE_GOLD, width=2, radius=20)
                draw.text((110, 1388), "🌸 Material Cotton Linen Sejuk Bernafas", font=f_sub, fill=C_WHITE)

            if t_sec >= 7.5:
                draw_rounded_card(draw, (70, 1485, WIDTH - 70, 1580), fill=(38, 28, 32), outline=C_ROSE_GOLD, width=2, radius=20)
                draw.text((110, 1508), "✨ Pesak Riau Kembang Sorok Pinggul", font=f_sub, fill=C_MAUVE_LIGHT)

            if t_sec >= 9.0:
                draw_rounded_card(draw, (70, 1605, WIDTH - 70, 1700), fill=(38, 28, 32), outline=C_ROSE_GOLD, width=2, radius=20)
                draw.text((110, 1628), "🤍 Kain Lipat Batik + Pinggang Getah Penuh", font=f_sub, fill=C_WHITE)

        # =================================================================
        # ACT 3: SIDE PROFILE & SEDONDON DETAIL (11.5s - 18.0s)
        # =================================================================
        elif t_sec < 18.0:
            act_progress = (t_sec - 11.5) / 6.5
            pan_x = int(math.sin(act_progress * math.pi) * 25.0)
            target_w, target_h = 750, 1200
            resized_f2 = img_f2.resize((target_w, target_h), Image.Resampling.LANCZOS)

            win_w, win_h = 720, 1050
            win_x = (WIDTH - win_w) // 2 + pan_x
            win_y = 205

            draw_rounded_card(draw, (win_x - 10, win_y - 10, win_x + win_w + 10, win_y + win_h + 10), fill=(235, 222, 215), outline=C_ROSE_GOLD, width=3, radius=28)
            frame.paste(resized_f2.crop((0, 0, win_w, win_h)), (win_x, win_y))
            draw = ImageDraw.Draw(frame)

            draw_rounded_card(draw, (70, 1300, WIDTH - 70, 1460), fill=(38, 28, 32), outline=C_ROSE_GOLD, width=3, radius=24)
            draw.text((110, 1325), "🌟 SET SEDONDON IBU & ANAK", font=f_title, fill=C_MAUVE_LIGHT)
            draw.text((110, 1400), "Tampil anggun bersama si kecil ke kenduri!", font=f_card, fill=C_WHITE)

            if t_sec >= 14.0:
                draw_rounded_card(draw, (70, 1490, WIDTH - 70, 1690), fill=C_CREAM, outline=C_MAUVE, width=2, radius=24)
                draw.text((110, 1515), "14 Pilihan Warna Memukau 🎨", font=f_sub, fill=C_DARK)
                draw.text((110, 1575), "• Saiz ibu S hingga 7XL (DD 36 hingga 56)", font=f_card, fill=C_GRAY)
                draw.text((110, 1620), "• Saiz anak 4 hingga 14 tahun tersedia", font=f_card, fill=C_GRAY)

        # =================================================================
        # ACT 4: COLOUR SHOWCASE & VERSATILITY (18.0s - 24.5s)
        # =================================================================
        elif t_sec < 24.5:
            act_progress = (t_sec - 18.0) / 6.5
            draw_badge(draw, "14 WARNA • SAIZ S - 7XL", WIDTH // 2, 178, f_sub, C_DARK, C_MAUVE_LIGHT, padding=(40, 16))

            orig_w, orig_h = 680, 680
            resized_orig = img_orig.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
            ox, oy = (WIDTH - orig_w) // 2, 245
            draw_rounded_card(draw, (ox - 10, oy - 10, ox + orig_w + 10, oy + orig_h + 10), fill=C_WHITE, outline=C_ROSE_GOLD, width=3, radius=24)
            frame.paste(resized_orig, (ox, oy))
            draw = ImageDraw.Draw(frame)

            color_samples = [
                ((210, 155, 170), "Dusty Anggun"),
                ((120, 90, 60), "Dark Brown"),
                ((80, 130, 85), "Olive Green"),
                ((140, 30, 50), "Maroon"),
                ((240, 180, 190), "Soft Pink"),
                ((60, 75, 130), "Dark Blue"),
                ((130, 110, 140), "Kelabu"),
                ((85, 135, 105), "Sage Green")
            ]
            swatch_start_y = 985
            draw.text((100, swatch_start_y), "Warna Terlaris Pelanggan:", font=f_sub, fill=C_DARK)

            for i, (col, cname) in enumerate(color_samples):
                row = i // 4
                col_idx = i % 4
                dot_x = 160 + col_idx * 220
                dot_y = swatch_start_y + 80 + row * 130
                dot_progress = ease_out_cubic(min(1.0, max(0.0, (t_sec - 18.5 - i * 0.12) / 0.4)))
                r = int(30 * dot_progress)
                if r > 0:
                    draw.ellipse([dot_x - r - 3, dot_y - r - 3, dot_x + r + 3, dot_y + r + 3], outline=C_ROSE_GOLD, width=2)
                    draw.ellipse([dot_x - r, dot_y - r, dot_x + r, dot_y + r], fill=col)
                    draw.text((dot_x - 50, dot_y + 38), cname, font=f_small, fill=C_DARK)

            draw_rounded_card(draw, (70, 1370, WIDTH - 70, 1680), fill=(38, 30, 35), outline=C_ROSE_GOLD, width=2, radius=24)
            draw.text((110, 1400), "Sesuai untuk Semua Majlis: 🕊️", font=f_sub, fill=C_MAUVE_LIGHT)
            draw.text((110, 1465), "🕌 Kenduri, Hari Raya & Majlis Keluarga", font=f_card, fill=C_WHITE)
            draw.text((110, 1530), "🏢 Pakaian Pejabat Sopan & Selesa", font=f_card, fill=C_WHITE)
            draw.text((110, 1595), "🌸 Gaya Harian Anggun Modest & Breathable", font=f_card, fill=C_WHITE)

        # =================================================================
        # ACT 5: CTA BELI SEKARANG (24.5s - 30.0s)
        # =================================================================
        else:
            act_progress = (t_sec - 24.5) / 5.5
            target_w, target_h = 680, 1000
            resized_f3 = img_f3.resize((target_w, target_h), Image.Resampling.LANCZOS)
            fx, fy = (WIDTH - target_w) // 2, 155
            draw_rounded_card(draw, (fx - 10, fy - 10, fx + target_w + 10, fy + target_h + 10), fill=C_WHITE, outline=C_ROSE_GOLD, width=3, radius=28)
            frame.paste(resized_f3, (fx, fy))
            draw = ImageDraw.Draw(frame)

            bounce = math.sin(t_sec * 8.0) * 10.0
            cta_y = int(1215 + bounce)
            draw_rounded_card(draw, (55, cta_y - 10, WIDTH - 55, cta_y + 350), fill=(255, 225, 120), outline=C_YELLOW, width=6, radius=36)
            draw_rounded_card(draw, (65, cta_y, WIDTH - 65, cta_y + 330), fill=C_YELLOW, outline=(220, 160, 0), width=3, radius=32)

            draw.text((100, cta_y + 30), "BEG KUNING DI BAWAH!", font=f_huge, fill=C_DARK)
            draw.text((100, cta_y + 130), "TEKAN UNTUK PILIH WARNA & SAIZ", font=f_sub, fill=(40, 30, 10))
            draw.text((100, cta_y + 190), "SEDONDON IBU & ANAK 👇💛", font=f_sub, fill=(60, 40, 15))
            draw.text((100, cta_y + 260), "Promosi TikTok Shop Eksklusif Hari Ini!", font=f_card, fill=(90, 70, 20))

            draw_rounded_card(draw, (80, 1630, WIDTH - 80, 1750), fill=(38, 28, 32), outline=C_ROSE_GOLD, width=2, radius=20)
            draw.text((110, 1665), "⚡ READY STOCK MALAYSIA  •  🚚 FAST SHIPPING", font=f_sub, fill=C_MAUVE_LIGHT)

        # Bottom progress bar
        bar_y = HEIGHT - 45
        bar_w = int(WIDTH * progress)
        draw.rectangle([0, bar_y, WIDTH, HEIGHT], fill=(38, 28, 32))
        draw.rectangle([0, bar_y, bar_w, HEIGHT], fill=C_ROSE_GOLD)
        draw.line([0, bar_y, WIDTH, bar_y], fill=C_MAUVE_LIGHT, width=2)
        draw.text((30, bar_y - 32), "TikTok Shop Policy Safe • AI Generated Media", font=get_font(20, bold=False), fill=(140, 135, 145))
        draw.text((WIDTH - 150, bar_y - 32), f"{t_sec:04.1f}s / 30s", font=get_font(20, bold=True), fill=C_MAUVE_LIGHT)

        proc.stdin.write(frame.tobytes())

        if frame_idx % 90 == 0 or frame_idx == TOTAL_FRAMES - 1:
            print(f"  Frame {frame_idx + 1}/{TOTAL_FRAMES} ({(frame_idx + 1) / TOTAL_FRAMES * 100:.1f}%) | {t_sec:.1f}s", flush=True)

    proc.stdin.close()
    proc.wait()
    elapsed = time.time() - start_time
    print(f"✅ Rendered & encoded video in {elapsed:.1f}s: {VIDEO_PATH}", flush=True)


if __name__ == "__main__":
    synthesize_audio(AUDIO_PATH)
    render_all_frames()
    print("🎉 30-Second Kurung Pahang Riau Motion Graphics Complete!")

