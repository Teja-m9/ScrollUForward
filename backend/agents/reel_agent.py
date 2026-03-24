"""
Reel Agent — Educational Motion Graphics Explainer Reels
Generates animated 1080x1920 vertical MP4 with:
  - Frame-by-frame Pillow animations (text reveal, diagrams, transitions)
  - Domain-specific visual diagrams (AI neurons, Physics waves, etc.)
  - ElevenLabs TTS voiceover
  - Smooth scene transitions

Pipeline:
  Groq script → ElevenLabs TTS → Animated Pillow frames → FFmpeg assembly → S3

Cost: ~$0.01 per reel.  Assembly time: ~90 seconds.
"""
import os
import json
import uuid
import math
import tempfile
import subprocess
import logging
import asyncio
from datetime import datetime

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    GROQ_API_KEY, GROQ_MODEL_PRIMARY,
    ELEVENLABS_API_KEY, SERPAPI_KEY,
)
from s3_client import upload_reel, upload_thumbnail

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────
# Render at half res for speed, upscale with FFmpeg
RW, RH = 540, 960  # render resolution
W, H = 1080, 1920  # output resolution
FPS = 30
TRANSITION_FRAMES = 12  # fade between scenes

# Domain color themes: (bg_top, bg_bottom, accent)
DOMAIN_COLORS = {
    "technology":           ((15, 15, 35),  (0, 60, 120),   (0, 180, 255)),
    "physics":              ((10, 5, 25),   (60, 15, 100),  (160, 80, 255)),
    "ai":                   ((0, 25, 18),   (0, 60, 45),    (0, 255, 150)),
    "space":                ((3, 3, 18),    (8, 8, 50),     (80, 130, 255)),
    "history":              ((35, 18, 8),   (100, 50, 15),  (255, 160, 60)),
    "nature":               ((8, 25, 8),    (15, 65, 25),   (80, 255, 100)),
    "biology":              ((18, 8, 25),   (50, 25, 70),   (180, 100, 255)),
    "chemistry":            ((25, 18, 8),   (80, 50, 15),   (255, 180, 40)),
    "mathematics":          ((8, 8, 25),    (30, 30, 80),   (100, 130, 255)),
    "philosophy":           ((20, 12, 25),  (55, 30, 65),   (180, 140, 200)),
    "engineering":          ((15, 20, 25),  (40, 55, 70),   (80, 180, 200)),
    "ancient_civilizations":((30, 20, 8),   (80, 55, 25),   (200, 160, 80)),
}


# ── Easing Functions ───────────────────────────────────────
def ease_in_out(t):
    """Smooth S-curve: slow start, fast middle, slow end."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

def ease_out(t):
    """Fast start, slow end."""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3

def ease_in(t):
    """Slow start, fast end."""
    t = max(0.0, min(1.0, t))
    return t ** 3

def pulse(t, speed=2.0):
    """Oscillating pulse 0→1→0→1..."""
    return (math.sin(t * math.pi * speed) + 1.0) / 2.0


# ── Font Cache ─────────────────────────────────────────────
_font_cache = {}

def get_font(size):
    if size in _font_cache:
        return _font_cache[size]
    for fp in ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"]:
        if os.path.exists(fp):
            _font_cache[size] = ImageFont.truetype(fp, size)
            return _font_cache[size]
    _font_cache[size] = ImageFont.load_default()
    return _font_cache[size]


# ── Background Generation ──────────────────────────────────
def create_gradient(w, h, color_top, color_bottom):
    """Create a smooth vertical gradient."""
    img = Image.new("RGB", (w, h))
    pixels = img.load()
    for y in range(h):
        ratio = y / h
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        for x in range(w):
            pixels[x, y] = (r, g, b)
    return img


def create_background(domain):
    """Create cached gradient background for a domain."""
    colors = DOMAIN_COLORS.get(domain, ((15, 15, 30), (0, 50, 80), (0, 150, 200)))
    return create_gradient(RW, RH, colors[0], colors[1])


# ── Animation Drawing Functions ────────────────────────────
def draw_text_reveal(draw, text, font, x, y, progress, color=(255, 255, 255), max_width=None):
    """Reveal text word-by-word based on progress (0.0-1.0)."""
    words = text.split()
    if not words:
        return
    num_visible = max(1, int(len(words) * ease_out(progress)))
    visible_text = " ".join(words[:num_visible])

    if max_width:
        visible_text = wrap_text(visible_text, font, max_width, draw)

    # Slight fade for the last revealed word
    alpha = int(255 * min(1.0, progress * len(words) - (num_visible - 1)))
    alpha = max(100, alpha)
    draw.text((x, y), visible_text, fill=(*color, alpha), font=font)


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def draw_line_animated(draw, x1, y1, x2, y2, progress, color, width=2):
    """Draw a line that extends from start to end based on progress."""
    p = ease_in_out(progress)
    ex = x1 + (x2 - x1) * p
    ey = y1 + (y2 - y1) * p
    draw.line([(x1, y1), (ex, ey)], fill=color, width=width)


def draw_circle_animated(draw, cx, cy, radius, progress, fill=None, outline=None, width=2):
    """Circle that scales in from 0 to full radius."""
    r = radius * ease_out(progress)
    if r < 1:
        return
    bbox = [(cx - r, cy - r), (cx + r, cy + r)]
    draw.ellipse(bbox, fill=fill, outline=outline, width=width)


def draw_progress_bar(draw, x, y, w, h, progress, bg_color, fill_color):
    """Animated progress bar."""
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=h // 2, fill=bg_color)
    fill_w = max(h, w * ease_in_out(progress))
    draw.rounded_rectangle([(x, y), (x + fill_w, y + h)], radius=h // 2, fill=fill_color)


def draw_glow(draw, cx, cy, radius, color, intensity):
    """Soft glow circle with variable intensity."""
    alpha = int(40 * intensity)
    for i in range(3):
        r = radius + i * 8
        a = max(0, alpha - i * 12)
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(*color, a))


def draw_number_badge(draw, number, cx, cy, progress, accent):
    """Animated number badge that pops in."""
    scale = ease_out(min(1.0, progress * 2))
    r = int(22 * scale)
    if r < 2:
        return
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=accent)
    if scale > 0.5:
        font = get_font(int(24 * scale))
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy - th // 2 - 2), text, fill=(0, 0, 0), font=font)


def draw_domain_badge(draw, domain, accent, progress):
    """Domain badge that slides in from left."""
    p = ease_out(min(1.0, progress * 3))
    x = int(-80 + 95 * p)
    y = 30
    text = domain.upper().replace("_", " ")
    font = get_font(12)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.rounded_rectangle([(x, y), (x + tw + 20, y + 22)], radius=11, fill=(*accent, int(200 * p)))
    draw.text((x + 10, y + 4), text, fill=(0, 0, 0, int(255 * p)), font=font)


# ── Domain-Specific Diagram Generators (BIG, BOLD, CENTER-SCREEN) ──
# All diagrams use the center area: cx=RW//2, cy=RH*0.3 (top 40% of screen)
# Sizes are LARGE — fills most of the width

def draw_diagram_ai(draw, progress, accent):
    """Neural network: BIG nodes + thick connections, fills screen."""
    cx, cy = RW // 2, int(RH * 0.3)
    layers = [3, 5, 4, 3]
    spacing_x = 110
    positions = []
    for li, count in enumerate(layers):
        lx = cx - (len(layers) - 1) * spacing_x // 2 + li * spacing_x
        layer_p = ease_out(max(0, min(1, (progress - li * 0.12) * 3)))
        lpos = []
        for ni in range(count):
            ny = cy - (count - 1) * 40 + ni * 80
            r = 18
            # Pulsing glow behind node
            glow_r = r + 8 + int(6 * pulse(progress + ni * 0.3, 2))
            draw.ellipse([(lx - glow_r, ny - glow_r), (lx + glow_r, ny + glow_r)],
                        fill=(*accent, int(30 * layer_p)))
            draw_circle_animated(draw, lx, ny, r, layer_p,
                               fill=(*accent, int(220 * layer_p)), outline=(255, 255, 255, int(200 * layer_p)), width=2)
            lpos.append((lx, ny))
        positions.append(lpos)
    # Thick connections with signal animation
    for li in range(len(positions) - 1):
        conn_p = ease_out(max(0, min(1, (progress - 0.2 - li * 0.1) * 3)))
        for p1 in positions[li]:
            for p2 in positions[li + 1]:
                if conn_p > 0:
                    draw_line_animated(draw, p1[0], p1[1], p2[0], p2[1], conn_p,
                                     (*accent, int(120 * conn_p)), 3)
    # Signal dot moving along a connection
    if progress > 0.4 and len(positions) > 1:
        sig_p = (progress - 0.4) * 3 % 1.0
        p1 = positions[0][1]
        p2 = positions[1][2] if len(positions[1]) > 2 else positions[1][0]
        sx = p1[0] + (p2[0] - p1[0]) * sig_p
        sy = p1[1] + (p2[1] - p1[1]) * sig_p
        draw.ellipse([(sx - 6, sy - 6), (sx + 6, sy + 6)], fill=(255, 255, 255, 255))


def draw_diagram_physics(draw, progress, accent):
    """BIG sine wave with moving particle."""
    cx, cy = RW // 2, int(RH * 0.3)
    amplitude = 100
    wave_w = RW - 80
    # Axes
    draw_line_animated(draw, 40, cy, RW - 40, cy, min(1, progress * 1.5), (*accent, 80), 2)
    draw_line_animated(draw, cx, cy + amplitude + 30, cx, cy - amplitude - 30, min(1, progress * 1.5), (*accent, 80), 2)
    # Wave draws progressively
    points = []
    n = int(200 * ease_in_out(progress))
    for i in range(n):
        x = 40 + i * (wave_w / 200)
        y = cy + math.sin(i * 0.06 + progress * 4) * amplitude * ease_out(min(1, progress * 2))
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=(*accent, 255), width=4)
    # Moving bright dot on wave tip
    if points:
        tip = points[-1]
        draw.ellipse([(tip[0] - 8, tip[1] - 8), (tip[0] + 8, tip[1] + 8)], fill=(255, 255, 255, 255))
        # Glow
        draw.ellipse([(tip[0] - 20, tip[1] - 20), (tip[0] + 20, tip[1] + 20)], fill=(*accent, 50))


def draw_diagram_space(draw, progress, accent):
    """Solar system with orbiting planets."""
    cx, cy = RW // 2, int(RH * 0.3)
    # Sun (center, pulses)
    sun_r = 25 + int(5 * pulse(progress, 1.5))
    draw.ellipse([(cx - sun_r - 10, cy - sun_r - 10), (cx + sun_r + 10, cy + sun_r + 10)], fill=(*accent, 30))
    draw.ellipse([(cx - sun_r, cy - sun_r), (cx + sun_r, cy + sun_r)], fill=accent)
    # Orbits + planets
    for i in range(4):
        orbit_r = 60 + i * 50
        rp = ease_out(max(0, min(1, (progress - i * 0.1) * 3)))
        if rp > 0:
            # Draw orbit ring
            draw_circle_animated(draw, cx, cy, orbit_r, rp, outline=(*accent, int(60 * rp)), width=2)
            # Planet moves along orbit
            speed = 2 + i * 0.8
            angle = progress * math.pi * speed + i * 1.2
            px = cx + orbit_r * math.cos(angle) * rp
            py = cy + orbit_r * math.sin(angle) * rp
            planet_r = 10 - i * 1.5
            draw.ellipse([(px - planet_r, py - planet_r), (px + planet_r, py + planet_r)],
                        fill=(255, 255, 255, int(255 * rp)))


def draw_diagram_history(draw, progress, accent):
    """BIG timeline spanning full width with event markers."""
    cy = int(RH * 0.3)
    x_start, x_end = 30, RW - 30
    # Main line
    draw_line_animated(draw, x_start, cy, x_end, cy, min(1, progress * 1.5), accent, 4)
    # Event markers
    events = 6
    for i in range(events):
        dp = ease_out(max(0, min(1, (progress - i * 0.12) * 4)))
        x = x_start + i * (x_end - x_start) // (events - 1)
        # Vertical line
        draw_line_animated(draw, x, cy - 50, x, cy + 50, dp, (*accent, int(200 * dp)), 3)
        # Circle marker
        r = int(14 * dp)
        if r > 2:
            draw.ellipse([(x - r, cy - r), (x + r, cy + r)], fill=(*accent, int(255 * dp)),
                        outline=(255, 255, 255, int(200 * dp)), width=2)
        # Glow on latest appearing
        if dp > 0.3 and dp < 0.9:
            glow_r = int(30 * dp)
            draw.ellipse([(x - glow_r, cy - glow_r), (x + glow_r, cy + glow_r)], fill=(*accent, int(25 * dp)))


def draw_diagram_biology(draw, progress, accent):
    """BIG cell with membrane, nucleus, organelles."""
    cx, cy = RW // 2, int(RH * 0.3)
    # Outer membrane (big)
    mem_r = 120
    draw_circle_animated(draw, cx, cy, mem_r, min(1, progress * 1.5),
                        outline=(*accent, 200), width=4)
    # Membrane glow
    draw_circle_animated(draw, cx, cy, mem_r + 10, min(1, progress * 1.5),
                        outline=(*accent, 40), width=8)
    # Nucleus
    nuc_p = max(0, min(1, (progress - 0.15) * 3))
    draw_circle_animated(draw, cx, cy, 40, nuc_p,
                        fill=(*accent, int(80 * nuc_p)), outline=accent, width=3)
    # Organelles orbiting
    for i in range(7):
        op = ease_out(max(0, min(1, (progress - 0.25 - i * 0.06) * 4)))
        angle = i * math.pi * 2 / 7 + progress * 1.5
        dist = 70 + (i % 3) * 15
        ox = cx + dist * math.cos(angle)
        oy = cy + dist * math.sin(angle)
        r = 12 - (i % 3) * 2
        draw_circle_animated(draw, ox, oy, r, op, fill=(*accent, int(160 * op)))


def draw_diagram_math(draw, progress, accent):
    """BIG coordinate system with animated curve + data points."""
    cx, cy = RW // 2, int(RH * 0.3)
    span_x, span_y = 200, 140
    # Axes (thick)
    draw_line_animated(draw, cx - span_x, cy, cx + span_x, cy, min(1, progress * 1.5), (*accent, 120), 3)
    draw_line_animated(draw, cx, cy + span_y, cx, cy - span_y, min(1, progress * 1.5), (*accent, 120), 3)
    # Arrow tips
    if progress > 0.3:
        draw.polygon([(cx + span_x - 5, cy - 6), (cx + span_x + 8, cy), (cx + span_x - 5, cy + 6)], fill=(*accent, 150))
        draw.polygon([(cx - 6, cy - span_y - 8), (cx, cy - span_y + 5), (cx + 6, cy - span_y - 8)], fill=(*accent, 150))
    # Curve
    points = []
    n = int(160 * ease_in_out(max(0, min(1, (progress - 0.2) * 2))))
    for i in range(n):
        t = i / 160
        x = cx - span_x + 10 + t * (span_x * 2 - 20)
        y = cy - span_y * 0.8 * math.sin(t * math.pi) * ease_out(t)
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=accent, width=4)
    # Data points appearing
    for i in range(6):
        dp = ease_out(max(0, min(1, (progress - 0.3 - i * 0.08) * 5)))
        t = (i + 0.5) / 6
        x = cx - span_x + 10 + t * (span_x * 2 - 20)
        y = cy - span_y * 0.8 * math.sin(t * math.pi) * ease_out(t) - 5
        r = int(7 * dp)
        if r > 1:
            draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=(255, 255, 255, int(255 * dp)))


def draw_diagram_technology(draw, progress, accent):
    """BIG circuit board grid with signals."""
    cx, cy = RW // 2, int(RH * 0.3)
    grid = 5
    sp = 60
    for r in range(grid):
        for c in range(grid):
            dp = ease_out(max(0, min(1, (progress - (r + c) * 0.04) * 3)))
            x = cx - (grid - 1) * sp // 2 + c * sp
            y = cy - (grid - 1) * sp // 2 + r * sp
            # Node
            nr = int(10 * dp)
            if nr > 1:
                draw.ellipse([(x - nr, y - nr), (x + nr, y + nr)],
                            fill=(*accent, int(200 * dp)), outline=(255, 255, 255, int(150 * dp)), width=2)
            # Lines to right
            if c < grid - 1 and dp > 0.3:
                nx = x + sp
                draw_line_animated(draw, x + nr, y, nx - nr, y, dp, (*accent, int(140 * dp)), 3)
            # Lines down
            if r < grid - 1 and dp > 0.3:
                ny = y + sp
                draw_line_animated(draw, x, y + nr, x, ny - nr, dp, (*accent, int(140 * dp)), 3)
    # Signal pulse moving through grid
    if progress > 0.5:
        sig_t = (progress - 0.5) * 4 % 1.0
        sx = cx - (grid - 1) * sp // 2 + sig_t * (grid - 1) * sp
        sy = cy
        draw.ellipse([(sx - 8, sy - 8), (sx + 8, sy + 8)], fill=(255, 255, 255, 255))


DIAGRAM_FUNCS = {
    "ai": draw_diagram_ai,
    "physics": draw_diagram_physics,
    "space": draw_diagram_space,
    "history": draw_diagram_history,
    "ancient_civilizations": draw_diagram_history,
    "biology": draw_diagram_biology,
    "nature": draw_diagram_biology,
    "mathematics": draw_diagram_math,
    "chemistry": draw_diagram_math,
    "technology": draw_diagram_technology,
    "engineering": draw_diagram_technology,
    "philosophy": draw_diagram_ai,
}


# ── Scene Visual Styles (each scene gets a DIFFERENT animation) ────
SCENE_VISUALS = [
    "title_zoom",      # Scene 0 (hook): big title zooms in + accent glow
    "diagram_build",   # Scene 1: domain diagram builds step by step
    "counter_bars",    # Scene 2: animated progress bars / comparison
    "diagram_evolve",  # Scene 3: diagram continues evolving with new elements
    "particles_flow",  # Scene 4: particle system flowing across screen
    "cta_pulse",       # Scene 5 (CTA): pulsing call to action
]


def draw_scene_title_zoom(draw, progress, text, accent, scene_num):
    """Hook: 3-phase cinematic intro. Glow → Title word-by-word → Decorations."""
    cx, cy = RW // 2, int(RH * 0.25)

    # Phase 1 (0-40%): Slow expanding glow rings from center
    glow_p = min(1, progress / 0.4) if progress < 0.4 else 1.0
    for ring in range(8):
        rp = ease_in_out(max(0, min(1, (glow_p - ring * 0.06) * 2)))
        r = int((15 + ring * 28) * rp)
        alpha = int(max(0, 45 - ring * 5) * rp)
        if r > 3:
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(*accent, alpha))

    # Phase 2 (25-80%): Text reveals one word at a time, SLOWLY
    if progress > 0.25:
        tp = min(1, (progress - 0.25) / 0.55)
        font = get_font(28)
        words = text.split()
        num_visible = max(1, int(len(words) * ease_in_out(tp)))
        y = int(RH * 0.4)
        line = ""
        for wi in range(num_visible):
            test = line + " " + words[wi] if line else words[wi]
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > RW - 80:
                # Draw current line centered
                bbox2 = draw.textbbox((0, 0), line, font=font)
                tw = bbox2[2] - bbox2[0]
                draw.text((cx - tw // 2, y), line, fill=(255, 255, 255, 255), font=font)
                y += 42
                line = words[wi]
            else:
                line = test
        # Draw remaining line
        if line:
            bbox2 = draw.textbbox((0, 0), line, font=font)
            tw = bbox2[2] - bbox2[0]
            # Last word fades in
            last_word_alpha = int(255 * min(1, (tp * len(words) - (num_visible - 1)) * 2))
            draw.text((cx - tw // 2, y), line, fill=(255, 255, 255, max(120, last_word_alpha)), font=font)

    # Phase 3 (70-100%): Accent underline draws under text
    if progress > 0.7:
        lp = ease_out((progress - 0.7) / 0.3)
        line_w = int((RW - 120) * lp)
        ly = int(RH * 0.62)
        draw_line_animated(draw, cx - line_w // 2, ly, cx + line_w // 2, ly, 1.0, (*accent, int(180 * lp)), 3)


def draw_scene_counter_bars(draw, progress, text, accent, scene_num):
    """3-phase: Bars appear one by one → fill slowly → text reveals below."""
    cy_start = int(RH * 0.12)
    bar_count = 4
    bar_h = 30
    bar_gap = 65
    max_w = RW - 110
    labels = ["Concept", "Example", "Application", "Impact"]
    fill_pcts = [0.85, 0.7, 0.9, 0.6]

    for i in range(bar_count):
        # Phase 1: Bar slides in from left (staggered)
        appear_p = ease_out(max(0, min(1, (progress - i * 0.08) * 2)))
        y = cy_start + i * bar_gap

        if appear_p <= 0:
            continue

        # Label fades in
        label_font = get_font(15)
        draw.text((50, y - 20), labels[i], fill=(255, 255, 255, int(200 * appear_p)), font=label_font)

        # Bar background
        bg_w = int(max_w * appear_p)
        draw.rounded_rectangle([(50, y), (50 + bg_w, y + bar_h)], radius=bar_h // 2, fill=(255, 255, 255, 20))

        # Phase 2: Bar fills SLOWLY after appearing
        fill_delay = 0.15 + i * 0.1
        fill_p = ease_in_out(max(0, min(1, (progress - fill_delay) * 1.5)))
        fill_w = max(bar_h, int(max_w * fill_pcts[i] * fill_p))
        draw.rounded_rectangle([(50, y), (50 + fill_w, y + bar_h)], radius=bar_h // 2,
                              fill=(*accent, int(220 * appear_p)))

        # Glowing tip
        if fill_p > 0.1 and fill_p < 0.95:
            tip_x = 50 + fill_w
            draw.ellipse([(tip_x - 6, y + bar_h // 2 - 6), (tip_x + 6, y + bar_h // 2 + 6)],
                        fill=(255, 255, 255, int(200 * appear_p)))

        # Percentage counter
        if fill_p > 0.3:
            pct_font = get_font(16)
            pct_val = int(fill_pcts[i] * 100 * fill_p)
            draw.text((50 + fill_w + 12, y + 5), f"{pct_val}%",
                     fill=(255, 255, 255, int(255 * fill_p)), font=pct_font)

    # Phase 3: Text reveals word-by-word below bars
    text_y = cy_start + bar_count * bar_gap + 30
    text_p = max(0, min(1, (progress - 0.5) / 0.5))
    font = get_font(18)
    draw_text_reveal(draw, text, font, 40, text_y, text_p, max_width=RW - 80)


def draw_scene_particles_flow(draw, progress, text, accent, scene_num):
    """3-phase: Particles emerge from center → flow outward → text overlays."""
    cx, cy = RW // 2, int(RH * 0.28)
    num_particles = 40

    # Phase 1 (0-100%): Particles continuously flow — slow, organic movement
    positions = []
    for i in range(num_particles):
        # Each particle on its own slow path
        life = (progress * 1.5 + i * 0.05) % 1.0
        # Spiral outward from center
        angle = i * 0.618 * math.pi * 2 + progress * math.pi * 0.5
        dist = life * 180
        x = cx + dist * math.cos(angle)
        y = cy + dist * math.sin(angle) * 0.6  # slightly elliptical

        r = 3 + (i % 5) * 2
        # Fade in near center, fade out at edges
        alpha = int(200 * math.sin(life * math.pi))
        if alpha > 15 and 0 < x < RW and 0 < y < RH:
            # Outer glow
            draw.ellipse([(x - r * 3, y - r * 3), (x + r * 3, y + r * 3)], fill=(*accent, alpha // 6))
            # Core
            draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=(*accent, alpha))
            positions.append((x, y))

    # Phase 2: Connecting lines between nearby particles (network effect)
    for i in range(len(positions)):
        for j in range(i + 1, min(i + 5, len(positions))):
            x1, y1 = positions[i]
            x2, y2 = positions[j]
            dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if dist < 80:
                line_alpha = int(50 * (1 - dist / 80))
                draw.line([(x1, y1), (x2, y2)], fill=(*accent, line_alpha), width=1)

    # Phase 3: Text in bottom portion, word by word
    text_y = int(RH * 0.58)
    tp = max(0, min(1, (progress - 0.15) / 0.7))
    font = get_font(19)
    # Dark backing
    bar_alpha = int(150 * ease_in_out(min(1, progress * 2)))
    draw.rectangle([(0, text_y - 15), (RW, text_y + 160)], fill=(0, 0, 0, bar_alpha))
    draw_text_reveal(draw, text, font, 35, text_y, tp, max_width=RW - 70)


def draw_scene_cta_pulse(draw, progress, text, accent, scene_num):
    """3-phase: Slow pulsing rings → question fades in → text reveals → button appears."""
    cx, cy = RW // 2, int(RH * 0.25)

    # Phase 1 (0-100%): Continuous slow pulsing rings
    for ring in range(5):
        rp = (progress * 0.8 + ring * 0.2) % 1.0  # slow pulse
        r = int(20 + rp * 150)
        alpha = int(60 * (1 - rp))
        if alpha > 5:
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(*accent, alpha), width=3)

    # Phase 2 (10-40%): Question mark slowly fades in
    if progress > 0.1:
        qp = ease_in_out(min(1, (progress - 0.1) / 0.3))
        q_font = get_font(80)
        draw.text((cx - 25, cy - 50), "?", fill=(*accent, int(255 * qp)), font=q_font)

    # Phase 3 (30-85%): Text word by word
    if progress > 0.3:
        tp = min(1, (progress - 0.3) / 0.55)
        font = get_font(22)
        wrapped = wrap_text(text, font, RW - 90, draw)
        lines = wrapped.split("\n")
        total_words = sum(len(l.split()) for l in lines)
        words_shown = max(1, int(total_words * ease_in_out(tp)))
        y = int(RH * 0.48)
        wc = 0
        for line in lines:
            ws = line.split()
            vis = [w for w in ws if (wc := wc + 1) <= words_shown]
            if vis:
                vt = " ".join(vis)
                bbox = draw.textbbox((0, 0), vt, font=font)
                tw = bbox[2] - bbox[0]
                draw.text((cx - tw // 2, y), vt, fill=(255, 255, 255, 255), font=font)
            y += 32

    # Phase 4 (75-100%): Follow button slides up
    if progress > 0.75:
        btn_p = ease_out((progress - 0.75) / 0.25)
        btn_w, btn_h = int(220 * btn_p), int(44 * btn_p)
        bx, by = cx - btn_w // 2, int(RH * 0.72)
        if btn_w > 20:
            draw.rounded_rectangle([(bx, by), (bx + btn_w, by + btn_h)], radius=btn_h // 2, fill=(*accent, int(240 * btn_p)))
            if btn_p > 0.6:
                bf = get_font(16)
                draw.text((bx + 40, by + 10), "FOLLOW FOR MORE", fill=(0, 0, 0, int(255 * btn_p)), font=bf)


# ── Scene Frame Generator ──────────────────────────────────
def generate_animated_frames(script_parts, domain, audio_duration, output_dir):
    """
    Generate animated frames synced to audio duration.
    Each scene gets a UNIQUE visual style that evolves slowly.
    """
    colors = DOMAIN_COLORS.get(domain, ((15, 15, 30), (0, 50, 80), (0, 150, 200)))
    accent = colors[2]
    bg_base = create_background(domain)
    diagram_func = DIAGRAM_FUNCS.get(domain, draw_diagram_ai)

    # Build scenes from script — each scene gets ALL animation layers
    scenes = []
    scenes.append({"type": "hook", "text": script_parts.get("hook", ""), "phase": "intro"})
    points = script_parts.get("points", [])[:4]
    for i, pt in enumerate(points):
        scenes.append({"type": "point", "text": pt, "num": i + 1, "phase": ["build", "deepen", "reveal", "connect"][i % 4]})
    scenes.append({"type": "cta", "text": script_parts.get("cta", ""), "phase": "close"})

    # Audio-synced timing
    total_dur = max(audio_duration, 15.0)
    scene_dur = total_dur / len(scenes)
    frames_per_scene = max(FPS * 3, int(scene_dur * FPS))  # at least 3 sec per scene

    frame_paths = []
    global_frame = 0
    total_scene_frames = frames_per_scene * len(scenes)

    for si, scene in enumerate(scenes):
        for fi in range(frames_per_scene):
            progress = fi / frames_per_scene  # 0.0 → 1.0 within this scene
            overall_progress = (si * frames_per_scene + fi) / total_scene_frames
            # Diagram progress builds across ALL scenes (0→1 over entire video)
            diagram_progress = ease_in_out(min(1, overall_progress * 1.2))

            # Background
            img = bg_base.copy()
            overlay = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay, "RGBA")

            # ═══ LAYER 1: Domain diagram — ALWAYS visible, evolves across entire video ═══
            diagram_func(draw, diagram_progress, accent)

            # ═══ LAYER 2: Ambient particles — ALWAYS flowing, subtle background life ═══
            cx, cy = RW // 2, int(RH * 0.3)
            for pi in range(20):
                life = (overall_progress * 1.2 + pi * 0.07) % 1.0
                angle = pi * 0.618 * math.pi * 2 + overall_progress * math.pi * 0.3
                dist = life * 200
                px = cx + dist * math.cos(angle)
                py = cy + dist * math.sin(angle) * 0.5
                r = 2 + (pi % 3) * 2
                alpha = int(80 * math.sin(life * math.pi))
                if alpha > 8 and 0 < px < RW and 0 < py < RH:
                    draw.ellipse([(px - r, py - r), (px + r, py + r)], fill=(*accent, alpha))

            # ═══ LAYER 3: Scene-specific accent animation ═══
            phase = scene.get("phase", "build")
            if phase == "intro":
                # Slow expanding glow rings
                for ring in range(6):
                    rp = ease_in_out(max(0, min(1, (progress - ring * 0.08) * 1.5)))
                    r = int((20 + ring * 30) * rp)
                    a = int(max(0, 40 - ring * 6) * rp)
                    if r > 3:
                        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(*accent, a))
            elif phase == "build":
                # Progress bars slowly filling
                for bi in range(3):
                    bp = ease_out(max(0, min(1, (progress - bi * 0.15) * 1.8)))
                    by = int(RH * 0.08) + bi * 50
                    bar_w = int((RW - 120) * [0.8, 0.6, 0.9][bi] * bp)
                    draw.rounded_rectangle([(60, by), (60 + bar_w, by + 22)], radius=11, fill=(*accent, int(150 * bp)))
                    draw.rounded_rectangle([(60, by), (60 + RW - 120, by + 22)], radius=11, outline=(*accent, 30), width=1)
            elif phase == "deepen":
                # Pulsing highlight rings around diagram center
                for ring in range(4):
                    rp = pulse(progress + ring * 0.25, 1.0)
                    r = 50 + ring * 35
                    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(*accent, int(40 * rp)), width=2)
            elif phase == "reveal":
                # Connecting lines radiating outward
                for li in range(8):
                    lp = ease_out(max(0, min(1, (progress - li * 0.06) * 2)))
                    angle = li * math.pi / 4
                    x1 = cx + 40 * math.cos(angle)
                    y1 = cy + 40 * math.sin(angle)
                    x2 = cx + (40 + 120 * lp) * math.cos(angle)
                    y2 = cy + (40 + 120 * lp) * math.sin(angle)
                    draw.line([(x1, y1), (x2, y2)], fill=(*accent, int(100 * lp)), width=2)
                    # End dot
                    draw.ellipse([(x2 - 4, y2 - 4), (x2 + 4, y2 + 4)], fill=(*accent, int(180 * lp)))
            elif phase == "connect":
                # Network mesh connecting dots
                pts = []
                for ni in range(12):
                    np_ = ease_out(max(0, min(1, (progress - ni * 0.04) * 2)))
                    nx = 60 + (ni % 4) * (RW - 120) // 3
                    ny = int(RH * 0.08) + (ni // 4) * 55
                    pts.append((nx, ny, np_))
                    draw.ellipse([(nx - 5, ny - 5), (nx + 5, ny + 5)], fill=(*accent, int(160 * np_)))
                for i in range(len(pts)):
                    for j in range(i + 1, len(pts)):
                        if abs(pts[i][0] - pts[j][0]) < 200 and abs(pts[i][1] - pts[j][1]) < 80:
                            a = int(40 * min(pts[i][2], pts[j][2]))
                            if a > 5:
                                draw.line([(pts[i][0], pts[i][1]), (pts[j][0], pts[j][1])], fill=(*accent, a), width=1)
            elif phase == "close":
                # Pulsing rings + question mark
                for ring in range(5):
                    rp = (progress * 0.6 + ring * 0.2) % 1.0
                    r = int(20 + rp * 130)
                    a = int(50 * (1 - rp))
                    if a > 3:
                        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(*accent, a), width=2)
                qp = ease_in_out(min(1, progress * 1.5))
                q_font = get_font(70)
                draw.text((cx - 22, cy - 45), "?", fill=(*accent, int(255 * qp)), font=q_font)

            # ═══ LAYER 4: Text — word-by-word reveal in bottom portion ═══
            text = scene.get("text", "")
            if text:
                text_y = int(RH * 0.60)
                # Dark backing for readability
                tp = max(0, min(1, (progress - 0.1) / 0.7))
                bar_alpha = int(160 * ease_in_out(min(1, progress * 3)))
                draw.rectangle([(0, text_y - 20), (RW, RH)], fill=(0, 0, 0, bar_alpha))
                font = get_font(18)
                draw_text_reveal(draw, text, font, 30, text_y, tp, max_width=RW - 60)

            # ── Domain badge (always visible, top-left)
            draw_domain_badge(draw, domain, accent, min(1, overall_progress * 5))

            # ── Number badge (for points)
            if scene.get("num"):
                draw_number_badge(draw, scene["num"], RW - 40, 35, min(1, progress * 3), accent)

            # ── Bottom progress bar
            draw_progress_bar(draw, 15, RH - 20, RW - 30, 4, overall_progress, (255, 255, 255, 25), (*accent, 200))

            # Composite
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            img = img.convert("RGB")

            fp = os.path.join(output_dir, f"frame_{global_frame:05d}.png")
            img.save(fp, "PNG", optimize=False)
            frame_paths.append(fp)
            global_frame += 1

        # Scene transition: smooth crossfade to darker
        if si < len(scenes) - 1:
            last = img.copy()
            for ti in range(TRANSITION_FRAMES):
                tp = ti / TRANSITION_FRAMES
                dark = Image.new("RGB", (RW, RH), colors[0])
                blended = Image.blend(last, dark, ease_in_out(tp) * 0.5)
                fp = os.path.join(output_dir, f"frame_{global_frame:05d}.png")
                blended.save(fp, "PNG", optimize=False)
                frame_paths.append(fp)
                global_frame += 1

    logger.info(f"[ReelAgent] Generated {len(frame_paths)} animated frames ({global_frame / FPS:.1f}s)")
    return frame_paths


# ── Groq Script Generation ─────────────────────────────────
def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


async def research_topic(domain):
    if SERPAPI_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("https://serpapi.com/search.json",
                    params={"q": f"latest {domain} discovery 2025", "api_key": SERPAPI_KEY, "num": 5})
                results = resp.json().get("organic_results", [])
                if results:
                    return {"topic": results[0].get("title", f"Latest in {domain}"), "snippet": results[0].get("snippet", "")}
        except Exception as e:
            logger.warning(f"SerpAPI failed: {e}")
    groq = _get_groq()
    resp = groq.chat.completions.create(model=GROQ_MODEL_PRIMARY,
        messages=[{"role": "system", "content": f"Suggest one trending educational topic in {domain}. Reply with just the topic title."},
                  {"role": "user", "content": f"What's a fascinating recent topic in {domain}?"}], max_tokens=50)
    return {"topic": resp.choices[0].message.content.strip(), "snippet": ""}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_script(topic, domain):
    groq = _get_groq()
    resp = groq.chat.completions.create(model=GROQ_MODEL_PRIMARY,
        messages=[
            {"role": "system", "content": (
                "You are an expert science communicator creating a 90-second educational reel "
                "in the style of popular YouTube explainer videos (like 3Blue1Brown, Kurzgesagt). "
                "Use the Story → Visual → Concept method. Start with a real-world analogy, "
                "then explain step by step with examples.\n\n"
                "Return ONLY a JSON object:\n"
                '{"hook": "Opening with a fascinating real-world analogy or mind-blowing fact (2-3 sentences, ~40 words)", '
                '"points": ['
                '"Step 1: Explain the basic concept using a simple analogy everyone understands (3 sentences, ~50 words)", '
                '"Step 2: Go deeper with a specific example or case study (3 sentences, ~50 words)", '
                '"Step 3: Reveal the surprising implication or cutting-edge application (3 sentences, ~50 words)", '
                '"Step 4: Connect it back to the bigger picture or future impact (2-3 sentences, ~40 words)"'
                '], '
                '"cta": "Thought-provoking closing question that makes the viewer reflect (1-2 sentences, ~20 words)"}\n\n'
                "IMPORTANT: Each section must be DETAILED with examples, not bullet points. "
                "Write like you're narrating a documentary. Make it conversational and engaging.")},
            {"role": "user", "content": f"Topic: {topic}. Domain: {domain}. Date: {datetime.utcnow().strftime('%Y-%m-%d')}. Make it for a curious adult."}
        ], max_tokens=1200, temperature=0.7)
    text = resp.choices[0].message.content.strip()
    try:
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"hook": topic, "points": [text[:80]], "cta": f"What do you think about {domain}?"}


# ── ElevenLabs TTS ─────────────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_voiceover(script_parts, output_path):
    if not ELEVENLABS_API_KEY:
        return ""
    full_text = script_parts["hook"] + ". " + ". ".join(script_parts.get("points", [])) + ". " + script_parts.get("cta", "")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post("https://api.elevenlabs.io/v1/text-to-speech/CwhRBWXzGAHq8TQ4Fs17",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={"text": full_text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}})
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)
    logger.info(f"[ReelAgent] TTS: {len(resp.content)} bytes")
    return output_path


def get_audio_duration(audio_path):
    try:
        result = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", audio_path],
            capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except:
        return 30.0


# ── FFmpeg Assembly ────────────────────────────────────────
def assemble_reel(frame_dir, audio_path, output_path):
    """Assemble animated frames + audio into MP4."""
    has_audio = audio_path and os.path.exists(audio_path)
    frame_pattern = os.path.join(frame_dir, "frame_%05d.png").replace("\\", "/")

    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", frame_pattern]
    if has_audio:
        cmd.extend(["-i", audio_path])

    cmd.extend([
        "-vf", f"scale={W}:{H}:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
    ])
    if has_audio:
        cmd.extend(["-c:a", "aac", "-shortest"])
    cmd.append(output_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr[-300:]}")
            return ""
        logger.info(f"[ReelAgent] Assembled: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"FFmpeg failed: {e}")
        return ""


# ── Full Pipeline ──────────────────────────────────────────
async def run_reel_agent(domain):
    reel_id = f"reel_{uuid.uuid4().hex[:12]}"
    logger.info(f"[ReelAgent] Starting domain={domain}, id={reel_id}")

    # Step 1: Topic
    topic_data = await research_topic(domain)
    topic = topic_data["topic"]
    logger.info(f"[ReelAgent] Topic: {topic}")

    # Step 2: Script
    script_parts = generate_script(topic, domain)
    full_script = script_parts["hook"] + " " + " ".join(script_parts.get("points", [])) + " " + script_parts.get("cta", "")
    logger.info(f"[ReelAgent] Script: {len(full_script)} chars")

    # Step 3: TTS
    tmp_dir = tempfile.mkdtemp(prefix="reel_anim_")
    audio_path = os.path.join(tmp_dir, "voiceover.mp3")
    try:
        await generate_voiceover(script_parts, audio_path)
    except Exception as e:
        logger.warning(f"[ReelAgent] TTS failed: {e}")
        audio_path = ""

    # Step 4: Get audio duration
    audio_dur = get_audio_duration(audio_path) if audio_path else 30.0
    logger.info(f"[ReelAgent] Audio duration: {audio_dur:.1f}s")

    # Step 5: Generate animated frames
    frame_paths = generate_animated_frames(script_parts, domain, audio_dur, tmp_dir)

    # Step 6: FFmpeg assembly
    output_mp4 = os.path.join(tmp_dir, f"{reel_id}.mp4")
    assembled = assemble_reel(tmp_dir, audio_path, output_mp4)

    # Step 7: Upload to S3
    s3_video_url = ""
    s3_thumb_url = ""
    if assembled and os.path.exists(assembled):
        size = os.path.getsize(assembled)
        logger.info(f"[ReelAgent] MP4: {size / 1024:.0f} KB")
        try:
            s3_video_url = upload_reel(assembled, domain, reel_id)
        except Exception as e:
            logger.error(f"[ReelAgent] S3 upload failed: {e}")

    if frame_paths:
        try:
            # Use a middle frame as thumbnail (more interesting than first)
            thumb_idx = len(frame_paths) // 3
            with open(frame_paths[thumb_idx], "rb") as f:
                s3_thumb_url = upload_thumbnail(f.read(), domain, reel_id)
        except Exception as e:
            logger.error(f"[ReelAgent] Thumb upload failed: {e}")

    return {
        "reel_id": reel_id,
        "domain": domain,
        "title": topic,
        "script_text": full_script,
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "source_type": "ai_generated",
        "content_type": "reel",
    }
