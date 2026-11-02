"""Caption phrasing, Whisper word timing and word-by-word ASS writing (see build_reel.py)."""

from reel_common import *  # noqa: F401,F403


DANGLERS = {"the", "a", "an", "to", "of", "for", "and", "or", "but", "no", "not",
            "its", "their", "his", "her", "this", "that", "about", "than",
            "through", "over", "with", "by", "at", "in", "on", "from", "into",
            "as", "if", "so", "when", "across", "after", "before", "between",
            "because", "while", "since", "around", "under", "until",
            "is", "are", "was", "were", "be"}
SPLIT_BEFORE = {"to", "for", "and", "or", "but", "across", "from", "with", "by",
                "at", "in", "on", "of", "over", "through", "that", "which",
                "who", "after", "before", "because", "while", "since",
                "about", "around", "nearly", "almost",
                # auxiliaries start the predicate: "a compromised laptop / may be involved"
                "may", "might", "can", "could", "will", "would", "should",
                "has", "have", "had", "is", "are", "was", "were"}
NUMBER_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "point", "hundred", "thousand",
                "million", "billion", "trillion", "percent"}


def chunk_words(words):
    """Split a clause into 2-5 word chunks by splitting near the middle,
    recursively. A split never leaves a chunk ending on an article,
    preposition or conjunction (never "rejected the" / "MSCI claim."), never
    falls inside a spoken number ("five point / five"), and never leaves a
    one-word chunk. If no clean split exists the clause stays whole."""
    def bare(w):
        return w.strip(".,;:!?\"'").lower()

    def is_num(w):
        b = bare(w)
        return b in NUMBER_WORDS or b.replace(".", "").replace("$", "").isdigit()

    if len(words) <= 5:
        return [words]
    mid, n = len(words) / 2, len(words)
    # Prefer a split that keeps both parts at 5 words or fewer, then one
    # that starts the new chunk with a preposition or conjunction (a
    # natural phrase break), then the one nearest the middle.
    order = sorted(range(2, n - 1), key=lambda k: (max(k, n - k) > 5,
                                                   bare(words[k]) not in SPLIT_BEFORE,
                                                   abs(k - mid)))
    for k in order:
        if bare(words[k - 1]) in DANGLERS:
            continue
        if is_num(words[k - 1]) and is_num(words[k]):
            continue
        # Keep a run of capitalised words (a name: "North Korea's") together.
        if words[k - 1][:1].isupper() and words[k][:1].isupper():
            continue
        return chunk_words(words[:k]) + chunk_words(words[k:])
    return [words]


ABBREVIATIONS = {"mr.", "mrs.", "ms.", "dr.", "st.", "no.", "vs.", "etc.", "inc.",
                 "co.", "corp.", "jan.", "feb.", "aug.", "sept.", "oct.", "nov.", "dec."}


def split_sentences(text):
    """Sentences, without splitting after abbreviations ("p.m.", "U.S.",
    "Dr.") and with one-word sentences merged into the previous one."""
    sents, cur = [], []
    for w in text.split():
        cur.append(w)
        low = w.lower().rstrip("\"')")
        is_abbr = low in ABBREVIATIONS or re.fullmatch(r"(?:[a-z]\.){2,}", low) is not None
        if low[-1:] in ".!?" and not is_abbr:
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    merged = []
    for sent in sents:
        if merged and (len(sent) < 2 or len(merged[-1]) < 2):
            merged[-1].extend(sent)   # no one-word caption phrase, at the start or end
        else:
            merged.append(sent)
    return [" ".join(x) for x in merged]


def chunk_narration(narration):
    """Chunk per clause (split after . ! ? ; : and commas) so no chunk starts
    mid-sentence or crosses a clause; clauses of one word join the next."""
    chunks = []
    for sent in split_sentences(narration):
        clauses, cur = [], []
        for w in sent.split():
            cur.append(w)
            if w[-1] in ",;:" and len(cur) >= 2:
                clauses.append(cur)
                cur = []
        if cur:
            if len(cur) < 2 and clauses:
                clauses[-1].extend(cur)
            else:
                clauses.append(cur)
        for cl in clauses:
            chunks.extend([" ".join(c) for c in chunk_words(cl)])
    return chunks or [""]


def fmt_ass(sec):
    # Round down: a cut at frame time 20.5667s must start the caption at
    # 20.56, not 20.57, or the old caption stays up one frame into the cut.
    cs = int(sec * 100 + 1e-6)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# --- timing: where each word is spoken -------------------------------------------

def speech_segments(path, threshold_db=-40, min_pause=0.08, highpass=None, start=None, dur=None):
    """Spoken stretches [(start, end), ...] in seconds, from ffmpeg silencedetect.

    highpass (Hz) removes the low music bed (110/165 Hz tones under 400 Hz)
    so pauses can be measured on a finished reel, not only on narration."""
    af = (f"highpass=f={highpass}," if highpass else "") + \
        f"silencedetect=n={threshold_db}dB:d={min_pause}"
    cmd = ["ffmpeg", "-v", "info"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-af", af, "-f", "null", "-"]
    r = run(cmd, check=False)
    total = dur if dur is not None else probe_duration(path)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r.stderr)]
    silences = []
    for k, s in enumerate(starts):
        e = ends[k] if k < len(ends) else total
        silences.append((max(0.0, s), min(total, e)))
    segs, t = [], 0.0
    for s, e in silences:
        if s > t + 1e-3:
            segs.append((t, s))
        t = max(t, e)
    if t < total - 1e-3:
        segs.append((t, total))
    return segs


WHISPER_MODEL = os.environ.get("REEL_WHISPER_MODEL", "small.en")


def whisper_words(path, prompt=""):
    """[(start, end, token)] for every word Whisper hears in an audio file,
    or None when no Whisper package is installed. The script is passed as
    the initial prompt, so names and figures are spelled as written."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(path, language="en", word_timestamps=True,
                                   initial_prompt=prompt or None, vad_filter=False)
        return [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or [])]
    except ImportError:
        pass
    try:
        import whisper
        res = whisper.load_model(WHISPER_MODEL).transcribe(
            path, language="en", word_timestamps=True, initial_prompt=prompt or None)
        return [(w["start"], w["end"], w["word"].strip())
                for s in res["segments"] for w in s.get("words", [])]
    except ImportError:
        return None


def norm_word(w):
    """Spelling-insensitive form for matching script words to Whisper
    tokens: "94%" == "94 percent", "$6.3" == "$6" + ".3", "U.S." == "US"."""
    w = w.lower().replace("%", "percent").replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", w)


def edit_distance(a, b):
    """Levenshtein distance between two strings."""
    prev = list(range(len(b) + 1))
    for x, ca in enumerate(a, 1):
        cur = [x]
        for y, cb in enumerate(b, 1):
            cur.append(min(prev[y] + 1, cur[y - 1] + 1, prev[y - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# Seconds per letter, for placing a word the recogniser missed at the very
# start of a beat (it ends where the first heard word begins).
SEC_PER_LETTER = 0.07


def match_words(script, tokens, notes=None):
    """Start time of every script word, from Whisper tokens.

    Split figure tokens are merged back first ("$6" + ".3" -> "$6.3",
    "94" + "%" -> "94%"): tokens are joined until they spell the script
    word. A token that spells several script words ("can't" style
    contractions, hyphenated words) gives them times spread over the token
    by length.

    Two recogniser slips are tolerated, because the voice said the word
    and only Whisper got it wrong; each is recorded in `notes` (a list)
    for the listen-through:
    - a name spelled slightly differently: a capitalised word in mid
      sentence, 4+ letters, within 1 letter edit (2 for 8+ letters) of
      what was heard ("Pati" heard as "Patti", "Nakamoto" as "Nakomoto");
    - the first spoken word of the beat missed entirely, when the rest
      lines up ("Then fuel..." heard as "fuel..."). Whisper often drops the
      opening word of a clip that starts right on speech. It is placed
      just before the first heard word.
    Anything else raises ValueError at the first word that doesn't match,
    because a caption must show exactly what was said: a dropped or
    changed word mid-beat, a changed common word, a second missed word,
    extra words."""
    words = script.split()
    toks = [(s, e, norm_word(t), t) for s, e, t in tokens if norm_word(t)]
    starts, i, j = [None] * len(words), 0, 0
    first = next((k for k, w in enumerate(words) if norm_word(w)), None)
    skipped = False
    notes = notes if notes is not None else []

    def context(k, seq, n=4):
        return " ".join(seq[max(0, k - n):k + n])

    def is_name(k):
        w = words[k].lstrip("\"'“‘(")
        if not w[:1].isupper() or not norm_word(w).isalpha() or len(norm_word(w)) < 4:
            return False
        prev = words[k - 1].rstrip("\"'”’)") if k else ""
        return bool(prev) and not prev.endswith((".", "!", "?", ":"))

    def span(i, j):
        """(script indices, token indices) of the exact match starting at
        script word i and token j, or None."""
        si, sj, A, B = [i], [j], norm_word(words[i]), toks[j][2]
        while A != B:
            if A.startswith(B) and j + 1 < len(toks):
                j += 1
                sj.append(j)
                B += toks[j][2]
            elif B.startswith(A) and i + 1 < len(words):
                i += 1
                if norm_word(words[i]):
                    si.append(i)
                    A += norm_word(words[i])
            else:
                return None
        return si, sj

    def near_name(i, j):
        """Token indices (1-3 joined tokens) that spell name i within the
        allowed edit distance, or None."""
        if not is_name(i):
            return None
        a = norm_word(words[i])
        limit = 1 if len(a) < 8 else 2
        B = ""
        for k in range(j, min(j + 3, len(toks))):
            B += toks[k][2]
            if edit_distance(a, B) <= limit:
                return list(range(j, k + 1))
        return None

    while i < len(words):
        a = norm_word(words[i])
        if not a:                         # a lone dash or symbol: not spoken
            i += 1
            continue
        if j >= len(toks):
            raise ValueError(f"word {i + 1} {words[i]!r} was never heard "
                             f"(script: ...{context(i, words)}...)")
        m = span(i, j)
        if m is None:
            sj = near_name(i, j)
            if sj:
                m = [i], sj
                notes.append(f"name {words[i]!r} heard as "
                             f"{' '.join(toks[k][3] for k in sj)!r}; captioned as written")
        if m is None and i == first and not skipped:
            nxt = next((k for k in range(i + 1, len(words)) if norm_word(words[k])), None)
            if nxt is not None and (span(nxt, j) or near_name(nxt, j)):
                skipped = True
                starts[i] = max(0.0, toks[j][0] - SEC_PER_LETTER * len(a))
                notes.append(f"first word {words[i]!r} not heard by Whisper; placed at "
                             f"{starts[i]:.2f}s, just before {toks[j][3]!r}. Check by ear "
                             "that the voice says it")
                i = nxt
                continue
        if m is None:
            heard = " ".join(t[3] for t in toks[max(0, j - 3):j + 4])
            raise ValueError(f"word {i + 1} {words[i]!r} doesn't match what was "
                             f"heard (script: ...{context(i, words)}...; "
                             f"heard: ...{heard}...)")
        si, sj = m
        i = si[-1]
        j = sj[-1]
        t0, t1 = toks[sj[0]][0], toks[sj[-1]][1]
        total = sum(len(norm_word(words[k])) for k in si) or 1
        acc = 0
        for k in si:
            starts[k] = t0 + (t1 - t0) * acc / total
            acc += len(norm_word(words[k]))
        i, j = i + 1, j + 1
    if j < len(toks):
        extra = " ".join(t[3] for t in toks[j:j + 6])
        raise ValueError(f"Whisper heard words after the script ends: {extra!r}")
    # Unspoken symbols take the time of the word before them.
    for k in range(len(starts)):
        if starts[k] is None:
            starts[k] = starts[k - 1] if k else 0.0
    return starts


def apply_nudges(words, starts, nudges, where):
    """Shift single word times by hand: {"$6.3": -0.2, "the#2": 0.1}
    (word as written in the narration; "#n" picks its nth occurrence).
    Only the named words move; times stay in order."""
    out = list(starts)
    for key, shift in (nudges or {}).items():
        word, _, nth = key.partition("#")
        hits = [k for k, w in enumerate(words) if w == word or w.strip(".,;:!?\"'") == word]
        n = int(nth or 1)
        if len(hits) < n:
            raise ValueError(f"{where}: caption_nudge {key!r} names no word in the narration")
        out[hits[n - 1]] += float(shift)
    for k in range(1, len(out)):
        out[k] = max(out[k], out[k - 1] + 0.02)
    return [max(0.0, t) for t in out]


def phrase_times(narration, word_starts, beat_start, speak, skip=()):
    """One beat's caption phrases, in reel time: [(words, starts, end)].

    A phrase appears with its first spoken word and stays until the next
    phrase's first word (the last phrase until the narration ends), so a
    phrase never lingers past the voice into the next beat. A phrase that
    would still be up when a `skip` span (the end card) starts is left out
    whole, never shown as a fragment the card cuts off.

    Returns (phrases, dropped): dropped are the (start, end) spans of
    phrases left out before a skip span, to mark as uncaptioned on purpose."""
    words = narration.split()
    phrases, used = [], 0
    for chunk in chunk_narration(narration):
        n = len(chunk.split())
        if chunk:
            phrases.append((words[used:used + n],
                            [beat_start + t for t in word_starts[used:used + n]]))
        used += n
    out, dropped = [], []
    for k, (ws, ts) in enumerate(phrases):
        end = phrases[k + 1][1][0] if k + 1 < len(phrases) else beat_start + speak
        end = max(end, ts[-1] + 1 / FPS)
        cut = [a for a, b in skip if a < end and b > ts[0]]
        if cut:
            if ts[0] < min(cut):
                dropped.append((ts[0], min(cut)))
            continue
        out.append((ws, ts, end))
    return out, dropped


def ass_font_size():
    """The ASS Fontsize that renders glyphs at CAPTION_SIZE px (em size, as
    Pillow measures it). libass sizes a font by its full line height
    (ascent + descent), which for DejaVu Sans is about 1.16 em, so a plain
    "38" in the ASS file would render the text about 14% smaller than the
    layout measured."""
    a, d = font(BOLD, 100).getmetrics()
    return round(CAPTION_SIZE * (a + d) / 100, 1)


def layout_phrase(words, top):
    """Each word's fixed top-left position: the whole phrase is wrapped by
    measured width first (at most CAPTION_MAX_W per line), each line is
    centred at its full width, then every word keeps its place while the
    phrase is up. Spoken words never move: there is no re-centring on the
    words revealed so far."""
    from PIL import Image, ImageDraw
    f = font(BOLD, CAPTION_SIZE)
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = wrap(d, " ".join(words), f, CAPTION_MAX_W)
    pos, k = [], 0
    for li, line in enumerate(lines):
        lw = d.textlength(line, font=f)
        x0 = (W - lw) / 2
        ws = line.split()
        for n, w in enumerate(ws):
            prefix = " ".join(ws[:n]) + (" " if n else "")
            pos.append((round(x0 + d.textlength(prefix, font=f)), top + li * CAPTION_LINE_H))
            k += 1
    widest = max(d.textlength(ln, font=f) for ln in lines)
    return pos, len(lines), widest


def caption_events(phrases, tops):
    """ASS events for word-by-word captions. Each word is its own event at
    its own fixed \\pos: yellow from the moment it is spoken until the next
    word, then white until the phrase is replaced. Returns (events,
    warnings); an event is (start, end, name, text) with name "p<phrase>w<word>"."""
    events, warnings = [], []
    for pi, ((words, starts, end), top) in enumerate(zip(phrases, tops)):
        pos, n_lines, widest = layout_phrase(words, top)
        if n_lines > CAPTION_LINES:
            warnings.append(f"caption {' '.join(words)!r} needs {n_lines} lines "
                            f"(max {CAPTION_LINES}); shorten the narration phrase.")
        if widest > CAPTION_MAX_W:
            warnings.append(f"caption word in {' '.join(words)!r} is {widest:.0f}px wide, "
                            f"over {CAPTION_MAX_W}px; it will clip.")
        for k, (w, t) in enumerate(zip(words, starts)):
            nxt = starts[k + 1] if k + 1 < len(words) else end
            x, y = pos[k]
            name = f"p{pi}w{k}"
            tag = f"{{\\an7\\pos({x},{y})"
            if nxt > t:
                events.append((t, nxt, name, f"{tag}\\1c&H00CCFF&}}{w}"))      # current: yellow
            if end > nxt:
                events.append((nxt, end, name, f"{tag}\\1c&HFFFFFF&}}{w}"))    # spoken: white
    return events, warnings


def ass_header():
    return [
    "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
    "WrapStyle: 2", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
    "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    # Bold sans, white, thick black outline, soft drop shadow (BackColour is
    # the shadow colour, half transparent). No box: BorderStyle 1.
    f"Style: Cap,DejaVu Sans,{ass_font_size()},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
    f"1,0,0,0,100,100,0,0,1,{CAPTION_OUTLINE},{CAPTION_SHADOW},7,0,0,0,1",
    "", "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]


def write_ass(path, events, no_caption=()):
    """events: [(start, end, name, text)] in seconds. no_caption: spans that
    carry narration but deliberately no captions (the end card); written as
    Comment lines so the sync check skips them."""
    lines = ass_header()
    for start, end in no_caption:
        lines.append(f"Comment: 0,{fmt_ass(start)},{fmt_ass(end)},NoCaption,,0,0,0,,end card")
    for start, end, name, text in sorted(events, key=lambda e: (e[0], e[2])):
        lines.append(f"Dialogue: 0,{fmt_ass(start)},{fmt_ass(end)},Cap,{name},0,0,0,,{text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _ass_lines(path, kind):
    def sec(t):
        h, m, s = t.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith(kind + ":"):
                parts = line.rstrip("\n").split(",", 9)
                out.append((sec(parts[1]), sec(parts[2]), parts[3], parts[4], re.sub(r"\{[^}]*\}", "", parts[9])))
    return out


def read_ass_words(path):
    """[(reveal time, word, phrase index)] for every caption word, in order."""
    first = {}
    for start, _, _, name, text in _ass_lines(path, "Dialogue"):
        m = re.fullmatch(r"p(\d+)w(\d+)", name)
        if m:
            key = (int(m.group(1)), int(m.group(2)))
            if key not in first or start < first[key][0]:
                first[key] = (start, text)
    return [(first[k][0], first[k][1], k[0]) for k in sorted(first)]


def read_ass(path):
    """[(start, end, text)]: one entry per caption phrase (from its first
    word's reveal until it is replaced). Files with plain one-line events
    (older builds) read as they are."""
    phrases = {}
    plain = []
    for start, end, _, name, text in _ass_lines(path, "Dialogue"):
        m = re.fullmatch(r"p(\d+)w(\d+)", name)
        if not m:
            plain.append((start, end, text))
            continue
        p = phrases.setdefault(int(m.group(1)), {"start": start, "end": end, "words": {}})
        p["start"], p["end"] = min(p["start"], start), max(p["end"], end)
        p["words"][int(m.group(2))] = text
    out = [(p["start"], p["end"], " ".join(p["words"][k] for k in sorted(p["words"])))
           for _, p in sorted(phrases.items())]
    return sorted(out + plain)


def read_no_caption(path):
    """[(start, end)] spans the build left uncaptioned on purpose."""
    return [(s, e) for s, e, style, _, _ in _ass_lines(path, "Comment") if style == "NoCaption"]
