"""Shared constants and small helpers for the reel build (see build_reel.py)."""

import json
import os
import re
import shutil
import subprocess
import sys

W, H = 720, 1280
FPS = 30
BLUE = (11, 74, 168)
BG = BLUE                    # the one background colour for every shot
PANEL = (20, 40, 90)         # darker blue for boxes drawn on the background
YELLOW = (255, 204, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
FAINT = (185, 195, 210)      # faint card body: subdued but readable

SAFE_TOP = 140               # first tag/headline line (>= 120px safe area)
HEADLINE_WRAP = 640          # headlines never run off the right edge
HEADLINE_SIZE = 52           # one-line headline
HEADLINE_SIZES_2 = (44, 40)  # a headline that needs two lines drops to the first of these
                             # that fits it in two, so the header stack (source line + 2
                             # lines) still ends above the caption band at y=300 and the
                             # captions keep their place. Two lines at 40px hold about
                             # 40 characters (6-8 words).
HEADLINE_MAX_LINES = 2
SOURCE_TEXT = (190, 205, 230)  # muted source line, above the headline
KEEP_BOTTOM = 1030           # bottom safe area: the platform's own caption, name and
                             # buttons cover the last ~250px, so content stays above
EDGE = 8                     # keep boxes stay this far from the side edges
BLUR_TINT = 0.6              # blurred fill: 60% reel blue over 40% blurred image
FIT_BOTTOM = 1000            # lowest edge for drawn content (maps)

# Captions (SKILL.md, "Captions"): burned in, word by word, upper middle.
CAPTION_TOP = 300            # top of the first caption line (about a quarter down)
CAPTION_SIZE = 38            # px; 44 overflowed the frame on long words
CAPTION_MAX_W = 680          # lines wrap by measured width, centred in the 720 frame
CAPTION_LINE_H = 46          # line pitch at 38px
CAPTION_LINES = 2            # a phrase takes at most 2 lines (a 3rd only as overflow)
CAPTION_GAP = 14             # space between the headline stack and the caption
CAPTION_CLEAR = 16           # space between the caption band and content below it
CAPTION_OUTLINE = 4          # thick black outline
CAPTION_SHADOW = 2           # soft drop shadow
TAIL = 0.15                  # pause after each scene's narration (s)
CREEP_SCALE = 0.02           # slow creep: at most 102% scale over a shot
CREEP_UP_PX = 5              # drift-up creep speed (px per second)
# Summary card and end card (SKILL.md, "End card"): the finished card must
# stay on screen long enough to read, or to screenshot. PHP2Shell v2 brought
# five panels in over 1.75s of a 2.2s shot, so the whole card showed for 0.4s.
SUMMARY_STAGGER = 0.35       # s between panels, at most...
SUMMARY_BUILD_SHARE = 0.4    # ...and every panel is in by this share of the shot
SUMMARY_HOLD_MIN = 1.5       # the finished card holds at least this long (s)...
SUMMARY_HOLD_PER_PANEL = 0.4 # ...or this per panel, whichever is longer
END_CARD_HOLD_MIN = 1.5      # the end card runs at least this long (s)
GRAIN_ALPHA = 0.035          # faint grain on flat graphics, as in the reference
GRAIN_FRAMES = 4             # grain frames cycled (enough to read as live)

FONT_DIR = os.environ.get("REEL_FONT_DIR", "/usr/share/fonts/truetype/dejavu")
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")
MONO_BOLD = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")
MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
TTS_DEFAULT = os.environ.get("REEL_TTS", "/opt/hatch/bin/tts")

MATERIALS = {"real", "ai", "recreated", "diagram"}
DIAGRAM_LABEL = "DIAGRAM — ALLEGED CHAIN, NOT SOURCE DATA"
AI_MAP_LABEL = "AI-GENERATED MAP • SCHEMATIC — NOT TO SCALE"
AI_LABEL = "AI-GENERATED ILLUSTRATION"


def run(cmd, check=True):
    # Build pitfall: an overlay with -shortest cut a 48s timeline to one
    # frame. Every overlay here is looped with an explicit frame count.
    if "-shortest" in cmd:
        raise RuntimeError("-shortest is not allowed in the build (it cut a past build to one "
                           "frame); loop the overlay and set an exact frame count or -t.")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r


def probe_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(r.stdout.strip())


def font(path, size):
    from PIL import ImageFont
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def headline_lines(text):
    """(size, lines) for a shot headline: one line at HEADLINE_SIZE if it
    fits, otherwise at the first of HEADLINE_SIZES_2 that fits two lines.
    Validation rejects a headline that needs more than HEADLINE_MAX_LINES."""
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    for n, size in enumerate((HEADLINE_SIZE,) + HEADLINE_SIZES_2):
        f = font(BOLD, size)
        lines = [ln for part in text.split("\n") for ln in wrap(d, part, f, HEADLINE_WRAP)]
        if len(lines) <= (1 if n == 0 else HEADLINE_MAX_LINES):
            break
    return size, lines


def cover_crop(img, tw, th):
    from PIL import Image
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
    x = (img.width - tw) // 2
    y = (img.height - th) // 2
    return img.crop((x, y, x + tw, y + th))


def frames_for(sec):
    return max(1, int(round(sec * FPS)))


def video_frames(path):
    """(frame count, frame rate string) of a file's first video stream,
    counted from its packets (fast; h264 has one packet per frame)."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
             "-show_entries", "stream=nb_read_packets,r_frame_rate", "-of", "json", path])
    st = (json.loads(r.stdout).get("streams") or [{}])[0]
    return int(st.get("nb_read_packets") or 0), st.get("r_frame_rate", "?")


def verify_video(path, frames, what):
    """Build pitfalls: a shot must be exactly `frames` frames at 30 fps, or
    joining shots drifts the video against the audio (mixed frame rates
    joined with -c copy once played a 48s timeline as a 1s file)."""
    got, rate = video_frames(path)
    if rate != f"{FPS}/1" or got != frames:
        raise RuntimeError(f"{what}: {got} frames at {rate}, expected {frames} at {FPS}/1 "
                           f"({path}). Re-render it (--force).")
    return got


def stream_md5(path, stream="a"):
    """MD5 of one stream's encoded packets: equal means the stream was
    copied unchanged."""
    r = run(["ffmpeg", "-v", "error", "-i", path, "-map", f"0:{stream}", "-c", "copy",
             "-f", "md5", "-"])
    return r.stdout.strip().split("=")[-1]
