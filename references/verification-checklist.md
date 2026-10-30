# Verification checklist (run by the independent verifier)

Every item is PASS or FAIL with evidence (a measured value, a timestamp, or a frame path). Measure the rendered file, never the planned timeline. Do not edit or re-render anything. The rules behind each item are in SKILL.md's "Visual spec".

## Contents
- A. Measurement commands
- B. Technical items
- C. Editorial items
- D. Visual items
- E. Report format

## A. Measurement commands

Replace `R` with the reel path and `OUT` with your output folder. They need ffmpeg, ffprobe and Python 3.

```bash
# Specs and duration
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of compact R
# Loudness (read "I:" in the summary)
ffmpeg -i R -af ebur128 -f null - 2>&1 | tail -12
# Silence gaps
ffmpeg -i R -af silencedetect=n=-45dB:d=0.3 -f null - 2>&1 | grep silence_
# Cut times (also check against the shot list: similar-looking cuts may not register)
ffmpeg -i R -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -o "pts_time:[0-9.]*"
# Holds over 1s
ffmpeg -i R -vf "freezedetect=n=0.001:d=1" -f null - 2>&1 | grep -E "freeze_(start|duration)"
# Motion profile: median frame difference and % fully still frames
ffmpeg -i R -vf "scale=180:-1,format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG" -f null - 2>&1 \
  | grep -o "YAVG=[0-9.]*" | cut -d= -f2 \
  | python3 -c "import sys,statistics as s; v=[float(x) for x in sys.stdin]; print('median',round(s.median(v),3),'still%',round(100*sum(x<=0.05 for x in v)/len(v)))"
# Contact sheets: 2 fps across the whole reel (16 frames per sheet)
ffmpeg -i R -vf "fps=2,scale=180:-1,tile=8x2" OUT/sheet_%02d.png
# Per-shot strip at 8 fps (repeat for each shot; S = shot start, D = duration)
ffmpeg -ss S -t D -i R -vf "fps=8,scale=180:-1,tile=8x2" -frames:v 1 OUT/shot_S.png
# Full-size frame for close inspection
ffmpeg -ss T -i R -frames:v 1 OUT/frame_T.png
```

Inspect the images themselves; do not infer them from the commands' output.

## B. Technical items

- [ ] **B1 Duration**: within the agreed length (default under 60s), and matches the shot list's total within 0.1s. The video stream is not shorter than the audio.
- [ ] **B2 Specs**: 720×1280, h264, AAC 48 kHz stereo.
- [ ] **B3 Loudness**: integrated loudness between −15.5 and −13.5 LUFS (target −14).
- [ ] **B4 Silence**: no gap over 0.3s except the final 0.5s; no narration word cut (listen at every cut point).
- [ ] **B5 Shot length**: no shot over 4s except headline cards and timeline shots (≤5s); shots mostly 1–3s.
- [ ] **B6 Holds**: list every freezedetect hold over 1s with its timestamp. FAIL if a frame is frozen across a cut, or if a shot never changes at all (it should at least creep).
- [ ] **B7 Clean cuts**: on the 2 fps sheets and around each cut, no frame from a previous scene leaks across a cut, and no frame mixes two layouts.
- [ ] **B8 Motion profile**: report the median frame difference and still %. FAIL if still % is over 50 (the reference reel is 12%). Then check the 8 fps per-shot strips:
  - FAIL if a subtitle, tag, source label, or a headline over a photo moves within a shot.
  - FAIL if the whole composited frame zooms or pans.
  - FAIL if a move is not one of the allowed moves in SKILL.md's Motion table, or breaks its parameters (creep over 102%, a fast move over 0.6s other than a wipe or graphic zoom, a wipe covering subtitles for more than 0.3s, two fast moves at once).
  - List each move found, with its timestamp and type.

## C. Editorial items (check against facts.md)

- [ ] **C1 Status tags**: every claim on screen carries the status tag facts.md gives it (CONFIRMED, STATED BY, ESTIMATE, UNCONFIRMED, DISPUTED, ALLEGED, DENIED, DISINFORMATION POST); no tag is stronger than the sources support.
- [ ] **C2 Confirmed vs not**: each claim's counterpart (denial, confirmed figure, company statement) appears in the same scene; no confirmed fact and unconfirmed claim are merged into one statement.
- [ ] **C3 False or unverified material**: every appearance of an image that is itself false or unverified carries its tag; none opens the reel, appears on the end card, or sits under a true line.
- [ ] **C4 Figures and quotes**: each matches facts.md, shows its source on screen, and says what it measures; where sources conflict, the range or disagreement is visible; changing figures carry an "AS OF" label; no invented chart.
- [ ] **C5 Attribution**: no perpetrator, operator or motive is named unless facts.md shows a source establishing it; comparisons and patterns are labelled as such.
- [ ] **C12 Narration transcript**: read every narration line in the manifest and check it against facts.md. FAIL if a line states something not in facts.md, credits it to the wrong party (for example "analysts" for a news outlet's wording), or is stronger than its source: "lost" for "impact", "blame" or "did it" for "likely" or "assess", "was" for "may be", a figure without "about" where the source estimates. FAIL if a line merges a confirmed fact with an unconfirmed claim. Quote the line and the facts.md row for every FAIL.
- [ ] **C13 Human-sounding narration**: join all narration lines and check them against SKILL.md "Write like a person talking". FAIL if any four sentences in a row are within 2 words of each other in length or share the same "[Source] [verb] [figure]" template; if any organisation is named more than about three times; if the script uses a stock AI marker (moreover, furthermore, notably, in summary, it's worth noting, delve, landscape, crucial, a stark reminder, here's the thing, "not just X, but Y"); if narration contains a semicolon, parenthesis or colon; if a scene re-narrates figures already said; or if the closing line is generic. Also read every scene boundary aloud (last line of scene N, then the first line of N+1): FAIL any transition where the next line doesn't follow from the one before it (no answer, contrast, next step or shared word or idea) or where a section change has no spoken bridge. Quote the offending lines. A rewrite that weakens a hedge or attribution fails C12 instead.
- [ ] **C14 Hook**: read only the first scene's narration and headline, as a viewer with no context. FAIL if it does not say who (with an identifier when the name isn't household), what happened in a plain verb, and the scale or stakes; if it is under about 12 words or runs past 7s; or if any part is stronger than facts.md. Quote the hook.
- [ ] **C11 Timeline** (if the reel has one): every event matches a timeline row in facts.md (time, wording, source); events run in chronological order; the time zone is stated on screen ("ALL TIMES UTC"); each event names its source; an estimate or allegation in an event says so (for example "(estimate)"); each line stays on screen long enough to read (at least about 1.2s from appearing to the end of the shot).
- [ ] **C10 Sources**: every receipt traces to an original report, statement or post listed in facts.md; no aggregator or unsigned page is shown as evidence. Every screenshot visibly contains the wording it is used for (not hidden behind "Show more"), and its displayed time matches the label's time zone.
- [ ] **C6 Spelling**: every name in headlines, diagram nodes and labels matches facts.md exactly.
- [ ] **C7 AI honesty**: every AI shot is labelled "AI-GENERATED ILLUSTRATION", is ≤3s, and shows no real named person, real place presented as evidence, the alleged event, an organisation's building or logo, or news/social-post look-alikes. No AI visual suggests something the narration or sources don't support.
- [ ] **C8 Real clips**: labelled with account + date; muted; no second caption track or clip logo colliding with the headline or subtitle.
- [ ] **C9 Headline cards**: each is set in the reel's own style (not the outlet's page design or logo) and quotes only wording in facts.md; none could pass as a screenshot.

## D. Visual items

- [ ] **D1 Safe area**: no headline above y=120; no subtitle below y=1030; nothing cropped at any edge.
- [ ] **D2 Keep box**: for every image shot, compare the first and last frame with the source image and its `keep` box in the manifest. FAIL if any part of the keep box is cut off, hidden under a tag, headline or subtitle, or if a crop cuts through a word or turns a claim into a fragment anywhere on screen. FAIL if the keep box clearly misses what makes the image relevant (for example, it frames a logo but cuts the headline the narration refers to). Report an image whose text is unreadable even when shown whole as a trade-off.
- [ ] **D3 Overlap**: no headline overlaps its image; no subtitle sits half off its background or over busy text.
- [ ] **D4 Representative image**: every shot has one; no headline-only screen on plain colour. Count the headline-card shots, not counting the end card. FAIL if there are more than 2. Also FAIL for any headline card without an entry in facts.md "Visual fallbacks" showing that re-crop, the article's picture, another source and AI illustration were each tried and why each failed.
- [ ] **D5 Little text**: at most a 2–4 word headline per shot; no paragraph repeats the subtitle. Besides the headline and subtitle, a shot shows at most about 25 words of image text (a screenshot cropped to the account name and the claim's one or two lines). FAIL on a whole post, a paragraph, or several posts, and FAIL when two text screenshots are cut back to back.
- [ ] **D6 Subtitles**: 2–5 words; ~30px bold monospace on a solid black box; no chunk ends on an article, preposition or conjunction, crosses a scene, or opens mid-sentence.
- [ ] **D7 Headline cards**: fill the card; body text readable (≥22px); single-word yellow highlights; each card used once.
- [ ] **D8 Diagram and map**: diagram nodes revealed on the narrated words; if facts.md marks a link as denied or disproved, the ✗ appears on that link at that beat (no ✗ when no link is denied). Map coastlines match Natural Earth, shown once, labelled "SCHEMATIC — NOT TO SCALE", with a generic arrow and no pipeline route.
- [ ] **D9 Label hierarchy**: source labels, tags and AI labels are present and readable; the source label is the small muted line between the tag and the headline, with nothing caption-like (no bar or text block) within 60px of the subtitle box; production notes are not shown.
- [ ] **D10 End card**: closing line, a full-story pointer that is a real screenshot of a referenced article page matching an article in facts.md, showing the outlet name or masthead, headline and byline, with either an absolute date in the screenshot or the capture date printed under it. FAIL on a recreated or headline-card pointer unless facts.md "Visual fallbacks" shows that every referenced article was tried and could not be captured; FAIL on a relative date ("13 hours ago") left in the screenshot, a crop with no outlet name, or any screenshot text that has been masked, blurred or retyped. Then check: one small disclosure line naming the AI voice, AI illustrations and sources; no silence after the final narration.
- [ ] **D11 One background**: every shot that shows a background (cards, diagrams, map sea, end card) uses the same blue (11, 74, 168), and blurred fill behind images is tinted with that blue. Sample a background pixel in each shot and FAIL on any other background colour. Full-bleed images and AI clips have no background and are exempt.

## E. Report format

```
VERDICT: PASS | FAIL
| # | Item | Result | Evidence (value / timestamp / frame) |
|---|------|--------|--------------------------------------|
| B1 | Duration | PASS | 48.50s; shot list 48.48s |
...
FAILS TO FIX (ranked, editorial first): ...
ACCEPTED TRADE-OFFS (if any): ...
```

VERDICT is PASS only if every item is PASS or an accepted trade-off that the spec explicitly allows (D2 readability).
