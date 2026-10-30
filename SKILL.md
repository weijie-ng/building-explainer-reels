---
name: building-explainer-reels
description: Builds and reviews short investigative explainer reels in a thesis-first, voiceover-only reel format, with burned-in subtitles, real article receipts as on-screen evidence, and clearly labelled AI or real-clip material, with every build passed through an independent verification gate. Use whenever the user asks for an explainer reel, an investigative reel in this format, a hybrid AI-voice reel, an investigative video about a claim, a money/power chain, a disinformation story, a reel mixing real news screenshots with AI visuals, or a review/critique of such a reel, even if they do not name this skill.
---

# Investigative Explainer Reel

Build (or review) a short, checkable investigative explainer reel. The model is the reel format in `references/reel-format.md`: an argument-led explainer, rebuilt so every key claim can be checked on screen. Nothing is delivered until it passes the verification gate (see Workflow, step 7).

## Glossary (use these terms consistently)

- **Scene**: one narration segment (one manifest entry). **Shot**: one visual between two cuts; a scene has one or more shots.
- **Tag**: a viewer-facing pill showing a claim's status (see "Status tags" below).
- **Label**: a small source or material line: outlet + date, account + date, or "AI-GENERATED ILLUSTRATION".
- **Headline card**: an outlet's headline set in the reel's own style (outlet, headline, line-and-dot, key sentence).
- **Keep box**: the part of an image that makes it relevant (a logo, a face, a headline, a chart). **Full-bleed**: the image fills the whole frame. **Blurred fill**: a blurred copy of the image, tinted with the reel's blue, fills space the image itself leaves.
- **Material type**: real | ai | recreated | diagram. Every shot has exactly one.

## When to use

Use it for a reel explaining a contested or developing story (a claim, an incident, a money or power chain, a disinformation campaign), and for reviewing such a reel against a reference. Do not use it for a neutral news bulletin, a presenter-led explainer, or a slides-only explainer unless the user asks. If the user wants a presenter or character, say so; do not silently switch formats.

## Reporting structure

Under 60 seconds by default (about 130–140 words for 55s). If the user asks for ~90s, keep the structure and say which length you are using.

1. **Thesis-first hook (0–7s, about 15–22 words, one or two sentences).** A viewer who has never heard of the story must understand it from the hook alone. It says:
   - **who**: named, with a short identifier from facts.md when the name isn't household ("crypto exchange Binance");
   - **what happened**, with a plain verb ("was hacked", "is accused of", "denied");
   - **the scale or stakes**: the key figure or consequence;
   - **the open question** the reel answers, when it fits ("So where did the money go?").

   No background before it. In a neutral reel, the hook states what is known and what is not, never a conclusion the sources don't support. Take the extra words from later scenes, never from the denial or distinction scenes.

   Too short: "Binance puts the hack's impact at about $6.3 billion." (no plain "what happened", no stakes for the viewer)
   Descriptive: "Crypto exchange Binance was hacked, and it puts the impact at about $6.3 billion. So where did that money go?"
2. **One chain.** Step by step on screen: who, what moves, to whom, why it matters. One chain only; a second belongs in the long form.
3. **Motive or cause.** Name the motive or cause the chain implies, labelled as the argument or the sources' assessment, not as proven fact, unless a source proves it.
4. **Two or three supporting details.** Concrete examples or context that illustrate the pattern; they do not prove it. Say so if the reel would imply otherwise.
5. **What's confirmed vs what isn't.** Put each claim's counterpart on screen in the same scene: a denial next to its claim, a confirmed figure next to an estimate, the company's statement next to the outside account. Never merge a confirmed fact and an unconfirmed claim into one statement.
6. **Timeline (optional, for developing stories).** Just before the end card, a timeline of the key events with times and sources, so the viewer leaves with the sequence straight. Every event must come from facts.md. Two shots of three events each, about 4–5s per shot, so each line can be read.
7. **Funnel ending (last 4–5s).** End card on the background blue, a closing line that fits the story (for example "Check before you share" for disinformation, or "This story is still developing" for breaking news), a screenshot of the full article as the pointer, one disclosure line.

## Tone and sourcing

Borrow the thesis-first hook, the one chain, short anecdotes and the funnel. Do not borrow blindly:
- **Loaded framing** ("scheme", "tearing apart", "cozy up to") only if the user explicitly wants that tone; otherwise neutral wording for the same facts.
- **Primary sources.** Trace every claim back to the original report, statement or post. An aggregator page, or a page with no byline, date or links, is a lead, not a receipt; never show it as evidence.
- **Figures** must be independently verified, with the source shown on screen. If unverifiable, cut the figure or label it as reported and name the outlet. Say what a figure measures (for example, "held by flagged addresses" is not "stolen").
- **Conflicting figures.** When sources disagree, show the range or the primary source's figure, and make the disagreement visible. Never pick the most dramatic number.
- **Attribution.** Never name a perpetrator, operator or motive the sources have not established. "Similar to past attacks" or "a coordinated pattern" stays labelled as a comparison or pattern, not an identification.
- **Developing stories.** Put an "AS OF [date, time]" label on figures that are still changing, and do not narrate the story as settled.
- **Design for checkability, not outrage.** A viewer who disagrees should still see what evidence was shown and where it came from.
- **Write like a person talking, not like a model.** Correct facts still read as AI when every line has the same length and template ("[Source] [verb] [figure]."), the same subject repeats, and stock transitions link them. The verifier's C13 holds the exact pass/fail thresholds.
  - **Vary length and shape.** Mix 2–4 word lines with longer ones; use at least one question or fronted clause ("By 2 a.m., …").
  - **Name each organisation about three times at most**; then use "the exchange", "it", or lead with the fact ("$3 billion is frozen, Binance says").
  - **Every scene change flows.** The first line of a scene follows from the last line of the one before: it answers, contrasts, takes the next step, or picks up a word or idea. A section change (what happened → where the money went → who's responsible) gets a spoken turn ("So who's behind it?", "Meanwhile…"). Each scene still opens with a whole sentence (subtitle rule); to carry one sentence across a cut, use `shots` inside one scene.
  - **Spoken, not written.** Contractions; no semicolons, parentheses or colons; times as said aloud ("just after 8 p.m. UTC"). No stock AI phrasing (listed in C13).
  - **No recap, no generic close.** Don't re-narrate figures already said; the closing line is specific to this story.
  - Style never overrides accuracy: every hedge and attribution from step 3 stays.

  Before (reads as AI, each scene restarts):
  > Binance puts the hack's impact at about $6.3 billion. / Reports call it the biggest crypto theft on record. / Funds left Binance's hot wallets for attacker addresses. / Analysts trace them across 9 or 10 blockchains.

  After (same facts and hedges, scenes linked):
  > About $6.3 billion. That's the impact Binance puts on this hack. / Reports call it the biggest crypto theft on record. / So where did it go? Out of Binance's hot wallets, to attacker addresses. / From there, analysts trace it across 9 or 10 blockchains.

## Visual spec (current; one rule per topic)

`references/msci-case-study.md` shows these rules applied to a real reel, and lists the defect behind each rule.

**Canvas and style.** 720×1280, h264 + AAC 48 kHz stereo. Voiceover-only; people appear only as subjects in photos or footage. Flat 2D motion-graphics collage on **one background colour for the whole reel**: saturated blue (11, 74, 168) behind every shot (headline cards, fitted images, diagrams, the map's sea and the end card). No shot switches to another background colour; blurred fill is tinted with the same blue, and full-bleed images and AI clips have no background. White headlines with single-word yellow highlights (DejaVu Sans Bold), black subtitle boxes.

**Layout.**
- Safe area: no headline closer than 120px to the top, no subtitle lower than y=1030 (ASS MarginV 270). Wrap headlines at 640px.
- **Images are as large as their keep box allows.** Look at each image and set its keep box (`keep` in the manifest): everything that makes it relevant, including every word of any text that must stay readable. The build zooms the image as far as it can while the whole keep box stays inside the frame and between the headline and the subtitles, even at the end of the creep. A small keep box (a logo, a face) goes full-bleed; a keep box covering the whole image (a screenshot, an article card, a chart) shows it whole and edge to edge. Space the image leaves is filled with blurred fill, so no shot shows empty background. Cropping is fine outside the keep box, never through it: a crop that cuts a word in half or turns a claim into a fragment is a defect. AI images are full-bleed.
- If an image's text is still unreadable when shown whole, report it as a trade-off; do not hide it.
- Every shot shows a representative image (real receipt, real clip, headline card, diagram, map or labelled AI illustration). No headline-only screens on plain colour.
- No double text: at most a 2–4 word headline per shot. A paragraph never repeats the subtitle.

**Motion.** The reference reel is almost never frozen: only 12% of its frames are fully still. It moves through a fixed set of moves, each tied to a narrated word or a cut (observed timings in `references/reel-format.md`). Use these moves; do not invent others, and never zoom or pan the whole composited frame.

What never moves: subtitles, tags and source labels, and headlines over photos. They hold their position for the whole shot.

Allowed moves:

| Move | Use it for | Parameters |
|---|---|---|
| Slow creep | The base layer of every card, diagram, map, fitted still and AI image, so no shot sits frozen | Push in or drift up, at most 102% scale (or about 5px/s) over the whole shot, linear. The keep box stays inside the frame throughout. |
| Graphic wipe | Transitions between beats, 1–3 per reel | A shape or object that fits the story's theme slides or flies across the frame, covering the old shot and revealing the next, over 0.3–1.5s. Must not cover subtitles for more than 0.3s. |
| Slide-in or pop-in | A photo, face cutout, icon or shape arriving on a card, diagram or map when it is named | It slides in from an edge or rises from below, or fades in from 0% over 0.3–0.5s, with an ease-out, then holds and creeps. |
| Highlight sweep | Headline cards | Yellow highlight moves word by word with the voice; the line-and-dot extends to the newly quoted sentence. |
| Build | Diagrams | Nodes and arrows appear on the narrated word; the red ✗ snaps on at the denial; small tokens (dots, coins) may flow along an arrow to show money or influence moving. |
| Map move | Maps | Pan or zoom between the narrated places (about 1s per move, ease in and out), with markers and cutouts popping in at each place. |
| Camera zoom on a graphic | Diagrams and maps only | Zoom into one section to show detail, then back out, over 1–4s, ease in and out. |
| Pan across a wide image | A wide real photo that needs to show more than fits (a crowd, a hall of flags) | One direction, 1–2s, ending on the subject; the keep box is fully visible at the end. |
| Particle overlay | Rarely, for an emotional beat on an AI or event image (confetti, sparks, falling paper) | Up to 3s, behind the subtitles, never over a real receipt or its text. |
| Inset grow | A clip or photo that starts as an inset card and grows to full frame | Once or twice per reel, 0.4s, ease-out. |
| Hard cut | Most shot changes | Cut on a narrated word. |

Rules:
- Real clips get no added zoom. AI clips keep their own motion and are never zoomed or panned further.
- Fast moves (wipes, slide-ins, pops) last 0.6s or less, except a wipe of up to 1.5s and camera zooms on graphics. After any move, the shot settles into creep. Never stack two fast moves at once.
- Shots are 1–3s, never over 4s (headline cards and timeline shots up to 5s).
- **Stillness cap:** at most 50% of the reel's frames may be fully still (measured as in the checklist, B8). A static slideshow fails even if every shot is well designed.

**Subtitles.** Burned in, 2–5 words, timed to the voice. Write figures in the narration as digits ("$6.3 billion", not "six point three billion"): subtitles come from the narration text, and spelled-out numbers make chunks too long to split. About 30px bold DejaVu Sans Mono, white on a solid black box, centred in the lower third, never over busy text. Break at phrase boundaries: a chunk never ends with an article, preposition or conjunction, never crosses a scene boundary, and never opens mid-sentence. Give headlines over busy photos a black stroke.

**Status tags.** Every claim on screen carries a tag for its status in the sources. Choose from: CONFIRMED, STATED BY [organisation], ESTIMATE, UNCONFIRMED, DISPUTED, ALLEGED, DENIED, DISINFORMATION POST. Use the tag the sources support, not the strongest one available. Red is for alleged, disputed or false claims; green for confirmed facts and denials; another colour for statements and estimates. Keep the colour scheme the same across the reel.

**Labels: viewer-relevant vs production notes.**
- Always present: source labels (outlet + date, or account + date); status tags; "AI-GENERATED ILLUSTRATION" on every AI shot.
- Placement: the source label is a small, muted line between the status tag and the headline, like an outlet name on a card. Never put it in a bar near the subtitles, where it reads as a second caption. The end card's disclosure line sits just under the pointer, well above the subtitles.
- Production notes (how a card was made, muted audio, masked captions) are left off the screen. Real-clip labels are account + date only.

**False or unverified material (highest priority).** Any image that *is* the false or unverified claim (a fake post, a doctored graphic, an unverified screenshot) carries its tag every time it appears, for example "DISINFORMATION POST — flagged by [verifying outlet]". It never opens the reel, never appears on the end card, and never sits under a true line; use a real receipt for true lines. An article's lead image (og:image) is often the false material itself, such as the fake posters a fact-check debunks. Look at it before using it; if it is, open the reel with a cropped screenshot of the article's outlet name and headline instead (or a labelled AI illustration), and show the false material later under its tag.

**Choosing the visual for a beat.** Since the headline and subtitle carry the claim, look for a picture first, in this order:
1. **A representative image from an article you cite**: its lead photo or cover art (og:image) or an inline photo or chart. Credit it as "IMAGE: OUTLET, DATE". Check what it actually shows: archive or stock photos from years ago are fine as illustration, but never present them as the event itself.
2. **A representative image found by searching** coverage of the same story from reputable outlets or agencies, or a freely licensed image (for example Wikimedia Commons) with its credit.
3. **A screenshot of the source**, cropped to the claim (rules below), when no picture fits or the wording itself is the point.
4. **A labelled AI illustration** of the concept (frozen funds, a paused queue, a laptop), within the AI-material rules.
5. **A headline card**, the last resort. A headline on plain blue is the weakest shot in the reel; at most 2 per reel, not counting the end card.

**When an image has too much text (fails D5), repair the shot; don't fall back to blue.** Try these in order and stop at the first that passes:
1. **Re-crop.** Shrink the keep box to the photo, chart or logo on the page, or to the account name plus the one or two claim lines (about 25 words).
2. **Swap for the article's picture.** Use the same article's lead photo (og:image) or an inline photo or chart, credited "IMAGE: OUTLET, DATE".
3. **Find another source.** Search other reputable coverage, the primary source, or Wikimedia Commons for a photo of the same subject, or a shorter post stating the same claim.
4. **Illustrate with AI.** Generate a labelled AI illustration of the concept, if the AI-material rules allow it for this beat.
5. **Headline card**, only after 1–4 fail. Record in facts.md, under "Visual fallbacks", what was tried at each step and why it failed. The verifier checks this log.

Vary the subjects across the reel: if most shots end up showing the same logo, look for photos of the people, places, or objects in the story instead. For freely licensed photos (Wikimedia Commons: search with `commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srsearch=…`, then read each file's licence, author and date):
- Credit the photographer, year and licence on screen (for example "PHOTO: GAGE SKIDMORE, 2025, CC BY-SA 3.0"), and record it in facts.md.
- Check what the photo shows. Crop out anything now false, such as an old job title on a slide behind the person.
- A photo of a person next to a claim must not suggest they made it unless they did. Name whose statement it is in the source line.
- A concept or stock photo is labelled "ILLUSTRATIVE PHOTO".

**Real receipts.** When you do use a screenshot of the actual source (the X post, the company statement, the article's headline), follow these capture rules:
- **The claim must be visible in the screenshot.** Posts cut off with "Show more" often hide the very line you need; use another post that states it in full, or a card.
- **Times must match the labels.** Capture with the browser set to UTC (or the time zone the reel uses), because posts show times in the viewer's time zone. X posts can be captured without logging in from `platform.twitter.com/embed/Tweet.html?id=<post id>&theme=dark`.
- **Crop out what isn't the source:** ads, cookie banners, site menus. Set a keep box on the part that carries the claim.
- **Wait for images before a screenshot.** Article images often load only when scrolled into view. Scroll each one into view and wait until it has loaded, or the capture shows grey boxes.
- **Download images as JPEG or PNG.** Image CDNs pick the format from the request, so a `.png` URL can return AVIF or WebP that the build can't read. Send `Accept: image/jpeg` (or change `f_auto` to `f_jpg` in Cloudinary-style URLs).
- **Re-read the page when you capture it.** Pages change: a headline figure updated between research and capture is a fact to update in facts.md, not a detail to ignore.
- **Never put a screenshot under a tag it doesn't support.** An analyst's headline naming a culprit doesn't belong under CONFIRMED.
- **Little to no text on screen besides the headline and subtitle.** The headline and subtitle already carry the claim, so the visual behind them should be a picture, not a page to read. Prefer a photo, logo, chart or graphic. When a screenshot is the receipt, crop the image itself to the account name plus the one or two lines that state the claim (about 25 words at most). Never show a whole post, a paragraph, or several posts.
- **No screen jumps.** At most one text screenshot per scene, and never two text screenshots back to back; put a photo, graphic or diagram between them. Several fast cuts between text-heavy frames make the screen jump and are unreadable.

A plain article photo or thumbnail is shown with outlet and date; it is not a screenshot of the page, so don't call it one.

**Headline cards.** Use one only when the repair ladder above found no picture, screenshot or AI illustration. Quote only established wording. Outlet name, the outlet's actual headline wording where known, single-word yellow highlights, line-and-dot to faint body text (≥22px, readable), and the key sentence highlighted. Fill the card with no blank half. Use each card once. Set it in the reel's own style, never in the outlet's page design or logo, so it can't be mistaken for a screenshot.

**Diagram.** One chain, with nodes revealed on the narrated word. Each link carries the status of the claim it represents. When a link is denied or disproved, a red ✗ appears on it at that beat. Check every node name against the facts sheet.

**Map.** Render from Natural Earth land/coastline data: light grey land on saturated blue sea. Labels and "SCHEMATIC — NOT TO SCALE" are drawn by the build, never inside generated media. Animate a generic flow arrow in the build, never a specific pipeline route. Show it once. Do not use an AI-generated or AI-animated map.

**Real clips.** Short, muted slices, only if cleanly obtained. Mask the clip's own burned-in captions and logos so they never collide with the headline or English subtitle; measure the bands from a rendered frame, never guess (ffmpeg delogo needs x > 0). If a clean slice cannot be obtained, omit it and say why; never invent one.

**AI material (Muse).** Use AI video or images wherever an illustration helps the viewer understand a beat and no real receipt fits. Choose them to suit each story; any subject is open unless the limits below rule it out. For examples from past reels, see `references/msci-case-study.md`. Never generate real named people, real places shown as evidence, the alleged event itself, organisations' buildings or logos, or anything that looks like a news photo or social post. No text in generated frames; all words are added by the build. Each AI shot is ≤3s, labelled, and muted. Real receipts stay on screen longer than illustrations. An AI visual must never suggest something the narration does not say or the sources do not support.

**Audio.** About −14 LUFS integrated: gentle compression (threshold −28 dB, ratio 12, makeup 12 dB) before loudnorm, because loudnorm alone stops short on true-peak limiting. Use an original low music bed (generated tones, no copyrighted music) with the voice clearly on top. Inter-sentence gaps of 0.15s; no silence over 0.3s except the final 0.5s; no narration words cut. Export 48 kHz stereo AAC at 192k (the default bitrate overshot true peak).

**End card.** On the background blue; the closing line; a pointer to the full story that is a **real screenshot** of a referenced article page (`pointer.image`), showing the outlet's name or masthead, the headline, the byline and a date (in the screenshot, or the capture date in `pointer.captured`), plus the lead photo when it fits, so it reads as the article itself and not a typed card. Relative times ("13 hours ago") go stale; handle them in this order, cheapest first:
  1. **At capture**, crop to the outlet name, headline and byline, leave the relative time out, and record the capture date in `pointer.captured` ("30 OCT 2026"); the build prints it under the screenshot.
  2. If the relative time sits inside the headline or byline block and can't be cropped out cleanly, recapture a view that shows an absolute date: the article page first, an archived copy only as a last resort.
  3. Never mask, blur or retype text inside a screenshot; it is a receipt.

  If one article blocks capture (paywall, bot wall), capture another article listed in facts.md. A headline-card pointer (`pointer.headline`, never a fake poster) is allowed only when no referenced article can be captured, with the attempts logged under "Visual fallbacks" in facts.md and `pointer.no_screenshot` set to the reason; one small disclosure line naming the AI voice, any AI illustrations and the sources. No silence after the final narration.

## Build pitfalls (each one has broken a past build)

- Never overlay a single-frame PNG with `-shortest`: it cuts the shot to one frame. Loop the overlay and set `-t`.
- Never concatenate with `-c copy` across mixed frame rates. Normalise every segment to 30 fps first.
- Use exact per-shot frame counts when re-encoding cuts, so the video is never shorter than the audio.
- When rebuilding a single shot, burn its subtitles onto the rebuilt segment if the original burned them at final mux.
- Verify the final duration against the shot list, not against the builder's printed total.
- Scope edits: a label-only or fit-only fix changes only the affected shots; copy the audio unchanged and confirm its checksum.

## Workflow

Copy this checklist into your working notes and tick items as you go:

```
Reel progress:
- [ ] 1. Confirm topic, length, tone
- [ ] 2. Facts sheet (claims, denials, sources, real-vs-false distinction)
- [ ] 3. Script with tags
- [ ] 4. Shot list + assets (real receipts, AI illustrations)
- [ ] 5. Manifest + dry run
- [ ] 6. Build
- [ ] 7. Verification gate (independent verifier) -> PASS
- [ ] 8. Deliver with notes
```

1. **Confirm before building.** Topic, length (default under 60s), and loaded argument-led tone or neutral tone. Do not reinterpret an ambiguous topic.
2. **Facts sheet.** Write `facts.md`: each claim with its status tag, its denial, the source and date for every figure and quote, and the careful distinction. For a developing story, add a timeline table (time with time zone, event, source) for the timeline beat. Cut anything that cannot be sourced. The verifier checks the reel against this file.
3. **Script.** About 130–140 words for 55s. Keep every line at the source's strength: "impact" stays "impact" (not "lost"), "likely" stays "likely" (not "did it" or "blame"), "may be" stays "may be", estimates keep "about". Credit wording to whoever said it: news outlets are not "analysts". Re-check the whole transcript against facts.md every time a line changes, including trims to fit the length. Give every claim its status tag, and put each claim's counterpart (denial, confirmed figure, statement) in the same scene. Then read the script aloud against "Write like a person talking" (Tone and sourcing) and check it with C13 in `references/verification-checklist.md`: rewrite failing lines and scene changes, recheck accuracy (C12), and repeat until both pass.
4. **Shot list and assets.** One representative image per shot, chosen in the order in "Choosing the visual for a beat": article images first, then searched or freely licensed photos, then screenshots cropped to the claim (captured in UTC, claim visible, ads and banners cropped out), then AI illustrations, then headline cards as a last resort. Any image with too much text goes through the repair ladder before it is dropped. Set a `keep` box for every image. Capture the end card's pointer as a screenshot of a referenced article page (outlet name, headline, byline; relative times cropped out at capture, capture date recorded; see "End card"). Generate AI illustrations only within the AI-material rules. Record each asset's file, source, date and licence in facts.md. Look at every asset once before writing the manifest; the build rejects an image it can't read or that is almost blank.
5. **Manifest and dry run.** Write the JSON manifest (see `examples/sample-manifest.json`) with `material` on every scene. Run `python3 scripts/build_reel.py manifest.json --dry-run` to check timings and word count.
6. **Build.** Run `python3 scripts/build_reel.py manifest.json --out reel.mp4 --workdir <dir>`. The script handles:
   - TTS narration, phrase-chunked subtitles, the music bed and loudness;
   - fitted real stills and full-bleed AI images;
   - slow creep on every shot's base layer, with tags, headlines and labels locked, and faint grain on flat graphics (a test build measured 16% still frames);
   - headline cards with the word-by-word highlight sweep;
   - the diagram with node reveal and the ✗ beat (`cross_after`);
   - the timeline (`timeline`: events with time, text and source, revealed one at a time);
   - the Natural Earth map with a thinning arrow (needs a Natural Earth land GeoJSON);
   - real clips with `clip_mask` delogo boxes, plus AI clips;
   - the end card with pointer and disclosure line;
   - multi-shot scenes (`shots`): one narration line cut into several shots, so lines stay whole sentences while shots stay 1–3s;
   - narration silence trimmed and pauses capped, so no gap exceeds 0.3s;
   - diagram nodes timed to the words that name them;
   - exact 30 fps frame counts.

   It rejects a manifest that breaks a hard rule: a missing `material`, a scene with no visual, an image it can't read or that is almost blank, a real shot without a source, disinformation material opening the reel or on the end card, or a mask box at the frame edge. It also fails if the total exceeds the length limit; then trim narration, never the denial or distinction scenes. It does not generate AI media or the graphic wipes, slide-ins, map moves and particle overlays from the motion table (make those with Muse or as clips, and pass them in), and it does not find a clip's caption or logo bands (measure them from a frame, then set `clip_mask`). Its closing self-check (duration, specs, loudness, contact sheets) is a start, not the verification gate.
7. **Verification gate.** See the next section. Mandatory for every build, including small fixes.
8. **Deliver.** Give the file; the verifier's report with measured duration, resolution, audio specs and loudness; a per-shot table (time, visual, material type, source/label); contact-sheet paths; and anything omitted or not fixed, and why.

## Verification gate (independent verifier agent)

The builder never certifies its own reel. After every build, hand verification to a **fresh verifier agent** (a separate subagent or new agent instance) that did not take part in the build.

**Give the verifier only:**
- the rendered reel path (and the reference reel path, if any);
- the manifest or shot list and `facts.md`;
- `references/verification-checklist.md`;
- a writable folder for its frames and report.

Do not give it your own assessment, the known issues, or what you expect it to find; a primed verifier tends to confirm what it is told.

**The verifier must:**
1. Run every measurement in the checklist itself on the rendered file (not the planned timeline), extract the contact sheets and per-shot strips, and look at them.
2. Mark each checklist item PASS or FAIL, with evidence: a measured value, a timestamp, or a frame path. "Looks fine" is not evidence.
3. Not edit, re-render or fix anything; it only reports.
4. Return the report in this format:

```
VERDICT: PASS | FAIL
| # | Item | Result | Evidence (value / timestamp / frame) |
|---|------|--------|--------------------------------------|
FAILS TO FIX (ranked): ...
ACCEPTED TRADE-OFFS (if any): ...
```

**Gate rules.**
- Any FAIL blocks delivery. The builder fixes the failures, rebuilds, and starts a **new** fresh verifier. Fix a D5 (too much text) FAIL with the repair ladder in "Choosing the visual for a beat", not by swapping in a headline card. Do not reuse the previous one, and do not tell the new one what was fixed.
- After 3 failed rounds, stop. Deliver the latest build to the user clearly marked "not passed", with the verifier's open FAIL items. Never present it as passed.
- The builder may not overrule a FAIL. If the builder believes a FAIL is wrong (for example, an intentional still hold flagged as a freeze), say so to the user with the evidence, and let the user decide.
- If the platform cannot run a separate agent, run the verification as a distinct pass in a clean context: reload only the inputs listed above, and do not rely on build notes. State in the delivery notes that the gate was self-run, not independent.

## Reviewing an existing reel

When asked to review or critique a reel (not build one):
1. Read this skill's current visual spec **before** suggesting changes, so suggestions do not reverse rules the user already set.
2. Run the verification checklist measurements on the reel and on the reference, if given (see `references/reel-format.md` for the reference reel's measured benchmarks).
3. Inspect the contact sheets and per-shot strips, judging motion by what it does for the viewer, not only by freeze metrics.
4. Report what improved, what regressed and what is still open, ranked by severity (editorial and labelling first, then visual, then polish). Where useful, end with a self-contained fix prompt for the next build.

## References

- `references/verification-checklist.md`: the pass/fail items and commands used by the verifier.
- `references/reel-format.md`: the reference reel: reporting beats, visual grammar, how it moves, and measured benchmarks.
- `references/msci-case-study.md`: the MSCI reel as a worked example: facts sheet, shot list, reusable build settings, and the defect behind each rule.
