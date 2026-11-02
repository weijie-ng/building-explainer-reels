"""Pace and variety report: does the reel play as a video or as a slideshow?

Every checklist item can pass while the reel still reads as a slideshow: a
run of still images, each small on blurred fill under a headline, the same
picture coming back, nothing on screen acting out the line. This report
measures those patterns from the plan, so the builder
sees them at the dry run, before any asset is final, and the verifier can
check them against the shot list (D12).

Shot kinds:
  video  a real or AI clip (it moves by itself)
  built  a graphic the build animates on the narrated words: headline card,
         diagram, timeline, stat
  still  a still image (creep, push, pan or inset only)
  end    the end card (not counted)
"""

from reel_common import *  # noqa: F401,F403

STILL_SHARE_MAX = 0.5      # stills may hold at most half the reel's time (end excluded)
STILL_STREAK_MAX = 6.0     # seconds of back-to-back still images
SAME_VISUAL_MAX = 4.0      # seconds one still image stays on screen across super changes
COVERAGE_MIN = 0.40        # a still image should cover at least 40% of the frame
VIDEO_EVERY = 15.0         # at least one video shot per ~15s (minimum 2)


def shot_kind(sh):
    if sh.get("end_card") or sh.get("summary"):
        return "end"
    if sh.get("clip"):
        return "video"
    if any(sh.get(k) for k in ("card", "diagram", "timeline", "stat")):
        return "built"
    if sh.get("image"):
        return "still"
    return "plain"


def coverage(sh):
    """Fraction of the 720x1280 frame the still image itself covers (not
    its blurred fill), or None for other shots."""
    if shot_kind(sh) != "still":
        return None
    from PIL import Image
    from reel_render import still_layout
    try:
        with Image.open(sh["image"]) as im:
            iw, ih = im.size
        _, _, _, s, x, y, _ = still_layout(sh, (iw, ih), [])
    except Exception:
        return None
    vis_w = max(0.0, min(W, x + s * iw) - max(0.0, x))
    vis_h = max(0.0, min(H, y + s * ih) - max(0.0, y))
    return vis_w * vis_h / (W * H)


def asset_of(sh):
    return sh.get("clip") or sh.get("image")


def pace_report(shots):
    """shots: [(beat index, shot index, shot dict, duration, name), ...] in
    order. Returns (rows, warnings); each row is one shot's kind, asset and
    coverage, for the printed table and the shot list."""
    rows, warnings, t = [], [], 0.0
    for i, j, sh, dur, name in shots:
        rows.append({"name": name, "start": t, "end": t + dur, "dur": dur, "kind": shot_kind(sh),
                     "asset": asset_of(sh), "coverage": coverage(sh), "wipe": bool(sh.get("wipe")),
                     "where": f"beat {sh.get('id', i)} shot {j + 1}"})
        t += dur
    body = [r for r in rows if r["kind"] != "end"]
    total = sum(r["dur"] for r in body) or 1.0

    still = sum(r["dur"] for r in body if r["kind"] == "still")
    if still / total > STILL_SHARE_MAX:
        warnings.append(f"pace: still images hold {100 * still / total:.0f}% of the reel's time "
                        f"(limit {100 * STILL_SHARE_MAX:.0f}%); it will play as a slideshow. Turn "
                        "AI stills into Muse video (the still as the start frame), use footage, "
                        "or show figures and chains as built graphics (stat, diagram).")
    videos = sum(1 for r in body if r["kind"] == "video")
    need = max(2, round(total / VIDEO_EVERY))
    if videos < need:
        warnings.append(f"pace: {videos} video shot(s) in {total:.0f}s; aim for at least {need} "
                        "(the hook first, then the concept and scale lines).")

    streak, start = 0.0, None
    for r in body + [{"kind": "stop", "dur": 0, "where": ""}]:
        if r["kind"] == "still":
            streak, start = streak + r["dur"], start or r["where"]
            continue
        if streak > STILL_STREAK_MAX:
            warnings.append(f"pace: {streak:.1f}s of still images back to back from {start}; "
                            "put a clip or a built graphic in the middle.")
        streak, start = 0.0, None

    seen = {}
    prev = None
    for r in body:
        a = r["asset"]
        if a:
            seen.setdefault(a, []).append(r)
            if prev is not None and prev.get("asset") != a and len(seen[a]) > 1:
                warnings.append(f"pace: {os.path.basename(a)} comes back at {r['where']} after "
                                "other shots; a returning picture reads as a loop. Use a different "
                                "visual for the new line.")
        prev = r
    for a, rs in seen.items():
        if len(rs) > 2:
            warnings.append(f"pace: {os.path.basename(a)} is in {len(rs)} shots (limit 2, super "
                            "changes included).")

    k = 0
    while k < len(body):
        r = body[k]
        n, dur = k + 1, r["dur"]
        while n < len(body) and body[n]["asset"] and body[n]["asset"] == r["asset"]:
            dur += body[n]["dur"]
            n += 1
        if r["kind"] == "still" and n - k > 1 and dur > SAME_VISUAL_MAX + 1 / FPS:
            warnings.append(f"pace: {os.path.basename(r['asset'])} stays on screen {dur:.1f}s from "
                            f"{r['where']} (limit {SAME_VISUAL_MAX:.0f}s); a new headline over the "
                            "same picture is not a visual change.")
        k = n

    for r in body:
        if r["coverage"] is not None and r["coverage"] < COVERAGE_MIN:
            warnings.append(f"pace: {r['where']}: the image covers only {100 * r['coverage']:.0f}% of "
                            "the frame (the rest is blurred fill). Tighten its keep box to the detail "
                            "that matters, crop the source to it, or choose a taller visual.")

    if total > 30 and not any(r["wipe"] for r in rows):
        warnings.append("pace: no graphic wipe; give the first shot of one or two new sections "
                        "\"wipe\": \"left\" (or \"up\") so the turn reads on screen.")
    return rows, warnings


def print_table(rows, out=sys.stdout):
    print("Pace (kind: video | built | still | end; cover = share of frame the still covers):",
          file=out)
    for r in rows:
        cov = f"{100 * r['coverage']:3.0f}%" if r["coverage"] is not None else "   -"
        asset = os.path.basename(r["asset"]) if r["asset"] else ""
        print(f"  {r['start']:6.2f}-{r['end']:6.2f}s  {r['kind']:5s} cover {cov}"
              f"{'  wipe' if r['wipe'] else ''}  {r['where']}  {asset}", file=out)
    body = [r for r in rows if r["kind"] != "end"]
    total = sum(r["dur"] for r in body) or 1.0
    share = {k: sum(r["dur"] for r in body if r["kind"] == k) / total for k in ("video", "built", "still")}
    print("  time share: " + ", ".join(f"{k} {100 * v:.0f}%" for k, v in share.items()), file=out)
