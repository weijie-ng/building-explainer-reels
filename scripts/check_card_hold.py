#!/usr/bin/env python3
"""
Check that the end card stays on screen long enough to read, measured on
the rendered reel.

An end card with summary panels brings its panels in one after another. If
the shot is short, the reel ends just as the last panel lands, so the
finished card is never seen. The build plans against this (references/end-card.md,
"Timing"); this script measures what actually rendered.

For an end card with panels ("summary" in the shot list), it finds the last
panel landing: the last sudden jump between consecutive frames below the
caption band (so the word-by-word captions above don't count, and a slow
creep never does). The hold is the time from that frame to the end. For an
end card without panels, the hold is the shot's measured length.

Usage:
  python3 check_card_hold.py REEL.mp4 --shots WORKDIR/shot_list.json [--json out.json]

PASS needs: panel hold >= max(SUMMARY_HOLD_MIN, SUMMARY_HOLD_PER_PANEL x
panels); end card >= END_CARD_HOLD_MIN (constants in reel_common.py).
Needs ffmpeg and numpy.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_common import (W, H, FPS, CAPTION_TOP, CAPTION_LINES, CAPTION_LINE_H,  # noqa: E402
                         CAPTION_CLEAR, SUMMARY_HOLD_MIN, SUMMARY_HOLD_PER_PANEL,
                         END_CARD_HOLD_MIN)

SW, SH = 180, 320           # comparison size (9:16)
PIXEL_DIFF = 40             # grey levels: above grain and compression noise
CHANGED_SHARE = 0.004       # share of compared pixels that counts as "not finished yet"


def frames(reel, start, end):
    import numpy as np
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", reel, "-t", f"{end - start:.3f}",
           "-vf", f"scale={SW}:{SH},format=gray", "-r", str(FPS), "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, SH, SW).astype(np.int16)


def summary_hold(reel, start, end):
    """Seconds, at the end of the shot, during which the frame matches the
    finished card below the caption band."""
    f = frames(reel, start, end)
    if len(f) < 2:
        return 0.0
    top = int((CAPTION_TOP + CAPTION_LINES * CAPTION_LINE_H + CAPTION_CLEAR) * SH / H)
    region = f[:, top:, :]
    # A panel landing is a jump between two consecutive frames; a slow creep
    # never is, so the card may creep while it holds.
    jumps = (abs(region[1:] - region[:-1]) > PIXEL_DIFF).mean(axis=(1, 2)) > CHANGED_SHARE
    hits = jumps.nonzero()[0]
    landed = hits[-1] + 1 if len(hits) else 0     # first frame of the finished card
    # A plain float, so the PASS flags derived from it can be written to JSON.
    return float(len(region) - landed) / FPS


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reel")
    ap.add_argument("--shots", required=True, help="shot_list.json from the build workdir")
    ap.add_argument("--json", help="write the results here")
    a = ap.parse_args()
    with open(a.shots, encoding="utf-8") as fh:
        shots = json.load(fh)["shots"]
    rows, ok = [], True
    for s in shots:
        if s["visual"] not in ("summary", "end_card"):
            continue
        where = f"beat {s['beat']} shot {s['shot']} ({s['start']:.2f}-{s['end']:.2f}s)"
        if s["visual"] == "summary":
            n = s.get("panels") or 0
            need = max(SUMMARY_HOLD_MIN, SUMMARY_HOLD_PER_PANEL * n)
            held = summary_hold(a.reel, s["start"], s["end"])
            what = f"end card, {n} summary panels"
        else:
            need, held, what = END_CARD_HOLD_MIN, s["end"] - s["start"], "end card"
        passed = held + 1 / FPS >= need
        ok = ok and passed
        rows.append({"beat": s["beat"], "shot": s["shot"], "visual": s["visual"],
                     "start": s["start"], "end": s["end"], "held": round(held, 2),
                     "needed": round(need, 2), "pass": passed})
        print(f"{'PASS' if passed else 'FAIL'}  {where}: {what} readable for {held:.2f}s "
              f"(needs {need:.1f}s)")
    if not rows:
        print("No end card in the shot list; nothing to check.")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"pass": ok, "shots": rows}, fh, indent=1)
    print("Card hold:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
