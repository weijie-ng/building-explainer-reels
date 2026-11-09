#!/usr/bin/env python3
"""
Show real clips as the posts they are, in one 9:16 shot
(references/graphics-and-clips.md, "Someone's post" and "Side-by-side
composite of real clips"):

- one tile: someone's post (a reel, TikTok, Short or other posted video),
  shown whole as a post card with the account above it (the "post"
  layout). It sits below the caption band and may run past the platform's
  bottom UI (KEEP_BOTTOM) to the frame's bottom edge, so a 9:16 reel is
  shown whole at 468x832 instead of 327x582. The script prints how much of
  the clip lies under the platform's UI: nothing the line depends on may
  be there.
- 2-4 tiles: the same content posted by several accounts, each clip whole
  in its own shape. Side by side ("row") they stay inside the content band;
  a 2x2 "grid" of tall clips runs past the platform's UI to the bottom edge
  like a post (four 9:16 clips at 218x388), with every account name above
  it, and the script prints how much of the bottom row is covered.

Either way none of the reel's own text lands on a tile or an account
name, and the tiles stay inside the headline's column (x 40-680), 16px
apart, so they never run to the frame's side edges. Behind the tiles is the reel's blue over a blurred copy of the
first clip, like the blurred fill behind any image. Each tile is the
account's own clip, only cropped, scaled, trimmed and synced; the source
clips' burned-in captions can be masked per tile. Above each tile is the
account's avatar (when given) and name, copied exactly from the post, and
the strip and clip are drawn as one card with rounded corners and a soft
shadow.
Several tiles can arrive one after another (--stagger) to show the spread.

Usage:
  python3 make_composite.py spec.json [--out composite.mp4] [--preview]

spec.json:
  {
    "duration": 3.0,                  // the shot's length (s); shots stay <= 6s
    "label": "TRACED EXAMPLES • 28 OCT 2026",   // the one source label for the set;
                                      //   one tile defaults to "<account> • <posted>"
    "layout": "auto",                 // "post" (one tile), "grid" (2 columns),
                                      //   "row" (1 x N) or "auto"
    "stagger": 0.3,                   // s between tiles appearing; 0 = all at once
    "caption_top": 300,               // the beat's caption position, if moved
    "tiles": [
      {"clip": "dagul.mp4", "start": 0.0,
       "account": "Dagul Udin",       // exactly as on the post
       "avatar": "dagul_avatar.jpg",  // optional: the post's own profile picture
       "post_url": "https://...", "posted": "27 OCT 2026",
       "focus": [0.5, 0.4],           // optional: centre of the crop (fractions), used
                                      //   only when this clip's shape differs from the
                                      //   other tiles'
       "mask": [[0.1, 0.78, 0.9, 0.86]]}  // optional: burned-in captions to blur
    ]                                 //   out (x0, y0, x1, y1 fractions of the clip)
  }

Paths in the spec are relative to the spec file. Writes the composite
(720x1280, 30 fps, h264, no audio), and prints the manifest entry and the
asset-log rows to paste into facts.md. --preview also writes
<out>_preview.png: the last frame with the header and caption bands
shaded, to check that nothing the viewer must read sits under them.

Needs ffmpeg and Pillow.
"""

import argparse
import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_common import (W, H, FPS, BLUE, BLUR_TINT, CAPTION_TOP, CAPTION_LINES,  # noqa: E402
                         CAPTION_LINE_H, CAPTION_CLEAR, KEEP_BOTTOM, SAFE_TOP,
                         HEADLINE_WRAP, WHITE, BOLD, font, run, frames_for, probe_duration)

SIDE = (W - HEADLINE_WRAP) // 2   # side padding: tiles stay inside the headline's
                                  # column (x 40-680), never near the frame edge
GAP = 16            # px between tiles
CHIP_H = 40         # account strip above each tile
CHIP_PAD = 10       # space between the card's edge and the avatar or name
RADIUS_MAX, RADIUS_MIN = 18, 12   # card corners: as round as the end card's link
                                  # preview (reel_pointer.py), less on small tiles
SHADOW_BLUR, SHADOW_DROP, SHADOW_ALPHA = 12, 6, 130   # soft shadow under each card
EDGE_ALPHA = 80     # faint light edge around each card
STRIP_ALPHA = 170   # the dark account strip at the card's top
SS = 4              # supersampling for smooth corners and edges
AVATAR = 30         # avatar diameter
NAME_SIZE = 22      # account name size; shrinks to NAME_MIN to fit, never truncated
NAME_MIN = 14
FADE = 0.2          # each tile fades in over this long
MAX_SHOT = 6.0      # SKILL.md: shots are never over 6s
MADE_BY = "make_composite"   # written to the output's comment tag


def fail(msg):
    sys.exit(f"make_composite: {msg}")


def load_spec(path):
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    tiles = spec.get("tiles") or []
    if not 1 <= len(tiles) <= 4:
        fail(f"needs 1 tile (someone's post) or 2-4 (the same content from several "
             f"accounts), got {len(tiles)}.")
    if len(tiles) == 1 and not spec.get("label") and tiles[0].get("account") \
            and tiles[0].get("posted"):
        spec["label"] = f"{tiles[0]['account']} • {tiles[0]['posted']}"
    if not spec.get("label"):
        fail("needs 'label': one source label describing the set, e.g. "
             "\"TRACED EXAMPLES • 28 OCT 2026\" (references/graphics-and-clips.md).")
    dur = float(spec.get("duration") or 0)
    if dur <= 0:
        fail("needs 'duration' (the shot's length in seconds).")
    for i, t in enumerate(tiles, 1):
        for key in ("clip", "account", "post_url", "posted"):
            if not t.get(key):
                fail(f"tile {i} needs '{key}'. Every tile traces to a post in the asset log: "
                     "the account name exactly as posted, the post URL and its date.")
        for key in ("clip", "avatar"):
            if t.get(key):
                t[key] = os.path.join(base, t[key])
        if not os.path.exists(t["clip"]):
            fail(f"tile {i}: clip not found: {t['clip']}")
        if t.get("avatar") and not os.path.exists(t["avatar"]):
            fail(f"tile {i}: avatar not found: {t['avatar']}")
        for box in t.get("mask", []):
            if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                fail(f"tile {i}: mask {box} must be [x0, y0, x1, y1] fractions of the clip.")
    return spec, base


def clip_size(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height", "-of", "csv=p=0", path])
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def band(spec):
    """The content band: below the caption band, above the platform's UI."""
    cap = int(spec.get("caption_top", CAPTION_TOP))
    return cap + CAPTION_LINES * CAPTION_LINE_H + CAPTION_CLEAR, KEEP_BOTTOM


def layout(spec, sizes):
    """Cells (x, y, w, h) for each tile's video, below its account strip.
    Every layout keeps the tiles inside the headline's column (SIDE padding
    on both sides) with GAP between them.
    Post (one tile): the clip whole, in its own shape, as large as the frame
    allows below the caption band; a tall clip runs past the platform's UI
    to the bottom edge, a wider one is centred in the content band.
    Grid: 2 columns, each tile keeping its clip's own shape, as large as the
    frame allows below the caption band; tall clips run past the platform's
    UI to the bottom edge, as a post does, while every account strip stays
    above it. Row: 1 x N, each tile keeping its clip's own shape inside the
    content band, so a portrait clip is shown whole but small: when the band
    caps the height, the tile narrows instead of cropping the clip.
    A tile's clip is cropped (around its focus) only when its shape differs
    from the tiles' shared shape."""
    n = len(sizes)
    top, bottom = band(spec)
    band_h = bottom - top
    mode = spec.get("layout", "auto")
    if mode == "auto":
        portrait = all(h > w for w, h in sizes)
        mode = "post" if n == 1 else "row" if portrait and n <= 3 else "grid"
    if n == 1 and mode != "post":
        fail("one tile takes the 'post' layout (or 'auto').")
    if n > 1 and mode == "post":
        fail(f"the 'post' layout is for one tile; {n} tiles take 'grid', 'row' or 'auto'.")
    usable_w = W - 2 * SIDE
    if mode == "post":
        sw, sh = sizes[0]
        y = top + CHIP_H
        th = min(H - y, int(usable_w * sh / sw))
        tw = int(th * sw / sh)
        if y + th < bottom:
            y += (bottom - y - th) // 2
        cells = [((W - tw) // 2, y, tw, th)]
    elif mode == "row":
        tw = (usable_w - (n - 1) * GAP) // n
        aspect = sum(h / w for w, h in sizes) / n
        th = min(int(tw * aspect), band_h - CHIP_H)
        tw = min(tw, int(th / aspect))   # capped height: narrow the tile, never crop the clip
        y = top + (band_h - CHIP_H - th) // 2 + CHIP_H
        x0 = (W - (n * tw + (n - 1) * GAP)) // 2
        cells = [(x0 + i * (tw + GAP), y, tw, th) for i in range(n)]
    elif mode == "grid":
        # Like the post: each clip keeps its shape, and tall clips may run
        # past the platform's UI to the bottom edge (four 9:16 clips are
        # 218x388 each instead of 148x263 inside the band).
        cols, rows = 2, math.ceil(n / 2)
        aspect = sum(h / w for w, h in sizes) / n
        cell_w = (usable_w - GAP) // cols
        row_h = (H - top - (rows - 1) * GAP) // rows - CHIP_H
        th = min(int(cell_w * aspect), row_h)
        tw = min(cell_w, int(th / aspect))
        grid_h = rows * (CHIP_H + th) + (rows - 1) * GAP
        y0 = top + max(0, (band_h - grid_h) // 2)   # centred in the band when it fits there
        cells = []
        for i in range(n):
            r, c = divmod(i, cols)
            in_row = min(cols, n - r * cols)
            x0 = (W - (in_row * tw + (in_row - 1) * GAP)) // 2
            cells.append((x0 + c * (tw + GAP), y0 + r * (th + CHIP_H + GAP) + CHIP_H, tw, th))
    else:
        fail(f"layout must be 'post', 'grid', 'row' or 'auto', not {mode!r}.")
    for w_, h_ in [(c[2], c[3]) for c in cells]:
        if w_ < 120 or h_ < 120:
            fail(f"tiles would be {w_}x{h_}px, too small to read; use fewer tiles or 'grid'.")
    return mode, cells


def radius(cell):
    """Corner radius of a tile's card: smaller on a small tile."""
    return max(RADIUS_MIN, min(RADIUS_MAX, cell[2] // 26))


def _card_shape(w, h, r, square_top=False):
    """Mask (L) of a w x h card with corners of radius r, drawn at SS times
    the size and scaled down so the curves are smooth. square_top keeps the
    top corners square: the clip's top edge meets its account strip."""
    from PIL import Image, ImageDraw
    m = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=r * SS, fill=255)
    if square_top:
        d.rectangle([0, 0, w * SS - 1, r * SS], fill=255)
    return m.resize((w, h), Image.LANCZOS)


def mask_png(cell, path):
    """The tile clip's alpha: its bottom corners rounded to match the card."""
    _, _, w, h = cell
    _card_shape(w, h, radius(cell), square_top=True).save(path)


def chip_png(tile, cell, path):
    """Transparent full-frame layer laid over the tile's clip, which makes
    the clip and its account strip read as one card with rounded corners: a
    soft shadow outside the card, the dark strip with the avatar and account
    name, and a faint light edge. Names are drawn exactly as given; a long
    name gets a smaller size, never an ellipsis."""
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
    x, y, w, h = cell
    r = radius(cell)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx0, cy0, ch = x, y - CHIP_H, CHIP_H + h          # the card: strip + clip
    pad = SHADOW_BLUR * 3 + SHADOW_DROP
    shape = _card_shape(w, ch, r)
    # Shadow: the card's shape dropped and blurred, cut away inside the card
    # so it never darkens the clip.
    sh = Image.new("L", (w + 2 * pad, ch + 2 * pad), 0)
    sh.paste(shape, (pad, pad + SHADOW_DROP))
    sh = sh.filter(ImageFilter.GaussianBlur(SHADOW_BLUR)).point(lambda v: v * SHADOW_ALPHA // 255)
    inside = Image.new("L", sh.size, 0)
    inside.paste(shape, (pad, pad))
    sh = ImageChops.multiply(sh, ImageChops.invert(inside))
    im.paste((0, 0, 0, 255), (cx0 - pad, cy0 - pad), sh)
    # The account strip: the card's top, down to where the clip starts.
    strip = shape.crop((0, 0, w, CHIP_H)).point(lambda v: v * STRIP_ALPHA // 255)
    im.alpha_composite(Image.merge("RGBA", [Image.new("L", strip.size, 0)] * 3 + [strip]),
                       (cx0, cy0))
    # A faint light edge along the whole card, over the clip's edge.
    e = Image.new("L", (w * SS, ch * SS), 0)
    ImageDraw.Draw(e).rounded_rectangle([0, 0, w * SS - 1, ch * SS - 1], radius=r * SS,
                                        outline=EDGE_ALPHA, width=int(1.5 * SS))
    e = e.resize((w, ch), Image.LANCZOS)
    im.alpha_composite(Image.merge("RGBA", [Image.new("L", (w, ch), 255)] * 3 + [e]), (cx0, cy0))
    d = ImageDraw.Draw(im)
    nx = x + CHIP_PAD
    cy = y - CHIP_H // 2
    if tile.get("avatar"):
        av = ImageOps.fit(Image.open(tile["avatar"]).convert("RGB"), (AVATAR * 4, AVATAR * 4))
        mask = Image.new("L", av.size, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, av.size[0] - 1, av.size[1] - 1], fill=255)
        av = av.resize((AVATAR, AVATAR), Image.LANCZOS)
        mask = mask.resize((AVATAR, AVATAR), Image.LANCZOS)
        im.paste(av, (nx, cy - AVATAR // 2), mask)
        nx += AVATAR + 8
    room = x + w - CHIP_PAD - nx
    size = NAME_SIZE
    while size > NAME_MIN and d.textlength(tile["account"], font=font(BOLD, size)) > room:
        size -= 1
    f = font(BOLD, size)
    if d.textlength(tile["account"], font=f) > room:
        fail(f"account name {tile['account']!r} doesn't fit a {w}px tile even at {NAME_MIN}px; "
             "use fewer tiles or the grid layout (names are never shortened).")
    d.text((nx, cy), tile["account"], font=f, fill=WHITE, anchor="lm",
           stroke_width=2, stroke_fill=(0, 0, 0, 200))
    im.save(path)


def build(spec, out, preview):
    tiles = spec["tiles"]
    dur = float(spec["duration"])
    stagger = float(spec.get("stagger", 0.3))
    warnings = []
    if dur > MAX_SHOT + 1e-6:
        warnings.append(f"duration {dur}s is over the {MAX_SHOT:.0f}s shot limit; split the beat.")
    if (len(tiles) - 1) * stagger + FADE > dur - 0.8:
        warnings.append(f"the last tile appears at {(len(tiles) - 1) * stagger:.2f}s of a {dur}s "
                        "shot; shorten 'stagger' so all tiles are seen together for a while.")
    sizes = [clip_size(t["clip"]) for t in tiles]
    mode, cells = layout(spec, sizes)
    work = tempfile.mkdtemp(prefix="composite_")

    cmd = ["ffmpeg", "-y", "-v", "error"]
    for t in tiles:
        start = float(t.get("start", 0))
        left = probe_duration(t["clip"]) - start
        if left + 1 / FPS < dur:
            warnings.append(f"{t['account']}: clip has {left:.2f}s from its start, under the "
                            f"{dur}s shot; its last frame would hold (a freeze).")
        cmd += ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", t["clip"]]
    for i, (t, cell) in enumerate(zip(tiles, cells)):
        p = os.path.join(work, f"chip{i}.png")
        chip_png(t, cell, p)
        cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
    for i, cell in enumerate(cells):
        p = os.path.join(work, f"mask{i}.png")
        mask_png(cell, p)
        cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]

    n = len(tiles)
    hold = f"fps={FPS},tpad=stop_mode=clone:stop_duration={dur:.3f},trim=duration={dur:.3f}"
    blue = "0x%02X%02X%02X" % BLUE
    g = [f"[0:v]split=2[src0][bgsrc]",
         f"[bgsrc]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
         f"boxblur=40:2,drawbox=c={blue}@{BLUR_TINT}:t=fill,setsar=1,{hold},format=yuv420p[bg]"]
    for i, (t, (x, y, w, h), (sw, sh)) in enumerate(zip(tiles, cells, sizes)):
        src = "[src0]" if i == 0 else f"[{i}:v]"
        f = []
        for x0, y0, x1, y1 in t.get("mask", []):
            # delogo needs the box strictly inside the frame.
            bx, by = max(1, int(x0 * sw)), max(1, int(y0 * sh))
            bw, bh = min(sw - 2 - bx, int((x1 - x0) * sw)), min(sh - 2 - by, int((y1 - y0) * sh))
            f.append(f"delogo=x={bx}:y={by}:w={bw}:h={bh}")
        fx, fy = (t.get("focus") or (0.5, 0.5))
        f.append(f"scale={w}:{h}:force_original_aspect_ratio=increase")
        f.append(f"crop={w}:{h}:min(max({fx}*iw-{w // 2}\\,0)\\,iw-{w}):"
                 f"min(max({fy}*ih-{h // 2}\\,0)\\,ih-{h})")
        f.append(f"setsar=1,{hold},format=rgba")
        g.append(f"{src}{','.join(f)}[v{i}]")
        g.append(f"[{2 * n + i}:v]fps={FPS},format=gray[k{i}]")
        f = ["alphamerge"]   # rounded bottom corners, matching the card
        delay = i * stagger
        if delay > 0:
            f.append(f"tpad=start_duration={delay:.3f}:start_mode=add:color=0x00000000,"
                     f"trim=duration={dur:.3f}")
        # The first tile is there from frame 0, so the shot never opens on
        # an empty background; later tiles fade in on their turn.
        fade = f",fade=in:st={delay:.3f}:d={FADE}:alpha=1" if delay > 0 else ""
        g.append(f"[v{i}][k{i}]{','.join(f)}{fade}[t{i}]")
        g.append(f"[{n + i}:v]fps={FPS},format=rgba{fade}[c{i}]")
    last = "[bg]"
    for i, (x, y, w, h) in enumerate(cells):
        # The clip first, then its card layer over it (shadow, strip, edge).
        g.append(f"{last}[t{i}]overlay={x}:{y}[m{i}a]")
        g.append(f"[m{i}a][c{i}]overlay=0:0[m{i}]")
        last = f"[m{i}]"
    g.append(f"{last}format=yuv420p[out]")
    cmd += ["-filter_complex", ";".join(g), "-map", "[out]", "-an",
            "-frames:v", str(frames_for(dur)), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            # The build reads this tag to tell a post or composite from a
            # clip that fills the frame (reel_manifest.py).
            "-metadata", f"comment={MADE_BY}", out]
    run(cmd)

    if preview:
        write_preview(spec, out, dur)
    return mode, cells, warnings


def write_preview(spec, out, dur):
    """The last frame with the header and caption bands shaded red: nothing
    the viewer must read (a tile, an account name) belongs under them."""
    from PIL import Image, ImageDraw
    png = os.path.splitext(out)[0] + "_preview.png"
    run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.1", "-i", out, "-frames:v", "1", png])
    im = Image.open(png).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    top, bottom = band(spec)
    d.rectangle([0, SAFE_TOP, W, top], fill=(255, 0, 0, 70))
    d.rectangle([0, bottom, W, H], fill=(255, 0, 0, 70))
    d.text((12, SAFE_TOP + 4), "HEADER + CAPTION BAND", fill=WHITE, font=font(BOLD, 18))
    d.text((12, bottom + 4), "PLATFORM UI", fill=WHITE, font=font(BOLD, 18))
    Image.alpha_composite(im, ov).convert("RGB").save(png)
    print(f"preview: {png}")


def main():
    ap = argparse.ArgumentParser(description="Show someone's post (one tile), or tile 2-4 "
                                 "accounts' clips, as one 9:16 shot.")
    ap.add_argument("spec")
    ap.add_argument("--out", default=None, help="output mp4 (default: composite.mp4 next to the spec)")
    ap.add_argument("--preview", action="store_true", help="also write <out>_preview.png")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # labels carry "•"
    spec, base = load_spec(a.spec)
    out = a.out or os.path.join(base, "composite.mp4")
    mode, cells, warnings = build(spec, out, a.preview)
    print(f"wrote {out}  ({len(spec['tiles'])} tile(s), {mode} layout, {spec['duration']}s, muted)")
    for w in warnings:
        print(f"WARNING: {w}")
    x, y, w, h = max(cells, key=lambda c: c[1])
    if y + h > KEEP_BOTTOM:
        cut = (KEEP_BOTTOM - y) / h
        pct = f"{1 - cut:.0%}"
        what = (f"The post is {w}x{h} at y={y}. Its bottom {pct}" if mode == "post" else
                f"The bottom row's tiles are {w}x{h} at y={y}. The bottom {pct} of each")
        print(f"\n{what} (below {cut:.2f} of the clip's height) sits under the platform's "
              "caption, name and buttons. Look at that part of the clip: nothing the line "
              "depends on may be there, and burned-in captions there still need a 'mask'.")
    entry = {"clip": os.path.basename(out), "material": "real", "image_source": spec["label"]}
    print("\nManifest entry (add the shot's headline, and keep the label as given):")
    print("  " + json.dumps(entry, ensure_ascii=False))
    print("\nAsset log rows for facts.md (one per tile):")
    print("| Tile | Account (as posted) | Post URL | Posted | File |")
    print("|---|---|---|---|---|")
    for i, t in enumerate(spec["tiles"], 1):
        print(f"| {i} | {t['account']} | {t['post_url']} | {t['posted']} | "
              f"{os.path.basename(t['clip'])} |")
    print("\nLook at the shot before it goes in the manifest: every tile is the account's "
          "own clip, the names match the posts, and no burned-in caption collides with the "
          "reel's headline or captions.")


if __name__ == "__main__":
    main()
