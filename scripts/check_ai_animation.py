#!/usr/bin/env python3
"""
Check an AI animation of a script-made graphic against the graphic itself.

When Muse animates a finished diagram (image + prompt), it redraws every
frame. It often keeps the opening frames faithful and then drifts: the
camera zooms and cuts words at the edge, text is re-rendered or fades,
frames and borders appear. This measures, frame by frame, how far the
clip has moved from the source image where the source has text and lines,
and reports the usable span: from the start until the text first changes.

Usage:
  python3 check_ai_animation.py SOURCE.png CLIP.mp4 [--json out.json] [--strip out.png]

Output: the usable span (seconds), per-second drift, where the clip adds
things (the animation's own events, such as a cross being drawn, with
their times), and a PASS if at least --min-usable seconds are usable.
Use the span as the shot's "clip_end" and an event time as "event_at" in
the manifest (see references/graphics-and-clips.md, "AI animation of a finished diagram").

Needs ffmpeg and Pillow. Compares at 180x320 greyscale, so it is fast and
ignores compression noise.
"""

import argparse
import json
import os
import subprocess
import sys

SW, SH = 180, 320          # comparison size (9:16)
TEXT_DRIFT = 0.10          # mean change on the source's text/lines (0-1) that counts as drift
RUN = 3                    # consecutive drifting frames before the span ends
EVENT_JUMP = 0.004         # rise in "new pixels" fraction that marks an event
FPS = 30


def source_gray(path):
    from PIL import Image, ImageOps
    im = Image.open(path).convert("RGB")
    return ImageOps.fit(im, (SW, SH)).convert("L")


def text_mask(gray):
    """Where the source has text and lines: strong edges, slightly dilated."""
    from PIL import ImageFilter
    edges = gray.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0)
    return edges.filter(ImageFilter.MaxFilter(3))


def frames(clip):
    """Greyscale frames of the clip at 30 fps, at the comparison size."""
    from PIL import Image
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", clip, "-an", "-vf",
                          f"fps={FPS},scale={SW}:{SH}:force_original_aspect_ratio=increase,"
                          f"crop={SW}:{SH},format=gray", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE)
    size = SW * SH
    while True:
        raw = p.stdout.read(size)
        if len(raw) < size:
            break
        yield Image.frombytes("L", (SW, SH), raw)
    p.wait()


def measure(source, clip):
    from PIL import ImageChops, ImageStat
    src = source_gray(source)
    mask = text_mask(src)
    inv = mask.point(lambda v: 0 if v else 255)
    mask_n = max(ImageStat.Stat(mask).sum[0] / 255, 1)
    inv_n = max(ImageStat.Stat(inv).sum[0] / 255, 1)
    rows = []
    for k, fr in enumerate(frames(clip)):
        diff = ImageChops.difference(fr, src)
        on_text = ImageStat.Stat(diff, mask).sum[0] / mask_n / 255
        # Pixels clearly changed away from the source's text and lines: new
        # marks, arrows, glows -- the animation itself, or invented extras.
        changed = diff.point(lambda v: 255 if v > 50 else 0)
        new_px = ImageStat.Stat(changed, inv).sum[0] / 255 / inv_n
        rows.append((k / FPS, on_text, new_px))
    return rows


def analyse(rows, min_usable):
    end, run = None, 0
    for t, drift, _ in rows:
        run = run + 1 if drift > TEXT_DRIFT else 0
        if run >= RUN:
            end = max(0.0, t - (RUN - 1) / FPS)
            break
    total = rows[-1][0] + 1 / FPS if rows else 0.0
    usable = end if end is not None else total
    events, prev = [], None
    for t, _, new in rows:
        if t > usable:
            break
        if prev is not None and new - prev > EVENT_JUMP:
            if not events or t - events[-1][0] > 0.3:
                events.append((round(t, 2), round(new, 3)))
        prev = new
    return {"duration": round(total, 2), "usable_end": round(usable, 2),
            "drift_starts": None if end is None else round(end, 2),
            "events": events, "pass": usable >= min_usable}


def strip(clip, out, usable_end):
    """A contact strip at 2 fps, for looking at what the clip does."""
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-vf",
                    "fps=2,scale=160:-1,tile=10x2", "-frames:v", "1", out], check=False)


def main():
    ap = argparse.ArgumentParser(description="Find how much of an AI animation still matches its source graphic.")
    ap.add_argument("source")
    ap.add_argument("clip")
    ap.add_argument("--min-usable", type=float, default=1.0,
                    help="seconds of faithful animation needed for a PASS (default 1.0)")
    ap.add_argument("--json", default=None)
    ap.add_argument("--strip", default=None)
    a = ap.parse_args()
    rows = measure(a.source, a.clip)
    if not rows:
        sys.exit("No frames read from the clip.")
    res = analyse(rows, a.min_usable)
    print(f"AI animation check: {a.clip}\n  against: {a.source}")
    print(f"  clip {res['duration']}s; text and lines match the source until "
          f"{res['usable_end']}s" + ("" if res["drift_starts"] is None else
                                     f" (then they drift: zoom, crop, re-rendered or faded text)"))
    print("  drift on text/lines by second: " + "  ".join(
        f"{int(t)}s:{d:.2f}" for t, d, _ in rows if abs(t - round(t)) < 1e-6))
    if res["events"]:
        print("  animation events (new marks appear): " + ", ".join(f"{t}s" for t, _ in res["events"]))
    print(f"  {'PASS' if res['pass'] else 'FAIL'}: {res['usable_end']}s usable "
          f"(need {a.min_usable}s). Use clip_end {res['usable_end']} in the manifest; "
          "look at the strip to confirm what each event is.")
    if a.strip:
        strip(a.clip, a.strip, res["usable_end"])
        print(f"  strip: {a.strip}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({**res, "frames": [{"t": round(t, 3), "text_drift": round(d, 4),
                                          "new": round(n, 4)} for t, d, n in rows]}, f, indent=1)
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
