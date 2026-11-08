#!/usr/bin/env python3
"""
Reusable builder for the building-explainer-reels skill (references/reel-format.md).

Input: a JSON manifest of beats (the "scenes" list). Output: a vertical
720x1280 mp4 (h264 + AAC 48 kHz stereo) with TTS narration, burned-in
word-by-word captions timed to the voice by Whisper, an original music bed
and loudness normalisation, plus a self-check, contact sheets and a caption
sync check.

The self-check is NOT the verification gate. Every build still goes to an
independent verifier agent (SKILL.md, "Verification gate").

Usage:
  python3 build_reel.py manifest.json --dry-run          # validate + estimated timings
  python3 build_reel.py manifest.json --stage hook       # build and check the hook alone
  python3 build_reel.py manifest.json --out reel.mp4 --workdir work/   # whole reel

Stages (--stage; "all" is the default and runs them in order). Each stage
reads the files earlier stages left in --workdir, so one part can be redone
without rebuilding the rest:
  check    validate the manifest; estimated timings (same as --dry-run)
  diagram-brief  for each diagram shot: a text-free start frame and a Muse
           prompt for an AI motion clip, with the length it needs ->
           <workdir>/diagram_brief/. Set diagram.motion_clip to the result.
  narrate  TTS or supplied audio, silence trim, Whisper word timing (the
           first word after each pause starts where the voice resumes) ->
           sceneN.wav, timeline.json. Stops if what Whisper hears doesn't match
           the script word for word (a name off by a letter or a missed
           first word only warns; see reel_subs.match_words). Cached per beat: unchanged narration is
           not re-spoken or re-transcribed. Prints each beat's and each
           shot's measured time (the length an asset must cover).
  hook     the hook's beats only (leading beats whose id starts with "hook",
           or the first beat): narration, shots, captions, audio ->
           <workdir>/hook/hook.mp4, then its length, word count and sync.
  preview  with --through ID: the reel from its first beat up to and
           including beat ID (narration, shots, captions, audio) ->
           <workdir>/preview/preview.mp4. Only those beats are checked, so
           later beats' assets need not exist yet (they may still be
           "planned"), and the loop-back check
           waits for the full reel. For building shot by shot with the user
           (SKILL.md, "User in the loop"); cached like the other stages.
  shots    render every shot to <workdir>/shots/. Cached: a shot is
           re-rendered only when its manifest entry, timing or asset file
           changed. --beat ID re-renders just that beat; --force ignores the cache.
  subs     captions -> subs.ass, each word revealed at its measured time
           (apply a caption_nudge, then re-run subs and mux)
  audio    beat audio, music bed, loudness -> audio_norm.wav
  mux      join the shots, burn the captions, mux -> --out, then the self-check
  sync     check_sync.py on --out: captions against the voice (S1-S6)
Modules: reel_common (constants, helpers), reel_manifest (loading,
validation), reel_continuity (what carries on across a cut), reel_render (shot renderers, stat, wipe), reel_pace (slideshow check), reel_subs (phrasing, Whisper
timing, caption ASS), reel_audio (narration, music, loudness), check_sync (sync check),
check_ai_animation (how long an AI animation of a graphic stays faithful),
check_card_hold (how long the finished end card stays on screen).

Manifest (see examples/sample-manifest.json):
{
  "title": "...", "output": "reel.mp4", "voice": "...", "max_duration": 60,
  "music_bed": true,
  "loop_back": true,               // one of the last two sentences echoes the hook's question
  "sfx": true,                     // generated low hit when a stat lands (false: none)
  "allow_save_prompt": false,      // true only if the user asked for "save this"
  "background": {"preset": "posts"},  // the story background behind every shot
                                   // that would be plain blue: posts | network |
                                   // pipeline | ticker | papers | custom (see
                                   // reel_background.py, references/background.md)
  "scenes": [{
    "id": "hook",
    "narration": "A market crash. A made-up meeting.",
    "material": "real",            // REQUIRED: real | ai | recreated | diagram
    "headline": "IDX STOCKS CRASH 8% IN A DAY",  // who + what, self-explaining;
                                   // one line at 52px, or two at 44px (max)
    "yellow_words": ["MARKET"],    // optional; default = first word yellow
    "disinformation": "CNA Verify",// optional: adds "DISINFORMATION POST -
                                   // flagged by CNA Verify" tag, the only
                                   // tag; status tags ("label") are rejected
    "image": "idx.jpg",            // still image
    "keep": [0.2, 0.3, 0.7, 0.85], // the part that makes it relevant, as
                                   // fractions of the image (x0, y0, x1, y1);
                                   // the image zooms as far as this allows
    "image_source": "BILYONARYO • IDX, OCT 2026",
    "full_bleed": true,            // optional: fill the screen (cover-crop,
                                   // centred on "keep", or the image centre
                                   // with no keep); a large keep box still
                                   // wins over filling. Hook stills always
                                   // fill; false is rejected on the hook
    "move": "push",                // optional, on a still image: push | pan |
                                   // inset (required on hook stills)
    "clip_end": 2.4,               // optional: stop the clip here and hold
                                   // (an AI animation's usable_end)
    "clip": "lutfi.mp4", "clip_start": 0.0,   // real footage or a Muse AI
                                   // video; "keep" picks the crop when it
                                   // isn't 9:16; its audio is dropped
    "clip_mask": [[4, 100, 556, 280]],  // delogo boxes [x, y, w, h] in
                                   // 720x1280 output pixels; x must be > 0
    "wipe": "left",                // optional: open this shot with a graphic
                                   // wipe from the previous one ("left" or
                                   // "up"); 1-3 per reel, at section turns
    "schematic": true,             // on an AI-generated map (material "ai"):
                                   // label "AI-GENERATED MAP • SCHEMATIC"
    "caption_nudge": {"$6.3": -0.2},  // optional: shift single caption words
                                   // (as written; "the#2" = 2nd "the") by
                                   // seconds after a sync report names them
    "card": {...}, "diagram": {...},   // scene types, below
    "end_card": true,              // with "pointer" and "disclosure", below
    "section": "chain",            // on the first beat of each section (later
                                   // beats inherit it; hook and end default):
                                   // its first sentence should bridge from
                                   // the beat before (SKILL.md, "Bridge every
                                   // section change"); the dry run prints the
                                   // story spine and warns at cold openers
    "planned": {"kind": "video", "placement": "full-bleed",
                "visual": "AI video: a vault door unlatching"},
                                   // in place of a visual whose asset isn't
                                   // made yet: the shot's row from the
                                   // approved plan (kind: video | built |
                                   // still | end). Accepted by check, narrate
                                   // and diagram-brief; every stage that
                                   // renders the beat refuses it (SKILL.md,
                                   // "User in the loop")
    "audio": null,                 // optional pre-made narration; skips TTS
    "shots": [                     // optional: cut the scene into several
      {"image": "a.jpg", "image_source": "...", "headline": "..."},
      {"card": {...}, "weight": 2} // shots sharing its narration; each shot
    ]                              // inherits narration/material and
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
  "cross_after": 1, "motion_clip": "chain_motion.mp4", "clip_start": 0}.
  "motion_clip" is an AI motion clip (from --stage diagram-brief) played
  behind the diagram, tinted to the reel's blue; the nodes, arrows, labels
  and X are still drawn by the build on the narrated words. "reveal" shows
  nodes one at a time, continuing from the nodes an earlier shot of the same
  diagram already showed ("from": n overrides); stage "X" shows all nodes,
  then snaps a red X onto the arrow leaving node "cross_after" (default 1,
  the second arrow).
- stat: {"value": "9.2", "label": "severity score, 10 = most severe",
  "source": "PHP ADVISORY • 21 OCT 2026", "motion_clip": "...", "clip_start": 0,
  "at": 0.4}. One sourced figure, big, with its label, landing on the word
  that says it (or "at" seconds): a plain number counts up, anything else
  ("0 of 5", "21 OCT") pops in. Over the story background, or over an AI
  motion clip like the diagram. Use material "recreated".
- Maps are not drawn here: generate one with Muse and pass it as "clip" or
  "image" with "material": "ai" and "schematic": true (SKILL.md, "Map").
- timeline: {"events": [{"time": "29 OCT 20:05", "text": "...",
  "source": "TRM LABS"}, ...]}. A vertical line with one dot per event,
  revealed one at a time. About 3 events fit per shot; use "shots" for more.
- end_card: "headline" (e.g. "CHECK BEFORE YOU SHARE"), "pointer":
  {"outlet", "title", "url", "date", "photo"?, "keep"?}: a link preview of
  the referenced article, drawn by the build (reel_pointer.py). "title" is
  the article's headline word for word; "date" its publish date, or
  "Accessed <date>" when the page gives none; "photo" the article's own
  image (never false material), cropped centred on "keep". Without a photo
  an outlet tile in the reel's colour is drawn. scripts/fetch_preview.py
  <article url> prints the block. Also "disclosure" (one line: AI voice,
  AI illustrations, sources).
- summary (on the end card only): {"panels": [{"value", "label", "source"} |
  {"pair": [{"title", "text"}, {"title", "text"}]} |
  {"value", "bar": share 0-1, "label", "source"} |
  {"value", "donut": share 0-1, "label", "source"} |
  {"compare": [{"label", "value", "amount"}, ...2-3], "source"}]}. The
  reel's key figures, distinctions and charts, between the caption band and
  the pointer: two rows at most (figures and donuts two to a row; a
  distinction, bar or compare chart on its own row), so up to 4 figures.
  Charts fill in as their panel lands. Panels share one size and type size, appear one by one, and
  never clip. An end card with panels keeps its captions; the pointer is
  drawn as the compact card (photo on the left).

Rules enforced (the spec is SKILL.md; where this docstring disagrees, SKILL.md
wins):
- Motion: the disinformation tag, headlines over photos, source labels and caption
  words never move (a caption word changes colour, never place). Each shot's base layer creeps (push in to 102%, or "creep": "up"
  drifts 5px/s; "creep": "none" holds); flat graphics get faint animated
  grain. Shots that continue the previous shot's visual (same clip, still with the
  same layout, card, summary, or a timeline or diagram whose list starts with the
  earlier items) carry on instead of restarting at the cut: the creep and "move" run
  once over the whole run, a clip without its own clip_start (and diagram.motion_clip
  with clip_start) starts where the last shot ended, a card starts with its words
  already lit, a timeline and diagram keep what they showed and the drawn X (see
  reel_continuity.py; "timeline": {"from": n} and "diagram": {"from": n} set it by
  hand). A different visual is a hard cut that starts its own motion. The card
  sweep is timed from the beat's measured word times when the key sentence is in
  the narration. On top of that: the card highlight sweep and the diagram reveal and X. Real clips get no added zoom; AI clips keep
  their own motion. "move" adds a push, pan or inset to a still image (the
  hook needs a clip or a moving image). Shots that would show plain blue
  (headline cards without an image, stats without a motion clip, the timeline,
  the end card, the space around an inset) are drawn over the manifest's
  "background", which moves on reel time and carries on across cuts; without
  one, the dry run warns. "wipe" on a shot opens it with a
  graphic wipe (a blue panel with yellow edges crossing the frame in 0.5s,
  under the captions). Slide-ins and particle overlays from SKILL.md's
  motion table are not generated here; make them as clips and pass them in.
- Stills zoom as far as their "keep" box allows: the keep box always stays
  whole, inside the frame and between the caption band and the bottom safe
  area (y=1030), even at the end of the creep. A small keep box (a logo, a face) fills the
  screen; a keep box covering the whole image (a screenshot, a chart) shows
  it whole. Space the image leaves is filled with a blurred copy of it,
  tinted with the reel's blue. No keep box means the whole image is kept.
  AI images, hook stills, and stills with "full_bleed": true, fill the
  screen. Clips (real or AI) are always cover-scaled to fill the screen.
- Pace (reel_pace.py, printed at the dry run and after the build, warnings
  only): stills over half the reel's time, fewer than one video shot per
  ~15s, over 6s of stills back to back, one image in more than 2 shots or
  coming back after other shots, one still on screen over 4s across super
  changes, a still covering under 40% of the frame, no wipe in a reel over 30s.
- Safe area: tags/headlines start at y=140; nothing the viewer must read
  goes below y=1030 (the platform's caption, name and buttons). The source
  line sits in small muted type between the tags and the headline.
- Captions sit at the upper middle: first line top at y=300, or just under
  the beat's tallest header stack, one position per beat. Each shot's own
  content (keep box, diagram, card body, timeline, summary panels) starts
  below the two-line caption band.
- Every scene needs a visual (image, clip, card, diagram, timeline) unless it is
  the end card or --allow-plain is passed, or, before any stage that renders
  it, carries "planned". "body" paragraphs are dropped (no double text).
- A disinformation scene may not open the reel or be the end card.
- No status tags: a scene with "label" or "label_color" is rejected.
- Caption timing: Whisper word timestamps from each beat's own narration
  audio, with split figure tokens merged back ("$6" + ".3" -> "$6.3", "94" +
  "%" -> "94%"); every beat must match its script word for word, except
  a mid-sentence name a letter off or a missed first word (warned). Never
  spaced evenly. caption_nudge shifts only the words it names. Diagram nodes
  use the same word times.
- Captions: one short phrase at a time (2-5 words, at most 2 lines at 38px
  bold DejaVu Sans, wrapped at 680px measured width, sentence case), white
  with a thick black outline and soft shadow, no box. Each word is placed at
  its final position in the full phrase layout and appears as it is spoken:
  the current word yellow, spoken words white, the same size; the phrase is
  replaced whole by the next. A phrase never ends on an article, preposition
  or conjunction, never splits a name or a number, and never crosses a beat.
  An end card without summary panels carries no captions.
- Audio: silence trimmed per scene, 0.15s tail, original sine-pad bed,
  compression then loudnorm to about -14 LUFS, AAC 192k 48 kHz stereo.
- Every shot file is exactly round(dur * 30) frames at 30 fps; concat
  re-encodes (never -c copy across frame rates); overlays are looped with an
  explicit frame count (never a single-frame overlay with -shortest).

Not covered here: generating AI clips (produce them with the platform's
video/image generation and pass them as "clip" or "image" with material
"ai"), and measuring a real clip's caption/logo bands (measure them from a
rendered frame, then set "clip_mask").

Dependencies: ffmpeg (with libass) + ffprobe on PATH, Pillow,
faster-whisper (or openai-whisper; model REEL_WHISPER_MODEL, default
small.en), a TTS command (default /opt/hatch/bin/tts; override with --tts or
REEL_TTS), and DejaVu fonts (default /usr/share/fonts/truetype/dejavu;
override with REEL_FONT_DIR). Only for Chinese, Japanese or Korean text on
the end card's pointer: a CJK font (REEL_CJK_FONT, REEL_CJK_BOLD_FONT, or
Noto Sans CJK, WenQuanYi, PingFang or Microsoft YaHei where installed).
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_common import *  # noqa: E402,F401,F403

# Modules that draw shots: a change to any of them (a skill update) re-renders
# every cached shot.
RENDERER_MODULES = ("reel_render.py", "reel_background.py", "reel_pointer.py", "reel_common.py")
from reel_subs import (WHISPER_MODEL, whisper_words, match_words, apply_nudges, phrase_times,  # noqa: E402
                       caption_events, write_ass, speech_segments, snap_to_speech,
                       SNAP_PAUSE, SNAP_DB, SNAP_HIGHPASS)
from reel_manifest import (load_manifest, validate, check_tools, expand_shots,  # noqa: E402
                           hook_indices, story_spine, sentences)
from reel_render import (render_shot, source_label, diagram_plate, header_bottom,  # noqa: E402
                         apply_wipe, stat_time, summary_hold, card_rows,
                         captioned)
from reel_pace import pace_report, print_table, shot_kind, coverage  # noqa: E402
from reel_continuity import Continuity  # noqa: E402
from reel_background import uses_background  # noqa: E402
import reel_audio  # noqa: E402
import check_sync  # noqa: E402

STAGES = ("check", "narrate", "diagram-brief", "hook", "preview", "shots", "subs", "audio", "mux",
          "sync", "all")


def file_sig(path):
    """Changes when the file changes (size and modification time)."""
    try:
        st = os.stat(path)
        return f"{path}:{st.st_size}:{int(st.st_mtime)}"
    except OSError:
        return f"{path}:missing"


def digest(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def cached(key_path, key):
    try:
        with open(key_path, encoding="utf-8") as f:
            return json.load(f).get("key") == key
    except (OSError, ValueError):
        return False


def save_key(key_path, key, **extra):
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump({"key": key, **extra}, f)


class Build:
    """One build: the manifest, the work folder, and the beats' timing."""

    def __init__(self, args):
        self.args = args
        self.man = load_manifest(args.manifest)
        self.scenes = self.man["scenes"]
        if getattr(args, "through", None):
            # A preview: only the beats up to and including this one.
            ids = [str(s.get("id")) for s in self.scenes]
            if args.through not in ids:
                sys.exit(f"Unknown beat id for --through: {args.through}")
            self.scenes = self.scenes[:ids.index(args.through) + 1]
            self.man = {**self.man, "loop_back": False}
        self.max_dur = args.max_duration or self.man.get("max_duration", 60)
        self.out = args.out or self.man.get("output", "reel.mp4")
        self.work = args.workdir or os.path.splitext(self.out)[0] + "_work"
        self.voice = args.voice or self.man.get("voice")
        self.timeline = []      # [{"i", "id", "start", "dur", "speak", "audio"}]

    # -- stage: check ---------------------------------------------------------
    def check(self, need_tools=True):
        errors, warnings = validate(self.scenes, self.args, self.man)
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        if errors:
            for e in errors:
                print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(f"{len(errors)} manifest error(s); nothing built.")
        if need_tools:
            missing = check_tools(self.scenes, self.args.tts)
            if missing:
                sys.exit("Missing dependencies:\n  " + "\n  ".join(missing))

    def estimate(self):
        """Dry run: timings from a ~150 wpm estimate, no audio."""
        t, words = 0.0, 0
        for i, s in enumerate(self.scenes):
            n = len(s.get("narration", "").split())
            words += n
            dur = frames_for(max(n / 150 * 60, 2.0) + TAIL) / FPS
            self.timeline.append({"i": i, "id": s.get("id"), "start": t, "dur": dur,
                                  "speak": dur, "audio": None})
            t += dur
        return words

    # -- stage: narrate -------------------------------------------------------
    def narrate(self, indices):
        """TTS (or supplied audio), silence trim, and word timing for the
        given beats, cached per beat. Writes timeline.json."""
        os.makedirs(self.work, exist_ok=True)
        t = 0.0
        for i in range(max(indices) + 1):
            s = self.scenes[i]
            wav = os.path.join(self.work, f"scene{i}.wav")
            key = digest([s.get("narration", ""), self.voice, self.args.tts,
                          file_sig(s["audio"]) if s.get("audio") else None])
            if self.args.force or not os.path.exists(wav) or not cached(wav + ".key", key):
                reel_audio.narrate(s, os.path.join(self.work, f"scene{i}_raw.mp3"), wav,
                                   self.args.tts, self.voice)
                save_key(wav + ".key", key)
            speak = probe_duration(wav) + TAIL
            dur = speak
            if s.get("clip") and s.get("material") == "real" and not s.get("shots"):
                # Let a real clip run up to 3s past its narration (music only
                # under the tail), never past the clip's remaining length.
                left = probe_duration(s["clip"]) - float(s.get("clip_start", 0))
                dur = max(dur, min(left, dur + 3.0))
            dur = frames_for(dur) / FPS
            speak = min(speak, dur)
            starts = self.word_times(s, wav, key)
            entry = {"i": i, "id": s.get("id"), "start": t, "dur": dur, "speak": speak,
                     "audio": wav, "word_times": starts}
            if i < len(self.timeline):
                self.timeline[i] = entry
            else:
                self.timeline.append(entry)
            t += dur
        self.save_timeline()

    def word_times(self, s, wav, key):
        """When each narration word starts, from a Whisper pass on the beat's
        own narration audio (cached with the audio). Never spaced evenly:
        figures take far longer to say than plain words. Stops if the
        words heard don't match the script word for word."""
        cache = wav + ".words.json"
        ckey = digest([key, WHISPER_MODEL, "snap-to-speech"])
        try:
            with open(cache, encoding="utf-8") as f:
                c = json.load(f)
            if c.get("key") == ckey:
                for n in c.get("notes", []):
                    print(f"WARNING: beat {s.get('id')}: {n}", file=sys.stderr)
                return c["starts"]
        except (OSError, ValueError):
            pass
        narration = s.get("narration", "")
        tokens = whisper_words(wav, narration)
        if tokens is None:
            sys.exit("No Whisper package: pip install faster-whisper (captions are timed "
                     "from the voice).")
        notes, ends = [], []
        try:
            starts = match_words(narration, tokens, notes, ends)
        except ValueError as e:
            sys.exit(f"beat {s.get('id')}: the narration audio doesn't match the script: {e}\n"
                     "Listen to it: if the voice dropped or changed a word, re-run narrate "
                     "(--force); if the script spells a figure differently from how it is "
                     "said, write it the way it is said.")
        # Whisper's start for the first word after a pause is unreliable
        # (often the previous word's end); take it from the audio instead.
        segs = speech_segments(wav, SNAP_DB, SNAP_PAUSE, SNAP_HIGHPASS)
        starts = snap_to_speech(starts, ends, segs)
        for n in notes:
            print(f"WARNING: beat {s.get('id')}: {n}", file=sys.stderr)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump({"key": ckey, "starts": starts, "notes": notes}, f)
        return starts

    def beat_word_times(self, i):
        """Measured word times of beat i with its caption_nudge applied."""
        s, b = self.scenes[i], self.timeline[i]
        words = s.get("narration", "").split()
        starts = b.get("word_times") or []
        if len(starts) != len(words):
            sys.exit(f"beat {s.get('id')}: word timing is stale; run --stage narrate again.")
        try:
            return apply_nudges(words, starts, s.get("caption_nudge"), f"beat {s.get('id')}")
        except ValueError as e:
            sys.exit(str(e))

    def save_timeline(self):
        with open(os.path.join(self.work, "timeline.json"), "w", encoding="utf-8") as f:
            json.dump({"manifest": os.path.abspath(self.args.manifest),
                       "beats": self.timeline}, f, indent=1)

    def load_timeline(self, need):
        path = os.path.join(self.work, "timeline.json")
        try:
            with open(path, encoding="utf-8") as f:
                self.timeline = json.load(f)["beats"]
        except (OSError, ValueError, KeyError):
            sys.exit(f"No narration timing in {path}; run --stage narrate first.")
        if len(self.timeline) < need:
            sys.exit(f"timeline.json covers {len(self.timeline)} beats, {need} needed; "
                     "run --stage narrate first.")
        for b in self.timeline:
            if b.get("audio") and not os.path.exists(b["audio"]):
                sys.exit(f"{b['audio']} is missing; run --stage narrate again.")

    # -- shot planning and rendering ------------------------------------------
    def plan(self, upto):
        """Every shot of beats 0..upto-1: (beat index, shot index, shot dict,
        duration, file name). Walks from the first beat so a shot that carries
        on the previous shot's visual (same clip, still, card, timeline or
        diagram) carries its animation on too: see reel_continuity."""
        plan, warnings, cont = [], [], Continuity()
        hold_errors = []        # end card on screen too briefly to read
        self.cues = []          # sound accents: (name, reel seconds, beat index)
        hook = set(hook_indices(self.scenes))
        self.caption_tops, self.no_caption = {}, []
        for b in self.timeline[:upto]:
            s = self.scenes[b["i"]]
            s["_narr_dur"] = b["speak"]
            s["_word_times"] = self.beat_word_times(b["i"])
            total = frames_for(b["dur"])
            shots = expand_shots(s)
            weights = [sh.get("weight", 1) for sh in shots]
            bounds = [round(total * sum(weights[:j]) / sum(weights)) for j in range(len(shots) + 1)]
            # One caption position per beat (phrases never cross a beat), so a
            # phrase never jumps at a cut: y=300, or just under the tallest
            # header stack of the beat's shots.
            heads = [header_bottom(sh) for sh in shots if captioned(sh)]
            top = max([CAPTION_TOP] + [h + CAPTION_GAP for h in heads])
            self.caption_tops[b["i"]] = top
            if top > CAPTION_TOP:
                warnings.append(f"beat {s.get('id')}: the header stack runs to y={top - CAPTION_GAP}, "
                                f"so captions sit at y={top} instead of {CAPTION_TOP}; a one-line "
                                "headline keeps them in place.")
            for j, sh in enumerate(shots):
                shot_dur = (bounds[j + 1] - bounds[j]) / FPS
                sh["_scene_dur"], sh["_shot_start"] = min(b["speak"], b["dur"]), bounds[j] / FPS
                sh["_caption_top"] = top
                sh["_hook"] = b["i"] in hook
                if not captioned(sh):
                    self.no_caption.append((b["start"] + bounds[j] / FPS,
                                            b["start"] + bounds[j + 1] / FPS))
                where = f"beat {s.get('id')} shot {j + 1}"
                ai_cap = 6.0 if sh.get("clip") else 3.0
                if sh.get("material") == "ai" and shot_dur > ai_cap + 1 / FPS:
                    warnings.append(f"{where}: AI shot runs {shot_dur:.2f}s; the spec caps AI "
                                    f"{'video' if sh.get('clip') else 'stills'} at {ai_cap:.0f}s.")
                limit = 4.0 if shot_kind(sh) == "still" else 6.0   # a still image shot stays <= 4s
                if b["i"] == len(self.scenes) - 1 and (sh.get("end_card") or sh.get("summary")):
                    # The end card runs for the loop-back narration, however
                    # long; its text must stay readable (checked by eye).
                    limit = max(limit, shot_dur)
                cont.link(b["i"], sh, shot_dur, where, warnings)
                moving = sh.get("clip") or (sh.get("diagram") or {}).get("motion_clip")
                if moving:
                    from reel_manifest import clip_info
                    info = clip_info(moving)
                    start = (sh.get("diagram") or {}).get("clip_start", 0) if not sh.get("clip") \
                        else sh.get("clip_start", 0)
                    end = min(info[0], float(sh.get("clip_end") or info[0])) if info else None
                    if info and sh.get("_clip_cont") and float(start) > end - 0.1:
                        # The predecessor already ran the clip out: start on its
                        # last frames (a freeze, warned below) rather than past its end.
                        start = round(max(end - 0.1, 0.0), 3)
                        if sh.get("clip"):
                            sh["clip_start"] = start
                        else:
                            sh["diagram"]["clip_start"] = start
                    left = end - float(start) if info else shot_dur
                    if left + 1 / FPS < shot_dur:
                        warnings.append(f"{where}: clip has {left:.2f}s for a {shot_dur:.2f}s shot; "
                                        f"its last frame would hold {shot_dur - left:.2f}s (a freeze). "
                                        "Use a longer clip or split the beat into shots.")
                if shot_dur > limit + 1 / FPS:
                    warnings.append(f"{where}: runs {shot_dur:.2f}s, over the {limit:.0f}s shot limit; "
                                    "add shots.")
                if sh.get("summary"):
                    held, need = summary_hold(sh, shot_dur)
                    if held + 1 / FPS < need:
                        hold_errors.append(
                            f"{where}: the end card's finished summary panels are on screen "
                            f"{held:.2f}s; they need {need:.1f}s ({SUMMARY_HOLD_PER_PANEL}s per "
                            f"panel, at least {SUMMARY_HOLD_MIN}s). Raise the end card's weight "
                            "(take it from the shot before), cut panels, or lengthen the "
                            "loop-back narration.")
                elif sh.get("end_card") and shot_dur + 1 / FPS < END_CARD_HOLD_MIN:
                    hold_errors.append(f"{where}: the end card runs {shot_dur:.2f}s; it needs "
                                       f"{END_CARD_HOLD_MIN}s. Raise its weight.")
                t_shot = b["start"] + bounds[j] / FPS
                if self.man.get("background") and uses_background(sh):
                    # Drawn over the story background, which runs on reel time.
                    sh["_background"] = self.man["background"]
                    sh["_reel_start"] = round(t_shot, 4)
                if sh.get("stat"):
                    self.cues.append(("hit", t_shot + stat_time(sh, shot_dur), b["i"]))
                plan.append((b["i"], j, sh, shot_dur, f"scene{b['i']}_{j}"))
        cont.finish()
        if hold_errors:
            sys.exit("Card too brief to read (SKILL.md, \"End card\"):\n  "
                     + "\n  ".join(hold_errors))
        self.pace_rows, pace_warnings = pace_report(plan)
        return plan, warnings + pace_warnings

    def render(self, plan, only=None):
        """Render the planned shots (only the given beat indices, if set),
        skipping shots whose inputs haven't changed since the last render."""
        shot_dir = os.path.join(self.work, "shots")
        os.makedirs(shot_dir, exist_ok=True)
        warnings, rendered = [], 0
        keys = []
        for n, (i, j, sh, dur, name) in enumerate(plan):
            assets = [sh.get("image"), sh.get("clip"), (sh.get("card") or {}).get("image"),
                      (sh.get("diagram") or {}).get("motion_clip"),
                      (sh.get("stat") or {}).get("motion_clip"),
                      (sh.get("pointer") or {}).get("photo") if isinstance(sh.get("pointer"), dict) else None]
            # A wipe shows the previous shot's last frame, so it re-renders when that shot changes.
            prev_key = keys[n - 1] if sh.get("wipe") and n else None
            keys.append(digest([{k: v for k, v in sh.items() if k not in ("_mode",)}, round(dur, 4),
                                [file_sig(a) for a in assets if a], FONT_DIR, prev_key,
                                # a renderer change (a skill update) re-renders every shot
                                [file_sig(os.path.join(os.path.dirname(os.path.abspath(__file__)), m))
                                 for m in RENDERER_MODULES]]))
        for n, (i, j, sh, dur, name) in enumerate(plan):
            if only is not None and i not in only:
                continue
            path = os.path.join(shot_dir, f"{name}.mp4")
            key = keys[n]
            if not self.args.force and os.path.exists(path) and cached(path + ".key", key):
                verify_video(path, frames_for(dur), f"shot {name}")
                continue
            render_shot(sh, dur, shot_dir, name, warnings)
            if sh.get("wipe") and n:
                prev = plan[n - 1]
                prev_path = os.path.join(shot_dir, f"{prev[4]}.mp4")
                if not os.path.exists(prev_path):
                    sys.exit(f"shot {name} wipes from {prev[4]}, which isn't rendered yet; "
                             "run --stage shots without --beat first.")
                apply_wipe(path, prev_path, frames_for(prev[3]), frames_for(dur),
                           "up" if sh["wipe"] == "up" else "left", shot_dir, name)
            verify_video(path, frames_for(dur), f"shot {name}")
            save_key(path + ".key", key, mode=sh.get("_mode"))
            rendered += 1
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        return rendered

    def shot_files(self, plan, indices):
        """The shots' files in order, each checked to be exactly its planned
        frame count at 30 fps (so joining them can't drift)."""
        files, frames = [], 0
        for i, _, _, dur, name in plan:
            if i not in indices:
                continue
            f = os.path.join(self.work, "shots", f"{name}.mp4")
            if not os.path.exists(f):
                sys.exit(f"Shot file missing: {f}; run --stage shots first.")
            frames += verify_video(f, frames_for(dur), f"shot {name}")
            files.append(f)
        return files, frames

    def write_shot_list(self, plan, indices, path):
        """The shot list: each shot's measured start, end, frames, visual,
        material and label. The final duration is checked against this,
        not against the build's own running total."""
        rows, t = [], 0
        for i, j, sh, dur, name in plan:
            if i not in indices:
                continue
            n = frames_for(dur)
            visual = next((k for k in ("clip", "image", "card", "stat", "diagram", "timeline",
                                       "summary", "end_card") if sh.get(k)), "plain")
            rows.append({"beat": self.scenes[i].get("id"), "shot": j + 1,
                         "start": round(t / FPS, 3), "end": round((t + n) / FPS, 3), "frames": n,
                         "visual": visual, "move": sh.get("move"), "material": sh.get("material"),
                         "kind": shot_kind(sh), "wipe": sh.get("wipe") or None,
                         "coverage": (lambda c: None if c is None else round(c, 2))(coverage(sh)),
                         "label": source_label(sh), "headline": sh.get("headline", ""),
                         "panels": (sum(len(r) for r in card_rows(sh))
                                    if sh.get("summary") else None)})
            t += n
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"frames": t, "seconds": round(t / FPS, 3), "shots": rows}, f, indent=1)
        return t

    # -- captions, audio, mux -------------------------------------------------
    def subtitles(self, indices, path):
        """Word-by-word captions for the given beats -> path (ASS), timed to
        the measured word times and rebased so the first beat starts at 0.
        An end card without summary panels carries none. Needs plan() first
        (caption positions)."""
        t0 = self.timeline[indices[0]]["start"]
        skip = [(a - t0, e - t0) for a, e in self.no_caption]
        phrases, tops, dropped = [], [], []
        for i in indices:
            b = self.timeline[i]
            ph, cut = phrase_times(self.scenes[i].get("narration", ""), self.beat_word_times(i),
                                   b["start"] - t0, b["speak"], skip)
            phrases += ph
            dropped += cut
            tops += [self.caption_tops[i]] * len(ph)
        events, warnings = caption_events(phrases, tops)
        for a, e in dropped:
            warnings.append(f"the phrase spoken at {a:.2f}s runs into the end card, so it is left "
                            f"uncaptioned ({e - a:.2f}s); move the cut to the end card to a phrase "
                            "boundary (shot weights) if that is too long.")
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        write_ass(path, events, sorted([(a, e) for a, e in skip if e > 0] + dropped))
        return path

    def audio(self, indices, folder):
        os.makedirs(folder, exist_ok=True)
        parts = [reel_audio.pad_audio(self.timeline[i].get("audio"), self.timeline[i]["dur"],
                                      os.path.join(folder, f"scene{i}_audio.wav")) for i in indices]
        total = sum(self.timeline[i]["dur"] for i in indices)
        # Sound accents: only those inside the beats being mixed, timed from
        # the first of them (the hook alone starts at 0 too).
        t0 = self.timeline[indices[0]]["start"] if indices else 0.0
        cues = [(n, t - t0) for n, t, i in getattr(self, "cues", []) if i in indices]             if self.man.get("sfx", True) else []
        norm = reel_audio.mix(parts, total, folder, self.man.get("music_bed", True), cues)
        return reel_audio.encode(norm, os.path.join(folder, "audio.m4a"))

    def mux(self, videos, frames, audio, ass, out):
        """Join the shots, burn the captions over the whole joined video,
        and add the audio, copied unchanged.

        Build pitfalls this guards: the join re-encodes at 30 fps (never
        -c copy across frame rates) and is checked to have exactly the
        shots' frames; captions are burned here, never into a shot, so a
        re-rendered shot always gets them; no -shortest anywhere."""
        folder = os.path.dirname(os.path.abspath(ass))
        video = os.path.join(folder, "video_only.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", reel_audio.concat_list(videos, os.path.join(folder, "videos.txt")),
             "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", video])
        verify_video(video, frames, "joined video")
        total = frames / FPS
        # Give libass the caption font directly, so it never falls back to a
        # proportional system font where DejaVu is not installed system-wide.
        os.makedirs(os.path.join(folder, "fonts"), exist_ok=True)
        shutil.copy(BOLD, os.path.join(folder, "fonts"))
        # The ass filter path is relative (Windows drive colons break filter
        # parsing), so ffmpeg runs from the caption file's folder.
        out_abs = os.path.abspath(out)
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", os.path.abspath(audio),
                            "-vf", f"ass={os.path.basename(ass)}:fontsdir=fonts",
                            "-map", "0:v", "-map", "1:a",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-frames:v", str(frames),
                            "-c:a", "copy", out_abs],
                           capture_output=True, text=True, cwd=folder)
        if r.returncode != 0:
            sys.exit(f"Final mux failed:\n{r.stderr[-2000:]}")
        # Scope check: the reel's audio must be the audio stage's stream,
        # copied unchanged; and say whether it changed since the last mux.
        md5 = stream_md5(out_abs, "a")
        if md5 != stream_md5(audio, "a"):
            sys.exit("The reel's audio differs from the audio stage's file; the mux must copy it.")
        state = os.path.join(folder, "mux.json")
        try:
            with open(state, encoding="utf-8") as f:
                prev = json.load(f).get("audio_md5")
        except (OSError, ValueError):
            prev = None
        print(f"Audio checksum {md5}: " + ("first mux" if prev is None else
              "unchanged since the last mux" if prev == md5 else
              "CHANGED since the last mux (the audio stage re-ran)"))
        with open(state, "w", encoding="utf-8") as f:
            json.dump({"audio_md5": md5, "frames": frames}, f)
        return out_abs, total

    def assemble(self, indices, folder, out, plan):
        """Captions, audio and mux for the given beats: the whole reel, or
        just the hook."""
        os.makedirs(folder, exist_ok=True)
        ass = self.subtitles(indices, os.path.join(folder, "subs.ass"))
        audio = self.audio(indices, folder)
        self.write_shot_list(plan, indices, os.path.join(folder, "shot_list.json"))
        videos, frames = self.shot_files(plan, indices)
        out, total = self.mux(videos, frames, audio, ass, out)
        return out, ass, total


def self_check(out, total, max_dur, work):
    """Duration against the shot list, specs, loudness and contact sheets
    (a start, not the gate)."""
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_name,width,height,sample_rate,channels", "-of", "csv=p=0", out], check=False)
    print(f"Built: {out}\nStreams:\n{r.stdout.strip()}")
    with open(os.path.join(work, "shot_list.json"), encoding="utf-8") as f:
        listed = json.load(f)["frames"]
    got, _ = video_frames(out)
    audio_s = float(run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                         "stream=duration", "-of", "csv=p=0", out]).stdout.strip() or 0)
    ok = got == listed and abs(audio_s - listed / FPS) <= 0.05
    print(f"{'PASS' if ok else 'FAIL'}: video {got} frames ({got / FPS:.2f}s), audio {audio_s:.2f}s, "
          f"shot list {listed} frames ({listed / FPS:.2f}s)")
    long_ok = listed / FPS <= max_dur
    print(f"{'PASS' if long_ok else 'FAIL'}: length {listed / FPS:.2f}s (limit {max_dur}s)"
          + ("" if long_ok else " -- shorten narration (the loop-back may use its short form; "
             "never cut the denial or distinction beats), or say so at delivery"))
    lufs = reel_audio.loudness(out)
    loud_ok = lufs is not None and -15.5 <= lufs <= -13.5
    print(f"{'PASS' if loud_ok else 'FAIL'}: loudness {lufs} LUFS (target -14)")
    sheets = os.path.join(work, "contact_sheets")
    os.makedirs(sheets, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", out, "-vf", "fps=2,scale=180:-1,tile=8x2",
         os.path.join(sheets, "sheet_%02d.png")], check=False)
    print(f"Contact sheets: {sheets}")
    return ok and loud_ok and long_ok


def hook_report(build, indices, out, total):
    """What C14 checks, measured on the hook alone."""
    words = sum(len(build.scenes[i].get("narration", "").split()) for i in indices)
    ok = total <= 7.0 + 1 / FPS and words >= 12
    print(f"{'PASS' if total <= 7.0 + 1 / FPS else 'FAIL'}: hook runs {total:.2f}s (limit 7s)")
    print(f"{'PASS' if words >= 12 else 'FAIL'}: hook has {words} words (about 15-22; under 12 fails C14)")
    print("Hook narration: " + " ".join(build.scenes[i].get("narration", "") for i in indices))
    print("Check by eye: who, what happened (plain verb), the scale or stakes; "
          "nothing stronger than facts.md.")
    return ok


def diagram_brief(b, plan):
    """For each diagram shot: a text-free start frame and a Muse prompt for
    an AI motion clip, with the length it needs (from the narration)."""
    folder = os.path.join(b.work, "diagram_brief")
    os.makedirs(folder, exist_ok=True)
    brief = []
    for i, j, sh, dur, name in plan:
        if not sh.get("diagram"):
            continue
        plate = os.path.join(folder, f"{name}_plate.png")
        diagram_plate(sh).save(plate)
        need = round(dur + 0.5, 1)
        prompt = ("Animate this image as a slow, subtle moving background. Soft light pulses "
                  "travel down the faint vertical line, from glow to glow; a few faint particles "
                  "drift. Keep the camera still. Keep the glows where they are. Do not add any "
                  "objects, shapes, people, text, letters, numbers or logos. Keep the same blue "
                  f"colours. Vertical 9:16, 720x1280, at least {need} seconds, no sound.")
        brief.append({"beat": b.scenes[i].get("id"), "shot": j + 1, "start_frame": plate,
                      "seconds_needed": need, "prompt": prompt,
                      "manifest": f'"diagram": {{..., "motion_clip": "{name}_motion.mp4"}}'})
        print(f"{b.scenes[i].get('id')} shot {j + 1}: {need}s\n  start frame: {plate}\n  prompt: {prompt}")
    with open(os.path.join(folder, "brief.json"), "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=1, ensure_ascii=False)
    if not brief:
        print("No diagram shots in this manifest.")
    print("Generate each clip with Muse from its start frame and prompt, look at it, put it in the "
          "assets folder and set diagram.motion_clip. One clip can serve every shot of the same "
          "diagram if it is long enough (set diagram.clip_start for later shots).")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Build an investigative explainer reel, whole or by stage.")
    ap.add_argument("manifest")
    ap.add_argument("--stage", choices=STAGES, default="all",
                    help="run one stage (default: all). Stages reuse earlier stages' files in --workdir.")
    ap.add_argument("--beat", action="append", default=None,
                    help="with --stage shots: re-render only this beat (its id); repeatable")
    ap.add_argument("--through", default=None,
                    help="with --stage preview: build up to and including this beat (its id)")
    ap.add_argument("--force", action="store_true", help="ignore cached narration and shots")
    ap.add_argument("--out", default=None)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--tts", default=TTS_DEFAULT)
    ap.add_argument("--max-duration", type=float, default=None)
    ap.add_argument("--dry-run", action="store_true", help="same as --stage check")
    ap.add_argument("--allow-plain", action="store_true")
    args = ap.parse_args()
    stage = "check" if args.dry_run else args.stage
    if (stage == "preview") != bool(args.through):
        sys.exit("--stage preview and --through go together: "
                 "--stage preview --through <beat id>.")
    b = Build(args)
    everything = list(range(len(b.scenes)))

    if stage == "check":
        b.check(need_tools=False)
        words = b.estimate()
        total = sum(x["dur"] for x in b.timeline)
        print(f"Beats: {len(b.scenes)}  Words: {words}  Total: {total:.2f}s (limit {b.max_dur}s, estimated)")
        for x in b.timeline:
            s = b.scenes[x["i"]]
            print(f"  {x['start']:6.2f}-{x['start'] + x['dur']:6.2f}s  {s.get('id')} "
                  f"[{s.get('material')}]: {s.get('headline', '')!r}")
        print("Hook beats: " + ", ".join(str(b.scenes[i].get("id")) for i in hook_indices(b.scenes)))
        # The story's spine: the hook's last line, then each section's opening
        # line. Read in order, they should tell the story by themselves.
        hook_text = " ".join(b.scenes[i].get("narration", "") for i in hook_indices(b.scenes))
        print("Story spine (read these in order; each should follow from the one before):")
        print(f"  hook: {(sentences(hook_text) or [''])[-1]}")
        for sec, sid, _, first in story_spine(b.scenes):
            print(f"  {sec} ({sid}): {first}")
        hook = set(hook_indices(b.scenes))
        shots = []
        for x in b.timeline:
            sc = b.scenes[x["i"]]
            exp = expand_shots(sc)
            wts = [sh.get("weight", 1) for sh in exp]
            for j, sh in enumerate(exp):
                sh["_hook"] = x["i"] in hook
                shots.append((x["i"], j, sh, x["dur"] * wts[j] / sum(wts), f"scene{x['i']}_{j}"))
        rows, pace_warnings = pace_report(shots)
        print_table(rows)
        for w in pace_warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        return 1 if total > b.max_dur else 0

    b.check(need_tools=stage in ("narrate", "hook", "preview", "all"))

    if stage == "diagram-brief":
        b.narrate(everything)
        plan, _ = b.plan(len(b.scenes))
        return diagram_brief(b, plan)

    if stage == "hook":
        hook = hook_indices(b.scenes)
        b.narrate(hook)
        plan, warnings = b.plan(len(hook))
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        b.render(plan, set(hook))
        folder = os.path.join(b.work, "hook")
        out, ass, total = b.assemble(hook, folder, os.path.join(folder, "hook.mp4"), plan)
        print(f"Built hook: {out}")
        ok = hook_report(b, hook, out, total)
        ok = check_sync.report(out, ass) and ok
        print("Review the hook before building the rest: --stage all reuses its narration and shots.")
        return 0 if ok else 1

    if stage == "preview":
        b.narrate(everything)
        plan, warnings = b.plan(len(b.scenes))
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        n = b.render(plan, None)
        folder = os.path.join(b.work, "preview")
        out, ass, total = b.assemble(everything, folder, os.path.join(folder, "preview.mp4"), plan)
        last = b.timeline[-1]
        print(f"Built preview through beat {last['id']}: {out} ({n} shot(s) rendered)")
        print(f"  beat {last['id']} runs {last['start']:.2f}-{last['start'] + last['dur']:.2f}s:")
        for (i, j, sh, dur, name) in plan:
            if i == last["i"]:
                print(f"    shot {j + 1}: {dur:.2f}s")
        ok = check_sync.report(out, ass)
        print("Show the new beat's shots to the user before the next beat.")
        return 0 if ok else 1

    if stage in ("narrate", "all"):
        b.narrate(everything)
        total = sum(x["dur"] for x in b.timeline)
        print(f"Beats: {len(b.scenes)}  Total: {total:.2f}s (limit {b.max_dur}s)")
        if total > b.max_dur:
            print(f"WARNING: total {total:.1f}s exceeds {b.max_dur}s -- cut a whole fact or "
                  "beat the story can lose, never squeeze lines until they lose who, what or "
                  "the link to the line before (SKILL.md, \"Fit the length\"). "
                  "Building anyway so it can be reviewed; the self-check will FAIL on length.",
                  file=sys.stderr)
        if stage == "narrate":
            for x in b.timeline:
                print(f"  {x['start']:6.2f}-{x['start'] + x['dur']:6.2f}s  {x['id']}")
                shots = expand_shots(b.scenes[x["i"]])
                total_f = frames_for(x["dur"])
                wts = [sh.get("weight", 1) for sh in shots]
                bounds = [round(total_f * sum(wts[:j]) / sum(wts)) for j in range(len(shots) + 1)]
                for j, sh in enumerate(shots):
                    pl = sh.get("planned") if isinstance(sh.get("planned"), dict) else {}
                    what = f"  planned: {pl['visual']}" if pl.get("visual") else ""
                    print(f"      shot {j + 1}: {(bounds[j + 1] - bounds[j]) / FPS:.2f}s{what}")
            planned = sum(1 for s in b.scenes for sh in expand_shots(s) if sh.get("planned"))
            if planned:
                print(f"{planned} shot(s) still planned. Each asset must run at least its shot's "
                      "time; put it in and remove 'planned' before its beat is rendered.")
            return 0
    else:
        b.load_timeline(len(b.scenes))

    plan, warnings = b.plan(len(b.scenes))
    if stage in ("shots", "all"):
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)
        only = None
        if args.beat:
            ids = {str(s.get("id")): i for i, s in enumerate(b.scenes)}
            unknown = [x for x in args.beat if x not in ids]
            if unknown:
                sys.exit(f"Unknown beat id(s): {', '.join(unknown)}")
            only = {ids[x] for x in args.beat}
        n = b.render(plan, only)
        considered = len([p for p in plan if only is None or p[0] in only])
        print(f"Shots: {n} rendered, {considered - n} unchanged (cached)")
        if stage == "shots":
            return 0

    total = sum(x["dur"] for x in b.timeline)
    ass = os.path.join(b.work, "subs.ass")
    if stage == "subs":
        b.subtitles(everything, ass)
        print(f"Captions: {ass}")
        return 0
    if stage == "audio":
        print(f"Audio: {b.audio(everything, b.work)}")
        return 0
    b.write_shot_list(plan, everything, os.path.join(b.work, "shot_list.json"))
    if stage == "sync":
        return 0 if check_sync.report(os.path.abspath(b.out), ass) else 1
    if stage == "mux":
        audio = os.path.join(b.work, "audio.m4a")
        if not os.path.exists(ass) or not os.path.exists(audio):
            sys.exit("Captions or audio missing; run --stage subs and --stage audio first.")
        videos, frames = b.shot_files(plan, everything)
        out, total = b.mux(videos, frames, audio, ass, b.out)
    else:   # all
        out, ass, total = b.assemble(everything, b.work, b.out, plan)

    ok = self_check(out, total, b.max_dur, b.work)
    print_table(b.pace_rows)
    print("Shots:")
    for x in b.timeline:
        s = b.scenes[x["i"]]
        print(f"  {x['start']:6.2f}-{x['start'] + x['dur']:6.2f}s  {s.get('id')} [{s.get('material')}] "
              f"label={' | '.join(source_label(sh) for sh in expand_shots(s))!r}")
    if stage == "all":
        ok = check_sync.report(out, ass) and ok
    hold = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        "check_card_hold.py"), out,
                           "--shots", os.path.join(b.work, "shot_list.json")])
    ok = hold.returncode == 0 and ok
    print("NEXT: run the independent verification gate (SKILL.md) before delivery.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
