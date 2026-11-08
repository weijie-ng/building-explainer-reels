"""The reel's story background (SKILL.md, "Background").

Faint flat shapes in two fixed tints of the reel's blue, drawn by the build
behind every shot that would otherwise show plain blue: headline cards
without an image, stat shots without a motion clip, the timeline, the end
card and the space around an inset. Set once in the manifest:

  "background": {"preset": "posts"}
  "background": {"preset": "custom", "shapes": [...]}

The background runs on reel time, so it carries on across cuts instead of
restarting. Its tints are fixed here, so no preset or custom shape can come
out loud enough to compete with the headline. It is drawn, not generated:
no AI label.
"""

import json
import math
import random

from reel_common import *  # noqa: F401,F403


def _tint(a):
    """The reel's blue with a share a of white over it."""
    return tuple(round(c + (255 - c) * a) for c in BG)


SHAPE = _tint(0.10)          # card and document bodies, pipes, grid
DETAIL = _tint(0.22)         # bars, avatars, links, flow, the chart line
LIT = _tint(0.30)            # the brightest a pulse gets, briefly
TONES = {"shape": SHAPE, "detail": DETAIL}

PRESETS = {
    "posts": "faint post cards drifting up in step, lighting together now and then "
             "(social media, disinformation, coordinated campaigns)",
    "network": "points and links with slow pulses along them (cyber, tech, data)",
    "pipeline": "pipe runs with a slow flow inside and a tanker outline crossing "
                "(energy, shipping, commodities)",
    "ticker": "a chart line scrolling slowly over a faint grid (markets, companies, economy)",
    "papers": "document outlines drifting up, a stamp ring pressing onto one at a time "
              "(policy, legal, regulation)",
}
SHAPES = ("card", "doc", "circle", "ring", "bar", "line")
MAX_SHAPES = 40
MAX_DRIFT = 40               # px per second: slow enough to stay behind the text


# --- drawing helpers -----------------------------------------------------------

def _sprite(w, h, draw, ss=2):
    """An RGBA sprite drawn at ss times its size and scaled down, so edges are smooth."""
    from PIL import Image, ImageDraw
    big = Image.new("RGBA", (w * ss, h * ss), BG + (0,))
    draw(ImageDraw.Draw(big), ss)
    return big.resize((w, h), Image.LANCZOS)


def _place(canvas, sprite, x, y):
    """Alpha-composite sprite with its top-left at (x, y), sub-pixel, so slow
    motion glides instead of stepping a pixel at a time."""
    from PIL import Image
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    if fx or fy:
        w, h = sprite.size
        sprite = sprite.transform((w + 1, h + 1), Image.AFFINE, (1, 0, -fx, 0, 1, -fy),
                                  resample=Image.BICUBIC, fillcolor=BG + (0,))
    # alpha_composite needs a destination inside the canvas: crop off what
    # hangs over the top or left edge.
    sx, sy = max(0, -ix), max(0, -iy)
    if sx >= sprite.width or sy >= sprite.height or ix >= canvas.width or iy >= canvas.height:
        return
    canvas.alpha_composite(sprite, (ix + sx, iy + sy), (sx, sy))


def _shift(strip, dx, dy):
    """A W x H window of strip, starting at (dx, dy), sub-pixel."""
    from PIL import Image
    return strip.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy), resample=Image.BICUBIC)


def _post_card(w, h, detail=DETAIL):
    """A blank post card: avatar, name bar, two text bars, a short bar."""
    def draw(d, s):
        d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=16 * s, fill=SHAPE)
        r = 18 * s
        d.ellipse([20 * s, 20 * s, 20 * s + 2 * r, 20 * s + 2 * r], fill=detail)
        bar = 10 * s

        def b(x, y, length):
            d.rounded_rectangle([x * s, y * s, (x + length) * s, y * s + bar], radius=bar // 2,
                                fill=detail)
        b(68, 33, w * 0.5)
        b(20, 82, w - 40)
        b(20, 106, w - 60)
        b(20, 152, w * 0.4)
    return _sprite(w, h, draw)


def _doc(w, h):
    """A document outline: page with a folded corner, a title bar and text bars."""
    def draw(d, s):
        fold = 34 * s
        d.polygon([(0, 0), (w * s - fold, 0), (w * s - 1, fold), (w * s - 1, h * s - 1),
                   (0, h * s - 1)], fill=SHAPE)
        d.polygon([(w * s - fold, 0), (w * s - fold, fold), (w * s - 1, fold)], fill=DETAIL)
        bar = 10 * s
        y = 30
        for k, frac in enumerate((0.55, 0.85, 0.78, 0.85, 0.6, 0.8, 0.45)):
            hb = bar * (1.6 if k == 0 else 1)
            d.rounded_rectangle([22 * s, y * s, (22 + (w - 44) * frac) * s, y * s + hb],
                                radius=bar // 2, fill=DETAIL)
            y += 34 if k == 0 else 24
    return _sprite(w, h, draw)


def _stamp(r):
    """A stamp: an outer ring, an inner ring and a bar across the middle."""
    def draw(d, s):
        R = r * s
        d.ellipse([0, 0, 2 * R - 1, 2 * R - 1], outline=DETAIL, width=9 * s)
        d.ellipse([18 * s, 18 * s, 2 * R - 18 * s, 2 * R - 18 * s], outline=DETAIL, width=4 * s)
        d.rounded_rectangle([26 * s, R - 9 * s, 2 * R - 26 * s, R + 9 * s], radius=4 * s,
                            fill=DETAIL)
    return _sprite(2 * r, 2 * r, draw)


def _dot(r, color=DETAIL):
    def draw(d, s):
        d.ellipse([0, 0, 2 * r * s - 1, 2 * r * s - 1], fill=color)
    return _sprite(2 * r, 2 * r, draw)


def _tanker(w):
    """A tanker outline in profile: hull with a raked bow, deck house, funnel."""
    h = round(w * 0.28)

    def draw(d, s):
        hull_top = h * 0.55 * s
        d.polygon([(0, hull_top), (w * s - 1, hull_top), (w * 0.9 * s, h * s - 1),
                   (w * 0.05 * s, h * s - 1)], fill=SHAPE)
        d.rectangle([w * 0.06 * s, h * 0.18 * s, w * 0.24 * s, hull_top], fill=SHAPE)
        d.rectangle([w * 0.1 * s, 0, w * 0.15 * s, h * 0.2 * s], fill=DETAIL)
        for k in range(5):
            x = (0.3 + k * 0.12) * w * s
            d.rounded_rectangle([x, h * 0.42 * s, x + w * 0.08 * s, hull_top], radius=3 * s,
                                fill=DETAIL)
    return _sprite(w, h, draw)


def _pulse(t, period, length=0.6):
    """0..1..0 once every period seconds: a brief lift, then rest."""
    u = (t % period) / length
    return math.sin(math.pi * u) ** 2 if u < 1 else 0.0


# --- presets: each is built once, then frame(t) returns an RGB image --------------

class _Posts:
    """Post cards in staggered rows, drifting up in step like one feed, and
    lighting together briefly every few seconds."""
    CW, CH, PITCH, SPEED, PERIOD = 250, 200, 250, 14, 4.0

    def __init__(self, rng):
        self.period = 2 * self.PITCH                 # two rows: the stagger repeats
        self.strip = self._strip(_post_card(self.CW, self.CH))
        self.lit = self._strip(_post_card(self.CW, self.CH, detail=LIT))

    def _strip(self, card):
        """Staggered rows (two side cards, then one centre card), tall enough to scroll a period."""
        from PIL import Image
        strip = Image.new("RGBA", (W, H + 2 * self.period), BG + (255,))
        cols = [(-60, W - 190), (W // 2 - self.CW // 2,)]
        for row in range((H + 2 * self.period) // self.PITCH + 1):
            for x in cols[row % 2]:
                _place(strip, card, x, row * self.PITCH)
        return strip.convert("RGB")

    def frame(self, t):
        from PIL import Image
        dy = (self.SPEED * t) % self.period
        base = _shift(self.strip, 0, dy)
        a = _pulse(t, self.PERIOD)
        return Image.blend(base, _shift(self.lit, 0, dy), a) if a > 0.01 else base


class _Network:
    """Points on a loose grid, links to near neighbours, and small pulses
    travelling along some of the links."""
    SPEED = 45

    def __init__(self, rng):
        from PIL import Image, ImageDraw
        pts = []
        for gy in range(-1, H // 170 + 2):
            for gx in range(-1, W // 170 + 2):
                pts.append((gx * 170 + 85 + rng.uniform(-50, 50), gy * 170 + 85 + rng.uniform(-50, 50)))
        links = [(a, b) for i, a in enumerate(pts) for b in pts[i + 1:]
                 if math.dist(a, b) < 230]
        layer = Image.new("RGB", (W * 2, H * 2), BG)
        d = ImageDraw.Draw(layer)
        for a, b in links:
            d.line([(a[0] * 2, a[1] * 2), (b[0] * 2, b[1] * 2)], fill=SHAPE, width=6)
        for x, y in pts:
            r = rng.choice((9, 12, 16)) * 2
            d.ellipse([x * 2 - r, y * 2 - r, x * 2 + r, y * 2 + r], fill=DETAIL)
        self.base = layer.resize((W, H), Image.LANCZOS)
        rng.shuffle(links)
        self.runs = [(a, b, rng.uniform(0, 10)) for a, b in links[:len(links) // 3]]
        self.dot = _dot(5, LIT)

    def frame(self, t):
        img = self.base.convert("RGBA")
        for a, b, phase in self.runs:
            length = math.dist(a, b)
            u = ((t + phase) * self.SPEED) % (length * 3) / length   # travel, then rest
            if u <= 1:
                _place(img, self.dot, a[0] + (b[0] - a[0]) * u - 5, a[1] + (b[1] - a[1]) * u - 5)
        return img.convert("RGB")


class _Pipeline:
    """Pipe runs with flanges and a slow flow of dashes inside, and a tanker
    outline crossing on a faint waterline."""
    FLOW, TANKER_SPEED, PIPE = 30, 16, 22

    def __init__(self, rng):
        from PIL import Image, ImageDraw
        self.paths = []
        for y in (360, 660, 1180):
            y += rng.uniform(-30, 30)
            bend = rng.uniform(0.3, 0.7) * W
            drop = rng.choice((-1, 1)) * rng.uniform(60, 110)
            self.paths.append([(-40, y), (bend, y), (bend, y + drop), (W + 40, y + drop)])
        layer = Image.new("RGB", (W * 2, H * 2), BG)
        d = ImageDraw.Draw(layer)
        for path in self.paths:
            pts = [(x * 2, y * 2) for x, y in path]
            d.line(pts, fill=SHAPE, width=self.PIPE * 2, joint="curve")
            for (x0, y0), (x1, y1) in zip(path, path[1:]):
                seg = math.dist((x0, y0), (x1, y1))
                for k in range(1, int(seg // 150) + 1):
                    u = k * 150 / seg
                    x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                    hx, hy = (0, 20) if y0 == y1 else (20, 0)
                    d.line([((x - hx) * 2, (y - hy) * 2), ((x + hx) * 2, (y + hy) * 2)],
                           fill=DETAIL, width=12)
        wl = 960
        d.line([(0, wl * 2), (W * 2, wl * 2)], fill=SHAPE, width=4)
        self.base = layer.resize((W, H), Image.LANCZOS)
        self.waterline = wl
        self.tanker = _tanker(300)

    def frame(self, t):
        from PIL import ImageDraw
        img = self.base.convert("RGBA")
        d = ImageDraw.Draw(img)
        for path in self.paths:
            # The flow: an 18px dash every 48px along the pipe, moving with time.
            segs = list(zip(path, path[1:]))
            total = sum(math.dist(a, b) for a, b in segs)
            s = (t * self.FLOW) % 48
            while s < total:
                d.line([_along(segs, s), _along(segs, min(s + 18, total))], fill=DETAIL, width=6)
                s += 48
        # Starts mid-frame, sails left, and comes back in from the right.
        span = W + self.tanker.width + 40
        x = (W * 0.55 - t * self.TANKER_SPEED + self.tanker.width) % span - self.tanker.width
        _place(img, self.tanker, x, self.waterline - self.tanker.height + 6)
        return img.convert("RGB")


def _along(segs, s):
    """The point s pixels along a polyline given as segments."""
    for a, b in segs:
        n = math.dist(a, b)
        if s <= n:
            u = s / n if n else 0
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        s -= n
    return segs[-1][1]


class _Ticker:
    """A chart line over a faint grid, scrolling slowly left, with a dot
    riding the line at a fixed point like a live price."""
    PERIOD, SPEED, GRID = 1440, 24, 120

    def __init__(self, rng):
        from PIL import Image, ImageDraw
        n = self.PERIOD // 24
        walk, v = [0.0], 0.0
        for _ in range(n - 1):
            v = 0.7 * v + rng.uniform(-1, 1)
            walk.append(walk[-1] + v)
        drift = walk[-1] / (n - 1)                   # end where it starts, so the scroll loops
        walk = [w - drift * k for k, w in enumerate(walk)]
        lo, hi = min(walk), max(walk)
        mid, amp = 760, 230
        self.ys = [mid + amp - (w - lo) / max(hi - lo, 1e-6) * 2 * amp for w in walk]
        width = W + self.PERIOD + 24
        ss = 2
        layer = Image.new("RGB", (width * ss, H * ss), BG)
        d = ImageDraw.Draw(layer)
        for x in range(0, width, self.GRID):
            d.line([(x * ss, 0), (x * ss, H * ss)], fill=SHAPE, width=2 * ss)
        for y in range(40, H, self.GRID):
            d.line([(0, y * ss), (width * ss, y * ss)], fill=SHAPE, width=2 * ss)
        pts = [(k * 24 * ss, self.ys[k % n] * ss) for k in range(width // 24 + 2)]
        d.line(pts, fill=DETAIL, width=6 * ss, joint="curve")
        self.strip = layer.resize((width, H), Image.LANCZOS)
        self.n = n
        self.dot = _dot(9, LIT)

    def y_at(self, x):
        k, u = divmod(x / 24, 1)
        k = int(k)
        return self.ys[k % self.n] * (1 - u) + self.ys[(k + 1) % self.n] * u

    def frame(self, t):
        dx = (self.SPEED * t) % self.PERIOD
        img = _shift(self.strip, dx, 0).convert("RGBA")
        x = W * 0.72
        _place(img, self.dot, x - 9, self.y_at(x + dx) - 9)
        return img.convert("RGB")


class _Papers:
    """Document outlines at slight angles drifting up at their own pace, and a
    stamp ring pressing onto one of them every few seconds."""
    PERIOD, PRESS, FADE = 3.2, 0.35, 0.4

    def __init__(self, rng):
        from PIL import Image
        self.docs = []
        slots = [(70, 0.05), (400, 0.2), (180, 0.45), (470, 0.62), (40, 0.8), (330, 0.95)]
        for x, frac in slots:
            sprite = _doc(220, 280).rotate(rng.uniform(-9, 9), expand=True,
                                           resample=Image.BICUBIC, fillcolor=BG + (0,))
            self.docs.append((sprite, x + rng.uniform(-20, 20), frac * (H + 320),
                              rng.uniform(9, 14)))
        self.stamp = _stamp(64)

    def _doc_pos(self, k, t):
        sprite, x, y0, v = self.docs[k]
        span = H + sprite.height
        return sprite, x, (y0 - v * t) % span - sprite.height

    def frame(self, t):
        from PIL import Image
        img = Image.new("RGBA", (W, H), BG + (255,))
        for k in range(len(self.docs)):
            sprite, x, y = self._doc_pos(k, t)
            _place(img, sprite, x, y)
        cycle, u = divmod(t, self.PERIOD)
        # Stamp the document nearest the middle of the frame at the press.
        t_press = cycle * self.PERIOD
        k = min(range(len(self.docs)),
                key=lambda j: abs(self._doc_pos(j, t_press)[2] + 140 - H * 0.55))
        sprite, x, y = self._doc_pos(k, t)
        if u < self.PERIOD - self.FADE:
            p = min(u / self.PRESS, 1.0)
            alpha = p
        else:
            p, alpha = 1.0, (self.PERIOD - u) / self.FADE
        scale = 1.25 - 0.25 * (1 - (1 - p) ** 3)
        size = max(2, round(self.stamp.width * scale))
        st = self.stamp.resize((size, size), Image.BICUBIC)
        if alpha < 1:
            st.putalpha(st.getchannel("A").point(lambda v: round(v * alpha)))
        cx, cy = x + sprite.width / 2, y + sprite.height * 0.62
        _place(img, st, cx - size / 2, cy - size / 2)
        return img.convert("RGB")


class _Custom:
    """Shapes listed in the manifest, each optionally drifting and wrapping
    around the frame."""

    def __init__(self, spec):
        self.items = []
        for sh in spec.get("shapes", []):
            kind = sh["shape"]
            tone = TONES[sh.get("tone", "detail" if kind in ("bar", "line", "ring") else "shape")]
            if kind == "line":
                self.items.append(("line", sh, tone))
                continue
            if kind == "card":
                sprite = _post_card(int(sh.get("w", 250)), int(sh.get("h", 200)))
            elif kind == "doc":
                sprite = _doc(int(sh.get("w", 220)), int(sh.get("h", 280)))
            elif kind in ("circle", "ring"):
                r = int(sh.get("r", 40))

                def draw(d, s, r=r, kind=kind, tone=tone):
                    box = [0, 0, 2 * r * s - 1, 2 * r * s - 1]
                    if kind == "circle":
                        d.ellipse(box, fill=tone)
                    else:
                        d.ellipse(box, outline=tone, width=max(2, r // 6) * s)
                sprite = _sprite(2 * r, 2 * r, draw)
            else:   # bar
                w, h = int(sh.get("w", 200)), int(sh.get("h", 12))

                def draw(d, s, w=w, h=h, tone=tone):
                    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=h * s // 2, fill=tone)
                sprite = _sprite(w, h, draw)
            if sh.get("angle"):
                from PIL import Image
                sprite = sprite.rotate(float(sh["angle"]), expand=True, resample=Image.BICUBIC,
                                       fillcolor=BG + (0,))
            self.items.append(("sprite", sh, sprite))

    def frame(self, t):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (W, H), BG + (255,))
        for kind, sh, obj in self.items:
            dx, dy = (sh.get("drift") or (0, 0))
            x, y = sh["x"] * W + dx * t, sh["y"] * H + dy * t
            if kind == "line":
                x1, y1 = sh["to"][0] * W + dx * t, sh["to"][1] * H + dy * t
                if dx or dy:   # wrap the line's start into the frame, keep its length
                    nx, ny = (x % (W + 200)) - 100, (y % (H + 200)) - 100
                    x1, y1, x, y = x1 + nx - x, y1 + ny - y, nx, ny
                ImageDraw.Draw(img).line([(x, y), (x1, y1)], fill=obj,
                                         width=int(sh.get("width", 6)))
                continue
            w, h = obj.size
            if dx or dy:
                x = (x + w) % (W + w) - w
                y = (y + h) % (H + h) - h
            _place(img, obj, x - w / 2, y - h / 2)
        return img.convert("RGB")


def uses_background(sh):
    """Whether a shot shows the story background: every shot that would
    otherwise show plain blue. Clips, diagrams (they have their own motion
    clip), stat shots with a motion clip, headline cards with an image, and
    stills (blurred fill) don't; a still with an inset move does, around the
    inset."""
    if sh.get("clip") or sh.get("diagram"):
        return False
    if sh.get("card"):
        return not sh["card"].get("image")
    if sh.get("stat"):
        return not sh["stat"].get("motion_clip")
    if sh.get("timeline") or sh.get("summary") or sh.get("end_card"):
        return True
    if sh.get("image"):
        return sh.get("_run_move", sh.get("move")) == "inset"
    return True


_BUILDERS = {"posts": _Posts, "network": _Network, "pipeline": _Pipeline,
             "ticker": _Ticker, "papers": _Papers}
_CACHE = {}


def background(spec):
    """The background for a manifest "background" spec, built once per spec."""
    key = json.dumps(spec, sort_keys=True)
    if key not in _CACHE:
        preset = spec.get("preset")
        if preset == "custom":
            _CACHE[key] = _Custom(spec)
        else:
            _CACHE[key] = _BUILDERS[preset](random.Random(spec.get("seed", 1)))
    return _CACHE[key]


def spec_problems(spec):
    """What is wrong with a manifest "background" spec ([] when it is fine)."""
    if not isinstance(spec, dict):
        return ['"background" must be an object, e.g. {"preset": "posts"}.']
    preset = spec.get("preset")
    if preset not in PRESETS and preset != "custom":
        return [f'background "preset" must be one of {sorted(PRESETS)} or "custom", '
                f"got {preset!r}."]
    if "seed" in spec and not isinstance(spec["seed"], int):
        return [f'background "seed" must be a whole number, got {spec["seed"]!r}.']
    if preset != "custom":
        return []
    shapes = spec.get("shapes")
    if not isinstance(shapes, list) or not shapes:
        return ['a "custom" background needs a "shapes" list.']
    if len(shapes) > MAX_SHAPES:
        return [f"a custom background has at most {MAX_SHAPES} shapes, got {len(shapes)}."]
    errors = []
    for n, sh in enumerate(shapes, 1):
        where = f"background shape {n}"
        if not isinstance(sh, dict) or sh.get("shape") not in SHAPES:
            errors.append(f"{where}: 'shape' must be one of {list(SHAPES)}.")
            continue
        if not all(isinstance(sh.get(k), (int, float)) and -0.5 <= sh[k] <= 1.5 for k in ("x", "y")):
            errors.append(f"{where}: 'x' and 'y' are fractions of the frame (0-1).")
        if sh.get("tone", "shape") not in TONES:
            errors.append(f"{where}: 'tone' is \"shape\" or \"detail\"; the tints are fixed.")
        if sh["shape"] == "line":
            to = sh.get("to")
            if not (isinstance(to, (list, tuple)) and len(to) == 2
                    and all(isinstance(v, (int, float)) for v in to)):
                errors.append(f"{where}: a line needs 'to': [x, y] as fractions of the frame.")
        for k in ("w", "h", "r", "width"):
            if k in sh and not (isinstance(sh[k], (int, float)) and 2 <= sh[k] <= W):
                errors.append(f"{where}: '{k}' is a size in pixels (2-{W}), got {sh[k]!r}.")
        drift = sh.get("drift")
        if drift is not None:
            if not (isinstance(drift, (list, tuple)) and len(drift) == 2
                    and all(isinstance(v, (int, float)) for v in drift)):
                errors.append(f"{where}: 'drift' is [dx, dy] in pixels per second.")
            elif math.hypot(*drift) > MAX_DRIFT:
                errors.append(f"{where}: drift {math.hypot(*drift):.0f}px/s is too fast to stay "
                              f"behind the text; keep it at or under {MAX_DRIFT}px/s.")
    return errors
