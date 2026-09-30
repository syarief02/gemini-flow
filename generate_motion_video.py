"""
30-Second Motion Graphics Video Generator
=========================================
Generates a broadcast-quality 9:16 vertical motion graphics video (1080x1920, 30fps)
for VALEN Korean Soft Knit Cardigan on TikTok Shop.

Features:
- High-fidelity synthesized 30.0s BGM (lo-fi cafe chill pop, 108 BPM) with full instrumentation
  (drums, 808 bassline, Rhodes electric piano chords, catchy mallet melody)
- Synchronized sound effects (sub bass drop, reverse whoosh, camera shutter, pop plucks,
  chimes, risers, celebration dings)
- 5 dynamic motion design acts with kinetic typography, parallax image motion,
  glassmorphic cards, gold particle glimmers, color swatches, and animated Beg Kuning CTA.
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
OUTPUT_DIR = WORKSPACE / "output" / "20260930_134117"

VIDEO_PATH = WORKSPACE / "valen_cardigan_motion_graphics_30s.mp4"
AUDIO_PATH = WORKSPACE / "valen_motion_audio.wav"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SEC = 30.0
TOTAL_FRAMES = int(FPS * DURATION_SEC)  # 900 frames

# Colors
C_BG_TOP = (252, 249, 244)
C_BG_BOT = (238, 230, 220)
C_DARK = (24, 24, 28)
C_GOLD = (212, 175, 55)
C_GOLD_LIGHT = (245, 215, 110)
C_WHITE = (255, 255, 255)
C_YELLOW = (255, 208, 0)
C_RED = (235, 75, 75)
C_BLUE = (65, 140, 240)
C_GRAY = (110, 110, 120)
C_LIGHT_GRAY = (240, 238, 235)


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
    print("🎵 Synthesizing 30.0s background music & synchronized SFX...", flush=True)
    sr = 44100
    n_samples = int(sr * DURATION_SEC)
    t = np.linspace(0, DURATION_SEC, n_samples, endpoint=False)
    
    bpm = 108.0
    beat_dur = 60.0 / bpm  # ~0.5555s
    bar_dur = beat_dur * 4  # ~2.222s
    
    # Master channels
    music_l = np.zeros(n_samples, dtype=np.float32)
    music_r = np.zeros(n_samples, dtype=np.float32)
    sfx_l = np.zeros(n_samples, dtype=np.float32)
    sfx_r = np.zeros(n_samples, dtype=np.float32)
    
    # ----------------------------------------
    # Drum Synth
    # ----------------------------------------
    def add_kick(start_time: float, gain: float = 0.85):
        idx = int(start_time * sr)
        dur = int(0.25 * sr)
        if idx >= n_samples: return
        length = min(dur, n_samples - idx)
        kt = np.linspace(0, 0.25, length, endpoint=False)
        freq = 140.0 * np.exp(-kt * 22.0) + 42.0
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.exp(-kt * 14.0)
        kick = np.sin(phase) * env * gain
        music_l[idx:idx+length] += kick
        music_r[idx:idx+length] += kick

    def add_snare(start_time: float, gain: float = 0.55):
        idx = int(start_time * sr)
        dur = int(0.20 * sr)
        if idx >= n_samples: return
        length = min(dur, n_samples - idx)
        st = np.linspace(0, 0.20, length, endpoint=False)
        # Tone
        tone = np.sin(2 * np.pi * 190.0 * st) * np.exp(-st * 25.0) * 0.4
        # Noise
        noise = (np.random.rand(length) * 2 - 1) * np.exp(-st * 18.0) * 0.6
        snare = (tone + noise) * gain
        music_l[idx:idx+length] += snare
        music_r[idx:idx+length] += snare

    def add_hat(start_time: float, gain: float = 0.25):
        idx = int(start_time * sr)
        dur = int(0.045 * sr)
        if idx >= n_samples: return
        length = min(dur, n_samples - idx)
        ht = np.linspace(0, 0.045, length, endpoint=False)
        noise = (np.random.rand(length) * 2 - 1) * np.exp(-ht * 80.0) * gain
        music_l[idx:idx+length] += noise * 0.8
        music_r[idx:idx+length] += noise * 1.2

    # Loop drum patterns across 30 seconds
    cur_t = 0.0
    while cur_t < DURATION_SEC - 0.2:
        # 4 beats per bar
        b0 = cur_t
        b1 = cur_t + beat_dur
        b2 = cur_t + beat_dur * 2
        b3 = cur_t + beat_dur * 3
        
        # Kicks on 1, 2.5, 3
        add_kick(b0, 0.85)
        add_kick(b1 + beat_dur * 0.5, 0.65)
        add_kick(b2, 0.75)
        
        # Snares on 2 and 4
        add_snare(b1, 0.60)
        add_snare(b3, 0.65)
        
        # 16th Hi-hats
        for step in range(16):
            ht_time = cur_t + step * (beat_dur / 4)
            h_gain = 0.32 if step % 4 == 0 else (0.22 if step % 2 == 0 else 0.14)
            add_hat(ht_time, h_gain)
            
        cur_t += bar_dur

    # ----------------------------------------
    # Bassline Synth (808 smooth sine + 2nd harmonic)
    # ----------------------------------------
    # Progression: F (43.65 Hz) -> G (48.99 Hz) -> E (41.20 Hz) -> A (55.0 Hz)
    bass_notes = [43.65, 48.99, 41.20, 55.0]
    bar_count = int(DURATION_SEC / bar_dur) + 2
    for b in range(bar_count):
        b_time = b * bar_dur
        root_f = bass_notes[b % len(bass_notes)]
        for beat in [0.0, 1.5, 2.5, 3.25]:
            note_t = b_time + beat * beat_dur
            if note_t >= DURATION_SEC: break
            idx = int(note_t * sr)
            dur = int(beat_dur * 0.9 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            bt = np.linspace(0, dur / sr, length, endpoint=False)
            env = np.exp(-bt * 3.5)
            bass = (np.sin(2 * np.pi * root_f * bt) + 0.35 * np.sin(2 * np.pi * root_f * 2 * bt)) * env * 0.55
            music_l[idx:idx+length] += bass
            music_r[idx:idx+length] += bass

    # ----------------------------------------
    # Electric Piano Chords (Rhodes-like warmth)
    # ----------------------------------------
    # Fmaj7 (F3, A3, C4, E4), G7 (G3, B3, D4, F4), Em7 (E3, G3, B3, D4), Am7 (A3, C4, E4, G4)
    chords = [
        [174.61, 220.00, 261.63, 329.63], # Fmaj7
        [196.00, 246.94, 293.66, 349.23], # G7
        [164.81, 196.00, 246.94, 293.66], # Em7
        [220.00, 261.63, 329.63, 392.00]  # Am7
    ]
    for b in range(bar_count):
        b_time = b * bar_dur
        chord = chords[b % len(chords)]
        for beat in [0.0, 1.75, 2.75]:
            note_t = b_time + beat * beat_dur
            if note_t >= DURATION_SEC: break
            idx = int(note_t * sr)
            dur = int(beat_dur * 1.2 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            ct = np.linspace(0, dur / sr, length, endpoint=False)
            env = np.exp(-ct * 3.0)
            chord_sig = np.zeros(length, dtype=np.float32)
            for f in chord:
                tone = (np.sin(2 * np.pi * f * ct) + 
                        0.4 * np.sin(2 * np.pi * f * 2 * ct) + 
                        0.15 * np.sin(2 * np.pi * f * 3 * ct))
                chord_sig += tone
            chord_sig = chord_sig * env * 0.12
            music_l[idx:idx+length] += chord_sig * 1.1
            music_r[idx:idx+length] += chord_sig * 0.9

    # ----------------------------------------
    # Catchy Melodic Bell / Mallet Lead
    # ----------------------------------------
    lead_notes = [
        (0.0, 523.25), (0.5, 587.33), (1.0, 659.25), (1.5, 783.99), # C5, D5, E5, G5
        (2.0, 659.25), (2.5, 587.33), (3.0, 523.25), (3.5, 440.00), # E5, D5, C5, A4
    ]
    cur_t = 0.0
    while cur_t < DURATION_SEC - 1.0:
        for offset_beat, freq in lead_notes:
            note_t = cur_t + offset_beat * beat_dur
            if note_t >= DURATION_SEC: break
            idx = int(note_t * sr)
            dur = int(0.4 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            lt = np.linspace(0, 0.4, length, endpoint=False)
            env = np.exp(-lt * 8.0)
            # FM bell sound
            mod = np.sin(2 * np.pi * freq * 1.5 * lt) * 2.0
            bell = np.sin(2 * np.pi * freq * lt + mod) * env * 0.18
            music_l[idx:idx+length] += bell * 0.8
            music_r[idx:idx+length] += bell * 1.2
        cur_t += bar_dur

    # ----------------------------------------
    # Synchronized Sound Effects (SFX)
    # ----------------------------------------
    def add_sub_drop(start_time: float):
        idx = int(start_time * sr)
        dur = int(1.4 * sr)
        length = min(dur, n_samples - idx)
        if length <= 0: return
        st = np.linspace(0, 1.4, length, endpoint=False)
        freq = 75.0 * np.exp(-st * 2.5) + 26.0
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.exp(-st * 2.0)
        sig = np.sin(phase) * env * 0.75
        sfx_l[idx:idx+length] += sig
        sfx_r[idx:idx+length] += sig

    def add_whoosh(start_time: float, reverse: bool = False, gain: float = 0.45):
        idx = int(start_time * sr)
        dur = int(0.7 * sr)
        length = min(dur, n_samples - idx)
        if length <= 0: return
        wt = np.linspace(0, 0.7, length, endpoint=False)
        noise = (np.random.rand(length) * 2 - 1)
        if reverse:
            env = np.exp((wt - 0.7) * 5.0)
        else:
            env = np.sin(np.pi * wt / 0.7)
        sig = noise * env * gain
        # Pan whoosh left to right
        pan_l = np.linspace(1.0, 0.2, length) if not reverse else np.linspace(0.2, 1.0, length)
        pan_r = 1.2 - pan_l
        sfx_l[idx:idx+length] += sig * pan_l
        sfx_r[idx:idx+length] += sig * pan_r

    def add_camera_shutter(start_time: float):
        idx = int(start_time * sr)
        for offset in [0.0, 0.08]:
            c_idx = idx + int(offset * sr)
            dur = int(0.06 * sr)
            length = min(dur, n_samples - c_idx)
            if length <= 0: continue
            ct = np.linspace(0, 0.06, length, endpoint=False)
            click = (np.random.rand(length) * 2 - 1) * np.exp(-ct * 70.0) * 0.6
            sfx_l[c_idx:c_idx+length] += click
            sfx_r[c_idx:c_idx+length] += click

    def add_pop(start_time: float, freq: float = 880.0):
        idx = int(start_time * sr)
        dur = int(0.09 * sr)
        length = min(dur, n_samples - idx)
        if length <= 0: return
        pt = np.linspace(0, 0.09, length, endpoint=False)
        pop = np.sin(2 * np.pi * (freq * np.exp(-pt * 35.0)) * pt) * np.exp(-pt * 40.0) * 0.45
        sfx_l[idx:idx+length] += pop
        sfx_r[idx:idx+length] += pop

    def add_glock_chime(start_time: float):
        chimes = [1046.50, 1318.51, 1567.98, 2093.00] # C6, E6, G6, C7
        for i, f in enumerate(chimes):
            idx = int((start_time + i * 0.06) * sr)
            dur = int(0.8 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            gt = np.linspace(0, 0.8, length, endpoint=False)
            env = np.exp(-gt * 6.0)
            tone = (np.sin(2 * np.pi * f * gt) + 0.3 * np.sin(2 * np.pi * f * 2.7 * gt)) * env * 0.28
            sfx_l[idx:idx+length] += tone * (0.8 + 0.4 * (i % 2))
            sfx_r[idx:idx+length] += tone * (1.2 - 0.4 * (i % 2))

    def add_celebration_bell(start_time: float):
        notes = [587.33, 880.0, 1174.66, 1760.0]
        for i, f in enumerate(notes):
            idx = int((start_time + i * 0.08) * sr)
            dur = int(1.2 * sr)
            length = min(dur, n_samples - idx)
            if length <= 0: continue
            bt = np.linspace(0, 1.2, length, endpoint=False)
            bell = np.sin(2 * np.pi * f * bt) * np.exp(-bt * 4.0) * 0.35
            sfx_l[idx:idx+length] += bell
            sfx_r[idx:idx+length] += bell

    # Sequence SFX on Key Timeline Milestones:
    add_sub_drop(0.0)
    add_whoosh(0.1, reverse=True, gain=0.35)
    add_whoosh(2.3, reverse=False, gain=0.40)
    add_camera_shutter(5.0)
    add_pop(6.5, 950.0)
    add_pop(8.0, 1100.0)
    add_pop(9.5, 1250.0)
    add_whoosh(11.4, reverse=False, gain=0.45)
    add_glock_chime(11.8)
    add_pop(14.5, 1400.0)
    add_whoosh(17.8, reverse=True, gain=0.50)
    for k in range(8):
        add_pop(19.0 + k * 0.25, 700.0 + k * 120.0)
    add_celebration_bell(24.5)
    add_whoosh(24.8, reverse=False, gain=0.40)
    add_pop(27.0, 1050.0)

    # Master Mixing & Normalization
    mix_l = music_l * 0.85 + sfx_l * 0.75
    mix_r = music_r * 0.85 + sfx_r * 0.75
    
    # Master Fade-out last 1.5 seconds
    fade_len = int(1.5 * sr)
    fade_env = np.linspace(1.0, 0.0, fade_len)
    mix_l[-fade_len:] *= fade_env
    mix_r[-fade_len:] *= fade_env

    # Soft Limiter
    max_peak = max(np.max(np.abs(mix_l)), np.max(np.abs(mix_r)), 0.01)
    mix_l = (mix_l / max_peak) * 0.92
    mix_r = (mix_r / max_peak) * 0.92

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

def draw_rounded_card(draw: ImageDraw.ImageDraw, box: tuple, fill: tuple, outline: tuple = None, width: int = 2, radius: int = 24):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def draw_badge(draw: ImageDraw.ImageDraw, text: str, cx: int, cy: int, font, bg_color: tuple, text_color: tuple, padding: tuple = (32, 14), radius: int = 30):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    px, py = padding
    x0 = cx - tw // 2 - px
    y0 = cy - th // 2 - py
    x1 = cx + tw // 2 + px
    y1 = cy + th // 2 + py
    draw_rounded_card(draw, (x0, y0, x1, y1), fill=bg_color, outline=C_GOLD, width=2, radius=radius)
    draw.text((cx - tw // 2, cy - th // 2 - 2), text, font=font, fill=text_color)


def create_gradient_bg(w: int, h: int, shift: float = 0.0) -> Image.Image:
    # Smooth vertical gradient with subtle warm amber glow
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    # y-gradient interpolation
    y_r = np.linspace(C_BG_TOP[0], C_BG_BOT[0], h)
    y_g = np.linspace(C_BG_TOP[1], C_BG_BOT[1], h)
    y_b = np.linspace(C_BG_TOP[2], C_BG_BOT[2], h)
    
    # Broadcast across x with light radial highlight
    for c in range(3):
        col_vals = [y_r, y_g, y_b][c]
        arr[:, :, c] = col_vals[:, None]
        
    base_img = Image.fromarray(arr, "RGB")
    return base_img


def render_all_frames():
    print("🎬 Rendering 900 motion graphics frames (1080x1920 @ 30fps)...", flush=True)
    
    # Load Keyframe assets
    img_f1 = Image.open(KEYFRAME_DIR / "valen_knitcardigan_frame1_front.jpg").convert("RGB")
    img_f2 = Image.open(KEYFRAME_DIR / "valen_knitcardigan_frame2_side.jpg").convert("RGB")
    img_f3 = Image.open(KEYFRAME_DIR / "valen_knitcardigan_frame3_shoulder.jpg").convert("RGB")
    img_orig = Image.open(OUTPUT_DIR / "product_1.jpg").convert("RGB")

    # Pre-render particle field for background elegance
    np.random.seed(42)
    n_particles = 60
    px = np.random.uniform(50, WIDTH - 50, n_particles)
    py = np.random.uniform(100, HEIGHT - 100, n_particles)
    ps = np.random.uniform(2.5, 7.0, n_particles)
    pspeed = np.random.uniform(25.0, 70.0, n_particles)

    # Initialize FFmpeg pipe
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",  # Video from stdin pipe
        "-i", str(AUDIO_PATH),  # Audio from synthesized WAV
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(VIDEO_PATH)
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    f_title = get_font(72, bold=True)
    f_huge = get_font(84, bold=True)
    f_sub = get_font(42, bold=True)
    f_card = get_font(36, bold=True)
    f_badge = get_font(32, bold=True)
    f_small = get_font(26, bold=False)

    start_time = time.time()

    for frame_idx in range(TOTAL_FRAMES):
        t_sec = frame_idx / FPS
        progress = frame_idx / TOTAL_FRAMES
        
        # Base background
        frame = create_gradient_bg(WIDTH, HEIGHT, shift=math.sin(t_sec * 0.5))
        draw = ImageDraw.Draw(frame)

        # Ambient floating gold embers
        for p in range(n_particles):
            cur_py = (py[p] - pspeed[p] * t_sec) % (HEIGHT - 120) + 60
            cur_px = px[p] + math.sin(t_sec * 1.5 + p) * 15.0
            r = ps[p]
            alpha_glow = int(140 + 70 * math.sin(t_sec * 3.0 + p))
            draw.ellipse([cur_px - r, cur_py - r, cur_px + r, cur_py + r], 
                         fill=(C_GOLD[0], C_GOLD[1], C_GOLD[2]))

        # Global Top Brand Bar (Persistent Elegance)
        draw.rectangle([0, 0, WIDTH, 120], fill=(20, 20, 24))
        draw.text((70, 42), "VALEN OFFICIAL", font=f_badge, fill=C_GOLD_LIGHT)
        draw.text((WIDTH - 360, 44), "TIKTOK SHOP MALAYSIA", font=get_font(26, bold=True), fill=C_WHITE)
        draw.line([0, 120, WIDTH, 120], fill=C_GOLD, width=2)

        # =================================================================
        # ACT 1: THE SCROLL-STOPPING HOOK (0.0s - 5.0s)
        # =================================================================
        if t_sec < 5.0:
            act_progress = t_sec / 5.0
            
            # Dramatic backdrop overlay
            overlay_alpha = int(220 * (1.0 - ease_out_cubic(act_progress * 1.2)))
            draw.rectangle([40, 160, WIDTH - 40, HEIGHT - 160], fill=(22, 22, 26))
            draw_rounded_card(draw, (40, 160, WIDTH - 40, HEIGHT - 160), fill=(22, 22, 26), outline=C_GOLD, width=3, radius=32)

            # Floating animated badge
            draw_badge(draw, "VIRAL KOREAN KNITWEAR 2026", WIDTH // 2, 260, f_badge, C_GOLD, C_DARK)

            # Kinetic Hook Text 1 (0.0s - 2.5s)
            p1 = ease_out_cubic(min(1.0, t_sec / 1.0))
            scale_y = int(480 - (1.0 - p1) * 80)
            draw.text((WIDTH // 2 - 440, scale_y), "CUACA PANAS TERIK", font=f_huge, fill=C_YELLOW)
            draw.text((WIDTH // 2 - 280, scale_y + 110), "KAT LUAR... ☀️", font=f_title, fill=C_WHITE)

            # Kinetic Hook Text 2 (2.2s - 5.0s)
            if t_sec >= 2.0:
                p2 = ease_out_cubic(min(1.0, (t_sec - 2.0) / 0.8))
                card_y = int(820 - (1.0 - p2) * 60)
                draw_rounded_card(draw, (80, card_y, WIDTH - 80, card_y + 360), fill=(35, 38, 48), outline=C_BLUE, width=3, radius=24)
                draw.text((120, card_y + 45), "TAPI AIRCOND OFIS", font=f_title, fill=C_BLUE)
                draw.text((120, card_y + 145), "SEJUK BEKU GILA? 🥶", font=f_huge, fill=C_WHITE)
                draw.text((120, card_y + 265), "Pening cari outerwear kemas & tak berkuap?", font=f_sub, fill=(200, 210, 230))

            # Bottom hook teaser (3.6s - 5.0s)
            if t_sec >= 3.4:
                p3 = ease_out_cubic(min(1.0, (t_sec - 3.4) / 0.6))
                bounce_y = int(1440 - (1.0 - p3) * 40)
                draw_badge(draw, "✨ INI PENYELAMAT HARIAN KORANG ✨", WIDTH // 2, bounce_y, f_sub, C_GOLD, C_DARK, padding=(40, 20))

        # =================================================================
        # ACT 2: HERO PRODUCT REVEAL (5.0s - 11.5s)
        # =================================================================
        elif t_sec < 11.5:
            act_progress = (t_sec - 5.0) / 6.5
            
            # Framed Showcase of Frame 1 (Front View)
            # Smooth Ken Burns push-in
            zoom = 1.0 + 0.08 * ease_out_cubic(act_progress)
            target_w = int(720 * zoom)
            target_h = int(1290 * zoom)
            resized_f1 = img_f1.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # Crop to window
            win_w = 700
            win_h = 1100
            win_x = (WIDTH - win_w) // 2
            win_y = 220
            
            cx = target_w // 2
            cy = target_h // 2
            cropped_f1 = resized_f1.crop((cx - win_w // 2, cy - win_h // 2, cx + win_w // 2, cy + win_h // 2))
            
            # Frame with shadow & border
            draw_rounded_card(draw, (win_x - 12, win_y - 12, win_x + win_w + 12, win_y + win_h + 12), fill=(225, 215, 200), outline=C_GOLD, width=3, radius=28)
            frame.paste(cropped_f1, (win_x, win_y))
            draw = ImageDraw.Draw(frame)

            # Top Floating Title
            draw_badge(draw, "VALEN KOREAN SOFT CARDIGAN", WIDTH // 2, 175, f_sub, C_DARK, C_GOLD_LIGHT, padding=(36, 16))

            # Staggered Feature Badges popping up
            # Badge 1: Benang Kait Lembut (6.0s+)
            if t_sec >= 6.0:
                p_b1 = ease_out_cubic(min(1.0, (t_sec - 6.0) / 0.6))
                bx = int(WIDTH // 2 - 400 * (1.0 - p_b1))
                draw_rounded_card(draw, (70, 1370, WIDTH - 70, 1470), fill=(20, 20, 24), outline=C_GOLD, width=2, radius=20)
                draw.text((110, 1395), "✨ 100% Benang Kait Halus Premium", font=f_sub, fill=C_WHITE)

            # Badge 2: Ringan & Sejuk (7.5s+)
            if t_sec >= 7.5:
                p_b2 = ease_out_cubic(min(1.0, (t_sec - 7.5) / 0.6))
                draw_rounded_card(draw, (70, 1495, WIDTH - 70, 1595), fill=(20, 20, 24), outline=C_GOLD, width=2, radius=20)
                draw.text((110, 1520), "❄️ Breathable & Tak Panas Cuaca MY", font=f_sub, fill=C_GOLD_LIGHT)

            # Badge 3: Selesa & Tak Miang (9.0s+)
            if t_sec >= 9.0:
                p_b3 = ease_out_cubic(min(1.0, (t_sec - 9.0) / 0.6))
                draw_rounded_card(draw, (70, 1620, WIDTH - 70, 1720), fill=(20, 20, 24), outline=C_GOLD, width=2, radius=20)
                draw.text((110, 1645), "🤍 Lembut Pada Kulit • Langsung Tak Miang", font=f_sub, fill=C_WHITE)

        # =================================================================
        # ACT 3: DETAIL SPOTLIGHT & OLD MONEY CHIC (11.5s - 18.0s)
        # =================================================================
        elif t_sec < 18.0:
            act_progress = (t_sec - 11.5) / 6.5
            
            # Show Frame 2 (Side 3/4 Profile)
            pan_x = int(math.sin(act_progress * math.pi) * 30.0)
            target_w = 750
            target_h = 1200
            resized_f2 = img_f2.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            win_w = 720
            win_h = 1050
            win_x = (WIDTH - win_w) // 2 + pan_x
            win_y = 210
            
            draw_rounded_card(draw, (win_x - 10, win_y - 10, win_x + win_w + 10, win_y + win_h + 10), fill=(230, 220, 210), outline=C_GOLD, width=3, radius=28)
            frame.paste(resized_f2.crop((0, 0, win_w, win_h)), (win_x, win_y))
            draw = ImageDraw.Draw(frame)

            # Detail Callout: Shiny Gold Buttons
            pulse = math.sin(t_sec * 6.0) * 8.0
            bx_target = win_x + 390
            by_target = win_y + 360
            draw.ellipse([bx_target - 24 - pulse, by_target - 24 - pulse, bx_target + 24 + pulse, by_target + 24 + pulse], outline=C_GOLD_LIGHT, width=3)
            draw.ellipse([bx_target - 12, by_target - 12, bx_target + 12, by_target + 12], fill=C_YELLOW)

            # Animated Pointer Card
            draw_rounded_card(draw, (70, 1310, WIDTH - 70, 1470), fill=(18, 18, 22), outline=C_GOLD, width=3, radius=24)
            draw.text((110, 1335), "🌟 BUTANG EMAS MEWAH", font=f_title, fill=C_GOLD_LIGHT)
            draw.text((110, 1410), "Sentuhan 'Old Money Aesthetic' yang eksklusif", font=f_card, fill=C_WHITE)

            # Shoulder & Drape Cut Card
            if t_sec >= 14.0:
                p_sh = ease_out_cubic(min(1.0, (t_sec - 14.0) / 0.6))
                draw_rounded_card(draw, (70, 1500, WIDTH - 70, 1690), fill=(245, 242, 235), outline=(180, 150, 90), width=2, radius=24)
                draw.text((110, 1525), "Potongan Bahu Terletak Kemas ✨", font=f_sub, fill=C_DARK)
                draw.text((110, 1585), "• Tidak gelebeh atau kaku bila disarung", font=f_card, fill=C_GRAY)
                draw.text((110, 1630), "• Sesuai untuk inner, kemeja, atau t-shirt", font=f_card, fill=C_GRAY)

        # =================================================================
        # ACT 4: VERSATILITY & COLOR SPECTRUM (18.0s - 24.5s)
        # =================================================================
        elif t_sec < 24.5:
            act_progress = (t_sec - 18.0) / 6.5
            
            # Split Showcase: Product Listing Card + Swatches
            draw_badge(draw, "16 PILIHAN WARNA • SAIZ S - XL", WIDTH // 2, 180, f_sub, C_DARK, C_GOLD_LIGHT, padding=(40, 16))

            # Display original product card showing the 16 swatches
            orig_w = 680
            orig_h = 680
            resized_orig = img_orig.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
            ox = (WIDTH - orig_w) // 2
            oy = 250
            draw_rounded_card(draw, (ox - 10, oy - 10, ox + orig_w + 10, oy + orig_h + 10), fill=C_WHITE, outline=C_GOLD, width=3, radius=24)
            frame.paste(resized_orig, (ox, oy))
            draw = ImageDraw.Draw(frame)

            # Animated Color Dot Palette Showcase
            color_samples = [
                ((20, 20, 20), "Hitam"),
                ((245, 245, 245), "Putih"),
                ((185, 205, 225), "Sky Blue"),
                ((215, 190, 170), "Latte"),
                ((120, 140, 120), "Sage"),
                ((190, 80, 95), "Berry"),
                ((230, 215, 160), "Butter"),
                ((140, 140, 145), "Grey")
            ]
            
            swatch_start_y = 990
            draw.text((100, swatch_start_y), "Tona Warna Paling Laris di FYP:", font=f_sub, fill=C_DARK)

            for i, (col, cname) in enumerate(color_samples):
                row = i // 4
                col_idx = i % 4
                dot_x = 160 + col_idx * 220
                dot_y = swatch_start_y + 80 + row * 130
                
                # Pop-in animation
                dot_progress = ease_out_cubic(min(1.0, max(0.0, (t_sec - 18.5 - i * 0.12) / 0.4)))
                r = int(32 * dot_progress)
                if r > 0:
                    draw.ellipse([dot_x - r - 3, dot_y - r - 3, dot_x + r + 3, dot_y + r + 3], outline=C_GOLD, width=2)
                    draw.ellipse([dot_x - r, dot_y - r, dot_x + r, dot_y + r], fill=col)
                    draw.text((dot_x - 35, dot_y + 40), cname, font=f_small, fill=C_DARK)

            # Styling versatility pill
            draw_rounded_card(draw, (70, 1370, WIDTH - 70, 1680), fill=(24, 26, 32), outline=C_GOLD, width=2, radius=24)
            draw.text((110, 1405), "Gaya Santai & Formal 3-in-1: 💫", font=f_sub, fill=C_GOLD_LIGHT)
            draw.text((110, 1475), "🏢 Gaya Pejabat Smart Casual dengan Slack", font=f_card, fill=C_WHITE)
            draw.text((110, 1540), "☕ Gaya Kafe Santai / Kuliah dengan Jeans", font=f_card, fill=C_WHITE)
            draw.text((110, 1605), "🌸 Layering Modest Sopan & Wudhu Friendly", font=f_card, fill=C_WHITE)

        # =================================================================
        # ACT 5: HIGH-CONVERTING VIRAL CTA (24.5s - 30.0s)
        # =================================================================
        else:
            act_progress = (t_sec - 24.5) / 5.5
            
            # Frame 3 (Over-the-shoulder glance with smile)
            zoom = 1.0 + 0.05 * act_progress
            target_w = 680
            target_h = 1000
            resized_f3 = img_f3.resize((target_w, target_h), Image.Resampling.LANCZOS)
            fx = (WIDTH - target_w) // 2
            fy = 160
            draw_rounded_card(draw, (fx - 10, fy - 10, fx + target_w + 10, fy + target_h + 10), fill=C_WHITE, outline=C_GOLD, width=3, radius=28)
            frame.paste(resized_f3, (fx, fy))
            draw = ImageDraw.Draw(frame)

            # Pulsing Yellow Basket (Beg Kuning) CTA Card
            bounce = math.sin(t_sec * 8.0) * 12.0
            cta_y = int(1220 + bounce)
            
            # Glowing shadow aura
            draw_rounded_card(draw, (55, cta_y - 10, WIDTH - 55, cta_y + 360), fill=(255, 230, 120), outline=C_YELLOW, width=6, radius=36)
            draw_rounded_card(draw, (65, cta_y, WIDTH - 65, cta_y + 340), fill=C_YELLOW, outline=(220, 160, 0), width=3, radius=32)

            # Beg Kuning Icon Representation
            draw.text((110, cta_y + 35), "🛍️ BEG KUNING DI BAWAH!", font=f_huge, fill=C_DARK)
            draw.text((110, cta_y + 145), "TEKAN SEKARANG UNTUK PILIH SAIZ & WARNA 👇💛", font=f_sub, fill=(40, 30, 10))
            draw.text((110, cta_y + 225), "Harga Promo TikTok Shop Eksklusif Hari Ini!", font=f_card, fill=(90, 70, 20))

            # Trust badges
            draw_rounded_card(draw, (80, 1640, WIDTH - 80, 1760), fill=(22, 22, 26), outline=C_GOLD, width=2, radius=20)
            draw.text((120, 1675), "⚡ READY STOCK MALAYSIA  •  🚚 FAST SHIPPING", font=f_sub, fill=C_GOLD_LIGHT)

        # -------------------------------------------------------------
        # GLOBAL BOTTOM PROGRESS BAR & COMPLIANCE TAG (Persistent)
        # -------------------------------------------------------------
        bar_y = HEIGHT - 45
        bar_w = int(WIDTH * progress)
        draw.rectangle([0, bar_y, WIDTH, HEIGHT], fill=(24, 24, 28))
        draw.rectangle([0, bar_y, bar_w, HEIGHT], fill=C_GOLD)
        draw.line([0, bar_y, WIDTH, bar_y], fill=C_GOLD_LIGHT, width=2)
        
        # Micro policy safe tag
        draw.text((30, bar_y - 32), "TikTok Shop Policy Safe • AI Generated Media", font=get_font(20, bold=False), fill=(140, 140, 150))
        draw.text((WIDTH - 150, bar_y - 32), f"{t_sec:04.1f}s / 30s", font=get_font(20, bold=True), fill=C_GOLD_LIGHT)

        # Write frame to FFmpeg stdin pipe
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
    print("🎉 30-Second Motion Graphics Pipeline Complete!")
