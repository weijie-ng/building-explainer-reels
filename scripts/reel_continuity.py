"""Continuity across cuts: when a shot carries on the previous shot's visual,
its animation carries on too instead of restarting.

Each shot is rendered as its own mp4 on its own clock (t = f/FPS from 0), so
nothing carries over a cut unless the planner passes it. expand_shots never
inherits visual keys, so continuity is never inferred from the manifest
alone: Continuity.link() compares each shot with the one before it (same
beat or the next beat) and writes "_"-prefixed fields into the shot dict.
They are part of the shot cache key, so a changed predecessor re-renders its
follower. What continues:

- clip / diagram.motion_clip: same file (and keep, clip_mask): the follower
  starts where the predecessor ended (clip_start + duration) unless it sets
  its own clip_start.
- still: same image, keep, full_bleed, material and identical layout: the
  base layer carries on from the transform it ended on (creep or move run on
  the run's own clock: _run_off, _run_frames, _run_move). Same image but a
  different layout (a taller headline moves band_top): the image cannot carry
  on, so the follower starts its own creep from 100% and does not rerun the move.
- card: same outlet, headline, key sentence and image: starts with the words
  that were lit at the end of the predecessor (_card_lit).
- timeline: the event list repeats the earlier events: they are drawn at once
  (_timeline_shown) at the run's common spacing (_timeline_extra); only new
  ones appear.
- diagram: the node list starts with the earlier nodes: nodes already shown
  stay (_diagram_shown), a drawn X stays drawn (_diagram_cross), and the run
  shares one geometry (_diagram_n).
- summary: same summary: panels already shown stay (_summary_shown).
Diagrams, timelines, cards and summaries also continue the base creep."""

from reel_common import *  # noqa: F401,F403
from reel_render import (still_layout, card_times, card_lit_end, timeline_layout, x_stage,
                         summary_panels_shown)


def kind_of(sh):
    """The renderer a shot goes to (same order as render_shot)."""
    for k in ("clip", "card", "diagram", "timeline", "summary", "end_card", "image"):
        if sh.get(k):
            return "still" if k == "image" else k
    return "plain"


def layout_sig(sh):
    """Where the image lands, rounded; None if it can't be worked out."""
    from PIL import Image
    try:
        with Image.open(sh["image"]) as im:
            size = im.size
        _, band, _, s, x, y, mode = still_layout(sh, size, [])
        return (round(band, 1), round(s, 4), round(x, 1), round(y, 1), mode)
    except Exception:
        return None


class Continuity:
    def __init__(self):
        self.prev = None        # the previous shot's record
        self.records = []
        self.diagrams = []      # (nodes, shown, crossed, cross_at), every diagram shot so far

    @staticmethod
    def run_creep(rec):
        """The creep mode a run is moving with at this record: a hold keeps
        the mode of the shots before it."""
        return rec.get("mode") or rec["sh"].get("creep", "in")

    def link(self, beat, sh, dur, where, warnings):
        kind = kind_of(sh)
        prev = self.prev
        near = prev is not None and prev["kind"] == kind and beat - prev["beat"] <= 1
        p = prev["sh"] if near else None
        rec = {"beat": beat, "sh": sh, "kind": kind, "dur": dur, "run": False, "end": {}}
        # A "creep": "none" shot inside a run holds the run's current frame
        # (finish() gives it the run's mode and stops its clock), so it never
        # snaps back to 100%; otherwise the creep modes must match.
        same_creep = bool(p) and (sh.get("creep", "in") == "none" or
                                  sh.get("creep", "in") == self.run_creep(prev))

        if kind == "clip":
            rec["end"]["start"] = float(sh.get("clip_start", 0))
            if p and all(sh.get(k) == p.get(k) for k in ("clip", "keep", "clip_mask")):
                if "clip_start" not in sh:
                    sh["clip_start"] = round(prev["end"]["start"] + prev["dur"], 3)
                    sh["_clip_cont"] = True
                    rec["end"]["start"] = sh["clip_start"]
        elif kind == "still":
            if p and all(sh.get(k) == p.get(k) for k in ("image", "keep", "full_bleed", "material",
                                                           "_hook")):
                sig = layout_sig(sh)
                rec["end"]["sig"] = sig
                if sig is not None and sig == prev["end"].get("sig"):
                    rec["run"] = same_creep
                else:
                    sh["_run_move"] = None
                    warnings.append(f"{where}: same image as the previous shot, but this shot's "
                                    "header changes where the image sits, so it cannot carry on "
                                    "from the previous transform. It starts its own gentle creep "
                                    "from 100% and does not rerun the move. Keep the headline's "
                                    "line count the same across the shots to avoid the jump.")
            else:
                rec["end"]["sig"] = layout_sig(sh) if sh.get("image") else None
        elif kind == "card":
            c, pc = sh["card"], (p or {}).get("card", {})
            if p and all(c.get(k) == pc.get(k) for k in ("outlet", "headline", "key_sentence",
                                                          "image")):
                sh["_card_lit"] = prev["end"]["lit"]
                rec["run"] = same_creep
            rec["end"]["lit"] = card_lit_end(card_times(sh, dur), dur)
        elif kind == "timeline":
            ev, pev = sh["timeline"]["events"], ((p or {}).get("timeline") or {}).get("events", [])
            if p and pev and ev[:len(pev)] == pev:
                sh["_timeline_shown"] = len(pev)
                rec["run"] = same_creep
            try:
                rec["end"]["extra"] = timeline_layout(sh)[2]
            except ValueError:
                rec["end"]["extra"] = None      # render reports it
        elif kind == "summary":
            if p and sh["summary"] == p["summary"]:
                sh["_summary_shown"] = prev["end"]["shown"]
                rec["run"] = same_creep
            rec["end"]["shown"] = summary_panels_shown(sh, dur)
        elif kind == "diagram":
            self.link_diagram(sh, dur, where, warnings, rec, prev if near else None, same_creep)

        mode = sh.get("creep", "in")
        rec["mode"] = self.run_creep(prev) if rec["run"] and mode == "none" else mode
        self.prev = rec
        self.records.append(rec)

    def link_diagram(self, sh, dur, where, warnings, rec, prev, same_creep):
        d = sh["diagram"] = dict(sh["diagram"])         # the manifest's own dict stays untouched
        key = tuple(d["nodes"])
        stage = d.get("stage", len(key))
        cross_at = d.get("cross_after", 1 if len(key) > 2 else 0)
        shown, crossed = 0, False
        for nodes, n, x, at in reversed(self.diagrams):
            if key[:len(nodes)] == nodes:
                shown = n
                crossed = x and nodes == key and at == cross_at
                break
        sh["_diagram_shown"] = shown
        if crossed and stage == "X":
            sh["_diagram_cross"] = True
        count = len(key) if stage == "X" else int(stage)
        if count < shown:
            warnings.append(f"{where}: diagram drops from {shown} to {count} nodes; "
                            "it will jump backwards.")
        if stage == "X":
            _, t_cross = x_stage(sh, dur)
            now_crossed = t_cross <= (frames_for(dur) - 1) / FPS
        else:
            now_crossed = False
        self.diagrams.append((key, count, now_crossed, cross_at))
        rec["end"]["start"] = float(d.get("clip_start", 0))
        if prev is not None:
            pd = prev["sh"]["diagram"]
            pkey = tuple(pd["nodes"])
            if key[:len(pkey)] == pkey and d.get("motion_clip") == pd.get("motion_clip"):
                rec["run"] = same_creep
                if d.get("motion_clip") and "clip_start" not in d:
                    d["clip_start"] = round(prev["end"]["start"] + prev["dur"], 3)
                    sh["_clip_cont"] = True
                    rec["end"]["start"] = d["clip_start"]

    def finish(self):
        """Group shots that carry on one another into runs and give each the
        run's clock, so a run creeps (or moves) as one shot. Single shots get
        no run fields, so their cache keys and looks are unchanged."""
        recs, i = self.records, 0
        while i < len(recs):
            j = i + 1
            while j < len(recs) and recs[j]["run"]:
                j += 1
            if j - i > 1:
                # Holds ("creep": "none" inside the run) freeze the run's frame
                # and don't advance its clock, so the next shot carries on
                # exactly where the hold stood.
                holds = [r["sh"].get("creep", "in") == "none" and k > 0
                         for k, r in enumerate(recs[i:j])]
                frames = [0 if hold else frames_for(r["dur"]) for r, hold in zip(recs[i:j], holds)]
                total = max(sum(frames), 1)
                off = 0
                for r, n, hold in zip(recs[i:j], frames, holds):
                    r["sh"]["_run_off"], r["sh"]["_run_frames"] = off, total
                    if hold:
                        r["sh"]["_run_hold"] = True
                        r["sh"]["_run_creep"] = r["mode"]
                    off += n
                first = recs[i]["sh"]
                if recs[i]["kind"] == "still":
                    move = first.get("_run_move", first.get("move"))
                    for r in recs[i + 1:j]:
                        r["sh"]["_run_move"] = move
                if recs[i]["kind"] == "timeline":
                    spacing = [r["end"]["extra"] for r in recs[i:j] if r["end"].get("extra") is not None]
                    for r in recs[i:j]:
                        if spacing and r["end"].get("extra") != min(spacing):
                            r["sh"]["_timeline_extra"] = min(spacing)
                if recs[i]["kind"] == "diagram":
                    widest = max(len(r["sh"]["diagram"]["nodes"]) for r in recs[i:j])
                    for r in recs[i:j]:
                        if widest > len(r["sh"]["diagram"]["nodes"]):
                            r["sh"]["_diagram_n"] = widest
            i = j
