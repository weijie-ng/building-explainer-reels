"""Shot renderers: each visual type becomes an exact-length 30 fps video file."""

from reel_common import *  # noqa: F401,F403
from reel_background import background as story_background


def canvas(scene):
    """A flat shot's base layer: transparent when the shot is drawn over the
    reel's story background (set by the planner as "_background"), else the
    reel's blue. Transparent pixels carry the blue, so edges blend toward it."""
    from PIL import Image
    if scene.get("_background"):
        return Image.new("RGBA", (W, H), BG + (0,))
    return Image.new("RGB", (W, H), BG)


# --- shared overlay text -----------------------------------------------------

def source_label(scene):
    mat = scene.get("material")
    if mat == "ai":
        return AI_MAP_LABEL if scene.get("schematic") else AI_LABEL
    if scene.get("timeline"):
        return scene.get("image_source") or "TIMELINE · TIMES UTC"
    if mat == "diagram":
        label = scene.get("image_source") or DIAGRAM_LABEL
        if (scene.get("diagram") or {}).get("motion_clip"):
            label += " · AI MOTION"
        return label
    if scene.get("stat"):
        label = scene["stat"].get("source", "")
        if scene["stat"].get("motion_clip"):
            label += " · AI MOTION"
        return label
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


def draw_headline(d, y, text, yellow_words=None, size=None):
    """Wrapped at 640px; single-word yellow highlights; black stroke so it
    stays readable over busy photos. Without an explicit size, a headline
    that needs two lines is set smaller (HEADLINE_SIZES_2) so the captions
    keep their place at y=300."""
    if size is None:
        size, lines = headline_lines(text)
    else:
        lines = [ln for part in text.split("\n")
                 for ln in wrap(d, part, font(BOLD, size), HEADLINE_WRAP)]
    f = font(BOLD, size)
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
    headline, like an outlet name on a card, above the caption band, so it
    never reads as a second caption."""
    from PIL import Image, ImageDraw
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    y = SAFE_TOP
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


def header_bottom(scene):
    """Lowest y of a shot's locked top text (tag, source line, headline;
    a headline card's outlet and headline): the caption goes below it."""
    from PIL import Image, ImageDraw
    if scene.get("card"):
        card = scene["card"]
        d = ImageDraw.Draw(Image.new("RGB", (W, H)))
        _, y = text_layer({k: scene[k] for k in ("disinformation",) if k in scene},
                          with_source=False)
        y += 34 * len(wrap(d, card["outlet"], font(MONO_BOLD, 26), HEADLINE_WRAP)) + 12
        y += 62 * sum(len(wrap(d, p, font(BOLD, 52), HEADLINE_WRAP))
                      for p in card["headline"].split("\n"))
        return y + (28 if card.get("image") and card.get("image_source") else 0)
    if scene.get("summary"):
        d = ImageDraw.Draw(Image.new("RGB", (W, H)))
        return SAFE_TOP + 62 * len(wrap(d, summary_title(scene), font(BOLD, 52), HEADLINE_WRAP))
    return text_layer(scene)[1]


def content_top(scene):
    """Where a shot's own content may start: below the caption band (two
    caption lines under the beat's caption position) and below the header."""
    cap = scene.get("_caption_top", CAPTION_TOP)
    return cap + CAPTION_LINES * CAPTION_LINE_H + CAPTION_CLEAR


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
    caption band and the bottom safe area vertically, even at the end of the creep
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
    # or the captions when nothing is gained by it.
    if s * ih <= (sy1 - sy0) + 1:
        y = (sy0 + sy1) / 2 - s * ih / 2
    if s * iw <= (sx1 - sx0) + 1:
        x = (sx0 + sx1) / 2 - s * iw / 2
    full = x <= 0 and y <= 0 and x + s * iw >= W and y + s * ih >= H
    mode = "full-bleed" if full else ("whole" if s <= s_whole + 1e-6 else "zoomed")
    return s, x, y, mode


def still_layout(scene, size, warnings):
    """Where a still image lands: (text layer, band_top, keep, scale, x, y,
    mode). Pure (the planner calls it to tell whether two shots of one image
    are laid out identically); render_still draws from it."""
    layer, text_bottom = text_layer(scene)
    band_top = max(text_bottom + 16, content_top(scene))
    hook_fill = bool(scene.get("_hook"))      # validation rejects "full_bleed": false here
    if hook_fill:
        # Hook stills fill the whole frame, centred on the keep box: the
        # first second has to read as footage, not a picture on a card.
        k = scene.get("keep") or (0, 0, 1, 1)
        keep = ((k[0] + k[2]) / 2, (k[1] + k[3]) / 2) * 2
    elif scene.get("material") == "ai" or scene.get("full_bleed"):
        keep = scene.get("keep", (0.5, 0.5, 0.5, 0.5))   # AI art: fill the screen
    else:
        keep = scene.get("keep")
        if not keep:
            keep = (0, 0, 1, 1)
            warnings.append(f"scene {scene.get('id')}: no 'keep' box, so the whole image is "
                            "shown; add one to let it zoom (see SKILL.md, Layout).")
    s, x, y, mode = keep_layout(size[0], size[1], keep, band_top, KEEP_BOTTOM)
    if hook_fill and scene.get("keep"):
        k = scene["keep"]
        kx0, ky0 = x + s * k[0] * size[0], y + s * k[1] * size[1]
        kx1, ky1 = x + s * k[2] * size[0], y + s * k[3] * size[1]
        if kx0 < 0 or ky0 < 0 or kx1 > W or ky1 > H:
            warnings.append(f"scene {scene.get('id')}: hook still fills the frame and crops its "
                            "keep box. Tighten the keep box to the one subject the hook needs "
                            "(a wide photo keeps a 9:16 slice of it), pick a taller photo, or "
                            "use a clip; the hook never shows a picture on blurred fill.")
    return layer, band_top, keep, s, x, y, mode


def render_still(scene, warnings):
    from PIL import Image, ImageFilter
    pic = Image.open(scene["image"]).convert("RGB")
    layer, band_top, keep, s, x, y, mode = still_layout(scene, pic.size, warnings)
    scene["_mode"] = mode
    # Where the keep box lands on screen, so a move ("push", "pan") keeps it whole.
    k = keep if keep[2] > keep[0] and keep[3] > keep[1] else (0.5, 0.5, 0.5, 0.5)
    scene["_keep_rect"] = (x + s * k[0] * pic.width, y + s * k[1] * pic.height,
                           x + s * k[2] * pic.width, y + s * k[3] * pic.height)
    scene["_band_top"] = band_top
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
    # A dark gradient behind the header and caption band keeps the tags,
    # headline and captions readable over whatever sits behind them.
    fade = content_top(scene) + 20
    grad = Image.new("L", (1, H))
    for yy in range(min(fade, H)):
        grad.putpixel((0, yy), int(150 * (1 - yy / fade)))
    base.paste(Image.new("RGB", (W, H), BLACK), (0, 0), grad.resize((W, H)))
    return [(base, layer, 0.0)]


def _norm_word(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def card_times(scene, dur):
    """When each word of the card's key sentence lights, in shot time (0.0 =
    lit from the first frame). Timed from the beat's measured word times
    (minus the shot's start) when the sentence is found in the narration;
    otherwise at 0.25s a word, finishing within 60% of the shot. A shot that
    continues the same card starts with the words the previous shot ended
    with already lit ("_card_lit")."""
    key = scene["card"].get("key_sentence", "").split()
    n = len(key)
    lit0 = min(int(scene.get("_card_lit", 0)), n)
    times = None
    words = [_norm_word(w) for w in scene.get("narration", "").split()]
    wt = scene.get("_word_times")
    kn = [_norm_word(w) for w in key]
    if n and wt and len(wt) == len(words) and all(kn):
        for a in range(len(words) - n + 1):
            if words[a:a + n] == kn:
                off = scene.get("_shot_start", 0.0)
                times = [max(wt[a + k] - off, 0.0) for k in range(n)]
                break
    if times is None:
        step = min(0.25, 0.6 * dur / max(n - lit0, 1))
        times = [max(k + 1 - lit0, 0) * step for k in range(n)]
    for k in range(n):
        if k < lit0:
            times[k] = 0.0
        elif k:
            times[k] = max(times[k], times[k - 1])
    return times


def card_lit_end(times, dur):
    """How many key-sentence words are lit on the shot's last frame."""
    last = (frames_for(dur) - 1) / FPS
    return sum(1 for t in times if t <= last + 1e-9)


def render_card(scene, dur):
    from PIL import Image, ImageDraw
    card = scene["card"]
    # The tag stays locked; the card content below it creeps with the shot.
    tag_layer, top = text_layer({k: scene[k] for k in ("disinformation",)
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
            # line-and-dot, body and key sentence anchored above the bottom safe area,
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
                                         card["headline"], card.get("yellow_words"), size=HEADLINE_SIZE)
                im.paste(Image.new("RGB", (W, H), BLACK), (0, 0),
                         scrim(max(head_end + 50, content_top(scene)), dot_top - 10))
                cache["base"] = im
            im = cache["base"].copy()
            d = ImageDraw.Draw(im)
            y = top
            for line in wrap(d, card["outlet"], f_out, HEADLINE_WRAP):
                d.text((40, y), line, font=f_out, fill=(200, 210, 230))
                y += 34
            y = draw_headline(d, y + 12, card["headline"], card.get("yellow_words"), size=HEADLINE_SIZE)
            if card.get("image_source"):
                d.text((40, y + 10), card["image_source"], font=font(REG, 18), fill=SOURCE_TEXT)
            d.line([(70, dot_top + 6), (70, dot_top + 40)], fill=YELLOW, width=4)
            d.ellipse([58, dot_top + 40, 82, dot_top + 64], fill=YELLOW)
            y = body_top
        else:
            im = canvas(scene)
            d = ImageDraw.Draw(im)
            y = top
            for line in wrap(d, card["outlet"], f_out, HEADLINE_WRAP):
                d.text((40, y), line, font=f_out, fill=(170, 185, 210))
                y += 34
            y = draw_headline(d, y + 12, card["headline"], card.get("yellow_words"), size=HEADLINE_SIZE)
            y = max(y, content_top(scene) - 20)     # the line-and-dot starts below the captions
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
    times = card_times(scene, dur)
    lit0 = sum(1 for t in times if t <= 0)
    return [(frame(lit0), tag_layer, 0.0)] +            [(frame(i), tag_layer, times[i - 1]) for i in range(lit0 + 1, n + 1)]


NODE_STEP, NODE_H = 140, 64


def diagram_geometry(scene):
    """(top, step) of the diagram's node column: it starts below the caption
    band, and the step shrinks so every node ends above the bottom safe area."""
    # A run of shots of one diagram shares the geometry of its longest node
    # list ("_diagram_n"), so earlier nodes never shift when later ones appear.
    n = max(len(scene["diagram"]["nodes"]), scene.get("_diagram_n", 0))
    top = max(text_layer(scene)[1] + 20, content_top(scene) + 20)
    step = NODE_STEP if n < 2 else min(NODE_STEP, (KEEP_BOTTOM - top - NODE_H) / (n - 1))
    if step < NODE_H + 40:
        raise ValueError(f"scene {scene.get('id')}: {n} diagram nodes don't fit between the "
                         "captions and the bottom safe area; show fewer nodes per shot.")
    return top, step


def diagram_plate(scene):
    """The text-free start frame Muse animates for a diagram's motion clip:
    the background blue, a faint guide line where the arrows run and soft
    glows where the nodes will sit. No words, boxes or arrows: those are
    drawn by the build on top, exactly and on the narrated word."""
    from PIL import Image, ImageDraw, ImageFilter
    n = len(scene["diagram"]["nodes"])
    top, step = diagram_geometry(scene)
    glow = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(glow)
    y0, y1 = top + NODE_H // 2, top + (n - 1) * step + NODE_H // 2
    d.line([(W // 2, y0), (W // 2, y1)], fill=(70, 130, 220), width=10)
    for i in range(n):
        cy = top + i * step + NODE_H // 2
        d.ellipse([W // 2 - 120, cy - 45, W // 2 + 120, cy + 45], fill=(40, 105, 200))
    return glow.filter(ImageFilter.GaussianBlur(18))


def render_diagram(scene, dur):
    """Diagram stages. With "motion_clip" the stages are transparent
    overlays, drawn over the AI motion clip by render_shot."""
    from PIL import Image, ImageDraw
    transparent = bool(scene["diagram"].get("motion_clip"))
    nodes = scene["diagram"]["nodes"]
    stage = scene["diagram"].get("stage", len(nodes))
    reveal = scene["diagram"].get("reveal", False)
    # Index of the node whose outgoing arrow gets the denial X; default is
    # the second arrow (e.g. SINGAPORE / GIC / TEMASEK -> MSCI).
    cross_at = scene["diagram"].get("cross_after", 1 if len(nodes) > 2 else 0)
    top, step = diagram_geometry(scene)

    def frame(count, cross):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if transparent else Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im)
        y = top
        for i, name in enumerate(nodes[:count]):
            f = font(BOLD, 34)
            tw = d.textlength(name, font=f)
            x = (W - tw) / 2 - 18
            d.rounded_rectangle([x, y, x + tw + 36, y + 64], radius=10,
                                fill=YELLOW if i == 0 else WHITE)
            d.text((x + 18, y + 14), name, font=f, fill=BLACK)
            if i < count - 1:
                d.line([(W // 2, y + NODE_H), (W // 2, y + step)], fill=YELLOW, width=5)
                d.polygon([(W // 2 - 12, y + step - 16), (W // 2 + 12, y + step - 16),
                           (W // 2, y + step)], fill=YELLOW)
            y += step
        if cross:
            cx, cy = W // 2, round(top + cross_at * step + (NODE_H + step) / 2)   # mid-arrow
            d.line([(cx - 40, cy - 40), (cx + 40, cy + 40)], fill=RED, width=10)
            d.line([(cx - 40, cy + 40), (cx + 40, cy - 40)], fill=RED, width=10)
        return im

    layer = text_layer(scene)[0]
    shown = min(int(scene["diagram"].get("from", scene.get("_diagram_shown", 0))), len(nodes))
    if stage == "X":
        first, t_cross = x_stage(scene, dur)
        if t_cross <= 0:      # the previous shot of this diagram already showed the X
            return [(frame(len(nodes), True), layer, 0.0)]
        return [(frame(c, False), layer, t) for c, t in first] +                [(frame(len(nodes), True), layer, t_cross)]
    count = int(stage)
    # Nodes already on screen from an earlier shot of this diagram stay put;
    # the reveal continues from there instead of rebuilding from node 1.
    shown = min(shown, count)
    if reveal and count > max(shown, 1):
        times = node_times(scene, nodes[:count], dur)
        start = max(shown, 1)
        return [(frame(start, False), layer, 0.0)] +                [(frame(i, False), layer, times[i - 1]) for i in range(start + 1, count + 1)]
    return [(frame(count, False), layer, 0.0)]


def x_stage(scene, dur):
    """Stage "X": ([(node count, start time), ...], cross time). Nodes already
    shown by an earlier shot of the diagram are drawn at once (the rest are
    revealed on their words when "reveal" is on, else all at once); the red X
    snaps on at 40% of the shot, or just after the last node. Cross time 0.0
    means the previous shot already showed the X: it is drawn from frame 0."""
    d = scene["diagram"]
    nodes = d["nodes"]
    if scene.get("_diagram_cross"):
        return [(len(nodes), 0.0)], 0.0
    shown = min(int(d.get("from", scene.get("_diagram_shown", 0))), len(nodes))
    t_cross = 0.4 * dur
    if d.get("reveal") and 1 <= shown < len(nodes):
        times = node_times(scene, nodes, dur)
        first = [(max(shown, 1), 0.0)] + [(i, times[i - 1]) for i in range(shown + 1, len(nodes) + 1)]
        t_cross = max(min(max(t_cross, times[-1] + 0.3), 0.9 * dur), times[-1] + 1 / FPS)
        return first, t_cross
    return [(len(nodes), 0.0)], t_cross


def node_times(scene, nodes, dur):
    """When each node appears, in shot time. A node appears when its first
    word is spoken, using the same word times as the captions (measured
    by Whisper on the narration, so the node and its caption word light up
    on the same frame). Nodes not named in the narration fall back to
    even spacing over the first 70% of the shot."""
    def norm(w):
        return re.sub(r"[^a-z0-9]", "", w.lower())
    words = [norm(w) for w in scene.get("narration", "").split()]
    scene_dur = scene.get("_scene_dur", dur)
    word_times = scene.get("_word_times")
    if not word_times or len(word_times) != len(words):
        word_times = [n / max(len(words), 1) * scene_dur for n in range(len(words))]
    offset = scene.get("_shot_start", 0.0)
    latest = max(0.0, dur - 0.5)
    times = []
    for k, node in enumerate(nodes):
        first = norm(node.split()[0])
        hit = next((n for n, w in enumerate(words) if first and w.startswith(first)), None)
        if k == 0:
            times.append(0.0)
        elif hit is not None and words:
            times.append(min(max(word_times[hit] - offset, 0.0), latest))
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


def timeline_layout(scene):
    """(text layer, blocks, spacing) of a timeline shot. A shot that
    continues an earlier one keeps that shot's spacing ("_timeline_extra",
    unless it no longer fits), so the events already shown stay where they were."""
    from PIL import Image, ImageDraw
    events = scene["timeline"]["events"]
    layer, top = text_layer(scene)
    f_text = font(BOLD, 30)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    blocks, y = [], max(top + 30, content_top(scene))
    for ev in events:
        lines = wrap(probe, ev["text"], f_text, 590)
        h = 34 + len(lines) * 38 + 30 + 36
        blocks.append((y, lines, ev))
        y += h
    if y > KEEP_BOTTOM:
        raise ValueError(f"scene {scene.get('id')}: timeline runs to y={y}, past the "
                         f"bottom safe area ({KEEP_BOTTOM}); split it into more shots.")
    # Spread the events over the free space above the bottom safe area (up to 90px
    # extra between events), so the frame doesn't end in an empty half.
    extra = min(90, (KEEP_BOTTOM - 40 - y) / max(len(events) - 1, 1))
    if scene.get("_timeline_extra") is not None:
        extra = min(extra, scene["_timeline_extra"])
    blocks = [(by + k * extra, lines, ev) for k, (by, lines, ev) in enumerate(blocks)]
    return layer, blocks, extra


def render_timeline(scene, dur):
    """Vertical timeline: a line with one dot per event; each event shows
    its time, what happened, and its source. Events appear one at a time
    over the first 75% of the shot, then hold. A shot that continues an
    earlier one (or has "from": n) draws the events already shown at once
    and reveals only the new ones. Fits about 3 events per shot; split a
    longer timeline into shots."""
    from PIL import Image, ImageDraw
    events = scene["timeline"]["events"]
    layer, blocks, _ = timeline_layout(scene)
    f_time, f_src = font(MONO_BOLD, 24), font(MONO_BOLD, 18)
    f_text = font(BOLD, 30)

    def frame(n):
        im = canvas(scene)
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

    shown = min(int(scene["timeline"].get("from", scene.get("_timeline_shown", 0))), len(events))
    if shown >= 1:
        new = len(events) - shown
        step = 0.75 * dur / (new + 1)
        return [(frame(shown), layer, 0.0)] +                [(frame(shown + j), layer, j * step) for j in range(1, new + 1)]
    step = 0.75 * dur / max(len(events), 1)
    return [(frame(k), layer, (k - 1) * step) for k in range(1, len(events) + 1)]


def pointer_image(p, max_h):
    """The pointer screenshot scaled to fit 640 x max_h (never upscaled);
    transparent areas go white, not black."""
    from PIL import Image
    raw = Image.open(p["image"]).convert("RGBA")
    img = Image.new("RGB", raw.size, WHITE)
    img.paste(raw, (0, 0), raw)
    img.thumbnail((640, max_h), Image.LANCZOS)
    return img


def pointer_height(scene, max_h):
    """Height draw_pointer will take, from the top of the screenshot (or
    fallback panel) to the bottom of the disclosure line."""
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (W, H)))
    p = scene.get("pointer") or {}
    h = 0
    if p.get("image"):
        h += pointer_image(p, max_h).height + 12 + (26 if p.get("captured") else 0) + 16 + 40
    elif p:
        h += 60 + len(wrap(d, p["headline"], font(BOLD, 38), 600)) * 46 + 50 + 24 + 40
    if scene.get("disclosure"):
        h += 30 + 24 * len(wrap(d, scene["disclosure"], font(REG, 17), 640))
    return h


def draw_pointer(im, d, scene, y, max_h, warnings, wide=False):
    """The pointer to the full story (a screenshot of the article page, or
    the last-resort headline panel), its "READ THE FULL STORY" line and the
    disclosure line under it, from y down. Returns the y below them.
    wide: the space is a short strip (the end card with summary panels), so
    a screenshot that isn't a wide strip comes out too small to read."""
    p = scene.get("pointer")
    if p and p.get("image"):
        # A screenshot of the article itself (headline and byline), shown
        # whole with a thin white frame.
        shot_img = pointer_image(p, max_h)
        if shot_img.width < 480 and (wide or shot_img.height < max_h):
            warnings.append(f"scene {scene.get('id')}: end-card screenshot is only "
                            f"{shot_img.width}x{shot_img.height}px on screen; recapture it larger "
                            "and wider (outlet, headline and byline as a strip about 1000px wide) "
                            "so its text is readable.")
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
        # Small and muted, directly under the pointer.
        f = font(REG, 17)
        yy = y + 30
        for line in wrap(d, scene["disclosure"], f, 640):
            d.text((40, yy), line, font=f, fill=SOURCE_TEXT)
            yy += 24
        y = yy
    return y


def render_end_card(scene, warnings):
    """The end card without summary panels: closing line, pointer and
    disclosure line, and no captions, so nothing competes with the pointer."""
    from PIL import ImageDraw
    im = canvas(scene)
    d = ImageDraw.Draw(im)
    y = draw_headline(d, SAFE_TOP, scene.get("headline", "CHECK BEFORE YOU SHARE"),
                      scene.get("yellow_words"), size=HEADLINE_SIZE)
    y = draw_pointer(im, d, scene, y + 40, 420, warnings)
    if y > KEEP_BOTTOM:
        warnings.append(f"scene {scene.get('id')}: end card runs to y={y}, into the bottom "
                        f"safe area (below {KEEP_BOTTOM}); shorten the disclosure or the closing line.")
    return [(im, None, 0.0)]


def fit_lines(d, text, path, size, min_size, max_w, max_h, gap=1.18):
    """The largest font size (size down to min_size) at which text wraps
    into max_w with its lines inside max_h. Returns (font, lines, line
    height), or None: text is never clipped; it shrinks or the build stops."""
    for sz in range(size, min_size - 1, -2):
        f = font(path, sz)
        lines = wrap(d, text, f, max_w)
        if all(d.textlength(ln, font=f) <= max_w for ln in lines) and \
                len(lines) * sz * gap <= max_h:
            return f, lines, sz * gap
    return None


def captioned(sh):
    """Whether a shot carries captions: every shot but an end card without
    summary panels, where nothing competes with the pointer. With panels, the
    loop-back narration is long and the panels need it, so it stays captioned."""
    return not (sh.get("end_card") and not sh.get("summary"))


def summary_title(scene):
    """The top line of the end card: its closing line."""
    return scene.get("headline") or "CHECK BEFORE YOU SHARE"


def half_panel(p):
    """A plain figure or a donut sits two to a row; a proportion bar, a
    compare chart and a distinction each take a full row."""
    return "value" in p and "bar" not in p and "compare" not in p


def summary_rows(panels):
    """Figures and donuts go two to a row; every other panel takes a full row."""
    rows, pend = [], []
    for p in panels:
        if half_panel(p):
            pend.append(p)
            if len(pend) == 2:
                rows.append(pend)
                pend = []
            continue
        if pend:
            rows.append(pend)
            pend = []
        rows.append([p])
    if pend:
        rows.append(pend)
    return rows


def card_rows(scene):
    """The summary panels of a shot, in rows as the card lays them out."""
    return summary_rows(scene["summary"].get("panels", []))


CHART_FILL_STEPS = 4         # a chart panel's fill grows in this many steps as it lands
TRACK = (52, 86, 160)        # the unfilled part of a bar or ring, lighter than PANEL


def is_chart(p):
    return any(k in p for k in ("bar", "compare", "donut"))


END_SUMMARY_ROWS = 2         # rows of panels that fit on the end card above the pointer
END_POINTER_MIN = 150        # px: the pointer screenshot's least height on that card
END_POINTER_MAX = 260


def end_summary_layout(scene, top):
    """Row height and pointer height for the end card with summary panels:
    the panels take up to 150px a row, the pointer what is left (150-260px).
    Raises when they don't fit above the bottom safe area."""
    sid = scene.get("id")
    rows = card_rows(scene)
    if len(rows) > END_SUMMARY_ROWS:
        raise RuntimeError(f"beat {sid}: the end card has {len(rows)} rows of summary panels; "
                           f"{END_SUMMARY_ROWS} fit above the pointer (up to 4 figures, or 2 "
                           "figures and one distinction). Cut panels.")
    gap = 12
    for row_h in range(150, 119, -2):
        panels_h = len(rows) * row_h + gap * (len(rows) - 1) + 24
        for ph in range(END_POINTER_MAX, END_POINTER_MIN - 1, -10):
            if top + panels_h + pointer_height(scene, ph) <= KEEP_BOTTOM:
                return row_h, ph
    raise RuntimeError(f"beat {sid}: the summary panels, pointer and disclosure line don't fit "
                       f"on the end card above y={KEEP_BOTTOM}. Cut a row of panels, shorten "
                       "the disclosure line or the closing line, or capture the pointer as a "
                       "wider strip.")


def render_summary(scene, dur, warnings):
    """The end card with summary panels ("end_card": true with "summary"):
    the closing line on top, the captions under it, the reel's key figures
    and distinctions (at most two rows), then the pointer and disclosure line,
    on the background blue. Readable at a glance and in a screenshot: equal
    panels, fixed margins, no clipped text. The pointer and disclosure line
    are there from the first frame; the panels appear one after another
    (SUMMARY_STAGGER apart, tighter in a short shot so all are in by
    SUMMARY_BUILD_SHARE of it), then the card holds.

    summary: {"panels": [...]}
    A panel is a figure {"value": "$6.3B", "label": "...", "source": "..."}
    or a distinction {"pair": [{"title": "REAL", "text": "..."},
    {"title": "FALSE", "text": "..."}]}."""
    from PIL import Image, ImageDraw
    sid = scene.get("id")
    base = canvas(scene)
    d = ImageDraw.Draw(base)
    y = draw_headline(d, SAFE_TOP, summary_title(scene), scene.get("yellow_words"),
                      size=HEADLINE_SIZE)
    rows = card_rows(scene)
    top = max(y + 24, content_top(scene))
    gap, margin, pad = 12, 40, 14
    row_h, ptr_h = end_summary_layout(scene, top)
    panels_bottom = top + len(rows) * row_h + gap * (len(rows) - 1)
    draw_pointer(base, d, scene, panels_bottom + 24, ptr_h, warnings, wide=True)
    boxes = []
    for r, row in enumerate(rows):
        ry = top + r * (row_h + gap)
        cw = (W - 2 * margin - gap * (len(row) - 1)) / len(row)
        for c, p in enumerate(row):
            x0 = margin + c * (cw + gap)
            boxes.append((x0, ry, x0 + cw, ry + row_h, p))
    # Every panel uses the same type sizes: the largest that fits the
    # fullest panel (first pass measures on a scratch image, second draws).
    defaults = {"value": (72, 34), "label": (26, 17), "title": (34, 20), "body": (26, 17),
                "ring": (30, 14), "side": (24, 15), "name": (22, 15), "amount": (26, 16)}
    cap = {role: hi for role, (hi, _) in defaults.items()}
    src_size = 15

    def fit(dd, role, text, path, max_w, max_h, fixed):
        hi, lo = defaults[role]
        size = cap[role] if fixed else hi
        r = fit_lines(dd, text, path, size, size if fixed else lo, max_w, max_h)
        if r and not fixed:
            cap[role] = min(cap[role], r[0].size)
        return r

    def source(dd, p, x, x1, y1, max_w, right=None):
        """The panel's source line at the bottom, shrunk (never clipped) to max_w."""
        if not p.get("source"):
            return
        r = fit_lines(dd, p["source"], MONO, src_size, 12, max_w, src_size * 1.3)
        if not r:
            raise RuntimeError(f"beat {sid}: summary source {p['source']!r} doesn't fit; "
                               "shorten it.")
        dd.text((x, y1 - pad - src_size - 2), r[1][0], font=r[0], fill=SOURCE_TEXT)
        if right:
            f = font(MONO, src_size)
            dd.text((x1 - pad - dd.textlength(right, font=f), y1 - pad - src_size - 2),
                    right, font=f, fill=SOURCE_TEXT)

    def panel(dd, box, fixed, t=1.0):
        x0, y0, x1, y1, p = box
        dd.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=PANEL)
        iw, ih = x1 - x0 - 2 * pad, y1 - y0 - 2 * pad
        src_h = src_size + 8 if p.get("source") else 0
        if "bar" in p:
            # Proportion bar: the figure and its label on one line, then a bar
            # from 0 to 100% filled to the share, then the source with "100%"
            # at the bar's end so the scale is on screen.
            v = fit(dd, "value", p["value"], BOLD, iw * 0.4, ih * 0.42, fixed)
            if not v:
                raise RuntimeError(f"beat {sid}: summary bar {p['value']!r} doesn't fit; "
                                   "shorten its value.")
            vw = max(dd.textlength(ln, font=v[0]) for ln in v[1])
            line_h = v[2] * len(v[1])
            lx = x0 + pad + vw + 14
            lab = fit(dd, "side", p.get("label", ""), REG, x1 - pad - lx, line_h, fixed) \
                if p.get("label") else (None, [], 0)
            bar_h = 16
            if not lab or line_h + 8 + bar_h + 6 + src_h > ih:
                raise RuntimeError(f"beat {sid}: summary bar {p['value']!r} doesn't fit "
                                   "without clipping; shorten its label.")
            yy = y0 + pad
            for ln in v[1]:
                dd.text((x0 + pad, yy), ln, font=v[0], fill=YELLOW)
                yy += v[2]
            ly = y0 + pad + (line_h - lab[2] * len(lab[1])) / 2
            for ln in lab[1]:
                dd.text((lx, ly), ln, font=lab[0], fill=WHITE)
                ly += lab[2]
            by = y0 + pad + line_h + 8
            bx0, bx1 = x0 + pad, x1 - pad
            dd.rounded_rectangle([bx0, by, bx1, by + bar_h], radius=bar_h // 2, fill=TRACK)
            share = max(0.0, min(1.0, float(p["bar"])))
            fw = (bx1 - bx0) * share * t
            if fw > 0:
                # A tiny share still shows as a sliver, never as nothing.
                dd.rounded_rectangle([bx0, by, bx0 + max(fw, 4), by + bar_h],
                                     radius=bar_h // 2, fill=YELLOW)
            source(dd, p, x0 + pad, x1, y1, iw * 0.7, right="100%")
            return
        if "compare" in p:
            # Compare bars: two or three amounts in one unit on one scale that
            # starts at zero, each with its name on the left and its figure at
            # the bar's end.
            items = p["compare"]
            rh = (ih - src_h) / len(items)
            names = []
            for it in items:
                r = fit(dd, "name", it.get("label", ""), REG, 200, rh, fixed)
                if not r or len(r[1]) > 1:
                    raise RuntimeError(f"beat {sid}: compare label {it.get('label')!r} doesn't "
                                       "fit on one line; shorten it.")
                names.append(r)
            f_name = names[0][0]
            nx = x0 + pad + max(dd.textlength(r[1][0], font=f_name) for r in names) + 14
            amts = []
            for it in items:
                r = fit(dd, "amount", it.get("value", ""), BOLD, 150, rh, fixed)
                if not r:
                    raise RuntimeError(f"beat {sid}: compare value {it.get('value')!r} doesn't "
                                       "fit; shorten it.")
                amts.append(r)
            vw = max(dd.textlength(r[1][0], font=r[0]) for r in amts) + 10
            span = x1 - pad - vw - nx
            top_amt = max(float(it["amount"]) for it in items) or 1.0
            bar_h = max(10, min(22, rh * 0.55))
            for k, (it, nm, am) in enumerate(zip(items, names, amts)):
                cy = y0 + pad + rh * k + rh / 2
                dd.text((x0 + pad, cy - nm[2] / 2), nm[1][0], font=nm[0], fill=WHITE)
                w = span * float(it["amount"]) / top_amt * t
                dd.rounded_rectangle([nx, cy - bar_h / 2, nx + span, cy + bar_h / 2],
                                     radius=4, fill=TRACK)
                if w > 0:
                    dd.rounded_rectangle([nx, cy - bar_h / 2, nx + max(w, 4), cy + bar_h / 2],
                                         radius=4, fill=YELLOW if k == 0 else WHITE)
                dd.text((nx + span + 10, cy - am[2] / 2), am[1][0], font=am[0], fill=YELLOW)
            source(dd, p, x0 + pad, x1, y1, iw)
            return
        if "donut" in p:
            # Donut: one share as a ring filled clockwise from the top, the
            # figure in its middle, the label beside it, the source along the
            # bottom as on every panel.
            avail = ih - src_h
            dia = min(avail, 100)
            rx0, ry0 = x0 + pad, y0 + pad + (avail - dia) / 2
            ring = max(10, dia * 0.15)
            dd.ellipse([rx0, ry0, rx0 + dia, ry0 + dia], outline=TRACK, width=int(ring))
            share = max(0.0, min(1.0, float(p["donut"])))
            if share * t > 0:
                dd.arc([rx0, ry0, rx0 + dia, ry0 + dia], -90, -90 + 360 * share * t,
                       fill=YELLOW, width=int(ring))
            inner = dia - 2 * ring
            v = fit(dd, "ring", p["value"], BOLD, inner * 0.85, inner * 0.6, fixed)
            if not v or len(v[1]) > 1:
                raise RuntimeError(f"beat {sid}: donut value {p['value']!r} doesn't fit "
                                   "inside the ring; shorten it.")
            tw = dd.textlength(v[1][0], font=v[0])
            dd.text((rx0 + dia / 2 - tw / 2, ry0 + dia / 2 - v[0].size * 0.62), v[1][0],
                    font=v[0], fill=YELLOW)
            sx = rx0 + dia + 14
            sw = x1 - pad - sx
            lab = fit(dd, "side", p.get("label", ""), REG, sw, avail, fixed) \
                if p.get("label") else (None, [], 0)
            if not lab:
                raise RuntimeError(f"beat {sid}: donut label {p.get('label')!r} doesn't fit "
                                   "beside the ring; shorten it.")
            yy = y0 + pad + (avail - lab[2] * len(lab[1])) / 2
            for ln in lab[1]:
                dd.text((sx, yy), ln, font=lab[0], fill=WHITE)
                yy += lab[2]
            source(dd, p, x0 + pad, x1, y1, iw)
            return
        if "value" in p:
            src_h = src_size + 8 if p.get("source") else 0
            v = fit(dd, "value", p["value"], BOLD, iw, ih * 0.42, fixed)
            used = v[2] * len(v[1]) if v else 0
            lab = fit(dd, "label", p.get("label", ""), REG, iw, ih - used - src_h - 6, fixed) \
                if p.get("label") else (None, [], 0)
            if not v or not lab:
                raise RuntimeError(f"beat {sid}: summary panel {p.get('value')!r} doesn't fit "
                                   "without clipping; shorten its value or label.")
            yy = y0 + pad
            for ln in v[1]:
                dd.text((x0 + pad, yy), ln, font=v[0], fill=YELLOW)
                yy += v[2]
            yy += 6
            for ln in lab[1]:
                dd.text((x0 + pad, yy), ln, font=lab[0], fill=WHITE)
                yy += lab[2]
            if p.get("source"):
                dd.text((x0 + pad, y1 - pad - src_size - 2), p["source"],
                        font=font(MONO, src_size), fill=SOURCE_TEXT)
            return
        hw = (x1 - x0 - gap) / 2
        for h, half in enumerate(p["pair"][:2]):
            hx0 = x0 + h * (hw + gap)
            if h:
                dd.line([(hx0 - gap / 2, y0 + pad), (hx0 - gap / 2, y1 - pad)],
                        fill=SOURCE_TEXT, width=2)
            t = fit(dd, "title", half.get("title", ""), BOLD, hw - 2 * pad, 50, fixed)
            body = fit(dd, "body", half.get("text", ""), REG, hw - 2 * pad, ih - 56, fixed)
            if not t or not body:
                raise RuntimeError(f"beat {sid}: summary distinction {half.get('title')!r} "
                                   "doesn't fit without clipping; shorten it.")
            yy = y0 + pad
            for ln in t[1]:
                dd.text((hx0 + pad, yy), ln, font=t[0], fill=YELLOW)
                yy += t[2]
            yy += 10
            for ln in body[1]:
                dd.text((hx0 + pad, yy), ln, font=body[0], fill=WHITE)
                yy += body[2]

    step = summary_stagger(scene, dur)
    scratch = ImageDraw.Draw(Image.new("RGB", (W, H)))
    for box in boxes:
        panel(scratch, box, fixed=False)
    stages = [(base.copy(), None, 0.0)]
    grow = [(base.copy(), None, 0.0)]       # the same, with charts filling in
    for k, box in enumerate(boxes):
        if is_chart(box[4]):
            # A chart fills over its own slot, ending as the panel lands, so
            # the finished card's hold is unchanged.
            for j in range(1, CHART_FILL_STEPS):
                panel(d, box, fixed=True, t=j / CHART_FILL_STEPS)
                grow.append((base.copy(), None, step * (k + j / CHART_FILL_STEPS)))
        panel(d, box, fixed=True)
        stages.append((base.copy(), None, step * (k + 1)))
        grow.append(stages[-1])
    stages_all = len(boxes)
    # A shot that continues the same summary starts with the panels the
    # previous shot ended with already shown.
    shown = min(int(scene.get("_summary_shown", 0)), stages_all)
    if shown:
        return [(stages[shown][0], None, 0.0)] + \
               [(stages[k][0], None, step * (k - shown)) for k in range(shown + 1, stages_all + 1)]
    return grow


def summary_stagger(scene, dur):
    """Seconds between panels: SUMMARY_STAGGER, tightened so the last panel
    is in by SUMMARY_BUILD_SHARE of the shot and the finished card holds."""
    n = sum(len(r) for r in card_rows(scene))
    todo = n - min(int(scene.get("_summary_shown", 0)), n)
    if todo <= 0:
        return SUMMARY_STAGGER
    return min(SUMMARY_STAGGER, SUMMARY_BUILD_SHARE * dur / todo)


def summary_hold(scene, dur):
    """(seconds the finished card is on screen, seconds it needs)."""
    n = sum(len(r) for r in card_rows(scene))
    todo = n - min(int(scene.get("_summary_shown", 0)), n)
    held = frames_for(dur) / FPS - todo * summary_stagger(scene, dur)
    return held, max(SUMMARY_HOLD_MIN, SUMMARY_HOLD_PER_PANEL * n)


def summary_panels_shown(scene, dur):
    """Panels on screen at the summary shot's last frame."""
    n = sum(len(r) for r in card_rows(scene))
    shown = min(int(scene.get("_summary_shown", 0)), n)
    last = (frames_for(dur) - 1) / FPS
    return min(n, shown + int(last / summary_stagger(scene, dur) + 1e-9))


STAT_COUNT_SECONDS = 0.6     # a numeric stat counts up over this, ease-out
STAT_POP = (0.72, 0.9, 1.06, 1.0)   # a non-numeric stat pops in over 4 steps (0.05s each)


def stat_time(scene, dur):
    """When the figure lands: the narrated word that starts with the
    figure's digits (the same measured word times as the captions), else
    stat.at, else 0.3s into the shot."""
    st = scene["stat"]
    if "at" in st:
        return max(0.0, min(float(st["at"]), dur - 0.3))
    digits = _norm_word(st["value"])
    words = [_norm_word(w) for w in scene.get("narration", "").split()]
    wt = scene.get("_word_times")
    if digits and wt and len(wt) == len(words):
        off = scene.get("_shot_start", 0.0)
        for n, w in enumerate(words):
            if w and (w.startswith(digits) or digits.startswith(w)) and wt[n] >= off - 0.05:
                return max(0.0, min(wt[n] - off, dur - 0.3))
    return min(0.3, dur / 4)


def render_stat(scene, dur):
    """A stat shot: one sourced figure, big, with a short label under it,
    arriving on the word that says it. A plain number counts up to its value
    (STAT_COUNT_SECONDS, ease-out); anything else ("0 of 5", "21 OCT") pops
    in. The label shows from the first frame. Over the story background (or the
    plain blue without one) with grain, or as transparent stages over an AI
    motion clip ("motion_clip"), like the diagram.

    stat: {"value": "9.2", "label": "severity score, 10 = most severe",
           "source": "PHP ADVISORY • 21 OCT 2026", "motion_clip": "...",
           "clip_start": 0, "at": 0.4}"""
    from PIL import Image, ImageDraw
    st = scene["stat"]
    transparent = bool(st.get("motion_clip"))
    layer = text_layer(scene)[0]
    value = str(st["value"])
    top, bottom = content_top(scene), KEEP_BOTTOM
    d0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    size = 230
    while size > 60 and d0.textlength(value, font=font(BOLD, size)) > W - 80:
        size -= 6
    f_lab = font(BOLD, 40)
    lab_lines = wrap(d0, st.get("label", ""), f_lab, W - 120)
    block = size + 30 + 50 * len(lab_lines)
    y_val = top + max(0, (bottom - top - block) // 2) - 20

    def frame(text, scale=1.0, label=True):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if transparent else canvas(scene)
        d = ImageDraw.Draw(im)
        f = font(BOLD, max(8, round(size * scale)))
        tw = d.textlength(text, font=f)
        yy = y_val + (size - f.size) / 2
        d.text(((W - tw) / 2, yy), text, font=f, fill=YELLOW, stroke_width=4, stroke_fill=BLACK)
        if label:
            ly = y_val + size + 30
            for ln in lab_lines:
                lw = d.textlength(ln, font=f_lab)
                d.text(((W - lw) / 2, ly), ln, font=f_lab, fill=WHITE, stroke_width=3,
                       stroke_fill=BLACK)
                ly += 50
        return im

    t0 = stat_time(scene, dur)
    # The label is on screen from the start, so the shot is never empty
    # while the voice leads up to the figure.
    stages = [(frame("", label=True), layer, 0.0)] if t0 > 0 else []
    m = re.fullmatch(r"([^\d]*)(\d+(?:\.\d+)?)([^\d]*)", value)
    if m and float(m.group(2)) > 0:
        pre, num, post = m.groups()
        dec = len(num.split(".")[1]) if "." in num else 0
        steps = max(2, round(STAT_COUNT_SECONDS * FPS / 2))
        for k in range(steps + 1):
            p = k / steps
            e = 1 - (1 - p) ** 3
            shown = f"{pre}{float(num) * e:.{dec}f}{post}" if k < steps else value
            stages.append((frame(shown), layer, t0 + p * STAT_COUNT_SECONDS))
    else:
        for k, sc in enumerate(STAT_POP):
            stages.append((frame(value, sc), layer, t0 + 0.05 * k))
    return stages


WIPE_SECONDS = 0.5     # a graphic wipe: a blue panel with yellow edges crosses the frame
WIPE_EDGE = 18


def apply_wipe(path, prev_path, prev_frames, frames, direction, work, name):
    """Turn the first WIPE_SECONDS of a rendered shot into a graphic wipe from
    the previous shot: a panel in the reel's blue with yellow edges sweeps
    across (from the right for "left", from the bottom for "up"), covering the
    previous shot's last frame and uncovering this one. The shot keeps its
    exact frame count. Captions are burned over the joined reel afterwards,
    so the wipe never covers them."""
    from PIL import Image, ImageDraw
    last = os.path.join(work, f"{name}_wipe_prev.png")
    run(["ffmpeg", "-y", "-v", "error", "-i", prev_path, "-vf", f"select=eq(n\\,{prev_frames - 1})",
         "-fps_mode", "passthrough", "-frames:v", "1", last])
    vertical = direction == "up"
    pw, ph = (W, H + 2 * WIPE_EDGE) if vertical else (W + 2 * WIPE_EDGE, H)
    panel = Image.new("RGB", (pw, ph), BG)
    d = ImageDraw.Draw(panel)
    if vertical:
        d.rectangle([0, 0, W, WIPE_EDGE - 1], fill=YELLOW)
        d.rectangle([0, ph - WIPE_EDGE, W, ph], fill=YELLOW)
    else:
        d.rectangle([0, 0, WIPE_EDGE - 1, H], fill=YELLOW)
        d.rectangle([pw - WIPE_EDGE, 0, pw, H], fill=YELLOW)
    pnl = os.path.join(work, f"{name}_wipe_panel.png")
    panel.save(pnl)
    D = WIPE_SECONDS
    p = f"min(t/{D},1)"          # every expression below sits inside '...': plain commas
    e = f"({p}*{p}*(3-2*{p}))"                       # smoothstep ease in and out
    span = (H + ph) if vertical else (W + pw)
    k = (H if vertical else W) / span                # the panel covers the frame from here
    pos = f"{H if vertical else W}-{span}*{e}"
    xy = f"x=0:y='{pos}'" if vertical else f"x='{pos}':y=0"
    tmp = os.path.join(work, f"{name}_wipe.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", path,
         "-loop", "1", "-framerate", str(FPS), "-i", last,
         "-loop", "1", "-framerate", str(FPS), "-i", pnl,
         "-filter_complex",
         f"[0:v][1:v]overlay=0:0:enable='lt({e},{k:.4f})'[a];"
         f"[a][2:v]overlay={xy}:eval=frame:enable='lt(t,{D})',format=yuv420p",
         "-an", "-frames:v", str(frames), "-c:v", "libx264", tmp])
    os.replace(tmp, path)
    return path


def render_plain(scene):
    return [(canvas(scene), text_layer(scene)[0], 0.0)]


MOVES = ("push", "pan", "inset")
PUSH_MAX = 1.10      # push: up to 110%, toward the keep box
PAN_SCALE = 1.12     # pan: the image is shown at 112% so it has room to travel
INSET_START = 0.62   # inset: starts at 62% of the frame, grows to fill it
MOVE_SECONDS = {"push": 1.5, "pan": 1.5, "inset": 0.4}


def move_room(keep_rect, band_top):
    """The largest scale (about the keep box centre) that keeps the keep box
    inside the frame and between the caption band and the bottom safe area."""
    x0, y0, x1, y1 = keep_rect
    kx, ky = (x0 + x1) / 2, (y0 + y1) / 2
    hw, hh = max((x1 - x0) / 2, 1), max((y1 - y0) / 2, 1)
    return min((kx - EDGE) / hw, (W - EDGE - kx) / hw, (ky - band_top) / hh,
               (KEEP_BOTTOM - ky) / hh)


def move_transform(move, t, dur, keep_rect=None, band_top=SAFE_TOP):
    """(scale, centre x, centre y, shift x) of the base layer at time t, for
    a move on a still image; the text layer never moves. The move eases out
    over MOVE_SECONDS (at most 60% of the shot) and lands on the subject,
    then the shot holds with a slow creep so it stays readable."""
    md = min(MOVE_SECONDS[move], 0.6 * dur)
    u = min(t / md, 1.0) if md > 0 else 1.0
    e = 1 - (1 - u) ** 3
    creep = 1 + 0.01 * max(0.0, t - md) / max(dur - md, 1e-6)
    cx, cy = W / 2, H / 2
    if keep_rect is not None:
        cx, cy = (keep_rect[0] + keep_rect[2]) / 2, (keep_rect[1] + keep_rect[3]) / 2
    if move == "push":
        room = move_room(keep_rect, band_top) if keep_rect else PUSH_MAX
        top = max(1.0, min(PUSH_MAX, room / 1.01))
        return (1 + (top - 1) * e) * creep, cx, cy, 0.0
    if move == "pan":
        sc = PAN_SCALE
        travel = (sc - 1) * W / 2          # never shows past the image's edge
        return sc * creep, W / 2, H / 2, travel * (1 - e)
    # inset: grows from a card on the background blue to the full frame
    return (INSET_START + (1 - INSET_START) * e) * creep, W / 2, H / 2, 0.0


def stages_to_video(stages, dur, work, name, creep="in", grain=False, move=None,
                    keep_rect=None, band_top=SAFE_TOP, run_off=0, run_frames=None, hold=False,
                    bg=None, bg_start=0.0):
    """Render a shot frame by frame and pipe it to ffmpeg (exact frame count).

    stages: [(base, overlay_or_None, start_seconds), ...]. The base layer
    creeps (sub-pixel, so no jitter); the overlay (tags, headlines, source
    label) is composited on top unmoved. creep: "in" = push in to 102% over
    the shot; "up" = drift up CREEP_UP_PX per second; "none" = static.
    grain: faint animated grain, for flat graphic backgrounds only.
    run_off, run_frames: this shot is one of a run of shots that continue the
    same visual (see reel_continuity): it starts run_off frames into a run of
    run_frames, and the creep or move is computed on run time, so the base layer
    carries on from where the previous shot ended instead of restarting.
    bg, bg_start: the reel's story background (reel_background) and the shot's
    start in reel seconds. The base layer, transparent where it would be plain
    blue, creeps or moves over the background, which keeps its own motion on
    reel time, so it carries on across cuts and through a hold."""
    from PIL import Image
    total = frames_for(dur)
    run_total = run_frames or total
    run_dur = run_total / FPS
    out = os.path.join(work, f"{name}.mp4")
    fill = BG + (0,) if bg is not None else BG
    if bg is not None:
        stages = [(b if b.mode == "RGBA" else b.convert("RGBA"), lay, s) for b, lay, s in stages]
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
        g = 0 if hold else f       # a hold freezes the run's frame for the whole shot
        frac = (run_off + g) / max(run_total - 1, 1)
        t_run = (run_off + g) / FPS
        if move:
            sc, cx, cy, sx = move_transform(move, t_run, run_dur, keep_rect, band_top)
            # Inverse map of: scale by sc about (cx, cy), then shift right by sx.
            a = 1 / sc
            img = base.transform((W, H), Image.AFFINE,
                                 (a, 0, cx - (cx + sx) * a, 0, a, cy - cy * a),
                                 resample=Image.BICUBIC, fillcolor=fill)
        elif creep == "in":
            # Inverse affine map: scale about the frame centre.
            a = 1 / (1 + CREEP_SCALE * frac)
            img = base.transform((W, H), Image.AFFINE,
                                 (a, 0, W / 2 * (1 - a), 0, a, H / 2 * (1 - a)),
                                 resample=Image.BICUBIC)
        elif creep == "up":
            # Drift up, zoomed just enough that the drift never exposes a
            # blank strip at the bottom.
            a = 1 / (1 + CREEP_UP_PX * run_dur / H)
            img = base.transform((W, H), Image.AFFINE,
                                 (a, 0, W / 2 * (1 - a), 0, a, CREEP_UP_PX * t_run * a),
                                 resample=Image.BICUBIC)
        else:
            img = base
        if bg is not None:
            img = compose(bg.frame(bg_start + f / FPS), img)
        if noise:
            img = Image.blend(img, noise[(run_off + f) % len(noise)], GRAIN_ALPHA)
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


MOTION_TINT = 0.45    # an AI motion clip is blended 45% toward the reel's blue


def stages_over_clip(stages, clip, clip_start, dur, work, name):
    """A graphic's transparent stages drawn over an AI motion clip.

    The clip is the base layer: cover-scaled to 720x1280 at 30 fps (its own
    frame rate and audio dropped), tinted toward the background blue so the
    reel keeps one background colour and the graphic stays readable. Each
    stage's overlay (nodes, arrows, labels, the X) and the text layer are
    composited on top unmoved, switching at the stage times, which come from
    the narrated words. A clip shorter than the shot holds its last frame."""
    from PIL import Image
    total = frames_for(dur)
    out = os.path.join(work, f"{name}.mp4")
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", f"{clip_start:.3f}", "-i", clip, "-an", "-vf",
         f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
         f"tpad=stop_mode=clone:stop_duration={dur:.3f}",
         "-frames:v", str(total), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-frames:v", str(total), "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    blue = Image.new("RGB", (W, H), BG)
    size, last, k = W * H * 3, None, 0
    for f in range(total):
        raw = dec.stdout.read(size)
        if len(raw) == size:
            last = Image.frombytes("RGB", (W, H), raw)
        img = Image.blend(last if last is not None else blue, blue, MOTION_TINT)
        t = f / FPS
        while k + 1 < len(stages) and t >= stages[k + 1][2]:
            k += 1
        overlay, layer = stages[k][0], stages[k][1]
        if overlay.mode == "RGBA":
            img = compose(img, overlay)
        if layer is not None:
            img = compose(img, layer)
        enc.stdin.write(img.tobytes())
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    err = enc.stderr.read().decode(errors="replace")
    if enc.wait() != 0:
        raise RuntimeError(f"Rendering {name} failed:\n{err[-2000:]}")
    return out


def clip_to_video(scene, dur, work, name):
    """A real or AI clip, cover-scaled to 720x1280 with no added zoom (the
    crop is centred on its 'keep' box, so a landscape AI video keeps its
    subject); its own audio dropped; its own caption/logo bands masked with delogo;
    text layer looped on top."""
    layer, _ = text_layer(scene)
    png = os.path.join(work, f"{name}_text.png")
    layer.save(png)
    k = scene.get("keep") or (0, 0, 1, 1)
    kx, ky = (k[0] + k[2]) / 2, (k[1] + k[3]) / 2
    crop_x = f"min(max({kx:.4f}*iw-{W // 2}\\,0)\\,iw-{W})"
    crop_y = f"min(max({ky:.4f}*ih-{H // 2}\\,0)\\,ih-{H})"
    # tpad holds the last frame if the clip is shorter than the shot (the
    # plan warns, since that is a freeze), so the shot always has exactly
    # frames_for(dur) frames.
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:{crop_x}:{crop_y},"
          f"setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={dur:.3f}")
    for x, y, w, h in scene.get("clip_mask", []):
        vf += f",delogo=x={x}:y={y}:w={w}:h={h}"
    out = os.path.join(work, f"{name}.mp4")
    # clip_end: stop at the last faithful frame of an AI animation (from
    # check_ai_animation.py); the shot holds that frame after it.
    span = ["-t", f"{max(float(scene['clip_end']) - float(scene.get('clip_start', 0)), 2 / FPS):.3f}"]         if scene.get("clip_end") else []
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(scene.get("clip_start", 0)), *span,
         "-i", scene["clip"], "-loop", "1", "-i", png,
         "-filter_complex", f"[0:v]{vf}[c];[c][1:v]overlay=0:0,format=yuv420p",
         "-an", "-frames:v", str(frames_for(dur)), "-c:v", "libx264", out])
    return out


def render_shot(sh, dur, work, name, warnings):
    if sh.get("clip"):
        return clip_to_video(sh, dur, work, name)
    if sh.get("card"):
        stages = render_card(sh, dur)
    elif sh.get("stat") and sh["stat"].get("motion_clip"):
        return stages_over_clip(render_stat(sh, dur), sh["stat"]["motion_clip"],
                                float(sh["stat"].get("clip_start", 0)), dur, work, name)
    elif sh.get("stat"):
        stages = render_stat(sh, dur)
    elif sh.get("diagram") and sh["diagram"].get("motion_clip"):
        return stages_over_clip(render_diagram(sh, dur), sh["diagram"]["motion_clip"],
                                float(sh["diagram"].get("clip_start", 0)), dur, work, name)
    elif sh.get("diagram"):
        stages = render_diagram(sh, dur)
    elif sh.get("timeline"):
        stages = render_timeline(sh, dur)
    elif sh.get("summary"):
        stages = render_summary(sh, dur, warnings)
    elif sh.get("end_card"):
        stages = render_end_card(sh, warnings)
    elif sh.get("image"):
        stages = render_still(sh, warnings)
    else:
        stages = render_plain(sh)
    # Every shot creeps unless the manifest says otherwise.
    # Grain only on flat graphics, never on real images.
    # A shot that continues the previous one's image does not rerun its move:
    # "_run_move" (set by the planner) is the move of the first shot of the run.
    move = sh.get("_run_move", sh.get("move")) if sh.get("image") and not sh.get("card") else None
    bg = story_background(sh["_background"]) if sh.get("_background") else None
    return stages_to_video(stages, dur, work, name, creep=sh.get("_run_creep", sh.get("creep", "in")),
                           grain=not sh.get("image"), move=move,
                           keep_rect=sh.get("_keep_rect"), band_top=sh.get("_band_top", SAFE_TOP),
                           run_off=sh.get("_run_off", 0), run_frames=sh.get("_run_frames"),
                           hold=bool(sh.get("_run_hold")), bg=bg, bg_start=sh.get("_reel_start", 0.0))
