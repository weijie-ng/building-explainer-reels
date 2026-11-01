"""Manifest loading, beat/shot expansion and validation."""

from reel_common import *  # noqa: F401,F403


# Keys that belong to one visual. A shot never inherits these from its scene;
# headline and yellow_words do inherit, so shots can share the scene headline.
VISUAL_KEYS = ("image", "fit_image", "clip", "card", "diagram", "end_card",
               "timeline", "keep",
               "image_source", "full_bleed", "clip_mask",
               "clip_start", "clip_end", "move", "summary", "schematic", "stat", "wipe")


def expand_shots(scene):
    """A scene's shots: each "shots" entry inherits the scene's non-visual
    keys (narration, headline, material...) and supplies its own visual."""
    if not scene.get("shots"):
        return [dict(scene)]
    base = {k: v for k, v in scene.items() if k not in VISUAL_KEYS + ("shots",)}
    shots = [{**base, **sh} for sh in scene["shots"]]
    if scene.get("wipe") and "wipe" not in shots[0]:
        shots[0]["wipe"] = scene["wipe"]     # a beat's wipe opens its first shot
    return shots


def image_problem(path):
    """Why an image asset is unusable, or None. Catches downloads a CDN served
    as AVIF/WebP under a .png name that this Pillow can't read, and screenshots
    taken before lazy images loaded (a flat grey or white box)."""
    from PIL import Image, ImageStat
    try:
        with Image.open(path) as im:
            im.load()
            gray = im.convert("L")
    except Exception as e:
        return (f"cannot be read ({type(e).__name__}). Re-download as JPEG or PNG "
                "(send 'Accept: image/jpeg', or use f_jpg instead of f_auto).")
    if ImageStat.Stat(gray).stddev[0] < 4:
        return ("is almost blank (one flat colour). Likely captured before its images "
                "loaded; scroll them into view, wait for them to load, and recapture.")
    return None


MOVES = ("push", "pan", "inset")
SAVE_PROMPT = re.compile(r"\b(save (this|it|for later)|screenshot|bookmark|share this|"
                         r"keep this|pin this)\b", re.I)
STOP = {"that", "this", "with", "from", "what", "where", "when", "which", "there", "their",
        "about", "into", "have", "were", "will", "your", "they", "them", "then", "than"}


def content_words(text):
    return {w for w in re.findall(r"[a-z0-9$.']+", text.lower().replace("’", "'"))
            if len(w) > 3 and w not in STOP}


def last_sentence(text, question=False):
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]
    if question:
        qs = [x for x in sents if x.endswith("?")]
        return qs[-1] if qs else None
    return sents[-1] if sents else ""


def loop_back_problem(scenes):
    """None, or why the last narration doesn't loop back to the hook: it
    should echo the hook's open question (or promise), in matching or
    shortened wording, in one of its last two sentences, so it can ask the
    question again and then answer it in a short clause."""
    hook = " ".join(scenes[i].get("narration", "") for i in hook_indices(scenes))
    q = last_sentence(hook, question=True) or last_sentence(hook)
    text = scenes[-1].get("narration", "").strip()
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()][-2:]
    a = content_words(q)
    if not a or not any(content_words(x) for x in sents):
        return None
    for x in sents:
        b = content_words(x)
        if b and len(a & b) / min(len(a), len(b)) >= 0.6:
            return None
    end = " ".join(sents)
    return (f"the reel's last lines {end!r} don't loop back to the hook's "
            f"{'question' if q.endswith('?') else 'promise'} {q!r}. Echo it in one of the last "
            "two sentences (then answer it in a short clause), or set \"loop_back\": false if "
            "the user asked not to.")


def clip_info(path):
    """(duration, width, height) of a clip's video stream, or None."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height:format=duration", "-of", "json", path], check=False)
    try:
        j = json.loads(r.stdout)
        st = j["streams"][0]
        return float(j["format"]["duration"]), int(st["width"]), int(st["height"])
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def summary_text(sm):
    parts = [sm.get("title", ""), sm.get("sources", "")]
    for p in sm.get("panels", []):
        parts += [p.get("value", ""), p.get("label", ""), p.get("source", "")]
        for half in p.get("pair", []):
            parts += [half.get("title", ""), half.get("text", "")]
    return " ".join(x for x in parts if x)


def validate(scenes, args, man=None):
    man = man or {}
    errors, warnings = [], []
    hook = set(hook_indices(scenes))
    units = [(i, j, scene, s) for i, scene in enumerate(scenes)
             for j, s in enumerate(expand_shots(scene))]
    for i, j, scene, s in units:
        sid = scene.get("id", f"#{i}") + (f" shot {j + 1}" if scene.get("shots") else "")
        if s.get("material") not in MATERIALS:
            errors.append(f"scene {sid}: 'material' must be one of {sorted(MATERIALS)}, "
                          f"got {s.get('material')!r}.")
        for legacy in ("punch", "layout", "clip_crop_bottom", "background"):
            if legacy in s:
                warnings.append(f"scene {sid}: '{legacy}' is no longer used and is ignored "
                                "(stills zoom to their 'keep' box; mask clip captions with "
                                "'clip_mask'; one background colour for every shot).")
        if s.get("body"):
            warnings.append(f"scene {sid}: 'body' dropped (no double text); keep it in narration.")
        has_visual = any(s.get(k) for k in ("image", "clip", "card", "diagram", "summary",
                                            "timeline", "stat"))
        if not has_visual and not s.get("end_card") and not args.allow_plain:
            errors.append(f"scene {sid}: no image, clip, card, diagram or timeline. Add one, or "
                          "pass --allow-plain and justify it in the delivery notes.")
        for key in ("image", "clip", "audio"):
            if s.get(key) and not os.path.exists(s[key]):
                errors.append(f"scene {sid}: {key} file not found: {s[key]}")
        p = s.get("pointer") if isinstance(s.get("pointer"), dict) else {}
        for path in (s.get("image"), p.get("image"), (s.get("card") or {}).get("image")):
            if path and os.path.exists(path):
                problem = image_problem(path)
                if problem:
                    errors.append(f"scene {sid}: {path}: {problem}")
        if "weight" in s and not (isinstance(s["weight"], (int, float)) and s["weight"] > 0):
            errors.append(f"scene {sid}: shot 'weight' must be a number above 0, got {s['weight']!r}.")
        if s.get("timeline") is not None and not s["timeline"].get("events"):
            errors.append(f"scene {sid}: timeline needs at least one event.")
        for ev in (s.get("timeline") or {}).get("events", []):
            if not ev.get("time") or not ev.get("text"):
                errors.append(f"scene {sid}: every timeline event needs 'time' and 'text'.")
        if s.get("headline") and not s.get("end_card") and not s.get("summary"):
            _, hl = headline_lines(s["headline"])
            if len(hl) > HEADLINE_MAX_LINES:
                errors.append(f"scene {sid}: headline {s['headline']!r} needs {len(hl)} lines; the "
                              f"limit is {HEADLINE_MAX_LINES} (about 40 characters). Keep who + what, "
                              "drop the rest to the caption.")
            elif len(s["headline"].split()) < 3 and not s.get("card"):
                warnings.append(f"scene {sid}: headline {s['headline']!r} has under 3 words; check "
                                "a viewer reading only it knows who did what (SKILL.md, Headlines).")
        if s.get("card") and not all(s["card"].get(k) for k in ("outlet", "headline")):
            errors.append(f"scene {sid}: card needs 'outlet' and 'headline'.")
        elif s.get("card") and len(s["card"]["headline"].replace("…", " ").split()) > 10:
            errors.append(f"scene {sid}: card headline has "
                          f"{len(s['card']['headline'].replace('…', ' ').split())} words; the limit "
                          "is 10. Trim it to a verbatim excerpt, marking cut words with an ellipsis.")
        card_img = (s.get("card") or {}).get("image")
        if card_img and not os.path.exists(card_img):
            errors.append(f"scene {sid}: card image not found: {card_img}")
        elif card_img and not s["card"].get("image_source"):
            errors.append(f"scene {sid}: card image needs 'image_source' (e.g. 'IMAGE: CNA, 29 OCT 2026').")
        if s.get("card") and i == 0 and j == 0 and not card_img:
            errors.append(f"scene {sid}: a headline card that opens the reel needs a representative "
                          "'image' on the card (see SKILL.md, Headline cards).")
        if s.get("diagram") and not s["diagram"].get("nodes"):
            errors.append(f"scene {sid}: diagram needs 'nodes'.")
        mc = (s.get("diagram") or {}).get("motion_clip")
        if mc:
            if not os.path.exists(mc):
                errors.append(f"scene {sid}: diagram motion_clip not found: {mc}")
            elif not clip_info(mc):
                errors.append(f"scene {sid}: diagram motion_clip has no readable video: {mc}")
        p = s.get("pointer")
        if p is not None and not (isinstance(p, dict) and p.get("outlet")
                                  and (p.get("headline") or p.get("image"))):
            errors.append(f"scene {sid}: pointer needs 'outlet' and either 'headline' or 'image'.")
        elif isinstance(p, dict) and not p.get("image") and not p.get("no_screenshot"):
            errors.append(f"scene {sid}: end-card pointer needs 'image', a screenshot of a referenced "
                          "article page. A headline-only pointer needs 'no_screenshot' giving why "
                          "no referenced article could be captured.")
        if "keep" in s:
            k = s["keep"]
            if not (isinstance(k, list) and len(k) == 4 and all(0 <= v <= 1 for v in k)
                    and k[0] < k[2] and k[1] < k[3]):
                errors.append(f"scene {sid}: 'keep' must be [x0, y0, x1, y1] as fractions "
                              f"of the image with x0 < x1 and y0 < y1, got {k!r}.")
        if s.get("material") == "real" and (s.get("image") or s.get("clip")) \
                and not s.get("image_source"):
            errors.append(f"scene {sid}: real material needs 'image_source' "
                          "(outlet + date, or account + date).")
        for box in s.get("clip_mask", []):
            x, y, w, h = box
            if x <= 0 or y <= 0 or x + w >= W or y + h >= H:
                errors.append(f"scene {sid}: clip_mask {box} must sit strictly inside "
                              f"{W}x{H} (delogo fails at x=0 or on the frame edge).")
        if "label" in s or "label_color" in s:
            errors.append(f"scene {sid}: status tags ('label') are not used; carry the "
                          "claim's status in the wording. Only 'disinformation' adds a tag.")
        if s.get("disinformation") and ((i == 0 and j == 0) or s.get("end_card")):
            errors.append(f"scene {sid}: disinformation material may not open the reel "
                          "or appear on the end card.")
        if "move" in s and (s["move"] not in MOVES or not s.get("image") or s.get("card")):
            errors.append(f"scene {sid}: 'move' must be one of {', '.join(MOVES)}, on a still "
                          f"image shot, got {s['move']!r}.")
        if i in hook and s.get("full_bleed") is False:
            errors.append(f"scene {sid}: the hook fills the frame; \"full_bleed\": false is not "
                          "allowed on a hook shot. Tighten the keep box to the subject, pick a "
                          "photo that fits 9:16, or use a clip.")
        if i in hook and s.get("image") and not s.get("clip") and not s.get("card"):
            warnings.append(f"scene {sid}: the hook is a still image. Footage or a Muse video "
                            "holds the first second far better; log in facts.md why no clip "
                            "works if you keep the still.")
        st = s.get("stat")
        if st is not None:
            if not (isinstance(st, dict) and st.get("value") and st.get("label")):
                errors.append(f"scene {sid}: 'stat' needs 'value' and 'label'.")
            elif not st.get("source"):
                errors.append(f"scene {sid}: stat {st['value']!r} needs 'source' (outlet + date): "
                              "a figure always shows where it comes from.")
            elif len(str(st["value"])) > 12:
                errors.append(f"scene {sid}: stat value {st['value']!r} is over 12 characters; "
                              "put the words in 'label'.")
            if isinstance(st, dict) and st.get("motion_clip") and not os.path.exists(st["motion_clip"]):
                errors.append(f"scene {sid}: stat motion_clip not found: {st['motion_clip']}")
        if s.get("wipe") not in (None, False, True, "left", "up"):
            errors.append(f"scene {sid}: 'wipe' must be \"left\" or \"up\", got {s['wipe']!r}.")
        if s.get("wipe") and i == 0 and j == 0:
            errors.append(f"scene {sid}: the first shot has nothing to wipe from.")
        if i in hook and s.get("image") and not s.get("card") and not s.get("clip") \
                and s.get("move") not in MOVES:
            errors.append(f"scene {sid}: the hook can't be a still image. Use a clip (real "
                          "footage or an AI video), or give the image a 'move' (push, pan "
                          "or inset) so it is processed into motion.")
        if s.get("clip") and os.path.exists(s["clip"]):
            info = clip_info(s["clip"])
            if not info:
                errors.append(f"scene {sid}: clip has no readable video stream: {s['clip']}")
            else:
                cdur, cw, ch = info
                if s.get("material") == "ai" and abs(cw / ch - W / H) > 0.05 and not s.get("keep"):
                    warnings.append(f"scene {sid}: AI clip is {cw}x{ch}, not 9:16; the build "
                                    "crops it to the middle. Generate it at 720x1280, or set "
                                    "'keep' to say which part to keep.")
                left = cdur - float(s.get("clip_start", 0))
                if left < 1.0:
                    errors.append(f"scene {sid}: clip has {left:.2f}s left after clip_start.")
        if s.get("summary") is not None:
            sm = s["summary"]
            if not isinstance(sm, dict) or not sm.get("panels"):
                errors.append(f"scene {sid}: 'summary' needs 'panels' (figures with "
                              "'value' and 'label', or distinctions with 'pair').")
            else:
                for pnl in sm["panels"]:
                    if not (pnl.get("value") or len(pnl.get("pair", [])) == 2):
                        errors.append(f"scene {sid}: each summary panel needs a 'value' or a "
                                      f"'pair' of two halves, got {pnl!r}.")
                said = SAVE_PROMPT.search(summary_text(sm) + " " + s.get("headline", ""))
                if said and not man.get("allow_save_prompt"):
                    errors.append(f"scene {sid}: the summary card says {said.group(0)!r}. It "
                                  "never tells the viewer what to do with it unless the user "
                                  "asked (set \"allow_save_prompt\": true).")
            if i != len(scenes) - 1:
                errors.append(f"scene {sid}: the summary card belongs in the last beat (the end).")
        if s.get("map"):
            errors.append(f"scene {sid}: the build no longer draws maps. Generate the map with "
                          "Muse (SKILL.md, \"Map\") and pass it as \"clip\" or \"image\" with "
                          "\"material\": \"ai\" and \"schematic\": true.")
        if s.get("schematic") and s.get("material") != "ai":
            errors.append(f"scene {sid}: 'schematic' marks an AI-generated map; set "
                          "\"material\": \"ai\".")
        nudge = s.get("caption_nudge")
        if nudge is not None and (not isinstance(nudge, dict) or
                                  not all(isinstance(v, (int, float)) and abs(v) <= 1
                                          for v in nudge.values())):
            errors.append(f"scene {sid}: 'caption_nudge' must map a narration word to a shift "
                          "of at most 1s, e.g. {\"$6.3\": -0.2}.")
        if s.get("end_card") and i != len(scenes) - 1:
            warnings.append(f"scene {sid}: end card is not the last scene.")
        if isinstance(s.get("pointer"), dict) and s["pointer"].get("image")                 and not os.path.exists(s["pointer"]["image"]):
            errors.append(f"scene {sid}: pointer image not found: {s['pointer']['image']}")
        if s.get("end_card") and not s.get("disclosure"):
            warnings.append(f"scene {sid}: end card has no disclosure line.")
    if man.get("loop_back", True) and len(scenes) > 1:
        problem = loop_back_problem(scenes)
        if problem:
            errors.append(problem)
    maps = [s for sc in scenes for s in expand_shots(sc) if s.get("schematic")]
    if len(maps) > 1:
        warnings.append("more than one map shot; the spec shows the map once.")
    wipes = sum(1 for _, _, _, sh in units if sh.get("wipe"))
    if wipes > 3:
        warnings.append(f"{wipes} graphic wipes; use 1-3 per reel, at section turns.")
    return errors, warnings


def check_tools(scenes, tts):
    missing = []
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            missing.append(f"{tool} not found on PATH.")
    if any(not s.get("audio") for s in scenes) and not (os.path.exists(tts) or shutil.which(tts)):
        missing.append(f"TTS command not found: {tts}. Pass --tts, set REEL_TTS, "
                       "or give every scene a pre-made 'audio' file.")
    import importlib.util
    if not any(importlib.util.find_spec(m) for m in ("faster_whisper", "whisper")):
        missing.append("No Whisper package: captions are timed from a Whisper pass on the "
                       "narration, never spaced evenly. pip install faster-whisper")
    for f in (BOLD, REG, MONO_BOLD, MONO):
        if not os.path.exists(f):
            missing.append(f"Font not found: {f}. Set REEL_FONT_DIR to a folder with DejaVu fonts.")
    return missing


def load_manifest(path):
    """The manifest dict, with asset paths resolved relative to it."""
    with open(path, encoding="utf-8") as f:
        man = json.load(f)
    scenes = man.get("scenes") or []
    if not scenes:
        sys.exit("Manifest has no scenes (beats).")
    base_dir = os.path.dirname(os.path.abspath(path))

    def resolve(d, key):
        if isinstance(d, dict) and d.get(key) and not os.path.isabs(d[key]):
            d[key] = os.path.join(base_dir, d[key])

    for s in [x for sc in scenes for x in [sc] + sc.get("shots", [])]:
        if s.get("fit_image") and not s.get("image"):
            s["image"] = s["fit_image"]   # legacy key; fit is now the default
        for key in ("image", "clip", "audio"):
            resolve(s, key)
        resolve(s.get("card"), "image")
        resolve(s.get("pointer"), "image")
        resolve(s.get("diagram"), "motion_clip")
    return man


def hook_indices(scenes):
    """The hook's beats: the leading beats whose id starts with "hook", or
    else just the first beat."""
    n = 0
    while n < len(scenes) and str(scenes[n].get("id", "")).lower().startswith("hook"):
        n += 1
    return list(range(max(n, 1)))
