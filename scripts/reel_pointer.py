"""The end card's pointer: a link preview of the referenced article, drawn by
the build (SKILL.md, "End card"; references/end-card.md).

Two forms. The full card (an end card without summary panels) has the
article's photo across the top, then the domain, the title and the outlet
and date. The compact card (an end card with summary panels, where about
150px is left) has the photo on the left at the card's height, its width
following the photo's own shape. Without a photo, a tile in the reel's
colour carries the outlet name, so the card keeps its shape for every
source. The title is the article's headline word for word: it shrinks, the
card grows, or the build stops; it is never shortened or clipped.
"""

from functools import lru_cache
from urllib.parse import urlparse

from reel_common import *  # noqa: F401,F403

# The compact card searches heights, so fonts are reused rather than reloaded.
font = lru_cache(maxsize=None)(font)  # noqa: F405

CARD_W = 640                 # the card spans the frame's content width (x 40-680)
COMPACT_H = 150              # the compact card's least height
COMPACT_MAX_H = 360          # it never grows past this (the end card's layout stops well before)
FULL_RATIOS = (16 / 9, 1.91)     # the full card's photo shape, narrowest to widest (w / h)
COMPACT_RATIOS = (1.0, 1.91)     # the compact card's photo shape
FULL_TILE_H = 360            # the full card's no-photo block (16:9 at 640 wide)
TITLE_INK = (17, 17, 17)
MUTED_INK = (102, 102, 102)
FULL_RADIUS, COMPACT_RADIUS = 18, 14


def pointer_domain(url):
    """The domain the card shows: the URL's host without a leading www., uppercased."""
    host = urlparse(url).hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host.upper()


def clamp_ratio(iw, ih, lo, hi):
    """The photo's shape (width / height), held between lo and hi."""
    return min(max(iw / ih, lo), hi)


def cover_at(img, tw, th, keep=None):
    """img scaled to cover tw x th and cropped to it, the crop window centred
    on the keep box's centre (fractions [x0, y0, x1, y1]; the image centre
    when keep is None) and held inside the image. Never stretched."""
    from PIL import Image
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    sw, sh = iw * s, ih * s
    if keep:
        cx, cy = (keep[0] + keep[2]) / 2 * sw, (keep[1] + keep[3]) / 2 * sh
    else:
        cx, cy = sw / 2, sh / 2
    # Clamp both ends: when a scaled side equals the target, float rounding
    # can make sw - tw a hair below zero, and Pillow refuses a negative box.
    x0 = max(0.0, min(cx - tw / 2, sw - tw))
    y0 = max(0.0, min(cy - th / 2, sh - th))
    box = (x0 / s, y0 / s, min(iw, (x0 + tw) / s), min(ih, (y0 + th) / s))
    return img.resize((tw, th), Image.LANCZOS, box=box)


def _photo(p):
    """The pointer's photo as RGB (transparency flattened onto white), or None."""
    from PIL import Image
    if not p.get("photo"):
        return None
    raw = Image.open(p["photo"]).convert("RGBA")
    img = Image.new("RGB", raw.size, WHITE)
    img.paste(raw, (0, 0), raw)
    return img


def _fits(d, lines, f, max_w):
    return all(d.textlength(ln, font=f) <= max_w for ln in lines)


def _title_lines(d, title, max_w, sizes, ok):
    """(font, lines, line height) for the title: the first size in sizes whose
    wrapped lines fit max_w and pass ok(size, lines), else the last size with
    as many lines as it needs. Stops when a single word is wider than max_w
    at the last size: the title is never clipped."""
    for sz in sizes:
        f = font(BOLD, sz)
        lines = wrap(d, title, f, max_w)
        if _fits(d, lines, f, max_w) and ok(sz, lines):
            return f, lines, sz * 1.2
    sz = sizes[-1]
    f = font(BOLD, sz)
    for word in title.split():
        if d.textlength(word, font=f) > max_w:
            raise RuntimeError(f"pointer title word {word!r} is wider than the card at the "
                               "smallest size; check the title is the article's headline.")
    return f, wrap(d, title, f, max_w), sz * 1.2


def _small_lines(d, text, path, size, max_w):
    """(font, lines, line height) for the domain or the outlet-and-date line:
    wrapped at size, shrunk down to 11px when one word is too wide."""
    for sz in range(size, 10, -1):
        f = font(path, sz)
        lines = wrap(d, text, f, max_w)
        if _fits(d, lines, f, max_w):
            return f, lines, sz * 1.2
    raise RuntimeError(f"pointer text {text!r} doesn't fit the card; shorten it.")


def _tile(w, h, outlet, size):
    """The no-photo tile: the reel's panel colour with the outlet name in white."""
    from PIL import Image, ImageDraw
    tile = Image.new("RGB", (w, h), PANEL)
    d = ImageDraw.Draw(tile)
    r = fit_lines(d, outlet, BOLD, size, 14, w - 16, h - 16)
    if not r:
        raise RuntimeError(f"pointer outlet {outlet!r} doesn't fit its {w}x{h} tile; use the "
                           "outlet's usual short name in 'outlet'.")
    f, lines, lh = r
    y = (h - lh * len(lines)) / 2
    for ln in lines:
        d.text(((w - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=WHITE)
        y += lh
    return tile


def _draw_lines(d, x, y, lines, f, lh, fill):
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


def _rounded(card, radius):
    """card (RGB) as RGBA with rounded corners."""
    from PIL import Image, ImageDraw
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, card.width - 1, card.height - 1],
                                           radius=radius, fill=255)
    out = card.convert("RGBA")
    out.putalpha(mask)
    return out


def preview_card(p, compact):
    """The pointer's link preview as an RGBA image CARD_W wide (transparent
    outside its rounded corners). p: the manifest's pointer ("outlet",
    "title", "url", "date", optional "photo" and "keep"). compact: the form
    for the end card with summary panels. Raises RuntimeError when text
    can't be placed without clipping."""
    return _compact_card(p) if compact else _full_card(p)


def _full_card(p):
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    pad_x, col_w = 24, CARD_W - 48
    dom = _small_lines(d, pointer_domain(p["url"]), REG, 20, col_w)
    title = _title_lines(d, p["title"], col_w, list(range(32, 23, -2)),
                         lambda sz, lines: len(lines) <= 3)
    meta = _small_lines(d, f"{p['outlet']} · {p['date']}", REG, 19, col_w)
    img = _photo(p)
    if img:
        top_h = round(CARD_W / clamp_ratio(img.width, img.height, *FULL_RATIOS))
        top = cover_at(img, CARD_W, top_h, p.get("keep"))
    else:
        top_h = FULL_TILE_H
        top = _tile(CARD_W, top_h, p["outlet"], 96)
    body_h = 20 + dom[2] * len(dom[1]) + 8 + title[2] * len(title[1]) + 10 \
        + meta[2] * len(meta[1]) + 24
    card = Image.new("RGB", (CARD_W, top_h + round(body_h)), WHITE)
    card.paste(top, (0, 0))
    cd = ImageDraw.Draw(card)
    y = top_h + 20
    y = _draw_lines(cd, pad_x, y, dom[1], dom[0], dom[2], MUTED_INK) + 8
    y = _draw_lines(cd, pad_x, y, title[1], title[0], title[2], TITLE_INK) + 10
    _draw_lines(cd, pad_x, y, meta[1], meta[0], meta[2], MUTED_INK)
    return _rounded(card, FULL_RADIUS)


def _compact_card(p):
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    img = _photo(p)
    base_w = round(COMPACT_H * clamp_ratio(img.width, img.height, *COMPACT_RATIOS)) \
        if img else COMPACT_H
    # The smallest card height at which the title fits. The photo slot is
    # never narrower than the card is tall, so when the card grows the tile
    # stays square and a photo is cropped no narrower than 1:1 (the slot
    # widening narrows the text column, which the search accounts for).
    for h in range(COMPACT_H, COMPACT_MAX_H + 1):
        slot_w = max(base_w, h)
        col_x = slot_w + 18
        col_w = CARD_W - 18 - col_x
        dom = _small_lines(d, pointer_domain(p["url"]), REG, 15, col_w)
        meta = _small_lines(d, f"{p['outlet']} · {p['date']}", REG, 15, col_w)
        fixed = 14 + dom[2] * len(dom[1]) + 5 + 6 + meta[2] * len(meta[1]) + 14
        f_min = font(BOLD, 17)
        lines = wrap(d, p["title"], f_min, col_w)
        if h > COMPACT_H and (not _fits(d, lines, f_min, col_w)
                              or fixed + 17 * 1.2 * len(lines) > h):
            continue        # not even the smallest size fits at this height
        title = _title_lines(d, p["title"], col_w, list(range(24, 16, -1)),
                             lambda sz, lines: fixed + sz * 1.2 * len(lines) <= h)
        body_h = fixed + title[2] * len(title[1])
        if body_h <= h:
            break
    else:
        raise RuntimeError(f"pointer title is too long for the compact card even at "
                           f"{COMPACT_MAX_H}px tall; leave the summary panels off so the end "
                           "card uses the full card.")
    card = Image.new("RGB", (CARD_W, h), WHITE)
    card.paste(cover_at(img, slot_w, h, p.get("keep")) if img
               else _tile(slot_w, h, p["outlet"], 38), (0, 0))
    cd = ImageDraw.Draw(card)
    y = (h - body_h) / 2 + 14
    y = _draw_lines(cd, col_x, y, dom[1], dom[0], dom[2], MUTED_INK) + 5
    y = _draw_lines(cd, col_x, y, title[1], title[0], title[2], TITLE_INK) + 6
    _draw_lines(cd, col_x, y, meta[1], meta[0], meta[2], MUTED_INK)
    return _rounded(card, COMPACT_RADIUS)
