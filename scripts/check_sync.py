#!/usr/bin/env python3
"""
Check that the burned-in captions stay in sync with the voice.

Measures the finished reel, not the build's plan: speech is found in the
reel's own audio track, with a high-pass filter that removes the music bed
(it sits under 400 Hz), and compared with the caption events that were
burned in (the build's subs.ass). Captions are word by word: a phrase
appears with its first spoken word, each word is revealed as it is spoken,
and the phrase stays until the next one replaces it. Spans the build marked
as uncaptioned on purpose (the end card) are skipped.

Usage:
  python3 check_sync.py reel.mp4 --subs work/subs.ass [--json report.json]

Checks (each PASS or FAIL, with the times that fail):
  S1 Streams     video and audio start at 0 and end within one frame of each other.
  S2 Coverage    no stretch of speech over 0.3s has no caption on screen.
  S3 Lingering   no caption phrase stays up over 0.6s of silence (a pause, or
                 a caption left up after the voice stopped).
  S4 Clause sync every phrase change at the end of a clause (after , . ; :
                 ? !) falls in the voice's pause there, within 0.25s. With
                 Whisper, "there" is the pause just before the new phrase's
                 first spoken word, so a change that lands in the pause after
                 that word (shown late) fails; without it, the nearest pause.
                 A change with no pause within 1s is listed, not failed.
  S5 Word sync   needs faster-whisper or openai-whisper: every caption word
                 is revealed within 0.3s of being spoken (about 0.2s of
                 Whisper drift is normal), and caption words the recogniser
                 never heard are listed (a word TTS may have dropped or
                 slurred; check by ear). The first word after each pause is
                 timed from where the voice resumes in the audio, not from
                 Whisper, which often starts it at the previous word's end
                 (the build has the same blind spot, so both would agree on
                 a wrong time).
  S6 Anchoring   every caption word keeps one position for as long as its
                 phrase is up (it changes colour, never place), and no two
                 words of a phrase overlap.

Needs ffmpeg and ffprobe on PATH.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_common import FPS, run, probe_duration  # noqa: E402
from reel_subs import (speech_segments, read_ass, read_ass_words,  # noqa: E402
                       read_no_caption, whisper_words, snap_to_speech)

HIGHPASS = 300          # Hz; removes the music bed (sine pads under 400 Hz)
THRESHOLD = -35         # dB; speech vs the filtered remainder
MIN_PAUSE = 0.1         # s; shorter dips are not pauses
COVER_GAP = 0.3         # S2
LINGER = 0.6            # S3
CLAUSE_TOL = 0.25       # S4
CLAUSE_SEARCH = 1.0     # S4: how far to look for a pause
WORD_TOL = 0.3          # S5


def stream_times(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,start_time,duration",
             "-of", "json", path])
    out = {}
    for st in json.loads(r.stdout).get("streams", []):
        out[st["codec_type"]] = (float(st.get("start_time") or 0), float(st.get("duration") or 0))
    return out


def overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def silences_within(t0, t1, segs):
    """Silent stretches inside [t0, t1], given the speech segments."""
    gaps, t = [], t0
    for a, b in segs:
        if b <= t0:
            continue
        if a >= t1:
            break
        if a > t:
            gaps.append((t, min(a, t1)))
        t = max(t, b)
    if t < t1:
        gaps.append((t, t1))
    return gaps


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def anchoring(subs):
    """S6 from the ASS itself: each word's position never changes, and words of
    one phrase on the same line don't overlap (measured with the caption font)."""
    from PIL import Image, ImageDraw
    from reel_common import font, BOLD, CAPTION_SIZE
    f = font(BOLD, CAPTION_SIZE)
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    pos, text, bad = {}, {}, []
    with open(subs, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("Dialogue:"):
                continue
            parts = line.rstrip("\n").split(",", 9)
            m = re.search(r"\\pos\(([-\d.]+),([-\d.]+)\)", parts[9])
            name = parts[4]
            if not m or not re.fullmatch(r"p\d+w\d+", name):
                continue
            p = (float(m.group(1)), float(m.group(2)))
            if name in pos and pos[name] != p:
                bad.append(f"{name} moves from {pos[name]} to {p}")
            pos.setdefault(name, p)
            text[name] = re.sub(r"\{[^}]*\}", "", parts[9])
    phrases = {}
    for name, p in pos.items():
        pi, wi = map(int, re.findall(r"\d+", name))
        phrases.setdefault(pi, []).append((wi, p, text[name]))
    for ws in phrases.values():
        ws.sort()
        for (_, p0, t0), (_, p1, t1) in zip(ws, ws[1:]):
            if p0[1] == p1[1] and p0[0] + d.textlength(t0, font=f) > p1[0]:
                bad.append(f"{t0!r} overlaps {t1!r}")
    return bad, len(pos)


def check(reel, subs):
    events = read_ass(subs)
    skip = read_no_caption(subs)
    total = probe_duration(reel)
    segs = [(a, b) for a, b in speech_segments(reel, THRESHOLD, MIN_PAUSE, HIGHPASS)
            if b - a >= 0.05]
    pauses = [(segs[k][1], segs[k + 1][0]) for k in range(len(segs) - 1)]
    results = []

    # S1 streams
    st = stream_times(reel)
    v, a = st.get("video", (0, 0)), st.get("audio", (0, 0))
    s1 = abs(v[0]) < 1 / FPS and abs(a[0]) < 1 / FPS and abs(v[1] - a[1]) <= 1 / FPS + 0.03
    results.append(("S1", "Streams", s1, f"video starts {v[0]:.3f}s, {v[1]:.3f}s long; "
                                          f"audio starts {a[0]:.3f}s, {a[1]:.3f}s long"))

    # S2 coverage
    bad = []
    for s0, s1_ in segs:
        t = s0
        spans = [(e[0], e[1]) for e in events] + skip
        covered = sorted((max(e0, s0), min(e1, s1_)) for e0, e1 in spans if overlap(e0, e1, s0, s1_) > 0)
        for c0, c1 in covered + [(s1_, s1_)]:
            if c0 - t > COVER_GAP:
                bad.append(f"{t:.2f}-{c0:.2f}s")
            t = max(t, c1)
    spoken = sum(b - a for a, b in segs) - sum(overlap(k0, k1, a, b) for a, b in segs
                                               for k0, k1 in skip)
    cov = sum(overlap(e0, e1, a, b) for a, b in segs for e0, e1, _ in events) / max(spoken, 1e-9)
    skipped = ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in skip)
    results.append(("S2", "Coverage", not bad,
                    f"{100 * min(cov, 1):.0f}% of speech has a caption"
                    + (f" (end card skipped: {skipped})" if skip else "")
                    + (f"; uncaptioned speech at {', '.join(bad)}" if bad else "")))

    # S3 lingering
    bad = []
    for e0, e1, text in events:
        for g0, g1 in silences_within(e0, e1, segs):
            if g1 - g0 > LINGER:
                bad.append(f"{g0:.2f}-{g1:.2f}s under {text!r}")
    results.append(("S3", "Lingering", not bad,
                    "no caption over silence" if not bad else "; ".join(bad)))

    # S5 word sync: matched first, so S4 can use when each phrase is spoken
    cap_words = read_ass_words(subs)
    heard = whisper_words(reel)
    said = {}                         # caption word index -> time it is spoken
    if heard is None:
        s5_result = ("S5", "Word sync", None,
                     "not run: install faster-whisper or openai-whisper for word-level timing")
    else:
        import difflib
        heard = [(s, e, norm(w)) for s, e, w in heard if norm(w)]
        snapped = snap_to_speech([h[0] for h in heard], [h[1] for h in heard], segs)
        heard = [(t, e, w) for t, (_, e, w) in zip(snapped, heard)]
        ours = [norm(w) for _, w, _ in cap_words]
        sm = difflib.SequenceMatcher(a=ours, b=[w for _, _, w in heard], autojunk=False)
        bad = []
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                i, t = blk.a + k, heard[blk.b + k][0]
                said[i] = t
                off = cap_words[i][0] - t
                if abs(off) > WORD_TOL:
                    bad.append(f"{cap_words[i][1]!r} shows {cap_words[i][0]:.2f}s, spoken {t:.2f}s "
                               f"({'early' if off < 0 else 'late'} by {abs(off):.2f}s)")
        missing = [cap_words[i][1] for i in range(len(cap_words)) if i not in said and ours[i]]
        detail = f"{len(said)}/{len(cap_words)} caption words matched to speech"
        if bad:
            detail += ("; off by more than 0.3s (nudge just these words with caption_nudge): "
                       + "; ".join(bad))
        if missing:
            detail += ("; not matched (split figures such as $6.3 often land here; check by ear): "
                       + ", ".join(missing[:20]))
        s5_result = ("S5", "Word sync", not bad, detail)
    # phrase start (its first word's reveal) -> when that word is spoken
    first_spoken = {}
    for i, (t, _, _) in enumerate(cap_words):
        if i in said and (i == 0 or cap_words[i - 1][2] != cap_words[i][2]):
            first_spoken[round(t, 2)] = said[i]

    # S4 clause sync
    rows, worst, fails, unmatched = [], 0.0, [], []
    for (e0, e1, text), (n0, _, ntext) in zip(events, events[1:]):
        if abs(e1 - n0) > 0.05 or text.rstrip()[-1:] not in ",.;:?!":
            continue          # not a clause-end change (or a gap between events)
        sp = first_spoken.get(round(n0, 2))
        if sp is not None:
            # the pause the voice takes just before the phrase's first word
            near = [p for p in pauses if abs(p[1] - sp) <= CLAUSE_SEARCH]
            pick = lambda p: abs(p[1] - sp)                      # noqa: E731
        else:
            near = [p for p in pauses if p[1] >= n0 - CLAUSE_SEARCH and p[0] <= n0 + CLAUSE_SEARCH]
            pick = lambda p: (0 if p[0] - 0.1 <= n0 <= p[1] + 0.1     # noqa: E731
                              else min(abs(n0 - p[0]), abs(n0 - p[1])))
        if not near:
            unmatched.append(f"{n0:.2f}s before {ntext!r}")
            continue
        p = min(near, key=pick)
        off = 0.0 if p[0] - 0.1 <= n0 <= p[1] + 0.1 else (n0 - p[1] if n0 > p[1] else n0 - p[0])
        rows.append((n0, ntext, off, p))
        worst = max(worst, abs(off))
        if abs(off) > CLAUSE_TOL:
            fails.append(f"{ntext!r} at {n0:.2f}s, pause {p[0]:.2f}-{p[1]:.2f}s "
                         f"({'early' if off < 0 else 'late'} by {abs(off):.2f}s)")
    detail = f"{len(rows)} clause changes checked, worst {worst:.2f}s off"
    if fails:
        detail += "; " + "; ".join(fails)
    if unmatched:
        detail += f"; no pause found near {len(unmatched)} change(s): " + ", ".join(unmatched)
    results.append(("S4", "Clause sync", not fails, detail))

    results.append(s5_result)

    # S6 anchoring
    moved, n = anchoring(subs)
    results.append(("S6", "Anchoring", not moved,
                    f"{n} caption words, each at one fixed position" if not moved
                    else "; ".join(moved[:10])))

    return results, {"speech": segs, "events": events, "duration": total}


def report(reel, subs, json_path=None):
    """Print the checks; True if none failed."""
    if not os.path.exists(subs):
        print(f"FAIL: caption file not found: {subs}")
        return False
    results, data = check(reel, subs)
    print(f"Caption sync: {reel}")
    for code, name, ok, detail in results:
        mark = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        print(f"  {mark}: {code} {name}: {detail}")
    passed = all(ok is not False for _, _, ok, _ in results)
    print(f"  SYNC: {'PASS' if passed else 'FAIL'}")
    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"pass": passed,
                       "checks": [{"id": c, "name": n, "result": None if o is None else bool(o),
                                   "detail": d} for c, n, o, d in results], **data}, f, indent=1)
    return passed


def main():
    ap = argparse.ArgumentParser(description="Check burned-in captions against the voice.")
    ap.add_argument("reel")
    ap.add_argument("--subs", required=True, help="the subs.ass burned into the reel")
    ap.add_argument("--json", default=None, help="also write the measurements here")
    a = ap.parse_args()
    return 0 if report(a.reel, a.subs, a.json) else 1


if __name__ == "__main__":
    sys.exit(main())
