# Verification checklist (run by the independent verifier)

Every item is PASS or FAIL with evidence (a measured value, a timestamp, or a frame path). Measure the rendered file, never the planned timeline. Do not edit or re-render anything. Work from the files you were given (reel, manifest, facts.md, assets folder). You may use web search and page-text fetches for D4; do not download assets or capture screenshots. The rules behind each item are in SKILL.md's "Visual spec".

## Contents
- A. Measurement commands
- B. Technical items
- C. Editorial items
- D. Visual items
- E. Report format
- F. Re-verification scope (rounds 2 and 3)
- G. Splitting the checklist across parallel verifiers

## A. Measurement commands

Replace `R` with the reel path and `OUT` with your output folder. They need ffmpeg, ffprobe and Python 3.

```bash
# Specs and duration
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of compact R
# Loudness (read "I:" in the summary)
ffmpeg -i R -af ebur128 -f null - 2>&1 | tail -12
# Silence gaps
ffmpeg -i R -af silencedetect=n=-45dB:d=0.3 -f null - 2>&1 | grep silence_
# Word-cut check: RMS of the first and last 20ms of each trimmed narration file (W = build workdir)
for f in W/scene[0-9]*.wav; do case $f in *_audio.wav) continue;; esac
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  h=$(ffmpeg -t 0.02 -i "$f" -af astats -f null - 2>&1 | grep "RMS level" | tail -1)
  t=$(ffmpeg -ss $(python3 -c "print($d-0.02)") -i "$f" -af astats -f null - 2>&1 | grep "RMS level" | tail -1)
  echo "$f head:${h##*:} tail:${t##*:}"; done
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
# Viewer sheet: the whole reel at 1 fps on one image (D12)
ffmpeg -i R -vf "fps=1,scale=160:-1,tile=8x8" -frames:v 1 OUT/viewer_sheet.png
# End card hold: how long the finished end card (every summary panel in) stays on screen (B5)
python3 scripts/check_card_hold.py R --shots W/shot_list.json --json OUT/card_hold.json
# Pace from the shot list (W = build workdir): each shot's kind and still coverage (D12)
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); [print(r['start'],r['end'],r.get('kind'),r.get('coverage'),r.get('wipe'),r['visual'],r['headline']) for r in d['shots']]" W/shot_list.json
# Per-shot strip at 8 fps (repeat for each shot; S = shot start, D = duration)
ffmpeg -ss S -t D -i R -vf "fps=8,scale=180:-1,tile=8x2" -frames:v 1 OUT/shot_S.png
# Full-size frame for close inspection
ffmpeg -ss T -i R -frames:v 1 OUT/frame_T.png
```

Inspect the images themselves; do not infer them from the commands' output.

## B. Technical items

- [ ] **B1 Duration**: within the agreed length (default under 60s), and matches the shot list's total (`shot_list.json` in the workdir) within 0.1s. The video stream is not shorter than the audio. If the loop-back narration takes it over the limit, it is an accepted trade-off only when the loop-back is already in its shortened form and the delivery notes say so.
- [ ] **B2 Specs**: 720×1280, h264, AAC 48 kHz stereo.
- [ ] **B3 Loudness**: integrated loudness between −15.5 and −13.5 LUFS (target −14).
- [ ] **B4 Silence and word cuts**: no gap over 0.3s except the final 0.5s. No agent can hear the audio, so measure word cuts: in the build workdir, every trimmed narration file `sceneN.wav` must start and end in silence, with the first and last 20ms below −45 dBFS RMS (commands in A). FAIL with the file and level if either edge is louder; speech at the edge means a word was clipped. Report that a human listen-through is still needed, because a word dropped inside a line by TTS cannot be measured this way.
- [ ] **B5 Shot length**: no shot over 6s except the end card, which runs for the loop-back narration (FAIL if its text can't be read in that time); no still image shot over 4s (an AI still ≤3s); shots mostly 2–5s. Run `scripts/check_card_hold.py` (command in A) and FAIL an end card with summary panels whose finished card (every panel in) stays on screen less than 0.4s per panel or 1.5s, whichever is longer, or an end card without panels under 1.5s, quoting the measured hold. A super change (new headline, same visual) starts a new shot.
- [ ] **B6 Holds**: list every freezedetect hold over 1s with its timestamp. FAIL if a frame is frozen across a cut, or if a shot never changes at all (it should at least creep).
- [ ] **B7 Clean cuts**: on the 2 fps sheets and around each cut, no frame from the previous shot leaks across a cut, and no frame mixes two layouts.
- [ ] **B8 Motion profile**: report the median frame difference and still %. FAIL if still % is over 50 (the reference reel is 12%). Then check the 8 fps per-shot strips:
  - FAIL if a caption word, tag, source label, or a headline over a photo moves within a shot.
  - FAIL if the whole composited frame zooms or pans.
  - FAIL if a move is not one of the allowed moves in SKILL.md's Motion table, or breaks its parameters (creep over 102%, a fast move over 0.6s other than a wipe or graphic zoom, a wipe covering the captions for more than 0.3s, two fast moves at once).
  - FAIL if a visual that continues across a cut jumps back: compare the last frame before and the first frame after each super change or repeated visual. The same clip frame must carry on (not return to its start), a still's zoom must not step back (no zoom-out and re-push), a repeated headline card must keep its words lit, a timeline must keep its events, and a drawn ✗ and the diagram nodes must stay. A visibly different layout of the same image (a taller header) is a build warning, not a FAIL, but report it.
  - List each move found, with its timestamp and type.
- [ ] **B9 Caption sync**: run `python3 scripts/check_sync.py R --subs W/subs.ass --json OUT/sync.json` (W = build workdir). FAIL if any of S1–S4 or S6 fails: streams misaligned; speech over 0.3s with no caption (the end card is skipped on purpose); a caption up over 0.6s of silence; a phrase change at a clause end more than 0.25s from the voice's pause (with Whisper, the pause just before the phrase's first word); a caption word that changes position. If S5 ran, FAIL on any word revealed more than 0.3s from when it is spoken, quoting the word and offset (the fix is a `caption_nudge` on that word only; the first word after a pause is timed from the audio onset, so a FAIL there is not Whisper noise), and list the words it did not match, for the human listen-through, along with the build's narrate warnings (a name Whisper misspelled, a first word it missed). If S5 did not run (no Whisper), say so: word timing is then unverified.
- [ ] **B10 Caption anchoring (by eye)**: extract frames at three consecutive word reveals of a two-line phrase and of a one-line phrase (times from `subs.ass`). FAIL if any already-revealed word shifts between them, or if spoken words are re-centred as words are added.

## C. Editorial items (check against facts.md)

- [ ] **C1 Tags**: the only tag on screen is DISINFORMATION POST, and only on false or unverified material. FAIL if any status tag appears (CONFIRMED, STATED BY, ESTIMATE, UNCONFIRMED, DISPUTED, ALLEGED, DENIED or similar), or if a headline states a claim more strongly than the status facts.md gives it.
- [ ] **C2 Confirmed vs not**: each claim's counterpart (denial, confirmed figure, company statement) appears in the same beat; no confirmed fact and unconfirmed claim are merged into one statement.
- [ ] **C3 False or unverified material**: every appearance of an image that is itself false or unverified carries its tag; none opens the reel, appears on the end card, or sits under a true line.
- [ ] **C4 Figures and quotes**: each matches facts.md, shows its source on screen, and says what it measures; where sources conflict, the range or disagreement is visible; changing figures carry an "AS OF" label; no invented chart.
- [ ] **C5 Attribution**: no perpetrator, operator or motive is named unless facts.md shows a source establishing it; comparisons and patterns are labelled as such.
- [ ] **C12 Narration transcript**: read every narration line in the manifest and check it against facts.md. FAIL if a line states something not in facts.md, credits it to the wrong party (for example "analysts" for a news outlet's wording), or is stronger than its source: "lost" for "impact", "blame" or "did it" for "likely" or "assess", "was" for "may be", a figure without "about" where the source estimates. FAIL if a line merges a confirmed fact with an unconfirmed claim. Quote the line and the facts.md row for every FAIL.
- [ ] **C13 Human-sounding narration**: join all narration lines and check them against SKILL.md "Write like a person talking". FAIL if any four sentences in a row are within 2 words of each other in length or share the same "[Source] [verb] [figure]" template; if any organisation is named more than about three times; if the script uses a stock AI marker (moreover, furthermore, notably, in summary, it's worth noting, delve, landscape, crucial, a stark reminder, here's the thing, "not just X, but Y"); if narration contains a semicolon, parenthesis or colon; if a beat re-narrates figures already said; or if the closing line is generic. Also read every beat boundary aloud (last line of beat N, then the first line of N+1): FAIL any transition where the next line doesn't follow from the one before it (no answer, contrast, next step or shared word or idea) or where a section change has no spoken bridge. Quote the offending lines. A rewrite that weakens a hedge or attribution fails C12 instead.
- [ ] **C14 Hook**: read only the hook's narration and headlines (the leading beats whose id starts with `hook`, or the first beat), as a viewer with no context. FAIL if it does not say who (with an identifier when the name isn't household), what happened in a plain verb, and the scale or stakes; if it is under about 12 words or runs past 7s; or if any part is stronger than facts.md. Quote the hook. Then watch the hook's 8 fps strips: FAIL if any hook shot is a still image that doesn't move (a clip, or an image with a push, pan or inset move, passes; creep alone does not), or if its move lands anywhere but the subject. FAIL if, once any inset move has finished (0.4s), the hook's visual does not fill the whole 720×1280 frame: blurred fill or background blue visible above, below or beside the picture is a FAIL, whatever the manifest says. If a hook shot is a still, read its asset log row: FAIL if it gives no reason why no clip (footage or Muse video) worked.
- [ ] **C15 Loop-back**: read the first and last beats' narration. FAIL if neither of the last two sentences echoes the hook's open question or promise (matching or shortened wording), if the question is echoed but never answered (the reel ends on the bare question or a to-do list), if the answer is stronger than facts.md, or if the end card leaves the screen before the narration finishes.
- [ ] **C16 Story shape**: read the whole narration once, start to finish, as a viewer who has never heard of the story, then check it against SKILL.md "Story shape". FAIL each of these, quoting the lines:
  - no single concrete example a viewer can picture (one named device, site, account or transfer and what happened to it), or that example gets one of the shortest beats;
  - context that lowers the stakes (a patch, a reassurance, "most were fine") comes before the strongest example, other than a claim's own denial or counterpart in its beat;
  - a stretch of more than about 12s of narration with no new question, turn or contrast;
  - two beats (adjacent, or with only a shot between) where the second seems to contradict or undercut the first, and no line before or in the second gives the reason both are true (or says no source gives one); check every row of facts.md's tensions table, and read as a viewer for pairs the table missed (a missing row is also a FAIL). The bridge's reason must be in facts.md (otherwise C12 FAILs), and the turn shot's headline must name the difference (C17);
  - a technical term the viewer must know (for example "rooted", "CVSS", "short seller", "index reweight") used without a plain-words gloss on first use;
  - more than about 7 distinct figures or claims in 55s, or a figure narrated with no shot showing it;
  - a line too compressed to follow on one hearing: a pronoun or "it" with no clear referent, a name with no identifier on first mention, or a subject or link dropped to save words (SKILL.md, "Fit the length"). Quote it and say what was lost;
  - a section change with no spoken bridge (SKILL.md, "Bridge every section change"). Write out the story spine: the hook's open question, then the first line of each section, in order (the dry run prints it). FAIL if, read alone, the spine doesn't tell the story as one sequence, each line following from the one before and moving toward the hook's question; if a section opener restarts cold (a bare new fact, a new name, a date with no turn); if more than two section openers (not counting the loop-back echo) start with the same word, or the bridges are all one kind, so the spine reads as a formula; or if a bridge asserts a cause ("So", "That's why") that facts.md doesn't support (that also fails C12). A section that doesn't move toward the hook's question is a cut candidate: name it. The build's bridge warnings are loose prompts: no warning is not a PASS here, and a warning on a line that does bridge is not a FAIL.
  A storytelling rewrite never excuses a weakened hedge or attribution: that fails C12.
- [ ] **C17 Headlines**: read only the shot headlines, in order, with no narration, as a viewer with the sound off. FAIL each headline that doesn't say who or what did what (a bare noun or figure like "RATED 9.2", "SECOND CLAIM", "~400 POSTS"); that names an organisation or person whose identity the viewer hasn't been given in that headline, its source label, or earlier on screen ("DREAM" with no "security firm" anywhere, "GIC" with no "Singapore state fund"); that drops words until it is ambiguous ("PHP POWERS WEB", "SAME TEMPLATES"); that uses unexplained jargon; that turns against the headline before it without naming the difference, so the two read as a contradiction with the sound off (a big figure followed by "NONE AFFECTED" with nothing saying which group or why); that gives a score or rating without what it measures, so the viewer can't tell whether high is good or bad ("9.2 OUT OF 10" with no "severity"); or that states a claim more strongly than facts.md (also C1). Quote each failing headline with a suggested rewrite.
- [ ] **C11 Timeline** (if the reel has one): every event matches a timeline row in facts.md (time, wording, source); events run in chronological order; the time zone is stated on screen ("ALL TIMES UTC"); each event names its source; an estimate or allegation in an event says so (for example "(estimate)"); each line stays on screen long enough to read (at least about 1.2s from appearing to the end of the shot).
- [ ] **C10 Sources**: every receipt traces to an original report, statement or post listed in facts.md; no aggregator or unsigned page is shown as evidence. Every screenshot visibly contains the wording it is used for (not hidden behind "Show more"), and its displayed time matches the label's time zone.
- [ ] **C6 Spelling**: every name in headlines, diagram nodes and labels matches facts.md exactly.
- [ ] **C7 AI honesty**: check every AI shot (image or Muse video) for each of the following.
  - **Basics.** FAIL unless it is labelled "AI-GENERATED ILLUSTRATION" and is ≤3s (an AI still) or ≤6s (an AI video), and no longer than the real receipt for the same claim.
  - **Never shown.** FAIL if it shows a real named person acting in the scene or with a face Muse invented, a real place presented as evidence, the alleged event, an organisation's building, or anything that could pass as a news photo or footage of a real event.
  - **Real thumbnails and logos.** The story's own people, accounts and organisations may appear as thumbnails, avatars or logos. FAIL any that facts.md or the asset log doesn't name, that doesn't match its real source image, that warps, morphs or merges in any frame (name the frame), that is a full-frame face rather than a small image among others, or that makes someone seem to say or do what the sources don't say.
  - **Simulated posts or feeds.** FAIL any of these:
    - a real platform's logo or interface;
    - a real account name, handle or face that isn't one of the story's own accounts, or isn't spelled exactly as it posts;
    - a recreated real post;
    - post text that breaks SKILL.md's simulated-post rules: a real account shown with its real post's wording, a misspelled or garbled message, counts that look like the story's figures, or place names the sources don't give;
    - a scale (number of posts, speed) beyond what facts.md supports;
    - a false message shown without the narration saying it is false in the same beat.
  - **Support.** FAIL any AI visual that suggests something the narration or sources don't support.
  - **Evidence passed over.** For each AI shot, read its asset log row and open the sources facts.md lists for that claim. FAIL if they contain a related real image that is the evidence for the line (the post, document, chart, person or place the line is about), and name it. A related image that isn't the evidence, logged as dull or generic with a reason, may be replaced by AI (generic images don't count); a log calling the evidence itself dull is no reason. Evidence passes in one case only: a still for a claim facts.md marks as confirmed and undisputed, replaced by an AI video of a generic scene. That case still FAILs if the AI is a still, if it could pass as footage of the real event or site, or if a real clip of the event was found.
- [ ] **C8 Real clips**: labelled with account + date; muted. FAIL if the clip's own running captions (subtitles that change with the speech) collide with the headline or our captions. The clip's static text (a logo, channel name or fixed title box) may sit behind the header stack; FAIL it only where it makes a headline or caption word hard to read, naming the word and frame. For a side-by-side composite of real clips, check three more things:
  - every tile traces to a post in the asset log;
  - the account names drawn on the tiles match those posts exactly;
  - the one label describes the set and doesn't present the tiles as a sourced count.
- [ ] **C9 Headline cards**: each is set in the reel's own style (not the outlet's page design or logo) and quotes only wording in facts.md; none could pass as a screenshot.

## D. Visual items

- [ ] **D1 Safe area**: no headline above y=120; nothing the viewer must read below y=1030; nothing cropped at any edge, including caption lines (FAIL any caption word touching or past the frame's side edges).
- [ ] **D2 Keep box**: for every image shot, compare the first and last frame with the source image and its `keep` box in the manifest. FAIL if any part of the keep box is cut off, hidden under a tag, headline or caption, or if a crop cuts through a word or turns a claim into a fragment anywhere on screen. FAIL if the keep box clearly misses what makes the image relevant (for example, it frames a logo but cuts the headline the narration refers to). An image whose incidental text is unreadable when shown whole is a trade-off to report. But FAIL when the unreadable text is what the line is about, such as a source's chain diagram whose node labels can't be read at full size: it should be cropped to the readable part or rebuilt as the reel's own diagram (SKILL.md, "Diagram").
- [ ] **D3 Overlap**: no headline overlaps its image; no caption overlaps the header stack or a shot's content (keep box, diagram node, card body, timeline, summary panel); every caption word stays readable against what is behind it.
- [ ] **D4 Representative visual and asset choice**: every shot has a visual; no shot shows only a headline on plain colour.
  - **Graphics.** FAIL if the reel has more than one diagram beat, one map or one timeline. An AI simulated spread over a world-map backdrop counts as the map only when it names or points at places. FAIL if any of them is used for a shot that isn't a chain of links, a location or the closing sequence of events.
  - **Asset log.** Every shot other than the diagram, map, timeline and end card needs a row in facts.md's asset log. FAIL a missing row, a row that doesn't show what each of places A–D gave, or a row with no reason for the choice.
  - **Choices.** Check each choice against `references/asset-gathering.md`. FAIL any of these, naming the shot:
    - a related real image that is the evidence for its line, replaced by AI or a headline card. The only exception is the one in C7: a still for a confirmed, undisputed claim, replaced by an AI video;
    - a real image kept although it reads as stock, a reused logo or a repeat of nearby shots, when AI was allowed;
    - a headline card that could take a related image or an AI illustration.
  - **Spot-check the search.** For the AI shots and headline cards, run a short web search: cited articles' image URLs from their page text, other coverage, the primary source's posts, and Wikimedia Commons. FAIL if it finds a related image that is the evidence for the line (the C7 exception applies), or one the log missed that would clearly beat the chosen visual; name its URL. If a page needs a live browser to check, FAIL with what to look for, and the main agent checks.
  - **Pace and variety.** FAIL any of these:
    - a stretch over about 6s with no visual change, other than the end card (a cut, a move, a highlight or a graphic build counts; creep alone does not, and nor does a new headline over the same picture);
    - three similar shots in a row;
    - the same subject or the same image file in more than two shots, counting every shot (super changes included; a "visual run" is still several shots);
    - an image or AI clip that comes back after other shots;
    - two AI shots with the same subject or near-identical frames.
  - **Headline cards.** Count the headline-card shots, not counting the end card, and FAIL if there are more than 2.
- [ ] **D5 Little text**: each shot headline fits in at most two lines (about 40 characters); no paragraph repeats the caption. Besides the headline and caption, a shot shows at most about 25 words of image text (a screenshot cropped to the account name and the claim's one or two lines). FAIL on a whole post, a paragraph, or several posts, and FAIL when two text screenshots are cut back to back. Text on a simulated post or feed (an AI shot) is texture, not image text, and doesn't count toward the 25 words. D3 still applies: every caption word must stay readable over it.
- [ ] **D6 Captions**: one phrase of 2–5 words at a time, at most two lines; bold sans-serif in sentence case (not all caps), about 38px, white with a thick black outline and a soft shadow, no box; centred at the upper middle (top line about y=300, just under the header stack), not the lower third; words appear one by one as spoken, the current word yellow and spoken words white at the same size, and the whole phrase is replaced by the next; no phrase ends on an article, preposition or conjunction, crosses a beat, or opens mid-sentence; the caption words match the narration word for word (figures as written, e.g. "$6.3", "94%"); the end card shows no captions; tags, source labels and headlines are still on screen alongside the captions.
- [ ] **D7 Headline cards**: each card headline is at most 10 words and is the outlet's wording or a verbatim excerpt of it (cuts marked "…"); a headline card that opens the reel has a representative image filling the frame behind it, credited, and not the false material; on every card with an image, the outlet, headline, credit, body and key sentence are all readable against it (FAIL any line lost in a bright or busy area); fill the card; body text readable (≥22px); single-word yellow highlights; each card used once.
- [ ] **D8 Diagram and map**: diagram nodes revealed on the narrated words; an AI animation of a finished diagram is used only up to its `clip_end`, and running `scripts/check_ai_animation.py` on it (source diagram, clip) PASSes with `usable_end` at or after that `clip_end` (FAIL any frame in the shot where text is cut, re-rendered, faded or joined by an invented frame or border); with an AI motion clip behind it, the label says "AI MOTION" and the clip shows no words, numbers, people, logos or shapes that could read as an extra node or link, and nothing in it contradicts the chain (C7); if facts.md marks a link as denied or disproved, the ✗ appears on that link when the denial is narrated (no ✗ when no link is denied). The map is AI-generated (Muse), shown once, labelled "AI-GENERATED MAP • SCHEMATIC — NOT TO SCALE", with no text in the generated frames other than post text on a simulated spread (C7 checks that); the places the narration names are recognisable and in the right relative position, nothing invented (countries, cities, routes), and no specific pipeline or transfer route unless a source shows it.
- [ ] **D9 Label hierarchy**: source labels, AI labels and any disinformation tag are present and readable; the source label is the small muted line just above the headline, and nothing else caption-like (no bar or text block) sits in or right next to the caption band; production notes are not shown.
- [ ] **D10 End card**: closing line, a full-story pointer that is a real screenshot of a referenced article page matching an article in facts.md, showing the outlet name or masthead, headline and byline, with either an absolute date in the screenshot or the capture date printed under it. FAIL on a recreated or headline-card pointer unless facts.md "Visual fallbacks" shows that every referenced article was tried and could not be captured; FAIL on a relative date ("13 hours ago") left in the screenshot, a crop with no outlet name, or any screenshot text that has been masked, blurred or retyped. Then check: one small disclosure line naming the AI voice, AI illustrations and sources; no silence after the final narration. If the end card has summary panels: they sit on the same card as the pointer (FAIL on a separate summary shot); every figure and wording matches facts.md at the source's strength and was already said in the reel; panels share one size, margin and type size; nothing is clipped or cut off; the captions sit above the panels without overlapping them; the pointer screenshot is a strip whose outlet name and headline are readable at full size; the whole card stays readable in a single full-size frame (a screenshot); every chart panel (proportion bar, donut, compare bars) draws the figure its `value` shows, from facts.md, with a bound drawn at the bound and its "<" or "over" kept, compare bars in one unit on one scale from zero, and any estimate's hedge in its label (FAIL otherwise, or if a chart is used where the comparison isn't the point and a plain figure would do); and FAIL if it tells the viewer what to do with it ("SAVE THIS", "screenshot", "share this") unless the user asked for that.
- [ ] **D12 Watchability (does it play as a video?)**: every item above can pass while the reel still plays as a slideshow, so judge this one as a viewer. Read the shot list's `kind` and `coverage` (command in A), then look at the 1 fps viewer sheet before anything else.
  - **Measured.** FAIL any of these, quoting the numbers:
    - still images (`kind` still) hold more than half the reel's time, the end card excluded;
    - fewer than one video shot (`kind` video) per ~15s, with a minimum of two;
    - more than about 6s of still images back to back;
    - a still covering less than 40% of the frame (`coverage` under 0.40) unless the asset log gives the reason a whole receipt must be shown, and in any case more than two such shots;
    - no graphic wipe in a reel over 30s with more than one section.
  - **As a viewer.** Look at the viewer sheet as if scrolling past. FAIL if it reads as a slideshow: most frames share one layout (a headline over a small picture on blurred fill), AI illustrations are flat icons rather than scenes, or nothing on screen acts out what the narration says. Name the frames.
  - **Missed opportunities.** Always list up to five specific missed opportunities, even on a PASS: the shot, what it shows now, and what would carry the line better (a Muse video acting it out, a stat on the figure, a built chain, a tighter crop of the receipt's key line). The builder uses them for the next version.
- [ ] **D11 One background**: every shot that shows a background (cards, diagrams, the AI map's sea, end card) uses the same blue (11, 74, 168), and blurred fill behind images is tinted with that blue. Sample a background pixel in each shot and FAIL on any other background colour. Full-bleed images, headline cards with a full-frame image, and AI clips have no background and are exempt.

## E. Report format

```
VERDICT: PASS | FAIL
| # | Item | Result | Evidence (value / timestamp / frame) |
|---|------|--------|--------------------------------------|
| B1 | Duration | PASS | 48.50s; shot list 48.48s |
...
FAILS TO FIX (ranked, editorial first): ...
ACCEPTED TRADE-OFFS (if any): ...
MISSED OPPORTUNITIES (D12, up to five): ...
```

VERDICT is PASS only if every item is PASS or an accepted trade-off that the spec explicitly allows (D2 incidental readability). There is no "PASS with note" for a rule breach: if a note describes something a rule forbids, the item is a FAIL. Apply each rule as written; do not reinterpret it to pass (for example, counting several shots of one photo as one "visual run").

## F. Re-verification scope (rounds 2 and 3)

Round 1 runs every item. After a FAIL round, the builder fixes, rebuilds and starts a new verifier on **only the items the fixes could have changed**. An item whose inputs did not change cannot change its result, so running it again costs time and finds nothing new. The scope comes from what changed in the files, not from what the builder thinks it fixed. The builder is the party least able to judge where a fix spilled over.

**1. Diff.** Before each round, the builder saves the manifest and facts.md it hands over (for example `verify/round1/`). For the next round, list every difference between the saved copy and the new one: which beats and shots changed, and which fields (narration, headline, asset, keep box, move, order, timing, asset-log row, facts row). Add any asset file replaced under the same name, and any change to the build scripts or style settings.

**2. Scope.** Start with the "Every round" row, then add the row for each kind of change found. "The shot" means each changed shot and the shots on either side of its cuts.

| What changed | Re-run |
|--------------|--------|
| Every round (each rebuild re-renders the whole file) | B1, B2, B3, B4, B6, B7, B9; B8's measured profile; D12's measured part; and every item that FAILed in any earlier round |
| Narration text of a beat | C2, C5, C12, C13, C16; B5, B10, D6; D3 for the beat's shots; D4 pace and variety; D12 in full; C14 if it is a hook beat; C15 if it is the first or last beat |
| Headline, source label, yellow words, disinformation tag | C1, C3, C6, C17; D1, D3, D5, D9 for the shot; C9 and D7 if it is a headline card |
| Image, clip or AI asset swapped or added; asset-log row | C3, C10; C7 if AI; C8 if a real clip; D2, D3, D5, D11 and B8's strips for the shot; D4 in full; D12 in full |
| Keep box, crop, move, wipe, `clip_start`, `clip_mask` | B8 strips for the shot; D1, D2, D3 for the shot |
| Shots added, removed, reordered or retimed | B5; B8 jump-back check; C2, C16; D4 pace and variety; D12 in full; C14 and C15 if the first or last beat moved |
| facts.md | C2, C3, C4, C5, C6, C10, C11, C12; D4 asset log |
| Diagram, map, timeline or stat | C4, C11; D4 graphics; D8 |
| End card or its summary panels | B5, C15, D10 |
| Build scripts, caption style, colours or fonts; or changes touching more than half the beats | The full checklist |

When unsure whether a change touches an item, include the item. A missed item costs a broken reel, and an extra one costs a few minutes.

**3. Hand-over.** Give the new verifier the usual inputs, plus the list of item IDs to run and the shot IDs that per-shot items cover. Do not tell it what was fixed, why, or what the earlier reports said. It runs those items in full, using the same commands and standards as round 1, and reports only those.

**4. Combined report.** The builder joins the new report with the latest result of every other item, marking each carried result "carried from round N". The builder copies results as the verifiers reported them and does not change any of them. VERDICT is PASS only if every item in the combined table is PASS. Deliver the combined table, with each verifier's own report attached.

## G. Splitting the checklist across parallel verifiers

Run the checklist as four fresh verifiers at once, each with its own items (no item in two lanes), so each one finishes sooner and gives every item its full attention:

| Lane | Items |
|------|-------|
| 1. Technical and motion | B1–B10 |
| 2. Script and sources | C1, C2, C4, C5, C6, C10–C13, C15–C17 |
| 3. On-screen frames | C3, C7–C9, D1–D3, D5–D11 |
| 4. Assets and watchability | C14, D4, D12 |

Each gets the usual inputs plus its item IDs, writes to its own folder (`OUT/lane1/` …), and reports only its items in the section E format. The builder joins the reports into one table without changing any result. In rounds 2 and 3, start only the lanes that have scoped items. If the platform can't run agents in parallel, run the lanes one after another, or all items in one verifier.

**Examples.**
- *Round 1 hand-over to lane 2:* "Verify reel `out/reel.mp4` against `references/verification-checklist.md`. Inputs: manifest `work/manifest.json`, `work/facts.md`, assets `work/assets/`, workdir `work/`. Run only items C1, C2, C4, C5, C6, C10–C13, C15–C17. Write frames and your report to `verify/round1/lane2/`." Lanes 1, 3 and 4 get the same message with their own items and folder, all sent at once.
- *Round 2, only one shot's crop was changed (round 1 failed only D2):* section F scopes the every-round items (B items in lane 1, D12's measured part in lane 4), B8 strips for the shot (lane 1), and D1, D2, D3 for the shot (lane 3). Start lanes 1, 3 and 4; lane 2 has no items, so its results are carried from round 1.
- *Round 2, an AI shot swapped for a real clip:* the scope covers C3, C8, C10, D2, D3, D5, D11 (lanes 2 and 3), D4 and D12 in full (lane 4), and the every-round items (lane 1). All four lanes run.

