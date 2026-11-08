"""Shared constants and small helpers for the reel build (see build_reel.py)."""

import functools
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
# stay on screen long enough to read, or to screenshot. A panel that lands just
# before the cut is never seen.
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


# --- Chinese, Japanese and Korean text --------------------------------------
# DejaVu has no CJK glyphs, so text with any CJK character is drawn in a CJK
# font (which also covers Latin), found from REEL_CJK_FONT (and optionally
# REEL_CJK_BOLD_FONT; a .ttc takes "path#index") or the usual install places.
CJK_CHARS = ("\u2e80-\u2fff\u3000-\u30ff\u3100-\u31ff\u3400-\u4dbf\u4e00-\u9fff"
             "\uac00-\ud7af\uf900-\ufaff\ufe30-\ufe4f\uff00-\uffef")
CJK_RE = re.compile(f"[{CJK_CHARS}]")
# (regular, bold) as (path, index in a .ttc); the first pair whose regular file exists wins
CJK_FONT_CANDIDATES = [
    ((os.path.join(FONT_DIR, "NotoSansCJK-Regular.ttc"), 2), (os.path.join(FONT_DIR, "NotoSansCJK-Bold.ttc"), 2)),
    ((os.path.join(FONT_DIR, "NotoSansSC-Regular.ttf"), 0), (os.path.join(FONT_DIR, "NotoSansSC-Bold.ttf"), 0)),
    (("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2),
     ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 2)),          # Debian, Ubuntu
    (("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 2),
     ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", 2)),               # Arch
    (("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc", 2),
     ("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc", 2)),        # Fedora
    (("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
     ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0)),               # WenQuanYi
    (("/System/Library/Fonts/PingFang.ttc", 0), ("/System/Library/Fonts/PingFang.ttc", 0)),   # macOS
    (("C:/Windows/Fonts/msyh.ttc", 0), ("C:/Windows/Fonts/msyhbd.ttc", 0)),                   # Windows
]
CJK_FONT_HELP = ("no Chinese/Japanese/Korean font found. Download Noto Sans SC (Google Fonts, "
                 "free) and set REEL_CJK_FONT to its regular file (REEL_CJK_BOLD_FONT to its "
                 "bold), or install fonts-noto-cjk.")


def has_cjk(text):
    return bool(CJK_RE.search(text or ""))


def _font_spec(value):
    path, _, index = value.partition("#")
    return path, int(index or 0)


@functools.lru_cache(maxsize=None)
def cjk_font_files():
    """((regular path, index), (bold path, index)) for CJK text, or None."""
    reg = os.environ.get("REEL_CJK_FONT")
    if reg:
        bold = os.environ.get("REEL_CJK_BOLD_FONT") or reg
        reg, bold = _font_spec(reg), _font_spec(bold)
        return (reg, bold) if os.path.exists(reg[0]) else None
    for reg, bold in CJK_FONT_CANDIDATES:
        if os.path.exists(reg[0]):
            return reg, (bold if os.path.exists(bold[0]) else reg)
    return None


@functools.lru_cache(maxsize=None)
def text_font(path, size, text):
    """The font to draw text in: the DejaVu font at path, or, when text has
    any CJK character, the CJK font of the same weight. Raises when CJK
    text has no font, so it never shows as empty boxes."""
    from PIL import ImageFont
    if not has_cjk(text):
        return font(path, size)
    files = cjk_font_files()
    if not files:
        raise RuntimeError(f"text {text[:40]!r}: {CJK_FONT_HELP}")
    p, index = files[1] if path in (BOLD, MONO_BOLD) else files[0]
    return ImageFont.truetype(p, size, index=index)


# A line never starts with closing punctuation; it stays on the line before.
NO_LINE_START = "，。、：；！？）》」』】〉”’%,.:;!?)"


def wrap_tokens(text):
    """The units a line may break between, each with whether a space goes
    before it: whole words for spaced scripts, single characters for CJK
    (which has no spaces), closing punctuation kept with what precedes it."""
    toks = []
    for chunk in text.split():
        for k, piece in enumerate(re.findall(f"[{CJK_CHARS}]|[^{CJK_CHARS}]+", chunk)):
            if toks and k > 0 and piece[0] in NO_LINE_START:
                toks[-1] = (toks[-1][0] + piece, toks[-1][1])
            else:
                toks.append((piece, k == 0))
    return toks


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for tok, spaced in wrap_tokens(text):
        trial = f"{cur} {tok}" if cur and spaced else cur + tok
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    return lines


def fit_lines(d, text, path, size, min_size, max_w, max_h, gap=1.18):
    """The largest font size (size down to min_size) at which text wraps
    into max_w with its lines inside max_h. Returns (font, lines, line
    height), or None: text is never clipped; it shrinks or the build stops."""
    for sz in range(size, min_size - 1, -2):
        f = text_font(path, sz, text)
        lines = wrap(d, text, f, max_w)
        if all(d.textlength(ln, font=f) <= max_w for ln in lines) and \
                len(lines) * sz * gap <= max_h:
            return f, lines, sz * gap
    return None


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
