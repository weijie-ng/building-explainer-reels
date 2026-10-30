#!/usr/bin/env python3
"""
Reusable builder for the building-explainer-reels skill (references/reel-format.md).

Input: a JSON manifest of scenes. Output: a vertical 720x1280 mp4 (h264 +
AAC 48 kHz stereo) with TTS narration, burned-in subtitles, an original
music bed and loudness normalisation, plus a self-check and contact sheets.

The self-check is NOT the verification gate. Every build still goes to an
independent verifier agent (SKILL.md, "Verification gate").

Usage:
  python3 build_reel.py manifest.json --dry-run      # validate + timings, no render
  python3 build_reel.py manifest.json --out reel.mp4 --workdir work/

Manifest (see examples/sample-manifest.json):
{
  "title": "...", "output": "reel.mp4", "voice": "...", "max_duration": 60,
  "music_bed": true,
  "scenes": [{
    "id": "hook",
    "narration": "A market crash. A made-up meeting.",
    "material": "real",            // REQUIRED: real | ai | recreated | diagram
    "headline": "MARKET CRASH",    // 2-4 words, at most 6; wrapped at 640px
    "yellow_words": ["MARKET"],    // optional; default = first word yellow
    "label": "UNCONFIRMED",        // optional status tag; "label_color":
                                   // red (alleged/disputed/false) | green
                                   // (confirmed/denied) | amber (stated/estimate)
    "disinformation": "CNA Verify",// optional: adds "DISINFORMATION POST -
                                   // flagged by CNA Verify" tag
    "image": "idx.jpg",            // still image
    "keep": [0.2, 0.3, 0.7, 0.85], // the part that makes it relevant, as
                                   // fractions of the image (x0, y0, x1, y1);
                                   // the image zooms as far as this allows
    "image_source": "BILYONARYO • IDX, OCT 2026",
    "clip": "lutfi.mp4", "clip_start": 0.0,
    "clip_mask": [[4, 100, 556, 280]],  // delogo boxes [x, y, w, h] in
                                   // 720x1280 output pixels; x must be > 0
    "card": {...}, "diagram": {...}, "map": {...},   // scene types, below
    "end_card": true,              // with "pointer" and "disclosure", below
    "audio": null,                 // optional pre-made narration; skips TTS
    "shots": [                     // optional: cut the scene into several
      {"image": "a.jpg", "image_source": "...", "headline": "..."},
      {"card": {...}, "weight": 2} // shots sharing its narration; each shot
    ]                              // inherits narration/label/material and
  }]                               // brings its own visual; time is split
}                                  // by "weight" (default 1)

Scene types:
- card: {"outlet", "headline" (at most 10 words), "yellow_words", "faint_body", "key_sentence",
  "image", "keep", "image_source"}. Headline card in the reel's own style; the
  key sentence is highlighted word by word over the first part of the shot,
  then holds. "image" (credited by "image_source") fills the whole frame
  behind the card, centred on "keep", with dark gradients behind the text;
  required when the card opens the reel.
- diagram: {"nodes": [...], "stage": int | "X", "reveal": true,
  "cross_after": 1}. "reveal" shows
  nodes one at a time, continuing from the nodes an earlier shot of the same
  diagram already showed ("from": n overrides); stage "X" shows all nodes,
  then snaps a red X onto the arrow leaving node "cross_after" (default 1,
  the second arrow).
- map: {"land": "ne_10m_land.geojson", "bbox": [lon0, lat0, lon1, lat1],
  "markers": [{"name", "lon", "lat"}], "arrow": [[lon, lat], [lon, lat]]}.
  Drawn from Natural Earth land GeoJSON; the arrow is generic (never a
  pipeline route) and thins over the shot. Labelled schematic.
- timeline: {"events": [{"time": "29 OCT 20:05", "text": "...",
  "source": "TRM LABS"}, ...]}. A vertical line with one dot per event,
  revealed one at a time. About 3 events fit per shot; use "shots" for more.
- end_card: "headline" (e.g. "CHECK BEFORE YOU SHARE"), "pointer":
  {"outlet", "image", "captured"} (a screenshot of a referenced article
  page: outlet name, headline, byline; "captured" is the capture date,
  printed under it when the screenshot has no absolute date). {"outlet", "headline",
  "no_screenshot": "<why>"} is the last-resort fallback; never a fake poster.
  Also
  "disclosure" (one line: AI voice, AI illustrations, sources).

Rules enforced (the spec is SKILL.md; where this docstring disagrees, SKILL.md
wins):
- Motion: tags, headlines over photos, source labels and subtitles never
  move. Each shot's base layer creeps (push in to 102%, or "creep": "up"
  drifts 5px/s; "creep": "none" holds); flat graphics get faint animated
  grain. On top of that: the card highlight sweep, the diagram reveal and X,
  and the thinning map arrow. Real clips get no added zoom; AI clips keep
  their own motion. Graphic wipes, slide-ins, map moves and particle
  overlays from SKILL.md's motion table are not generated here; make them
  as clips and pass them in.
- Stills zoom as far as their "keep" box allows: the keep box always stays
  whole, inside the frame and between the headline and the subtitles, even
  at the end of the creep. A small keep box (a logo, a face) fills the
  screen; a keep box covering the whole image (a screenshot, a chart) shows
  it whole. Space the image leaves is filled with a blurred copy of it,
  tinted with the reel's blue. No keep box means the whole image is kept.
  AI images fill the screen.
- Safe area: tags/headlines start at y=140 (>= 120px from the top);
  subtitle bottom at y=1010 (MarginV 270). The source line sits in small
  muted type between the tags and the headline, never near the subtitles.
- Every scene needs a visual (image, clip, card, diagram, map, timeline) unless it is
  the end card or --allow-plain is passed. "body" paragraphs are dropped
  (no double text).
- A disinformation scene may not open the reel or be the end card.
- Subtitles: 2-5 word chunks per sentence (a clause with no clean split point,
  such as a long spoken number, stays whole); a chunk never ends on an
  article, preposition or conjunction, never splits a name or a number, and
  never crosses a scene. Abbreviations ("p.m.", "U.S.") don't end sentences.
- Audio: silence trimmed per scene, 0.15s tail, original sine-pad bed,
  compression then loudnorm to about -14 LUFS, AAC 192k 48 kHz stereo.
- Every segment is exactly round(dur * 30) frames at 30 fps; concat
  re-encodes (never -c copy across frame rates); overlays are looped with an
  explicit frame count (never a single-frame overlay with -shortest).

Not covered here: generating AI clips (produce them with the platform's
video/image generation and pass them as "clip" or "image" with material
"ai"), and measuring a real clip's caption/logo bands (measure them from a
rendered frame, then set "clip_mask").

Dependencies: ffmpeg + ffprobe on PATH, Pillow, a TTS command (default
/opt/hatch/bin/tts; override with --tts or REEL_TTS), DejaVu fonts (default
/usr/share/fonts/truetype/dejavu; override with REEL_FONT_DIR), and a
Natural Earth land GeoJSON for map scenes
(https://www.naturalearthdata.com/downloads/, e.g. ne_10m_land).
"""

import argparse
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
GREEN = (22, 130, 70)
AMBER = (196, 112, 0)        # statements and estimates; white text stays readable
TAG_COLORS = {"red": RED, "green": GREEN, "amber": AMBER}
LAND = (220, 225, 230)
FAINT = (185, 195, 210)      # faint card body: subdued but readable

SAFE_TOP = 140               # first tag/headline line (>= 120px safe area)
HEADLINE_WRAP = 640          # headlines never run off the right edge
SOURCE_TEXT = (190, 205, 230)  # muted source line, above the headline
KEEP_BOTTOM = 950            # keep boxes stay above the subtitle box (top ~965)
EDGE = 8                     # keep boxes stay this far from the side edges
BLUR_TINT = 0.6              # blurred fill: 60% reel blue over 40% blurred image
FIT_BOTTOM = 1000            # lowest edge for drawn content (maps)
TAIL = 0.15                  # pause after each scene's narration (s)
CREEP_SCALE = 0.02           # slow creep: at most 102% scale over a shot
CREEP_UP_PX = 5              # drift-up creep speed (px per second)
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
MAP_LABEL = "MAP: NATURAL EARTH • SCHEMATIC — NOT TO SCALE"
AI_LABEL = "AI-GENERATED ILLUSTRATION"


def run(cmd, check=True):
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


# --- subtitles ---------------------------------------------------------------

DANGLERS = {"the", "a", "an", "to", "of", "for", "and", "or", "but", "no", "not",
            "its", "their", "his", "her", "this", "that", "about", "than",
            "through", "over", "with", "by", "at", "in", "on", "from", "into",
            "as", "if", "so", "when", "across", "after", "before", "between",
            "because", "while", "since", "around", "under", "until",
            "is", "are", "was", "were", "be"}
SPLIT_BEFORE = {"to", "for", "and", "or", "but", "across", "from", "with", "by",
                "at", "in", "on", "of", "over", "through", "that", "which",
                "who", "after", "before", "because", "while", "since",
                "about", "around", "nearly", "almost",
                # auxiliaries start the predicate: "a compromised laptop / may be involved"
                "may", "might", "can", "could", "will", "would", "should",
                "has", "have", "had", "is", "are", "was", "were"}
NUMBER_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "point", "hundred", "thousand",
                "million", "billion", "trillion", "percent"}


def chunk_words(words):
    """Split a clause into 2-5 word chunks by splitting near the middle,
    recursively. A split never leaves a chunk ending on an article,
    preposition or conjunction (never "rejected the" / "MSCI claim."), never
    falls inside a spoken number ("five point / five"), and never leaves a
    one-word chunk. If no clean split exists the clause stays whole."""
    def bare(w):
        return w.strip(".,;:!?\"'").lower()

    def is_num(w):
        b = bare(w)
        return b in NUMBER_WORDS or b.replace(".", "").replace("$", "").isdigit()

    if len(words) <= 5:
        return [words]
    mid, n = len(words) / 2, len(words)
    # Prefer a split that keeps both parts at 5 words or fewer, then one
    # that starts the new chunk with a preposition or conjunction (a
    # natural phrase break), then the one nearest the middle.
    order = sorted(range(2, n - 1), key=lambda k: (max(k, n - k) > 5,
                                                   bare(words[k]) not in SPLIT_BEFORE,
                                                   abs(k - mid)))
    for k in order:
        if bare(words[k - 1]) in DANGLERS:
            continue
        if is_num(words[k - 1]) and is_num(words[k]):
            continue
        # Keep a run of capitalised words (a name: "North Korea's") together.
        if words[k - 1][:1].isupper() and words[k][:1].isupper():
            continue
        return chunk_words(words[:k]) + chunk_words(words[k:])
    return [words]


ABBREVIATIONS = {"mr.", "mrs.", "ms.", "dr.", "st.", "no.", "vs.", "etc.", "inc.",
                 "co.", "corp.", "jan.", "feb.", "aug.", "sept.", "oct.", "nov.", "dec."}


def split_sentences(text):
    """Sentences, without splitting after abbreviations ("p.m.", "U.S.",
    "Dr.") and with one-word sentences merged into the previous one."""
    sents, cur = [], []
    for w in text.split():
        cur.append(w)
        low = w.lower().rstrip("\"')")
        is_abbr = low in ABBREVIATIONS or re.fullmatch(r"(?:[a-z]\.){2,}", low) is not None
        if low[-1:] in ".!?" and not is_abbr:
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    merged = []
    for sent in sents:
        if merged and (len(sent) < 2 or len(merged[-1]) < 2):
            merged[-1].extend(sent)   # no one-word subtitle, at the start or end
        else:
            merged.append(sent)
    return [" ".join(x) for x in merged]


def chunk_narration(narration):
    """Chunk per clause (split after . ! ? ; : and commas) so no chunk starts
    mid-sentence or crosses a clause; clauses of one word join the next."""
    chunks = []
    for sent in split_sentences(narration):
        clauses, cur = [], []
        for w in sent.split():
            cur.append(w)
            if w[-1] in ",;:" and len(cur) >= 2:
                clauses.append(cur)
                cur = []
        if cur:
            if len(cur) < 2 and clauses:
                clauses[-1].extend(cur)
            else:
                clauses.append(cur)
        for cl in clauses:
            chunks.extend([" ".join(c) for c in chunk_words(cl)])
    return chunks or [""]


def fmt_ass(sec):
    # Round down: a cut at frame time 20.5667s must start the subtitle at
    # 20.56, not 20.57, or the old subtitle stays up one frame into the cut.
    cs = int(sec * 100 + 1e-6)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# --- shared overlay text -----------------------------------------------------

def source_label(scene):
    mat = scene.get("material")
    if mat == "ai":
        return AI_LABEL
    if scene.get("map"):
        return MAP_LABEL
    if scene.get("timeline"):
        return scene.get("image_source") or "TIMELINE · TIMES UTC"
    if mat == "diagram":
        return scene.get("image_source") or DIAGRAM_LABEL
    if mat == "recreated":
        return ""   # cards show their outlet on the card itself
    return scene.get("image_source", "")


def draw_tag(d, y, text, color):
    """Rounded tag pill; wraps to two lines rather than run off the edge."""
    f = font(BOLD, 30)
    lines = wrap(d, text, f, W - 120)
    lh = 40
    tw = max(d.textlength(l, font=f) for l in lines) + 36
    d.rounded_rectangle([40, y, 40 + tw, y + lh * len(lines) + 14], radius=10, fill=color)
    for i, l in enumerate(lines):
        d.text((58, y + 8 + i * lh), l, font=f, fill=WHITE)
    return y + lh * len(lines) + 14 + 14


def draw_headline(d, y, text, yellow_words=None, size=52):
    """Wrapped at 640px; single-word yellow highlights; black stroke so it
    stays readable over busy photos."""
    f = font(BOLD, size)
    lines = []
    for part in text.split("\n"):
        lines.extend(wrap(d, part, f, HEADLINE_WRAP))
    def norm(w):
        return w.strip(".,!?:;\"'()…").upper()
    yellow = {norm(w) for w in yellow_words} if yellow_words else None
    first = True
    for line in lines:
        x = 40
        for w in line.split():
            hit = (norm(w) in yellow) if yellow is not None else first
            d.text((x, y), w, font=f, fill=YELLOW if hit else WHITE,
                   stroke_width=3, stroke_fill=BLACK)
            x += d.textlength(w + " ", font=f)
            first = False
        y += size + 10
    return y


def text_layer(scene, with_source=True):
    """Transparent RGBA layer: tags, source line, headline. Returns
    (layer, y_after_text). Used unchanged for every frame of a shot.

    The source line sits in small muted type between the tags and the
    headline, like an outlet name on a card, and far from the subtitles,
    so it never reads as a second caption."""
    from PIL import Image, ImageDraw
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    y = SAFE_TOP
    if scene.get("label"):
        col = TAG_COLORS.get(scene.get("label_color", "red"), RED)
        y = draw_tag(d, y, scene["label"], col)
    if scene.get("disinformation"):
        y = draw_tag(d, y, f"DISINFORMATION POST — flagged by {scene['disinformation']}", RED)
    src = source_label(scene) if with_source else ""
    if src:
        f = font(MONO_BOLD, 18)
        for line in wrap(d, src, f, HEADLINE_WRAP):
            d.text((40, y), line, font=f, fill=SOURCE_TEXT,
                   stroke_width=2, stroke_fill=(0, 0, 0, 160))
            y += 26
        y += 8
    if scene.get("headline"):
        y = draw_headline(d, y, scene["headline"], scene.get("yellow_words"))
    return ov, y


def compose(base, layer):
    out = base.convert("RGBA")
    out.alpha_composite(layer)
    return out.convert("RGB")


# --- scene renderers: each returns [(base, overlay_or_None, start), ...] ----

def keep_layout(iw, ih, keep, band_top, band_bottom):
    """Zoom as far as the keep box allows (see SKILL.md, Layout).

    keep: (x0, y0, x1, y1) as fractions of the image: the part that makes
    the image relevant. Returns (scale, x_off, y_off, mode). The keep box
    stays inside the frame horizontally and inside the band between the
    headline and the subtitles vertically, even at the end of the creep
    (which scales the frame by 1 + CREEP_SCALE about its centre). The image
    zooms in up to filling the screen; it is never shown smaller than
    whole-image-fits-the-band."""
    c, cx, cy = 1 + CREEP_SCALE, W / 2, H / 2
    sx0, sx1 = cx - (cx - EDGE) / c, cx + (cx - EDGE) / c
    sy0, sy1 = cy + (band_top - cy) / c, cy + (band_bottom - cy) / c
    kx0, ky0, kx1, ky1 = [v * d for v, d in zip(keep, (iw, ih, iw, ih))]
    s_cover = max(W / iw, H / ih)
    s_whole = min((sx1 - sx0) / iw, (sy1 - sy0) / ih)
    # A zero-area keep box (an AI image with no keep) means: fill the screen.
    s = min(s_cover, (sx1 - sx0) / max(kx1 - kx0, 1e-9), (sy1 - sy0) / max(ky1 - ky0, 1e-9))
    s = max(s, s_whole)

    def place(img_len, frame_len, k0, k1, safe0, safe1):
        # Offsets that keep the keep box inside [safe0, safe1], and offsets
        # that make the image cover the whole frame.
        lo_k, hi_k = safe0 - s * k0, safe1 - s * k1
        lo_f, hi_f = frame_len - s * img_len, 0.0
        centre = (safe0 + safe1) / 2 - s * (k0 + k1) / 2
        lo, hi = max(lo_k, lo_f), min(hi_k, hi_f)
        if lo <= hi:                       # can fill and keep: prefer centred keep
            return min(max(centre, lo), hi)
        return min(max(centre, lo_k), hi_k)  # keep wins over filling

    x = place(iw, W, kx0, kx1, sx0, sx1)
    y = place(ih, H, ky0, ky1, sy0, sy1)
    # If the whole image fits in the band at this scale, keep all of it in
    # the band: parts outside the keep box shouldn't sit under the headline
    # or the subtitles when nothing is gained by it.
    if s * ih <= (sy1 - sy0) + 1:
        y = (sy0 + sy1) / 2 - s * ih / 2
    if s * iw <= (sx1 - sx0) + 1:
        x = (sx0 + sx1) / 2 - s * iw / 2
    full = x <= 0 and y <= 0 and x + s * iw >= W and y + s * ih >= H
    mode = "full-bleed" if full else ("whole" if s <= s_whole + 1e-6 else "zoomed")
    return s, x, y, mode


def render_still(scene, warnings):
    from PIL import Image, ImageFilter
    pic = Image.open(scene["image"]).convert("RGB")
    layer, text_bottom = text_layer(scene)
    if scene.get("material") == "ai" or scene.get("full_bleed"):
        keep = scene.get("keep", (0.5, 0.5, 0.5, 0.5))   # AI art: fill the screen
    else:
        keep = scene.get("keep")
        if not keep:
            keep = (0, 0, 1, 1)
            warnings.append(f"scene {scene.get('id')}: no 'keep' box, so the whole image is "
                            "shown; add one to let it zoom (see SKILL.md, Layout).")
    s, x, y, mode = keep_layout(pic.width, pic.height, keep, text_bottom + 16, KEEP_BOTTOM)
    scene["_mode"] = mode
    if mode == "full-bleed":
        base = Image.new("RGB", (W, H), BG)
    else:
        # Blurred copy of the image, tinted with the reel's blue, fills the
        # space the image leaves, so the background stays one colour family.
        blur = cover_crop(pic, W, H).filter(ImageFilter.GaussianBlur(36))
        base = Image.blend(blur, Image.new("RGB", (W, H), BG), BLUR_TINT)
    scaled = pic.resize((max(1, round(pic.width * s)), max(1, round(pic.height * s))),
                        Image.LANCZOS)
    base.paste(scaled, (round(x), round(y)))
    # Dark gradients top and bottom keep the tags, headline and subtitles
    # readable over whatever sits behind them.
    grad = Image.new("L", (1, H))
    for yy in range(H):
        if yy < 420:
            grad.putpixel((0, yy), int(150 * (1 - yy / 420)))
        elif yy > H - 360:
            grad.putpixel((0, yy), int(150 * ((yy - (H - 360)) / 360)))
    base.paste(Image.new("RGB", (W, H), BLACK), (0, 0), grad.resize((W, H)))
    return [(base, layer, 0.0)]


def render_card(scene, dur):
    from PIL import Image, ImageDraw
    card = scene["card"]
    # The tag stays locked; the card content below it creeps with the shot.
    tag_layer, top = text_layer({k: scene[k] for k in ("label", "label_color", "disinformation")
                                 if k in scene}, with_source=False)

    def full_bleed_picture():
        """The card's image cover-cropped to the full frame, centred on its
        keep box so the relevant part stays in view."""
        pic = Image.open(card["image"]).convert("RGB")
        iw, ih = pic.size
        k = card.get("keep", (0, 0, 1, 1))
        s = max(W / iw, H / ih)
        cx = min(max((k[0] + k[2]) / 2 * iw * s, W / 2), iw * s - W / 2)
        cy = min(max((k[1] + k[3]) / 2 * ih * s, H / 2), ih * s - H / 2)
        pic = pic.resize((max(W, round(iw * s)), max(H, round(ih * s))), Image.LANCZOS)
        return pic.crop((round(cx - W / 2), round(cy - H / 2),
                         round(cx - W / 2) + W, round(cy - H / 2) + H))

    def scrim(head_end, block_top):
        """Dark gradients behind the top text and the bottom text, leaving the
        middle of the picture clear."""
        grad = Image.new("L", (1, H))
        for yy in range(H):
            top_a = 185 if yy <= head_end else max(0, 185 * (1 - (yy - head_end) / 110))
            bot_a = 205 if yy >= block_top else max(0, 205 * (1 - (block_top - yy) / 150))
            grad.putpixel((0, yy), int(max(top_a, bot_a)))
        return grad.resize((W, H))

    cache = {}

    def frame(n_lit):
        f_out = font(MONO_BOLD, 26)
        f2, f3 = font(REG, 26), font(BOLD, 34)
        body = card.get("faint_body", "")
        if card.get("image"):
            # Full-frame picture card: outlet and headline at the top, the
            # line-and-dot, body and key sentence anchored above the subtitles,
            # dark gradients behind both so every line stays readable.
            probe = ImageDraw.Draw(Image.new("RGB", (W, H)))
            key_lines = wrap(probe, card.get("key_sentence", ""), f3, 580)
            body_lines = wrap(probe, body, f2, 560)
            key_top = KEEP_BOTTOM - (len(key_lines) * 46 + 24)
            body_top = key_top - 30 - len(body_lines) * 36
            dot_top = body_top - 70
            if "base" not in cache:
                im = full_bleed_picture()
                d = ImageDraw.Draw(im)
                y = top + 34 * len(wrap(d, card["outlet"], f_out, HEADLINE_WRAP))
                head_end = draw_headline(ImageDraw.Draw(Image.new("RGB", (W, H))), y + 12,
                                         card["headline"], card.get("yellow_words"))
                im.paste(Image.new("RGB", (W, H), BLACK), (0, 0), scrim(head_end + 50, dot_top - 10))
                cache["base"] = im
            im = cache["base"].copy()
            d = ImageDraw.Draw(im)
            y = top
            for line in wrap(d, card["outlet"], f_out, HEADLINE_WRAP):
                d.text((40, y), line, font=f_out, fill=(200, 210, 230))
                y += 34
            y = draw_headline(d, y + 12, card["headline"], card.get("yellow_words"))
            if card.get("image_source"):
                d.text((40, y + 10), card["image_source"], font=font(REG, 18), fill=SOURCE_TEXT)
            d.line([(70, dot_top + 6), (70, dot_top + 40)], fill=YELLOW, width=4)
            d.ellipse([58, dot_top + 40, 82, dot_top + 64], fill=YELLOW)
            y = body_top
        else:
            im = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(im)
            y = top
            for line in wrap(d, card["outlet"], f_out, HEADLINE_WRAP):
                d.text((40, y), line, font=f_out, fill=(170, 185, 210))
                y += 34
            y = draw_headline(d, y + 12, card["headline"], card.get("yellow_words"))
            d.line([(70, y + 20), (70, y + 140)], fill=YELLOW, width=4)
            d.ellipse([58, y + 140, 82, y + 164], fill=YELLOW)
            y += 190
        for line in wrap(d, body, f2, 560):
            d.text((110, y), line, font=f2, fill=FAINT)
            y += 36
        y += 30
        lines = wrap(d, card.get("key_sentence", ""), f3, 580)
        d.rectangle([40, y, 680, y + len(lines) * 46 + 24], fill=PANEL)
        yy, k = y + 12, 0
        for line in lines:
            x = 60
            for w in line.split():
                ww = d.textlength(w, font=f3)
                lit = k < n_lit
                if lit:
                    d.rectangle([x - 4, yy - 2, x + ww + 4, yy + 42], fill=YELLOW)
                d.text((x, yy), w, font=f3, fill=BLACK if lit else WHITE)
                x += d.textlength(w + " ", font=f3)
                k += 1
            yy += 46
        return im

    n = len(card.get("key_sentence", "").split())
    # Sweep at ~0.25s per word but finish within 60% of the shot, then hold.
    step = min(0.25, 0.6 * dur / max(n, 1))
    return [(frame(i), tag_layer, i * step) for i in range(n + 1)]


def render_diagram(scene, dur):
    from PIL import Image, ImageDraw
    nodes = scene["diagram"]["nodes"]
    stage = scene["diagram"].get("stage", len(nodes))
    reveal = scene["diagram"].get("reveal", False)
    # Index of the node whose outgoing arrow gets the denial X; default is
    # the second arrow (e.g. SINGAPORE / GIC / TEMASEK -> MSCI).
    cross_at = scene["diagram"].get("cross_after", 1 if len(nodes) > 2 else 0)

    def frame(count, cross):
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        y = 380
        for i, name in enumerate(nodes[:count]):
            f = font(BOLD, 34)
            tw = d.textlength(name, font=f)
            x = (W - tw) / 2 - 18
            d.rounded_rectangle([x, y, x + tw + 36, y + 64], radius=10,
                                fill=YELLOW if i == 0 else WHITE)
            d.text((x + 18, y + 14), name, font=f, fill=BLACK)
            if i < count - 1:
                d.line([(W // 2, y + 64), (W // 2, y + 140)], fill=YELLOW, width=5)
                d.polygon([(W // 2 - 12, y + 124), (W // 2 + 12, y + 124),
                           (W // 2, y + 140)], fill=YELLOW)
            y += 140
        if cross:
            cx, cy = W // 2, 380 + cross_at * 140 + 64 + 38   # mid-arrow
            d.line([(cx - 40, cy - 40), (cx + 40, cy + 40)], fill=RED, width=10)
            d.line([(cx - 40, cy + 40), (cx + 40, cy - 40)], fill=RED, width=10)
        return im

    layer = text_layer(scene)[0]
    if stage == "X":
        return [(frame(len(nodes), False), layer, 0.0),
                (frame(len(nodes), True), layer, 0.4 * dur)]
    count = int(stage)
    # Nodes already on screen from an earlier shot of this diagram stay put;
    # the reveal continues from there instead of rebuilding from node 1.
    shown = min(scene["diagram"].get("from", scene.get("_diagram_shown", 0)), count)
    if reveal and count > max(shown, 1):
        times = node_times(scene, nodes[:count], dur)
        start = max(shown, 1)
        return [(frame(start, False), layer, 0.0)] + \
               [(frame(i, False), layer, times[i - 1]) for i in range(start + 1, count + 1)]
    return [(frame(count, False), layer, 0.0)]


def node_times(scene, nodes, dur):
    """When each node appears, in shot time. A node appears when its first
    word is spoken, estimated the same way the subtitles are timed (word
    position over the scene's duration). Nodes not named in the narration
    fall back to even spacing over the first 70% of the shot."""
    def norm(w):
        return re.sub(r"[^a-z0-9]", "", w.lower())
    words = [norm(w) for w in scene.get("narration", "").split()]
    scene_dur = scene.get("_scene_dur", dur)
    offset = scene.get("_shot_start", 0.0)
    latest = max(0.0, dur - 0.5)
    times = []
    for k, node in enumerate(nodes):
        first = norm(node.split()[0])
        hit = next((n for n, w in enumerate(words) if first and w.startswith(first)), None)
        if k == 0:
            times.append(0.0)
        elif hit is not None and words:
            times.append(min(max(hit / len(words) * scene_dur - offset, 0.0), latest))
        else:
            times.append(None)     # not named: placed between its neighbours below
    # Nodes the narration never names go evenly between the named ones
    # around them (or toward 70% of the shot at the end).
    k = 1
    while k < len(times):
        if times[k] is None:
            j = k
            while j < len(times) and times[j] is None:
                j += 1
            t0 = times[k - 1]
            t1 = times[j] if j < len(times) else min(latest, max(0.7 * dur, t0 + 0.6 * (j - k)))
            for n in range(k, j):
                times[n] = t0 + (t1 - t0) * (n - k + 1) / (j - k + 1)
            k = j
        k += 1
    # Keep nodes in order even if the narration names them out of order.
    for k in range(1, len(times)):
        times[k] = max(times[k], times[k - 1] + 1 / FPS)
    return times


def load_land(path, bbox):
    """Polygons (lists of (lon, lat) rings) from a GeoJSON file, keeping only
    those whose extent overlaps bbox (ne_10m_land is large)."""
    lon0, lat0, lon1, lat1 = bbox
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)
    feats = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
    rings = []
    for ft in feats:
        g = ft.get("geometry", ft)
        polys = [g["coordinates"]] if g["type"] == "Polygon" else \
            g["coordinates"] if g["type"] == "MultiPolygon" else []
        for poly in polys:
            ring = poly[0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            if max(xs) < lon0 or min(xs) > lon1 or max(ys) < lat0 or min(ys) > lat1:
                continue
            rings.append(ring)
    return rings


def render_map(scene, dur):
    import math
    from PIL import Image, ImageDraw
    m = scene["map"]
    lon0, lat0, lon1, lat1 = m["bbox"]
    # Equirectangular, longitudes scaled by cos(mid-latitude), fitted into
    # the area between the headline and the subtitles.
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    layer, text_bottom = text_layer(scene)
    area_x, area_y, area_w = 0, text_bottom + 20, W
    area_h = FIT_BOTTOM - area_y
    s = min(area_w / ((lon1 - lon0) * kx), area_h / (lat1 - lat0))
    ox = area_x + (area_w - (lon1 - lon0) * kx * s) / 2
    oy = area_y + (area_h - (lat1 - lat0) * s) / 2

    def xy(lon, lat):
        return (ox + (lon - lon0) * kx * s, oy + (lat1 - lat) * s)

    # Draw the land on its own layer, then keep only the map rectangle, so
    # large polygons (whole continents) never spill under the headline or
    # into the subtitle area.
    land = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(land)
    for ring in load_land(m["land"], m["bbox"]):
        d.polygon([xy(p[0], p[1]) for p in ring], fill=LAND)
    box = (max(0, int(ox)), max(0, int(oy)),
           min(W, int(ox + (lon1 - lon0) * kx * s)), min(H, int(oy + (lat1 - lat0) * s)))
    base = Image.new("RGB", (W, H), BG)
    base.paste(land.crop(box), box[:2])

    def frame(width):
        im = base.copy()
        dd = ImageDraw.Draw(im)
        if m.get("arrow") and width:
            (a0, b0), (a1, b1) = m["arrow"]
            p0, p1 = xy(a0, b0), xy(a1, b1)
            dd.line([p0, p1], fill=YELLOW, width=width)
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            hl = 10 + 2 * width
            dd.polygon([p1, (p1[0] - hl * math.cos(ang - 0.45), p1[1] - hl * math.sin(ang - 0.45)),
                        (p1[0] - hl * math.cos(ang + 0.45), p1[1] - hl * math.sin(ang + 0.45))],
                       fill=YELLOW)
        f = font(BOLD, 26)
        for mk in m.get("markers", []):
            x, y = xy(mk["lon"], mk["lat"])
            dd.ellipse([x - 9, y - 9, x + 9, y + 9], fill=YELLOW, outline=BLACK, width=2)
            # Label offset right of the dot so it never covers the marker.
            dd.text((x + 16, y - 14), mk["name"], font=f, fill=WHITE,
                    stroke_width=3, stroke_fill=BLACK)
        return im

    # The flow arrow thins over the shot (supply reduced), then holds.
    return [(frame(10), layer, 0.0), (frame(6), layer, 0.4 * dur), (frame(3), layer, 0.7 * dur)]


def render_timeline(scene, dur):
    """Vertical timeline: a line with one dot per event; each event shows
    its time, what happened, and its source. Events appear one at a time
    over the first 75% of the shot, then hold. Fits about 3 events per shot;
    split a longer timeline into shots."""
    from PIL import Image, ImageDraw
    events = scene["timeline"]["events"]
    layer, top = text_layer(scene)
    f_time, f_text, f_src = font(MONO_BOLD, 24), font(BOLD, 30), font(MONO_BOLD, 18)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    blocks, y = [], top + 30
    for ev in events:
        lines = wrap(probe, ev["text"], f_text, 590)
        h = 34 + len(lines) * 38 + 30 + 36
        blocks.append((y, lines, ev))
        y += h
    if y > KEEP_BOTTOM:
        raise ValueError(f"scene {scene.get('id')}: timeline runs to y={y}, past the "
                         f"subtitle area ({KEEP_BOTTOM}); split it into more shots.")
    # Spread the events over the free space above the subtitles (up to 90px
    # extra between events), so the frame doesn't end in an empty half.
    extra = min(90, (KEEP_BOTTOM - 40 - y) / max(len(events) - 1, 1))
    blocks = [(by + k * extra, lines, ev) for k, (by, lines, ev) in enumerate(blocks)]

    def frame(n):
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        if n:
            last_y = blocks[n - 1][0] + 12
            d.line([(58, blocks[0][0] + 12), (58, last_y)], fill=YELLOW, width=4)
        for k, (by, lines, ev) in enumerate(blocks[:n]):
            d.ellipse([47, by + 1, 69, by + 23], fill=YELLOW, outline=BLACK, width=2)
            d.text((90, by), ev["time"], font=f_time, fill=YELLOW)
            yy = by + 34
            for line in lines:
                d.text((90, yy), line, font=f_text, fill=WHITE)
                yy += 38
            d.text((90, yy + 4), ev.get("source", ""), font=f_src, fill=SOURCE_TEXT)
        return im

    step = 0.75 * dur / max(len(events), 1)
    return [(frame(k), layer, (k - 1) * step) for k in range(1, len(events) + 1)]


def render_end_card(scene, warnings):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    y = draw_headline(d, SAFE_TOP, scene.get("headline", "CHECK BEFORE YOU SHARE"),
                      scene.get("yellow_words"))
    p = scene.get("pointer")
    if p and p.get("image"):
        # A screenshot of the article itself (headline and byline), shown
        # whole within 640x420 (never upscaled), with a thin white frame.
        y += 40
        raw = Image.open(p["image"]).convert("RGBA")
        shot_img = Image.new("RGB", raw.size, WHITE)       # transparent areas go white, not black
        shot_img.paste(raw, (0, 0), raw)
        shot_img.thumbnail((640, 420), Image.LANCZOS)
        if shot_img.width < 480 and shot_img.height < 420:
            warnings.append(f"scene {scene.get('id')}: end-card screenshot is only "
                            f"{shot_img.width}x{shot_img.height}px on screen; recapture it larger "
                            "(about 1000px wide) so its text is readable.")
        x0 = (W - shot_img.width) // 2
        d.rectangle([x0 - 4, y - 4, x0 + shot_img.width + 3, y + shot_img.height + 3], fill=WHITE)
        im.paste(shot_img, (x0, y))
        y += shot_img.height + 12
        if p.get("captured"):
            # Stands in for a relative time ("13 hours ago") cropped out at capture.
            d.text((x0, y), f"CAPTURED {p['captured']}", font=font(REG, 18), fill=SOURCE_TEXT)
            y += 26
        y += 16
        d.text((40, y), f"READ THE FULL STORY — {p['outlet']}", font=font(BOLD, 26), fill=YELLOW)
        y += 40
    elif p:
        y += 40
        f_out, f_head = font(MONO_BOLD, 22), font(BOLD, 38)
        lines = wrap(d, p["headline"], f_head, 600)
        h = 60 + len(lines) * 46 + 50
        d.rectangle([40, y, 680, y + h], fill=PANEL)
        d.text((64, y + 20), p["outlet"], font=f_out, fill=(170, 185, 210))
        yy = y + 56
        for line in lines:
            d.text((64, yy), line, font=f_head, fill=WHITE)
            yy += 46
        y += h + 24
        d.text((40, y), f"READ THE FULL STORY — {p['outlet']}", font=font(BOLD, 26), fill=YELLOW)
        y += 40
    if scene.get("disclosure"):
        # Small and muted, directly under the pointer: well clear of the
        # subtitle box, so it never reads as part of the caption.
        f = font(REG, 17)
        yy = y + 30
        for line in wrap(d, scene["disclosure"], f, 640):
            d.text((40, yy), line, font=f, fill=SOURCE_TEXT)
            yy += 24
        y = yy
    if y > KEEP_BOTTOM:
        warnings.append(f"scene {scene.get('id')}: end card runs to y={y}, into the subtitle "
                        f"area (below {KEEP_BOTTOM}); shorten the disclosure or the closing line.")
    return [(im, None, 0.0)]


def render_plain(scene):
    from PIL import Image
    return [(Image.new("RGB", (W, H), BG), text_layer(scene)[0], 0.0)]


def stages_to_video(stages, dur, work, name, creep="in", grain=False):
    """Render a shot frame by frame and pipe it to ffmpeg (exact frame count).

    stages: [(base, overlay_or_None, start_seconds), ...]. The base layer
    creeps (sub-pixel, so no jitter); the overlay (tags, headlines, source
    label) is composited on top unmoved. creep: "in" = push in to 102% over
    the shot; "up" = drift up CREEP_UP_PX per second; "none" = static.
    grain: faint animated grain, for flat graphic backgrounds only."""
    from PIL import Image
    total = frames_for(dur)
    out = os.path.join(work, f"{name}.mp4")
    noise = [Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).convert("RGB")
             for _ in range(GRAIN_FRAMES)] if grain else []
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-frames:v", str(total), "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    k = 0
    for f in range(total):
        t = f / FPS
        while k + 1 < len(stages) and t >= stages[k + 1][2]:
            k += 1
        base, layer, _ = stages[k]
        frac = f / max(total - 1, 1)
        if creep == "in":
            # Inverse affine map: scale about the frame centre.
            a = 1 / (1 + CREEP_SCALE * frac)
            img = base.transform((W, H), Image.AFFINE,
                                 (a, 0, W / 2 * (1 - a), 0, a, H / 2 * (1 - a)),
                                 resample=Image.BICUBIC)
        elif creep == "up":
            # Drift up, zoomed just enough that the drift never exposes a
            # blank strip at the bottom.
            a = 1 / (1 + CREEP_UP_PX * dur / H)
            img = base.transform((W, H), Image.AFFINE,
                                 (a, 0, W / 2 * (1 - a), 0, a, CREEP_UP_PX * t * a),
                                 resample=Image.BICUBIC)
        else:
            img = base
        if noise:
            img = Image.blend(img, noise[f % len(noise)], GRAIN_ALPHA)
        if layer is not None:
            img = compose(img, layer)
        try:
            p.stdin.write(img.tobytes())
        except BrokenPipeError:
            break                     # ffmpeg died; its error is reported below
    try:
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode(errors="replace")
    if p.wait() != 0:
        raise RuntimeError(f"Rendering {name} failed:\n{err[-2000:]}")
    return out


def clip_to_video(scene, dur, work, name):
    """Native vertical clip, cover-scaled to 720x1280 with no added zoom;
    caption/logo bands masked with delogo; text layer looped on top."""
    layer, _ = text_layer(scene)
    png = os.path.join(work, f"{name}_text.png")
    layer.save(png)
    # tpad holds the last frame if the clip is shorter than the shot, so the
    # segment always has exactly frames_for(dur) frames.
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
          f"fps={FPS},tpad=stop_mode=clone:stop_duration={dur:.3f}")
    for x, y, w, h in scene.get("clip_mask", []):
        vf += f",delogo=x={x}:y={y}:w={w}:h={h}"
    out = os.path.join(work, f"{name}.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(scene.get("clip_start", 0)),
         "-i", scene["clip"], "-loop", "1", "-i", png,
         "-filter_complex", f"[0:v]{vf}[c];[c][1:v]overlay=0:0,format=yuv420p",
         "-an", "-frames:v", str(frames_for(dur)), "-c:v", "libx264", out])
    return out


# Keys that belong to one visual. A shot never inherits these from its scene;
# headline and yellow_words do inherit, so shots can share the scene headline.
VISUAL_KEYS = ("image", "fit_image", "clip", "card", "diagram", "map", "end_card",
               "timeline", "keep",
               "image_source", "full_bleed", "clip_mask",
               "clip_start")


def expand_shots(scene):
    """A scene's shots: each "shots" entry inherits the scene's non-visual
    keys (narration, label, material...) and supplies its own visual."""
    if not scene.get("shots"):
        return [dict(scene)]
    base = {k: v for k, v in scene.items() if k not in VISUAL_KEYS + ("shots",)}
    return [{**base, **sh} for sh in scene["shots"]]


def render_shot(sh, dur, work, name, warnings):
    if sh.get("clip"):
        return clip_to_video(sh, dur, work, name)
    if sh.get("card"):
        stages = render_card(sh, dur)
    elif sh.get("diagram"):
        stages = render_diagram(sh, dur)
    elif sh.get("map"):
        stages = render_map(sh, dur)
    elif sh.get("timeline"):
        stages = render_timeline(sh, dur)
    elif sh.get("end_card"):
        stages = render_end_card(sh, warnings)
    elif sh.get("image"):
        stages = render_still(sh, warnings)
    else:
        stages = render_plain(sh)
    # Every shot creeps unless the manifest says otherwise.
    # Grain only on flat graphics, never on real images.
    return stages_to_video(stages, dur, work, name, creep=sh.get("creep", "in"),
                           grain=not sh.get("image"))


# --- validation --------------------------------------------------------------

def image_problem(path):
    """Why an image asset is unusable, or None. Catches downloads a CDN served
    as AVIF/WebP under a .png name that this Pillow can't read, and screenshots
    taken before lazy images loaded (a flat grey or white box)."""
    from PIL import Image, ImageStat
    try:
        with Image.open(path) as im:
            im.load()
            gray = im.convert("L")
    except Exception as e:
        return (f"cannot be read ({type(e).__name__}). Re-download as JPEG or PNG "
                "(send 'Accept: image/jpeg', or use f_jpg instead of f_auto).")
    if ImageStat.Stat(gray).stddev[0] < 4:
        return ("is almost blank (one flat colour). Likely captured before its images "
                "loaded; scroll them into view, wait for them to load, and recapture.")
    return None


def validate(scenes, args):
    errors, warnings = [], []
    units = [(i, j, scene, s) for i, scene in enumerate(scenes)
             for j, s in enumerate(expand_shots(scene))]
    for i, j, scene, s in units:
        sid = scene.get("id", f"#{i}") + (f" shot {j + 1}" if scene.get("shots") else "")
        if s.get("material") not in MATERIALS:
            errors.append(f"scene {sid}: 'material' must be one of {sorted(MATERIALS)}, "
                          f"got {s.get('material')!r}.")
        for legacy in ("punch", "layout", "clip_crop_bottom", "background"):
            if legacy in s:
                warnings.append(f"scene {sid}: '{legacy}' is no longer used and is ignored "
                                "(stills zoom to their 'keep' box; mask clip captions with "
                                "'clip_mask'; one background colour for every shot).")
        if s.get("body"):
            warnings.append(f"scene {sid}: 'body' dropped (no double text); keep it in narration.")
        has_visual = any(s.get(k) for k in ("image", "clip", "card", "diagram", "map",
                                            "timeline"))
        if not has_visual and not s.get("end_card") and not args.allow_plain:
            errors.append(f"scene {sid}: no image, clip, card, diagram, map or timeline. Add one, or "
                          "pass --allow-plain and justify it in the delivery notes.")
        for key in ("image", "clip", "audio"):
            if s.get(key) and not os.path.exists(s[key]):
                errors.append(f"scene {sid}: {key} file not found: {s[key]}")
        p = s.get("pointer") if isinstance(s.get("pointer"), dict) else {}
        for path in (s.get("image"), p.get("image"), (s.get("card") or {}).get("image")):
            if path and os.path.exists(path):
                problem = image_problem(path)
                if problem:
                    errors.append(f"scene {sid}: {path}: {problem}")
        if "weight" in s and not (isinstance(s["weight"], (int, float)) and s["weight"] > 0):
            errors.append(f"scene {sid}: shot 'weight' must be a number above 0, got {s['weight']!r}.")
        if s.get("timeline") is not None and not s["timeline"].get("events"):
            errors.append(f"scene {sid}: timeline needs at least one event.")
        for ev in (s.get("timeline") or {}).get("events", []):
            if not ev.get("time") or not ev.get("text"):
                errors.append(f"scene {sid}: every timeline event needs 'time' and 'text'.")
        if s.get("headline") and len(s["headline"].split()) > 6:
            errors.append(f"scene {sid}: headline has {len(s['headline'].split())} words; "
                          "the limit is 6 per shot (aim for 2-4).")
        if s.get("card") and not all(s["card"].get(k) for k in ("outlet", "headline")):
            errors.append(f"scene {sid}: card needs 'outlet' and 'headline'.")
        elif s.get("card") and len(s["card"]["headline"].replace("…", " ").split()) > 10:
            errors.append(f"scene {sid}: card headline has "
                          f"{len(s['card']['headline'].replace('…', ' ').split())} words; the limit "
                          "is 10. Trim it to a verbatim excerpt, marking cut words with an ellipsis.")
        card_img = (s.get("card") or {}).get("image")
        if card_img and not os.path.exists(card_img):
            errors.append(f"scene {sid}: card image not found: {card_img}")
        elif card_img and not s["card"].get("image_source"):
            errors.append(f"scene {sid}: card image needs 'image_source' (e.g. 'IMAGE: CNA, 29 OCT 2026').")
        if s.get("card") and i == 0 and j == 0 and not card_img:
            errors.append(f"scene {sid}: a headline card that opens the reel needs a representative "
                          "'image' on the card (see SKILL.md, Headline cards).")
        if s.get("diagram") and not s["diagram"].get("nodes"):
            errors.append(f"scene {sid}: diagram needs 'nodes'.")
        p = s.get("pointer")
        if p is not None and not (isinstance(p, dict) and p.get("outlet")
                                  and (p.get("headline") or p.get("image"))):
            errors.append(f"scene {sid}: pointer needs 'outlet' and either 'headline' or 'image'.")
        elif isinstance(p, dict) and not p.get("image") and not p.get("no_screenshot"):
            errors.append(f"scene {sid}: end-card pointer needs 'image', a screenshot of a referenced "
                          "article page. A headline-only pointer needs 'no_screenshot' giving why "
                          "no referenced article could be captured.")
        if "keep" in s:
            k = s["keep"]
            if not (isinstance(k, list) and len(k) == 4 and all(0 <= v <= 1 for v in k)
                    and k[0] < k[2] and k[1] < k[3]):
                errors.append(f"scene {sid}: 'keep' must be [x0, y0, x1, y1] as fractions "
                              f"of the image with x0 < x1 and y0 < y1, got {k!r}.")
        if s.get("material") == "real" and (s.get("image") or s.get("clip")) \
                and not s.get("image_source"):
            errors.append(f"scene {sid}: real material needs 'image_source' "
                          "(outlet + date, or account + date).")
        for box in s.get("clip_mask", []):
            x, y, w, h = box
            if x <= 0 or y <= 0 or x + w >= W or y + h >= H:
                errors.append(f"scene {sid}: clip_mask {box} must sit strictly inside "
                              f"{W}x{H} (delogo fails at x=0 or on the frame edge).")
        if s.get("disinformation") and ((i == 0 and j == 0) or s.get("end_card")):
            errors.append(f"scene {sid}: disinformation material may not open the reel "
                          "or appear on the end card.")
        if s.get("map"):
            m = s["map"]
            if not isinstance(m, dict) or "land" not in m or "bbox" not in m:
                errors.append(f"scene {sid}: 'map' needs {{'land': <Natural Earth GeoJSON>, "
                              "'bbox': [lon0, lat0, lon1, lat1]}; schematic blob maps are "
                              "no longer drawn.")
            elif not os.path.exists(m["land"]):
                errors.append(f"scene {sid}: map land file not found: {m['land']}")
        if s.get("end_card") and i != len(scenes) - 1:
            warnings.append(f"scene {sid}: end card is not the last scene.")
        if isinstance(s.get("pointer"), dict) and s["pointer"].get("image")                 and not os.path.exists(s["pointer"]["image"]):
            errors.append(f"scene {sid}: pointer image not found: {s['pointer']['image']}")
        if s.get("end_card") and not s.get("disclosure"):
            warnings.append(f"scene {sid}: end card has no disclosure line.")
    maps = [s for s in scenes if s.get("map")]
    if len(maps) > 1:
        warnings.append("more than one map scene; the spec shows the map once.")
    return errors, warnings


def check_tools(scenes, tts):
    missing = []
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            missing.append(f"{tool} not found on PATH.")
    if any(not s.get("audio") for s in scenes) and not (os.path.exists(tts) or shutil.which(tts)):
        missing.append(f"TTS command not found: {tts}. Pass --tts, set REEL_TTS, "
                       "or give every scene a pre-made 'audio' file.")
    for f in (BOLD, REG, MONO_BOLD, MONO):
        if not os.path.exists(f):
            missing.append(f"Font not found: {f}. Set REEL_FONT_DIR to a folder with DejaVu fonts.")
    return missing


# --- main --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Build an investigative explainer reel.")
    ap.add_argument("manifest")
    ap.add_argument("--out", default=None)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--tts", default=TTS_DEFAULT)
    ap.add_argument("--max-duration", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-plain", action="store_true")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        man = json.load(f)
    scenes = man.get("scenes") or []
    if not scenes:
        sys.exit("Manifest has no scenes.")
    base_dir = os.path.dirname(os.path.abspath(args.manifest))
    for s in [x for sc in scenes for x in [sc] + sc.get("shots", [])]:
        # Resolve asset paths relative to the manifest (scenes and shots).
        if s.get("fit_image") and not s.get("image"):
            s["image"] = s["fit_image"]   # legacy key; fit is now the default
        if isinstance(s.get("card"), dict) and s["card"].get("image")                 and not os.path.isabs(s["card"]["image"]):
            s["card"]["image"] = os.path.join(base_dir, s["card"]["image"])
        for key in ("image", "clip", "audio"):
            if s.get(key) and not os.path.isabs(s[key]):
                s[key] = os.path.join(base_dir, s[key])
        if isinstance(s.get("map"), dict) and s["map"].get("land") \
                and not os.path.isabs(s["map"]["land"]):
            s["map"]["land"] = os.path.join(base_dir, s["map"]["land"])
        if isinstance(s.get("pointer"), dict) and s["pointer"].get("image") \
                and not os.path.isabs(s["pointer"]["image"]):
            s["pointer"]["image"] = os.path.join(base_dir, s["pointer"]["image"])

    errors, warnings = validate(scenes, args)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(f"{len(errors)} manifest error(s); nothing built.")
    if not args.dry_run:
        missing = check_tools(scenes, args.tts)
        if missing:
            sys.exit("Missing dependencies:\n  " + "\n  ".join(missing))

    max_dur = args.max_duration or man.get("max_duration", 60)
    out = args.out or man.get("output", "reel.mp4")
    work = args.workdir or os.path.splitext(out)[0] + "_work"
    if not args.dry_run:
        os.makedirs(work, exist_ok=True)

    # Narration audio and exact per-scene durations (whole frames at 30 fps).
    timeline, t, total_words = [], 0.0, 0
    for i, s in enumerate(scenes):
        words = len(s.get("narration", "").split())
        total_words += words
        audio = s.get("audio")
        if args.dry_run:
            dur = max(words / 150 * 60, 2.0) + TAIL   # ~150 wpm estimate
        else:
            if audio:
                raw = audio
            else:
                raw = os.path.join(work, f"scene{i}_raw.mp3")
                cmd = [args.tts, "speak", "--text", s.get("narration", ""),
                       "--format", "mp3", "--output", raw]
                if args.voice or man.get("voice"):
                    cmd += ["--voice", args.voice or man["voice"]]
                run(cmd)
            # Trim leading/trailing silence from every narration file, TTS or
            # supplied, so scene joins keep the 0.15s gap and nothing longer,
            # and cap pauses inside the narration at about 0.25s (the spec
            # allows no gap over 0.3s). -40 dB catches TTS pauses that sit
            # just above digital silence; tested on the Binance preview.
            audio = os.path.join(work, f"scene{i}.wav")
            run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af",
                 "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
                 "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse,"
                 "silenceremove=start_periods=0:stop_periods=-1:stop_duration=0.15:"
                 "stop_threshold=-40dB:stop_silence=0.12",
                 audio])
            dur = probe_duration(audio) + TAIL
            s["_narr_dur"] = dur
            if s.get("clip") and s.get("material") == "real" and not s.get("shots"):
                # Let a real clip run up to 3s past its narration (music only
                # under the tail), never past the clip's remaining length.
                left = probe_duration(s["clip"]) - float(s.get("clip_start", 0))
                dur = max(dur, min(left, dur + 3.0))
        s.setdefault("_narr_dur", dur)
        dur = frames_for(dur) / FPS
        timeline.append((s, t, dur, audio))
        t += dur
    print(f"Scenes: {len(scenes)}  Words: {total_words}  Total: {t:.2f}s (limit {max_dur}s)")
    if t > max_dur:
        print(f"ERROR: total {t:.1f}s exceeds {max_dur}s -- trim narration, "
              "never the denial or distinction scenes.", file=sys.stderr)
        if not args.dry_run:
            sys.exit(1)
    if args.dry_run:
        for s, start, dur, _ in timeline:
            print(f"  {start:6.2f}-{start + dur:6.2f}s  {s.get('id')} [{s.get('material')}]: "
                  f"{s.get('headline', '')!r}")
        return 0

    # Render every shot to an exact-length 30 fps segment. A scene with
    # "shots" is cut into several shots that share its narration.
    video_list, audio_list, render_warnings = [], [], []
    diagram_shown = {}     # node list -> nodes already on screen, so reveals continue
    for i, (s, start, dur, audio) in enumerate(timeline):
        name = f"scene{i}"
        total_frames = frames_for(dur)
        shots = expand_shots(s)
        weights = [sh.get("weight", 1) for sh in shots]
        bounds = [round(total_frames * sum(weights[:j]) / sum(weights))
                  for j in range(len(shots) + 1)]
        for j, sh in enumerate(shots):
            shot_dur = (bounds[j + 1] - bounds[j]) / FPS
            sh["_scene_dur"], sh["_shot_start"] = min(s["_narr_dur"], dur), bounds[j] / FPS
            if sh.get("material") == "ai" and shot_dur > 3.0 + 1 / FPS:
                render_warnings.append(f"scene {s.get('id')} shot {j + 1}: AI shot runs "
                                       f"{shot_dur:.2f}s; the spec caps AI shots at 3s.")
            limit = 5.0 if any(sh.get(k) for k in ("card", "timeline", "end_card")) else 4.0
            if shot_dur > limit + 1 / FPS:
                render_warnings.append(f"scene {s.get('id')} shot {j + 1}: runs {shot_dur:.2f}s, "
                                       f"over the {limit:.0f}s shot limit; add shots.")
            if sh.get("diagram"):
                key = tuple(sh["diagram"]["nodes"])
                stage = sh["diagram"].get("stage", len(key))
                count = len(key) if stage == "X" else int(stage)
                sh["_diagram_shown"] = diagram_shown.get(key, 0)
                if count < sh["_diagram_shown"]:
                    render_warnings.append(f"scene {s.get('id')} shot {j + 1}: diagram drops from "
                                           f"{sh['_diagram_shown']} to {count} nodes; it will "
                                           "jump backwards.")
                diagram_shown[key] = count
            video_list.append(render_shot(sh, shot_dur, work, f"{name}_{j}", render_warnings))
            if sh.get("_mode"):
                s["_mode"] = ", ".join(filter(None, [s.get("_mode"), sh["_mode"]])) \
                    if j else sh["_mode"]
        a = os.path.join(work, f"{name}_audio.wav")
        if audio:
            run(["ffmpeg", "-y", "-v", "error", "-i", audio, "-af", "apad",
                 "-ar", "48000", "-ac", "2", "-t", f"{dur:.4f}", a])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                 "anullsrc=r=48000:cl=stereo", "-t", f"{dur:.4f}", a])
        audio_list.append(a)
    for w in render_warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    # Subtitles: chunked per sentence, timed proportionally within the scene.
    ass_path = os.path.join(work, "subs.ass")
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
           "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
           "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           # BorderStyle 3 = opaque black box; MarginV 270 puts the subtitle
           # bottom at y=1010, inside the 250px bottom safe area.
           "Style: Sub,DejaVu Sans Mono,30,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
           "1,0,0,0,100,100,0,0,3,1,0,2,40,40,270,1",
           "", "[Events]",
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for s, start, dur, _ in timeline:
        # Time chunks over the spoken length only; a real clip's tail runs on
        # after the last subtitle instead of stretching the captions.
        speak = min(s.get("_narr_dur", dur), dur)
        chunks = chunk_narration(s.get("narration", ""))
        words_total = max(1, len(s.get("narration", "").split()))
        pos, used = start, 0
        for ci, chunk in enumerate(chunks):
            cw = len(chunk.split())
            cend = start + speak if ci == len(chunks) - 1 else start + speak * (used + cw) / words_total
            if chunk:
                ass.append(f"Dialogue: 0,{fmt_ass(pos)},{fmt_ass(cend)},Sub,,0,0,0,,{chunk}")
            pos, used = cend, used + cw
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass))
    # Give libass the subtitle font directly, so it never falls back to a
    # proportional system font where DejaVu is not installed system-wide.
    os.makedirs(os.path.join(work, "fonts"), exist_ok=True)
    for fnt in (MONO_BOLD, MONO):
        shutil.copy(fnt, os.path.join(work, "fonts"))

    def concat(paths, listname):
        listing = os.path.join(work, listname)
        with open(listing, "w", encoding="utf-8") as f:
            for p in paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        return listing

    total = sum(d for _, _, d, _ in timeline)
    concat_v = os.path.join(work, "video_only.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", concat(video_list, "videos.txt"), "-vf", f"fps={FPS},format=yuv420p",
         "-c:v", "libx264", concat_v])
    concat_a = os.path.join(work, "audio_only.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", concat(audio_list, "audios.txt"), "-c", "copy", concat_a])

    # Original sine-pad music bed (no copyrighted music), mixed low.
    if man.get("music_bed", True):
        music = os.path.join(work, "music.wav")
        run(["ffmpeg", "-y", "-v", "error",
             "-f", "lavfi", "-i", f"sine=frequency=110:duration={total:.2f}",
             "-f", "lavfi", "-i", f"sine=frequency=164.8:duration={total:.2f}",
             "-filter_complex",
             "[0:a]volume=0.05[a0];[1:a]volume=0.03[a1];[a0][a1]amix=inputs=2:normalize=0,"
             "lowpass=f=400,afade=t=in:st=0:d=1,"
             f"afade=t=out:st={max(0, total - 1):.2f}:d=1,aformat=sample_rates=48000:channel_layouts=stereo[m]",
             "-map", "[m]", music])
        mixed = os.path.join(work, "mixed.wav")
        run(["ffmpeg", "-y", "-v", "error", "-i", concat_a, "-i", music,
             "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]",
             "-map", "[a]", mixed])
        concat_a = mixed
    # loudnorm alone stopped short of -14 LUFS on true-peak limiting, so a
    # gentle compressor runs first.
    norm_a = os.path.join(work, "audio_norm.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", concat_a, "-af",
         "acompressor=threshold=-28dB:ratio=12:attack=5:release=100:makeup=12dB,"
         "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", norm_a])

    # Final mux. Explicit -t, not -shortest: video and audio are both exact.
    # The ass filter path is relative to work/ (Windows drive colons break
    # filter parsing), so ffmpeg runs from work/.
    out_abs = os.path.abspath(out)
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.abspath(concat_v),
                        "-i", os.path.abspath(norm_a), "-vf", "ass=subs.ass:fontsdir=fonts",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        # 192k AAC: the default bitrate overshot true peak above 0 dB.
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                        "-t", f"{total:.4f}", out_abs],
                       capture_output=True, text=True, cwd=work)
    if r.returncode != 0:
        sys.exit(f"Final mux failed:\n{r.stderr[-2000:]}")

    # Self-check (a start, not the verification gate).
    print(f"Built: {out_abs}")
    got = probe_duration(out_abs)
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_name,width,height,sample_rate,channels", "-of", "csv=p=0", out_abs],
            check=False)
    print(f"Streams:\n{r.stdout.strip()}")
    ok = abs(got - total) <= 0.1
    print(f"{'PASS' if ok else 'FAIL'}: duration {got:.2f}s vs shot list {total:.2f}s")
    r = run(["ffmpeg", "-i", out_abs, "-af", "ebur128", "-f", "null", "-"], check=False)
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    loud_ok = False
    if lufs:
        val = float(lufs[-1])
        loud_ok = -15.5 <= val <= -13.5
        print(f"{'PASS' if loud_ok else 'FAIL'}: loudness {val} LUFS (target -14)")
    else:
        print("FAIL: loudness could not be measured")
    sheets = os.path.join(work, "contact_sheets")
    os.makedirs(sheets, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", out_abs, "-vf", "fps=2,scale=180:-1,tile=8x2",
         os.path.join(sheets, "sheet_%02d.png")], check=False)
    print(f"Contact sheets: {sheets}")
    print("Shots:")
    for s, start, dur, _ in timeline:
        print(f"  {start:6.2f}-{start + dur:6.2f}s  {s.get('id')} [{s.get('material')}] "
              f"label={' | '.join(source_label(sh) for sh in expand_shots(s))!r}"
              + (f" layout={s['_mode']}" if s.get("_mode") else ""))
    print("NEXT: run the independent verification gate (SKILL.md) before delivery.")
    if got > max_dur or not ok or not loud_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
