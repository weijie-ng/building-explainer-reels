---
name: building-explainer-reels
description: Builds and reviews short investigative explainer reels in a thesis-first, voiceover-only reel format, with burned-in word-by-word captions, real article receipts as on-screen evidence, and clearly labelled AI or real-clip material, with every build passed through an independent verification gate. Use whenever the user asks for an explainer reel, an investigative reel in this format, a hybrid AI-voice reel, an investigative video about a claim, a money/power chain, a disinformation story, a reel mixing real news screenshots with AI visuals, or a review/critique of such a reel, even if they do not name this skill.
---

# Investigative Explainer Reel

Build (or review) a short, checkable investigative explainer reel. The model is the reel format in `references/reel-format.md`: an argument-led explainer, rebuilt so every key claim can be checked on screen. Nothing is delivered until it passes the verification gate (see Workflow, step 7).

## Glossary (use these terms consistently)

**Structure, from largest to smallest.**
- **Section**: one part of the reporting structure below (hook, chain, motive, details, confirmed vs not, timeline, ending). A section spans one or more beats.
- **Beat**: one narration line (one or more whole sentences) and its visuals, like one row of a two-column explainer script (voiceover left, visuals right). In the manifest a beat is one entry in `scenes`; the key keeps its old name so existing manifests still build. "Scene" in film means a unit of story in one place and time, which is why these docs don't use it. Caption phrases never cross a beat boundary.
- **Shot**: one visual between two cuts (the film meaning). A beat has one or more shots (`shots` in the manifest). Shot lengths, motion and "one image per shot" are all counted per shot.
- **Cut**: the instant one shot changes to the next; a hard cut on a narrated word, or a graphic wipe. A new beat always starts with a cut.
- **Super change**: a new headline over the same visual. Editors wouldn't call it a cut, but the build renders it as a new shot (a separate `shots` entry), so it counts as a shot for shot length (1–3s) and "one image per shot" allows the repeat. The visual carries on across the cut (the same clip frame, zoom, highlight, events and ✗), because the build treats shots that continue one visual as a run (see Build pitfalls); a different visual is a hard cut that starts its own motion.
- **Frame**: one video frame (1/30 s). "The frame" also means the whole 720×1280 picture: an image that "fills the frame" covers all of it. "On screen" just means visible to the viewer; "screen" is not a unit.
- **Hook**: the opening beat or beats, 0–7s: the leading beats whose `id` starts with `hook`, or else the first beat. **End card**: the last shot (closing line, pointer, disclosure line).

**What a shot shows.**
- **Visual**: what a shot shows behind its text: an image, a clip, a headline card, the diagram, the map, the timeline or the end card.
- **Image**: a still picture file: a photo, screenshot, chart, logo or AI illustration. **Photo**: a photographic image. **Clip**: a video file, real or AI.
- **Screenshot**: a capture of a source page or post (an X post, a statement, an article page).
- **Receipt**: real material from a cited source, shown as evidence: a screenshot, or an article's own photo or chart. A headline card is not a receipt; it is recreated.
- **Headline card**: a graphic the build draws in the reel's own style, quoting an outlet's article headline: outlet name, the article headline, a line-and-dot leading to faint body text, and the key sentence highlighted word by word. The last-resort visual (at most 2 per reel).
- **Stat**: a graphic shot of one sourced figure, set big with a short label, that counts up or pops in on the word that says it (`stat` in the manifest).
- **Graphic**: a visual the build draws itself: headline cards, stats, the diagram, the timeline, the summary card and the end card. (The map is AI-generated, not drawn by the build.)
- **Shot kind** (what the pace report counts): **video** (a real or AI clip), **built** (a graphic animated on the narrated words: card, stat, diagram, timeline), **still** (a still image, with only creep or a move), **end** (summary and end card).
- **Inset**: an image or clip shown smaller than the frame, in a rounded rectangle on the background blue.
- **Material type**: real | ai | recreated | diagram. Every shot has exactly one. Headline cards and the end card are `recreated`; the diagram and timeline are `diagram`; the map is `ai`.

**Text on screen.**
- **Headline**: the reel's own line at the top of a shot (manifest `headline`; one or two lines, about 3–8 words; see "Headlines"), white with single-word yellow highlights. It is what editors call a **super** (superimposed title); "headline" is this skill's name for it. Not the same as an **article headline**: the outlet's headline on its page, which appears in screenshots and on headline cards.
- **Caption**: the burned-in narration, one short phrase (2–5 words, at most two lines) at a time at the upper middle of the frame, revealed word by word as it is spoken (see "Captions"). It replaces the old black-box subtitle; it does not replace labels, tags or headlines.
- **Label**: a small line of information: the source label (outlet + date, account + date, or an image credit), "AI-GENERATED ILLUSTRATION", "AS OF [date, time]", or "SCHEMATIC — NOT TO SCALE".
- **Tag**: the red DISINFORMATION POST pill on false or unverified material. It is the only tag; there are no status tags (see "Tags" below).
- **Pointer**: the end card's screenshot of a referenced article page. **Closing line**: the end card's story-specific last line. **Disclosure line**: one small line naming the AI voice, AI illustrations and sources.

**Layout and layers.**
- **Keep box**: the part of an image that makes it relevant (a logo, a face, a headline, a chart).
- How an image is placed: **full-bleed** (it fills the whole frame), **zoomed** (enlarged as far as its keep box allows, with blurred fill around it), or **shown whole** (the entire image visible, with blurred fill around it). **Blurred fill**: a blurred copy of the image, tinted with the reel's blue, filling space the image itself leaves.
- **Base layer**: the visual, which may creep. **Text layer**: the tag, source label and headline, which never move. Captions are burned on top of both.
- **Header stack**: the tag, source label and headline at the top of a shot (from y=140). **Caption band**: the two caption lines under it (top line at y=300). **Content band**: everything a shot shows below the caption band, down to the bottom safe area (y=1030). The **composited frame** is all of them together; it is never zoomed or panned.

**Files.** **facts.md** (the facts sheet: claims, statuses, sources), the **manifest** (the JSON the build reads), and the **shot list** (each shot's time, visual, material type and labels, given at delivery).

## When to use

Use it for a reel explaining a contested or developing story (a claim, an incident, a money or power chain, a disinformation campaign), and for reviewing such a reel against a reference. Do not use it for a neutral news bulletin, a presenter-led explainer, or a slides-only explainer unless the user asks. If the user wants a presenter or character, say so; do not silently switch formats.

## Reporting structure

Under 60 seconds by default (about 130–140 words for 55s). If the user asks for ~90s, keep the structure and say which length you are using.

1. **Thesis-first hook (0–7s, about 15–22 words, one or two sentences).** A viewer who has never heard of the story must understand it from the hook alone. It says:
   - **who**: named, with a short identifier from facts.md when the name isn't household ("crypto exchange Binance");
   - **what happened**, with a plain verb ("was hacked", "is accused of", "denied");
   - **the scale or stakes**: the key figure or consequence;
   - **the open question** the reel answers, when it fits ("So where did the money go?").

   No background before it. In a neutral reel, the hook states what is known and what is not, never a conclusion the sources don't support. Take the extra words from later beats, never from the denial or distinction beats.

   **The hook moves and fills the frame, edge to edge.** It is the viewer's first second, and a picture sitting on blurred fill reads as a slideshow and loses them. Give each hook shot a clip: downloaded footage that represents the story, or an AI video generated with Muse that acts out the hook's line (see "AI material"). A still image is the fallback, allowed only when no clip works (log why in the asset log) and only with a `move` (`push`, `pan` or `inset`); the build rejects a hook still without one. Hook stills are always cover-cropped to fill 9:16 around their keep box, and the build rejects `"full_bleed": false` on the hook. So set the keep box on the one subject the hook needs (a wide photo keeps a 9:16 slice of it), or pick a taller photo or a clip; never a keep box covering a whole wide image. Keep the subject's face or key detail out of the caption band (about y 290–420), where the caption would cover it.

   Too short: "Binance puts the hack's impact at about $6.3 billion." (no plain "what happened", no stakes for the viewer)
   Descriptive: "Crypto exchange Binance was hacked, and it puts the impact at about $6.3 billion. So where did that money go?"
2. **One chain.** Step by step on screen: who, what moves, to whom, why it matters. One chain only; a second belongs in the long form.
3. **Motive or cause.** Name the motive or cause the chain implies, labelled as the argument or the sources' assessment, not as proven fact, unless a source proves it.
4. **Two or three supporting details.** Concrete examples or context that illustrate the pattern; they do not prove it. Say so if the reel would imply otherwise.
5. **What's confirmed vs what isn't.** Put each claim's counterpart on screen in the same beat: a denial next to its claim, a confirmed figure next to an estimate, the company's statement next to the outside account. Never merge a confirmed fact and an unconfirmed claim into one statement.
6. **Timeline (optional, for developing stories).** Just before the end card, a timeline of the key events with times and sources, so the viewer leaves with the sequence straight. Every event must come from facts.md. Two shots of three events each, about 4–5s per shot, so each line can be read.
7. **Funnel ending.** End card on the background blue, a closing line that fits the story (for example "Check before you share" for disinformation, or "This story is still developing" for breaking news), a screenshot of the full article as the pointer, one disclosure line. It may instead be, or start with, a summary card (see "End card").

   **Loop-back: ask, then answer.** The final narration echoes the hook's open question or promise, worded to match the hook, and pays it off with a short answer at the sources' strength: "So where did the money go? Most of it, analysts say, is still moving." A shortened echo is fine. Repeating the question with no answer ends on a to-do list instead of the story, which is how the PHP2Shell v1 reel ended ("Patch, then check back… So what got hacked?"). The echo and answer still lead back into the hook when the reel replays. The end card runs for that whole narration, like a headline card or timeline shot, even past 4s, as long as its text stays readable. Adding it lengthens the reel: check the total against the limit afterwards (the build prints it), shorten the loop-back or other lines (never the denial or distinction beats), and say at delivery if the total still exceeds the limit. The build rejects a reel whose last two sentences don't echo most of the hook's question or promise; set `"loop_back": false` only if the user asks for a different ending.

### Story shape: a story, not a list of facts

The sections above say what must be in the reel. This says how it plays. Viewers scroll away the moment nothing new is at stake, and a reel where every beat is one more fact (rated 9.2, fixed on 21 October, 25 firewalls, 0 of 5…) plays as a list even when each fact is right. Every rule here keeps every hedge, attribution and source label; if a storytelling change would drop one, don't make it.
- **One concrete example the viewer can picture, given the longest beat.** One named device, site, account or transfer, and what happened to it, in plain words. It is the shot the viewer remembers; give it the strongest visual.
- **Escalate, then turn.** Order the beats so the stakes rise toward that example. Context that lowers the stakes (a patch, a reassurance, "most weren't affected") comes after the strongest example, not before it. A claim's own denial or counterpart still stays in its beat (step 5).
- **Re-hook every 8–10s.** Open a new small question or turn ("But who actually got hit?", "Then a third flaw appeared.") and don't deflate it in the very next line.
- **Bridge every contrast: say why both are true.** Real stories often hold two true facts that point opposite ways: a flaw that is widely exploited but failed in tests, a company fined that saw its shares rise, a claim shared by thousands of accounts that traces back to a handful, an official denial next to documents that seem to confirm it. Put two such beats side by side with no explanation and the viewer hears a contradiction. They can't tell which fact to believe, so they trust neither, and the reel loses them right at its most interesting point. A tension handled well is a turn, which is what "Re-hook" asks for. So the line where the story turns gives the reason both are true, before or together with the second fact, in plain words, and signals the turn ("But", "Unlike", "Yet"). That shot's headline names the difference, so the two headlines don't contradict each other with the sound off. Where a visual can carry the contrast (a split, a before/after, a wipe into the turn), use it. The reason must come from facts.md at the source's strength. If no source says why, say so plainly ("the company hasn't explained") rather than supply a mechanism. A plausible explanation that nobody published is invention, however good it sounds. (Worked example: PHP2Shell v2 in `references/php2shell-case-study.md`.)
- **Plain words for terms of art.** Gloss each technical term on first use, or replace it with what it means at the source's strength: "rated 9.2" becomes "rated 9.2 out of 10 for severity"; "rooted" becomes "gained root, full control of the device". A viewer who needs a glossary has already left.
- **Fewer facts, each landed.** About five or six distinct figures or claims in 55s. Each figure that stays gets its own visual moment (a stat shot, a document crop on the line); a figure that no shot shows is a candidate to cut.
- **Say who it affects.** One clause of plain stakes for the viewer ("the boxes guarding company networks"), never a perpetrator the sources haven't named.

  Before (PHP2Shell v1, each beat one more fact):
  > PHP2Shell rated 9.2. / Fixes landed on 21 October for PHP 8.2 to 8.5. / Still, the clearest break-in came at firewalls. / Dream says 25 Palo Alto firewalls were rooted, then chained to full control.

  After (same facts and attributions, escalating, glossed):
  > It's rated 9.2 out of 10 for severity. / But who actually got hit? The clearest break-in wasn't a website. It was firewalls, the boxes guarding company networks. / Security firm Dream says attackers gained full control of 25 Palo Alto firewalls. / PHP had shipped fixes on 21 October.

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
  - **Every beat change flows.** The first line of a beat follows from the last line of the one before: it answers, contrasts, takes the next step, or picks up a word or idea. A section change (what happened → where the money went → who's responsible) gets a spoken turn ("So who's behind it?", "Meanwhile…"). Each beat still opens with a whole sentence (caption rule); to carry one sentence across a cut, use `shots` inside one beat.
  - **Spoken, not written.** Contractions; no semicolons, parentheses or colons; times as said aloud ("just after 8 p.m. UTC"). No stock AI phrasing (listed in C13).
  - **No recap, no generic close.** Don't re-narrate figures already said; the closing line is specific to this story.
  - Style never overrides accuracy: every hedge and attribution from step 3 stays.

  Before (reads as AI, each beat restarts):
  > Binance puts the hack's impact at about $6.3 billion. / Reports call it the biggest crypto theft on record. / Funds left Binance's hot wallets for attacker addresses. / Analysts trace them across 9 or 10 blockchains.

  After (same facts and hedges, beats linked):
  > About $6.3 billion. That's the impact Binance puts on this hack. / Reports call it the biggest crypto theft on record. / So where did it go? Out of Binance's hot wallets, to attacker addresses. / From there, analysts trace it across 9 or 10 blockchains.

## Visual spec (current; one rule per topic)

`references/msci-case-study.md` shows these rules applied to a real reel, and lists the defect behind each rule.

**Canvas and style.** 720×1280, h264 + AAC 48 kHz stereo. Voiceover-only; people appear only as subjects in photos or footage. Flat 2D motion-graphics collage on **one background colour for the whole reel**: saturated blue (11, 74, 168) behind every shot (headline cards, images shown whole or zoomed, diagrams, the AI map's sea and the end card). No shot switches to another background colour; blurred fill is tinted with the same blue, and full-bleed images and AI clips have no background. White ALL-CAPS headlines with single-word yellow highlights (DejaVu Sans Bold); sentence-case captions with a black outline and no box.

**Layout.**
- Frame, top to bottom: the header stack from y=140 (headlines wrapped at 640px: one line at 52px, or two at 44/40px, so the caption keeps its place); the caption band, top line at y=300; the content band below it, down to y=1030. Below 1030 the platform's own caption, name and buttons cover the frame, so nothing the viewer must read goes there; photos may bleed into it. Text the viewer must read in a screenshot is safest above about y=830, the conservative "bottom 35%" platform guide.
- **Images are as large as their keep box allows.** Look at each image and set its keep box (`keep` in the manifest): everything that makes it relevant, including every word of any text that must stay readable. The build zooms the image as far as it can while the whole keep box stays inside the frame and inside the content band (below the caption band, above y=1030), even at the end of the creep. A small keep box (a logo, a face) goes full-bleed; a keep box covering the whole image (a screenshot, an article thumbnail, a chart) shows it whole and edge to edge. Space the image leaves is filled with blurred fill, so no shot shows empty background. Cropping is fine outside the keep box, never through it: a crop that cuts a word in half or turns a claim into a fragment is a defect. AI images are full-bleed, and clips (real or AI) always fill the frame.
- **Full-bleed real photos.** To make a real photo fill the whole frame (for example, a strong photo as the hook), set `"full_bleed": true`. It is cover-cropped to the frame, centred on its `keep` box (or the image centre with no `keep`). A keep box too large to fit the frame still wins: the image is then shown whole on blurred fill. Use it for photos, never for screenshots or text the crop would cut.
- If an image's text is still unreadable when shown whole, report it as a trade-off; do not hide it.
- Every shot shows a representative visual (a receipt, a real clip, a headline card, the diagram, the map or a labelled AI illustration). No shot shows only a headline on plain colour.
- **Headlines.** A viewer who reads only the headline, with the sound off and a glance, should know who did what. So each headline is a self-explaining line: a subject and a verb or figure, about 3–8 words (roughly 40 characters). It takes one line at 52px or two at 44/40px; the build sizes it so the captions stay at y=300, and rejects one that needs a third line. Write it this way:
  - **Name the subject, with who they are the first time.** A name the viewer hasn't heard is just a word ("DREAM"). Put the identifier in the headline ("SECURITY FIRM DREAM…") or, when it won't fit, in the source label ("DREAM, SECURITY RESEARCH FIRM • 26 OCT 2026"), and have the narration introduce it.
  - **No telegraphese.** Dropping words until the line turns ambiguous ("PHP POWERS WEB": powers what, which web?) is the failure; keep the articles and objects that carry the meaning.
  - **No unexplained jargon.** "ROOTED", "RCE", "KEV", "CVSS" mean nothing to most viewers; say what they mean.
  - **A score says what it measures.** "9.2 OUT OF 10" alone reads like a good review. Name the measure so the direction is obvious ("SEVERITY", "RISK", "DROP"), and use the source's own band word when it gives one ("CRITICAL").
  - **The takeaway, not a caption repeat.** The caption already says the sentence; the headline states its point. It carries the claim's status at the source's strength ("DREAM SAYS…", "ALLEGED…"), because there are no status tags.
  - **Keep it the same line count across a super change**, so the image under it doesn't jump.

  | v1 headline | Problem | Better |
  |---|---|---|
  | PHP POWERS WEB | ambiguous telegraphese | PHP RUNS MUCH OF THE WEB |
  | RATED 9.2 | what is rated, out of what, and is high good or bad? | FLAW SEVERITY: 9.2 OUT OF 10 |
  | FIXES OUT 21 OCT | whose fixes? | PHP PATCHED IT ON 21 OCT |
  | 25 ROOTED | who is Dream, what is rooted? | DREAM: 25 FIREWALLS TAKEN OVER (label: "DREAM, SECURITY FIRM • 26 OCT") |
  | MOST DID NOT FALL | most what? And after the firewall line it reads as a contradiction | TENABLE: SAME ATTACK FAILED ON 5 ORDINARY SITES |
  | UNUSUAL SETUP ONLY | of what? | THIRD FLAW NEEDS A RARE SETUP |

  A paragraph never repeats the caption.

**Motion.** The reference reel is almost never frozen: only 12% of its frames are fully still. It moves through a fixed set of moves, each tied to a narrated word or a cut (observed timings in `references/reel-format.md`). Use these moves; do not invent others, and never zoom or pan the whole composited frame.

What never moves: caption words (a revealed word changes colour, never place), tags and source labels, and headlines over photos. They hold their position for the whole shot.

Allowed moves:

| Move | Use it for | Parameters |
|---|---|---|
| Slow creep | The base layer of every headline card, diagram, map and image (real or AI), so no shot sits frozen | Push in or drift up, at most 102% scale (or about 5px/s) over the whole shot, linear. The keep box stays inside the frame throughout. Shots that continue one visual across a cut (a super change) share one creep, and one `move`, timed over the whole run: it never restarts at the cut. A `"creep": "none"` shot inside a run holds the run's current frame, and the next shot carries on from there. |
| Graphic wipe | Transitions between sections, 1–3 per reel | `"wipe": "left"` (or `"up"`) on the first shot of the new section: a panel in the reel's blue with yellow edges crosses the frame in 0.5s, covering the old shot and uncovering the new one. Captions are burned on top, so it never covers them. Silent (no whoosh). |
| Stat count-up or pop | One sourced figure the narration lands on (a score, a count, a date) | A `stat` shot: the figure counts up to its value over 0.6s (a plain number) or pops in (anything else), on the measured time of the word that says it; its label is on screen from the first frame and a low generated hit sounds as it lands. |
| Slide-in or pop-in | A photo, face cutout, icon or shape arriving on a headline card, diagram or map when it is named | It slides in from an edge or rises from below, or fades in from 0% over 0.3–0.5s, with an ease-out, then holds and creeps. |
| Highlight sweep | Headline cards | Yellow highlight moves word by word with the voice, each word lit when it is spoken (the beat's measured word times; a fixed 0.25s a word only if the key sentence isn't in the narration); the line-and-dot extends to the newly quoted sentence. A card repeated in the next shot starts with the words already lit. |
| Build | Diagrams | Nodes and arrows appear on the narrated word; the red ✗ snaps on at the denial; small tokens (dots, coins) may flow along an arrow to show money or influence moving. |
| Map move | The AI-generated map | The map clip's own pan or zoom between the narrated places (ask Muse for it in the prompt). |
| Camera zoom on a graphic | Diagrams only | Zoom into one section to show detail, then back out, over 1–4s, ease in and out. |
| Pan across a wide image | A wide real photo that needs to show more than fits (a crowd, a hall of flags) | One direction, 1–2s, ending on the subject; the keep box is fully visible at the end. `"move": "pan"` on an image. |
| Particle overlay | Rarely, for an emotional moment on an AI or event image (confetti, sparks, falling paper) | Up to 3s, behind the captions, never over a real receipt or its text. |
| Inset grow | A clip or photo that starts as an inset and grows to fill the frame | Once or twice per reel, 0.4s, ease-out. `"move": "inset"` on an image. |
| Push toward the subject | A still image in the hook (or anywhere a photo needs to move) | `"move": "push"`: 100% to at most 110% over 1.5s, ease-out, toward the keep box, which stays whole; then creep. |
| Hard cut | Most shot changes | Cut on a narrated word. |

Rules:
- Real clips get no added zoom. AI clips keep their own motion and are never zoomed or panned further.
- Fast moves (wipes, slide-ins, pops) last 0.6s or less, except a wipe of up to 1.5s and camera zooms on graphics. After any move, the shot settles into creep. Never stack two fast moves at once.
- Shots are 1–3s, never over 4s (headline cards and timeline shots up to 5s; the end card and summary card run for the loop-back narration).
- **Stillness cap:** at most 50% of the reel's frames may be fully still (measured as in the checklist, B8). A static slideshow fails even if every shot is well designed.

**Play as a video, not a slideshow.** The stillness cap is not enough: a 2% creep counts as motion, so a reel of still pictures passes it. The PHP2Shell v1 reel did: still images held 82% of its time, the same headline-over-small-picture layout repeated in nearly every shot, one photo appeared in four shots, and nothing on screen acted out a line. What makes a reel feel like video is shots that do something: a clip with its own action, or a graphic that builds on the word. The build's pace report (printed at the dry run and after the build, from `scripts/reel_pace.py`) measures this; treat each warning as a fix to make, or a reason to give at delivery:
- **Stills hold at most half the reel's time** (end card and summary excluded). The rest is video (real footage, Muse AI video) or built graphics (stat, diagram, timeline, headline card).
- **At least one video shot per ~15s** (two or more in any reel), the hook first.
- **No more than ~6s of still images back to back.**
- **A picture is used once.** At most two shots per image (super changes count), never coming back after other shots, and never on screen over 4s across super changes: a new headline over the same picture is not a visual change.
- **A still covers at least 40% of the frame.** Shown whole on blurred fill, a 16:9 photo covers about 30%; it reads as a small picture on a slide. Tighten the keep box to the detail that carries the line (a device's port, the one sentence of an advisory, a face), crop the source to it, or choose a taller visual.
- **Vary the layout.** Alternate full-bleed pictures, tight detail crops, clips, and built graphics, so consecutive shots don't share one template.

**Captions.** Burned into the video, in the style of short-form social reels: no black box, no lower third. They carry the narration for viewers watching muted, so they must match the voice word for word and in time.
- **One short phrase at a time**, 2–5 words, at most two lines. Words appear one by one as they are spoken and accumulate in place; then the whole phrase is replaced by the next. Break at phrase boundaries: a phrase never ends with an article, preposition or conjunction, never splits a name or a number, never crosses a beat boundary, and never opens mid-sentence. Write figures in the narration as digits ("$6.3 billion", not "six point three billion"): captions come from the narration text.
- **Look.** Bold sans-serif (DejaVu Sans Bold), 38px, sentence case as written in the narration (headlines stay ALL CAPS; captions do not), white with a thick black outline and a soft drop shadow. The current word is bright yellow; already-spoken words are white. Same size for both: no size change, no box, no pop.
- **Place.** Centred at the upper middle, about a quarter down: the top line at y=300, under the header stack and above the visual, so the eye moves a short way from the words to the evidence. If a beat's header stack runs past y=286 (a two-line headline under a tag), the build drops that beat's captions just under it and warns; shorten the headline instead. Lines wrap by measured width, at most 680px; a third line is allowed only as overflow safety, and the build warns when a phrase needs one.
- **Anchored.** Each line is laid out at its full phrase width first, and every word is drawn at its final position from the moment it appears. Never re-centre on the words spoken so far: that shoves earlier words sideways with each new word.
- **Timed from the voice, never spaced evenly.** Word times come from a Whisper pass on each beat's own narration audio, with split figure tokens merged back first ("$6" + ".3" → "$6.3", "94" + "%" → "94%"). Every captioned beat must match its script word for word after that merge; the build stops if it doesn't (listen to it: a dropped or changed word means re-narrating; a figure written differently from how it's said means rewriting the script line). Even spacing caused the original misalignment, because figures take far longer to say than plain words ("$6.3" took 0.8s). About 0.2s of Whisper drift is still expected. To fix a word the sync check (or a listen) reports, nudge only that word with `"caption_nudge": {"$6.3": -0.2}` on its beat (`"the#2"` picks the second "the"), then re-run `--stage subs` and `--stage mux`. Don't re-estimate the whole reel.
- **Alongside, not instead of, the labels.** Tags, source labels and headlines stay on screen with the captions. The end card is the exception: it carries no captions, so nothing competes with the pointer. A phrase that would still be on screen when the end card cuts in is left out whole rather than cut to a fragment (the build warns; to keep it, move the end card's cut to a phrase boundary with shot `weight`s).
- **Sample before a full rebuild** when the caption style or layout is new or has changed: build the hook (`--stage hook`) and look at it. Measured timing can't prove a word wasn't dropped or slurred, so ask the user for a listen-through before posting.

Give headlines over busy photos a black stroke.

**Tags.** The only tag on screen is DISINFORMATION POST, on false or unverified material (see below). No status tags: no CONFIRMED, STATED BY, ESTIMATE, UNCONFIRMED, DISPUTED, ALLEGED or DENIED pills. A claim's status is carried by the narration and headline wording at the source's strength ("alleged", "about", "says", "denied") and by the source label; facts.md still records each claim's status so that wording can be checked.

**Labels: viewer-relevant vs production notes.**
- Always present: source labels (outlet + date, or account + date); "AI-GENERATED ILLUSTRATION" on every AI shot; the DISINFORMATION POST tag on false material.
- Placement: the source label is a small, muted line just above the headline (below the disinformation tag, when there is one), like an outlet name on a card. Never put it in a bar near the captions, where it reads as a second caption. The end card's disclosure line sits just under the pointer.
- Production notes (how a headline card was made, muted audio, masked captions) are left off the screen. Real-clip labels are account + date only. A composite of several accounts' clips uses one label describing the set, with each account named on its tile (see "Real clips").

**False or unverified material (highest priority).** Any image that *is* the false or unverified claim (a fake post, a doctored graphic, an unverified screenshot) carries its tag every time it appears, for example "DISINFORMATION POST — flagged by [verifying outlet]". It never opens the reel, never appears on the end card, and never sits under a true line; use a real receipt for true lines. An article's lead image (og:image) is often the false material itself, such as the fake posters a fact-check debunks. Look at it before using it; if it is, open the reel with a cropped screenshot of the article's outlet name and article headline instead (or a labelled AI illustration), and show the false material later under its tag.

**Asset gathering.** Every shot gets its visual this way, except the diagram, the map, the timeline and the end card. Those are not a way around it: use the diagram only for the one chain of links, the map once, and the timeline once, just before the end card. Gathering has two parts: a search that always runs in full, then a choice that takes judgment.

**1. Search every place, for every shot.** Before choosing, look in all four places and note what each gave:
- **A. Cited articles.** Each article's lead image (og:image) and its inline photos or charts. A page-text fetch lists the page's image URLs.
- **B. Other coverage and free images.** Reputable outlets or agencies covering the same story, and Wikimedia Commons (how-to below).
- **C. The primary source.** The post, statement or page itself, for a screenshot cropped to the claim (see "Screenshots").
- **D. Footage.** A real clip of the people, place or event, if one can be cleanly obtained (see "Real clips"). For the hook, look for footage first.

A find counts only when it is **related**: it shows the people, organisations, products, places, documents or data the shot is about. A stock "hacker in a hoodie", an unrelated archive photo, or a logo shot reused from another story is not related. An archive photo of the people involved is related, but never present it as the event itself.

**2. Choose.** This is a judgment, not a fixed order. Put the best related find next to what a Muse AI image or video could show, and ask which makes this shot's line clearer and more watchable.
- **Keep the real find** when it is the evidence for the line (the post, the document, the chart, the actual person or place), or when it shows something the viewer couldn't otherwise picture. Never swap evidence for AI because it looks dull. Give it motion instead: `push`, `pan`, `inset`, or a tighter keep box on the detail that matters.
- **Use Muse AI** in three cases:
  - the line is a concept, a process or a scale (money frozen, a queue paused, a message spreading across thousands of accounts);
  - nothing related was found;
  - the related find is still dull after a tighter crop and motion: a reused logo, a stock-looking photo, a small or blurry image, a plain head shot already used, or the same subject as the shots around it.

  Make AI material a video by default: an AI still is only the start frame you check and then animate (see "AI material"). An AI still left still is the weakest moving shot there is, so log why video didn't work. See "AI material" for the limits.
- **A figure is a stat shot.** When a line lands on one sourced figure (a score, a count, a date, "0 of 5"), show it as a `stat` rather than a picture: it arrives on the word and carries its source label.
- **Weigh trust.** Viewers trust a labelled AI visual less, even when it is accurate. So don't use AI where a real image carries the line just as well.
- **Headline card**, only when no real find works and AI can't show the line. It is the weakest shot (a headline on plain blue); at most 2 per reel, not counting the end card.

**3. Check the reel as a whole.**
- Something on screen changes every 2–4s: a cut, a move, a highlight, or a node or graphic build.
- Shot types take turns. Never three similar images in a row, no subject in more than two shots, and no two text screenshots back to back.
- If most shots show one logo, look for photos of the people, places or objects in the story instead.
- Run the dry run and read its pace report (see "Play as a video, not a slideshow") before generating or capturing anything more: it is far cheaper to swap a planned still for a clip or a stat now than after the build.

**4. Log it.** For each shot, add a row to the **asset log** in facts.md with four entries:
- the shot;
- what each of A–D gave (or "nothing related");
- what was chosen;
- why, in a few words, for example "B: Reuters photo of the minister, the receipt" or "A: only the logo, already used twice; AI: frozen funds".

Record each asset's file, source, date and licence there too. The verifier checks this log (D4, C7).

**When an image has too much text (fails D5), repair it before dropping it.** Stop at the first step that works:
1. Re-crop the keep box to the photo, chart or logo, or to the account name plus the one or two claim lines (about 25 words).
2. Use the same article's lead image, or an inline photo or chart.
3. Use another source's image, or a shorter post stating the same claim.
4. Use AI.
5. Use a headline card, only after steps 1–4. Note each attempt in the asset log.

**Downloading and checking images.**
- **Download as JPEG or PNG.** Image CDNs pick the format from the request, so a `.png` URL can return AVIF or WebP, which the build can't read. Send `Accept: image/jpeg`, or change `f_auto` to `f_jpg` in Cloudinary-style URLs.
- **Wikimedia Commons.** Search with `commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srsearch=…`, then read each file's licence, author and date. Download either the original file URL or the `thumburl` the API returns with `prop=imageinfo&iiurlwidth=1280`. Commons rejects thumbnail sizes it didn't generate (HTTP 400).
- **Credit the photo on screen** with photographer, year and licence (for example "PHOTO: GAGE SKIDMORE, 2025, CC BY-SA 3.0"), or "IMAGE: OUTLET, DATE" for an article's image. A concept or stock photo is labelled "ILLUSTRATIVE PHOTO".
- **Check what each photo shows.** Crop out anything now false, such as an old job title on a slide behind the person. A photo of a person next to a claim must not suggest they made it unless they did, so name whose statement it is in the source label.
- **Look at every image and clip before it goes in the manifest.** The build rejects an image it can't read or that is almost blank.

**Screenshots.** When you use a screenshot of the actual source (the X post, the company statement, the article page), follow these capture rules:
- **The claim must be visible in the screenshot.** Posts cut off with "Show more" often hide the very line you need; use another post that states it in full, or choose again (see "Asset gathering").
- **Times must match the labels.** Capture with the browser set to UTC (or the time zone the reel uses), because posts show times in the viewer's time zone. X posts can be captured without logging in from `platform.twitter.com/embed/Tweet.html?id=<post id>&theme=dark`.
- **Crop out what isn't the source:** ads, cookie banners, site menus. Set a keep box on the part that carries the claim.
- **Wait for images before a screenshot.** Article images often load only when scrolled into view. Scroll each one into view and wait until it has loaded, or the capture shows grey boxes.
- **Re-read the page when you capture it.** Pages change: a headline figure updated between research and capture is a fact to update in facts.md, not a detail to ignore.
- **Never put a screenshot under a headline or line it doesn't support.** An analyst's headline naming a culprit doesn't belong under a line stating it as fact.
- **Little to no text on screen besides the headline and caption.** The headline and caption already carry the claim, so the visual behind them should be an image to look at, not a page to read. Prefer a photo, logo, chart or graphic. When a screenshot is the receipt, crop the image itself to the account name plus the one or two lines that state the claim (about 25 words at most). Never show a whole post, a paragraph, or several posts.
- **No screen jumps.** At most one text screenshot per beat, and never two text screenshots back to back; put a photo, graphic or diagram between them. Several fast cuts between text-heavy frames make the screen jump and are unreadable.

A plain article photo or thumbnail is shown with outlet and date; it is not a screenshot of the page, so don't call it one.

**Headline cards.** Use one only when "Asset gathering" found no real image that works and AI can't show the line. Quote only established wording. Outlet name, the outlet's actual article headline where known (at most 10 words: trim a longer one to a verbatim excerpt, marking cut words with "…", never rewording it), single-word yellow highlights, line-and-dot to faint body text (≥22px, readable), and the key sentence highlighted. Fill the card with no blank half. Use each card once. A headline card that opens the reel carries a representative image filling the whole frame behind it (`card.image`, credited by `card.image_source`, centred on `card.keep`); any other card may too. The build darkens the image behind the top and bottom text with gradients, so every line stays readable and the middle of the image stays clear. The image follows the rules for any image: never the false material, always credited, and an AI illustration labelled. Set it in the reel's own style, never in the outlet's page design or logo, so it can't be mistaken for a screenshot.

**Diagram.** One chain, with nodes revealed on the narrated word: the same measured word time that turns that word yellow in the caption, so the node and the word change on the same frame. When the diagram continues over several shots, nodes already shown stay on screen (a later shot whose node list starts with the earlier nodes continues it), the spacing is the same in every shot, and a ✗ already drawn stays drawn. The node column starts below the caption band, and the build tightens the spacing so up to five nodes end above y=1030. Each link carries the status of the claim it represents. When a link is denied or disproved, a red ✗ appears on it when the denial is narrated. Check every node name against the facts sheet.

  **A source's own chain figure is a receipt, not the reel's diagram.** If a source draws the chain (a research firm's attack-path figure), show it as a receipt only when its labels can be read at phone size, cropped to the part the line is about. A wide figure shown whole becomes a thin strip of unreadable boxes (the Dream figure in PHP2Shell v1). Then rebuild the chain as the reel's own diagram, with nodes revealed on the words and the source in its label ("CHAIN AS DESCRIBED BY DREAM, 26 OCT 2026"), keeping the source's node names and claim status.

  **AI motion behind the diagram.** Give every diagram an AI motion clip behind it, because a still blue plate reads as a slide. The only exception is when the nodes fill the frame too tightly for the motion to show. A diagram can move like an AI video without handing the AI anything that must be exact. The words, boxes, arrows and ✗ have to match facts.md and land on the narrated word; AI video can't spell reliably and can't be timed to a word, and an AI-animated diagram has clipped its own labels at the frame edge before. So split the work:
  1. Run `python3 scripts/build_reel.py manifest.json --stage diagram-brief --workdir <dir>`. For each diagram shot it writes a text-free start frame (the background blue, a faint guide line where the arrows run, soft glows where the nodes will sit), the length the clip needs (measured from the narration), and a ready Muse prompt, in `<dir>/diagram_brief/`.
  2. Generate the clip with Muse from that start frame and prompt (image animation; a text-only prompt also works). Look at it: no words, numbers, shapes or objects the plate doesn't have, nothing pushed off the frame.
  3. Set `"diagram": {..., "motion_clip": "chain_motion.mp4"}` (and `clip_start` to reuse one long clip across several shots of the same diagram).

  The build plays the clip as the base layer, tinted toward the background blue, and draws the nodes, arrows, labels and ✗ on top at the narrated words, exactly as without it. The label reads "… · AI MOTION". Never ask the AI to draw the diagram itself or its words; if a beat needs a move the plate can't give (a node sliding in, tokens along an arrow), build it in the script.

  **AI animation of a finished diagram (image + prompt).** Muse can animate a script-made diagram with its text, but it redraws every frame, so it drifts. In a test on a causation diagram ("keep all text exactly as shown"), it began a slow zoom within 0.3s, cut "FALSE CAUSE" to "ALSE CAUSE" by 2s, invented a dark screen frame, and faded the timeline note it was told to keep. Use such a clip only for the span where it still matches its source:
  1. Run `python3 scripts/check_ai_animation.py diagram.png clip.mp4 --strip strip.png`. It compares every frame with the source where the source has text and lines, reports how long the clip stays faithful (`usable_end`) and when new marks appear (a cross being drawn), and PASSes only if at least 1s is usable.
  2. On a PASS, use the clip as the shot's `clip` with `"material": "diagram"`, `"clip_end": <usable_end>`, and `clip_start` chosen so the event you need (the cross) lands on the narrated word; the shot holds the last faithful frame after `clip_end`. Look at the strip: an event must be what the narration says, at the place it says.
  3. On a FAIL, don't use it. Animate those moves in the build instead (the reveal and the ✗ on the narrated word), with an AI motion clip behind the diagram for movement.

**Map.** Generate it with Muse (an AI video, or an AI image the build moves), not with the build. Use it once, to show where the story happens or which way something moved. Set `"material": "ai"` and `"schematic": true`: the build labels it "AI-GENERATED MAP • SCHEMATIC — NOT TO SCALE".
  - Ask Muse for a stylised map on the reel's saturated blue (11, 74, 168) with light grey land, 9:16, 720×1280, with its own slow pan or zoom between the places, and **no text, labels, flags or logos**. Place names come from the narration, and so from the captions and the headline.
  - AI draws coastlines and borders loosely. Look at the result: the places the narration names must be recognisable and in the right relative position, with no invented countries, cities or routes. A generic flow arrow or glow is fine; a specific pipeline, shipping lane or transfer route is not, unless a source shows it, and then it must be accurate (otherwise show a real map from that source as a receipt instead).
  - Keep the region of interest in the content band, below the caption band, and inside y=1030.
  - **A simulated spread over a world-map backdrop** (posts popping up across a map; see "AI material") is an AI illustration, not the reel's map, when it claims nothing about where: no place names, and posts scattered without pointing at particular places. If it names or points at places, it counts as the reel's one map: set `"schematic": true`, and use only places the sources name.

**Real clips.** Short, muted slices, only if cleanly obtained. Mask the clip's own burned-in captions and logos so they never collide with the headline or our captions; measure the bands from a rendered frame, never guess (ffmpeg delogo needs x > 0). If a clean slice cannot be obtained, omit it and say why; never invent one.

  **Side-by-side composite of real clips.** To show the same content posted by several accounts, a script may tile their real clips (2×2 or side by side) into one 9:16 clip. Pass it as `"clip"` with `"material": "real"`. The rules:
  - **Unedited tiles.** Each tile is that account's actual clip, changed only by crop, scale, trim and sync.
  - **Names copied exactly.** The account name and avatar drawn above each tile are taken word for word from the post.
  - **Logged.** Each account, post URL and date goes in the asset log.
  - **A label that describes the set.** Use one source label saying what the tiles are, plus the trace date (e.g. "TRACED EXAMPLES • 28 OCT 2026"). If the tiles aren't part of a figure in the reel, say so ("NOT CNA'S 68"). Never imply the tiles are the whole set or a sourced count.
  - **Room for the reel's text.** Leave the headline band and the caption band free of account names and other tile text the viewer must read.
  - **Burned-in captions.** Mask the source clips' captions (`clip_mask`) wherever they would collide with the reel's headline or captions.
  - **Muted**, like any real clip.

  Build it with `python3 scripts/make_composite.py spec.json --out composite.mp4 --preview`:
  - **What the script does:**
    - places 2–4 tiles in the content band, between the caption band and y=1030, with the reel's blue over a blurred fill behind them;
    - draws each account's avatar and name exactly as given;
    - masks the source clips' captions per tile;
    - can bring the tiles in one after another (`stagger`).
  - **What it refuses:** a tile without its account, post URL and date, or a composite without the set's label.
  - **What it prints:** the manifest entry and the asset-log rows.
  - **The preview:** shades the header, caption and platform-UI bands, so you can check that nothing readable sits under them.

  The spec format is at the top of the script.

**AI material (Muse).** AI images and video are a creative tool, chosen as described in "Asset gathering":
- for concepts, processes and scale;
- for shots where the real finds are missing or dull.

Subject and style are open: flat illustration or photoreal, still or moving. The one condition is that the result can't be taken for evidence. This follows AP's standard: AI imagery only as clearly labelled illustration, never as a news photo. For examples from past reels, see `references/msci-case-study.md`. The limits are the same for images and video:
- **Never show:**
  - a real named person;
  - the alleged event itself;
  - a real place shown as evidence;
  - an organisation's building or logo;
  - anything that could pass as a news photo or footage of a real event.
- **Simulated posts and feeds are allowed**, to show a message spreading: a wall of posts multiplying, a feed scrolling, the same message appearing across many phones.
  - **Keep them generic.** Use invented post shapes. Show no real platform's logo or interface, no real account name, handle or face, and never recreate a real post.
  - **Post text may be readable, as texture.** Viewers aren't meant to read the posts; the headline and caption carry the claim. Check every frame:
    - account names are invented and generic (`@user_1234`), never a real account;
    - the message is either a neutral placeholder ("INFO A001", "Excited to share…") or the sourced wording spelled exactly. If the message comes out garbled, regenerate, mask it (`clip_mask`), or pick a clean slice (`clip_start`/`clip_end`);
    - like counts, shares and times are small, generic decoration, never the story's own figures and never beyond the scale the sources give;
    - place names, on the posts or on a map behind them, appear only where the sources place the spread.
  - **Stay within the sources on scale.** How many posts, and how fast, must not go beyond what the sources say.
  - **When the message is false**, the narration says so in the same beat, and the visual never sits under a line that presents the message as true.
  - **A simulated post is never evidence.** When the reel needs to show what was actually posted, use the real post: a screenshot, its clip, or a side-by-side composite of real clips (see "Real clips"). Simulated posts carry the AI label, not the DISINFORMATION POST tag, which is for real false material.
- **No readable text in generated frames**, except on simulated posts and feeds (rules above). All other words are added by the build.
- **Short, labelled and muted.** Each AI still is ≤3s and each AI video ≤4s, labelled. Real receipts stay on screen longer than illustrations.
- **A scene with one purposeful action, not an icon.** Flat clip-art (a server icon, a shield, a padlock on a plain background) looks like a slide graphic and tells the viewer nothing the headline doesn't. Ask for an illustrative scene with depth and light, and one physical action that acts out the line: a vault door unlatching for "without logging in", one cube after another turning red for "chained to full control", a key failing in a lock for "exploits had to be tuned to each target". Metaphors like these keep it clearly an illustration, never footage of the real event.

  **Making AI video move with purpose.** Generate the still first, look at it, then animate it with Muse as the start frame. Write the prompt as: start frame, one camera move, one action that acts out the line, and constraints. Ask for 5s so a clean 3–4s can be trimmed with `clip_start`/`clip_end`. Templates:
  - Access or breach: "A heavy vault door in a dark server corridor, blue light. Slow dolly forward as the door unlatches and swings open, light spilling out. One motion only. No people, text or logos. Keep the subject centred, no morphing, no scene change. 9:16."
  - Chain or spread: "Five identical glass cubes in a row on a dark floor. The first glows red, then a thin beam of light travels to the next and it turns red, one after another. Camera fixed. No text. No morphing. 9:16."
  - Defence holds: "Macro shot of a brass pin-tumbler lock. A key slides in and fails to turn, then a second key fails. Camera pushes in slowly. No text. 9:16."
  - Money or scale: "Stacks of coins on a flat blue surface. A conveyor carries them left to right into a frosted box where they vanish. Camera locked. No text or currency symbols. 9:16."
  - Process paused: "Paper cards on a conveyor belt halt at a barrier; one card is lifted and stamped. One smooth motion. No text. 9:16."

  Look at the result: the action must be the one asked for, finish inside the trimmed span, and invent nothing the line doesn't say.
- **Never beyond the narration or sources.** An AI visual must not suggest something the narration does not say or the sources do not support.

  **Bringing in an AI video from Muse.** Muse saves the generated video as an mp4; put it in the assets folder and reference it like any clip: `"clip": "ai_frozen_funds.mp4", "material": "ai"`. Ask Muse for:
  - **9:16, 720×1280**, so nothing is cropped. Any other shape is cropped to fill the frame, around the clip's `keep` box (fractions of the frame, as for images), or the centre without one; the build warns when an AI clip isn't 9:16.
  - **At least as long as its shot** (3–5s). A shorter clip would hold its last frame, a freeze, and the build warns; use `clip_start` to pick the best part of a longer one.
  - **No text, logos or watermark** in the frame, except post text on a simulated feed (see the rules above). If one appears anyway, cover it with `clip_mask` or regenerate.
  - **For a simulated feed or wall of posts**, still ask for 9:16, with the posts large enough to fill the frame. A 16:9 grid cropped to 9:16 keeps only about two columns and loses the sense of many accounts.

  The build handles the rest: any frame rate becomes 30 fps with an exact frame count, the clip's own audio is dropped, and the "AI-GENERATED ILLUSTRATION" label is added. Look at the clip before it goes in the manifest, as with any asset.

**Audio.** About −14 LUFS integrated: gentle compression (threshold −28 dB, ratio 12, makeup 12 dB) before loudnorm, because loudnorm alone stops short on true-peak limiting. Use an original low music bed (generated tones, no copyrighted music) with the voice clearly on top. Inter-sentence gaps of 0.15s; no silence over 0.3s except the final 0.5s; no narration words cut. Export 48 kHz stereo AAC at 192k (the default bitrate overshot true peak).

**End card.** On the background blue; the closing line; a pointer to the full story that is a **real screenshot** of a referenced article page (`pointer.image`), showing the outlet's name or masthead, the headline, the byline and a date (in the screenshot, or the capture date in `pointer.captured`), plus the lead photo when it fits, so it reads as the article itself and not a typed card. Relative times ("13 hours ago") go stale; handle them in this order, cheapest first:
  1. **At capture**, crop to the outlet name, headline and byline, leave the relative time out, and record the capture date in `pointer.captured` ("30 OCT 2026"); the build prints it under the screenshot.
  2. If the relative time sits inside the headline or byline block and can't be cropped out cleanly, recapture a view that shows an absolute date: the article page first, an archived copy only as a last resort.
  3. Never mask, blur or retype text inside a screenshot; it is a receipt.

  If one article blocks capture (paywall, bot wall), capture another article listed in facts.md. A headline-card pointer (`pointer.headline`, never a fake poster) is allowed only when no referenced article can be captured, with the attempts logged under "Visual fallbacks" in facts.md and `pointer.no_screenshot` set to the reason; one small disclosure line naming the AI voice, any AI illustrations and the sources. No silence after the final narration.

**Summary card.** The end card may instead be, or start with (as the first of the end beat's `shots`), a summary card: one infographic restating the reel's key figures and distinctions, in the reel's own style on the background blue, so a viewer can take it in at a glance or in a screenshot. Give it `"summary": {"title", "panels", "sources"}`; a panel is a figure (`value`, `label`, `source`) or a distinction (`pair` of two halves, each `title` and `text`, such as what's confirmed and what isn't). The build lays the panels out in a grid with the same panel sizes, margins and type sizes, shrinks text to fit and stops rather than clip it, starts the panels below the caption band and ends the footer above y=1030, and brings the panels in one after another, all of them within the first 40% of the shot. The finished card then has to stay on screen long enough to read or screenshot: at least 0.4s per panel and never under 1.5s (2s for five panels). The end card needs only 1.5s, so take the time from it: raise the summary shot's `weight` and lower the end card's. The build stops with the numbers when the finished card would show too briefly, and its self-check measures the rendered reel with `scripts/check_card_hold.py`. A panel that lands just before the cut is never actually seen, so the summary may as well not be there. It is still captioned; only the end card isn't. Every figure and wording on it comes from facts.md, at the source's strength. It never tells the viewer what to do with it: no "SAVE THIS", "screenshot to save" or similar on the card, unless the user explicitly asks (`"allow_save_prompt": true`). Four to six panels read well; the build stops when they don't fit.

## Build pitfalls (each one has broken a past build)

`scripts/build_reel.py` guards against each of these, and stops with an error rather than build around one. Keep the guards if you change the script, and follow the same rules for any ffmpeg command you run by hand.

- **Never overlay a single-frame PNG with `-shortest`**: it cut a 48s timeline to one frame. Loop the overlay and set an exact frame count. *Guard:* every ffmpeg call goes through one helper that refuses `-shortest`.
- **Never join with `-c copy` across mixed frame rates.** *Guard:* every shot is rendered at 30 fps (a 24 fps AI clip is converted), and the join re-encodes at 30 fps.
- **Use exact per-shot frame counts**, so the video is never shorter than the audio. *Guard:* each shot file is checked for exactly its planned frame count at 30/1 after rendering and again before the join, and so is the joined video.
- **When rebuilding a single shot, it still needs its captions.** *Guard:* captions are never burned into a shot; the mux burns them over the whole joined video every time, so `--stage shots --beat <id>` then `--stage mux` gives the rebuilt shot its captions.
- **Captions spaced evenly drift off the voice, and re-centred captions jump.** *Guard:* the narrate stage times every word with Whisper and stops when the words heard don't match the script; each caption word is its own event at a fixed position, and the sync check's S6 fails if any word's position changes.
- **libass and Pillow size fonts differently.** libass sizes a font by its full line height (about 1.16 em for DejaVu Sans), so a plain "38" in an ASS file renders smaller than the layout measured with Pillow, and the gaps between words come out wrong. *Guard:* the caption writer converts the 38px em size to the matching ASS size.
- **Verify the final duration against the shot list, not the builder's own total.** *Guard:* the build writes `shot_list.json` (each shot's frames, start, end, visual, material and label) and checks the reel's video frame count and audio length against it.
- **Scope edits: a label-only or fit-only fix changes only the affected shots; copy the audio unchanged and confirm its checksum.** *Guard:* the audio stage encodes the AAC once (`audio.m4a`); the mux copies it, checks the reel's audio stream has the same checksum, and prints whether it changed since the last mux. Run `--stage shots --beat <id>`, then `--stage mux`: "unchanged since the last mux" confirms the audio was untouched.
- **A visual that continues across a cut must not restart.** Each shot is its own file on its own clock, so the same clip jumped back to its first frame, a still zoomed out and re-pushed, a repeated headline card re-swept from no lit words, a timeline split over shots re-revealed its events, and a diagram dropped and redrew its ✗, all at the cut. *Guard:* `Build.plan` compares each shot with the one before it (same or next beat): same `clip` or `diagram.motion_clip` (the follower starts at the previous start plus its length, unless it sets its own `clip_start`), same still with the same layout (creep and `move` run once over the whole run), same card, a timeline or diagram whose list starts with the earlier items, same summary. The shot carries `_`-prefixed continuity fields, so the shot cache re-renders a follower when its predecessor changes. If the same image sits differently because a taller header moved the content band, it cannot carry on: the follower starts its own creep from 100% without the `move`, and the build warns. Keep the header's line count the same across such shots. A `"creep": "none"` shot inside a run holds the frame it was on instead of snapping back to 100%. A different visual is still a hard cut.

## Workflow

Copy this checklist into your working notes and tick items as you go:

```
Reel progress:
- [ ] 1. Confirm topic, length, tone
- [ ] 2. Facts sheet (claims, denials, sources, real-vs-false distinction)
- [ ] 3. Script
- [ ] 4. Shot list + assets (real receipts, AI illustrations)
- [ ] 5. Manifest + dry run
- [ ] 6. Build: hook first, then the whole reel (sync check PASS)
- [ ] 7. Verification gate (independent verifier) -> PASS
- [ ] 8. Deliver with notes
```

1. **Confirm before building.** Topic, length (default under 60s), and loaded argument-led tone or neutral tone. Do not reinterpret an ambiguous topic.
2. **Facts sheet.** Write `facts.md`: each claim with its status, its denial, the source and date for every figure and quote, and the careful distinction. For a developing story, add a timeline table (time with time zone, event, source) for the timeline section. Add a **tensions** table: every pair of facts that seem to pull against each other (a large number next to a small one, a confirmation next to a denial, "dangerous" next to "failed"), with the reason both hold and its source, or "no source gives a reason". The script bridges each pair that sits in adjacent or nearby beats (see "Bridge every contrast"). Cut anything that cannot be sourced. The verifier checks the reel against this file.
3. **Script.** About 130–140 words for 55s. Keep every line at the source's strength: "impact" stays "impact" (not "lost"), "likely" stays "likely" (not "did it" or "blame"), "may be" stays "may be", estimates keep "about". Credit wording to whoever said it: news outlets are not "analysts". Re-check the whole transcript against facts.md every time a line changes, including trims to fit the length. Keep each claim's status (from facts.md) in its wording, not in a tag, and put each claim's counterpart (denial, confirmed figure, statement) in the same beat. Then read the script aloud against "Write like a person talking" (Tone and sourcing) and "Story shape", and check it with C13 and C16 in `references/verification-checklist.md`: rewrite failing lines and beat changes, recheck accuracy (C12), and repeat until all pass.
4. **Shot list and assets.** Follow "Asset gathering" for every shot and fill the asset log in facts.md. How the work is split depends on the platform:
   - **Helper agents.** If the platform can start them, they can run the web searches, read page text (which lists a page's image URLs) and download images (for example with `curl`). That lets the search be shared out. Each helper looks at what it downloads and reports back its asset log rows.
   - **Screenshots need a live browser that can save an image file.** So does anything that needs clicking, scrolling or a set time zone, because a page fetch returns text and image URLs, not a rendered page. An agent with such a browser captures every screenshot: X posts, article pages and the end-card pointer. A downloaded article image is not a substitute for a page screenshot. Seeing the page is not enough: the build needs the file.
   - **Ask for the file, not the capture.** When the browser is a separate agent or worker, it may take the screenshot for its own checking and send back only a text description, because files flow into it by default, not back out. So every screenshot request names the deliverable: the image file itself, returned to your workspace (or saved to the platform's shared file storage) under a filename you give, cropped to what the shot must show. A description of the page is not a screenshot. When the reply comes back, check the file exists and look at it before logging it.
   - **Before relying on the browser**, test it once with one such file request on any page. If it returns no file, ask again more explicitly (as a file or artifact, or saved to shared storage under a name), and try any other route the platform offers (an element or full-page capture, or a page saved as PDF and rendered to PNG) before giving up.
   - **If no agent has a live browser**, ask the user for the screenshots. Otherwise use a headline card for the end-card pointer, record why under "Visual fallbacks" in facts.md (D10 checks it), and say so at delivery.

   Set a `keep` box for every image. Capture the end card's pointer as a screenshot of a referenced article page (outlet name, headline, byline; relative times cropped out at capture, capture date recorded; see "End card"). Look at every asset once before writing the manifest.
5. **Manifest and dry run.** Write the JSON manifest (see `examples/sample-manifest.json`) with `material` on every beat (entry in `scenes`). Run `python3 scripts/build_reel.py manifest.json --dry-run` to check timings and word count. It also prints the pace report (each shot's kind and how much of the frame a still covers, plus the time share of video, built and still shots). Fix every pace warning before building: swap a still for a clip or a stat, tighten a keep box, add a wipe at a section turn. Give the reason at delivery for any warning you keep. Then read only the headlines, in order, as a viewer with the sound off: each one should say who did what (see "Headlines").
6. **Build, hook first.** The hook decides whether anyone watches the rest, and it is the cheapest part to redo, so build it alone before the whole reel:
   - `python3 scripts/build_reel.py manifest.json --stage hook --workdir <dir>` builds the hook's beats (the leading beats whose `id` starts with `hook`, or the first beat) to `<dir>/hook/hook.mp4`, then reports its length (7s limit), word count and caption sync. Look at it and fix the hook until it passes.
   - Then `python3 scripts/build_reel.py manifest.json --out reel.mp4 --workdir <dir>` builds everything. It reuses the hook's narration and shots, because each beat's narration and each shot is cached and redone only when its manifest entry, timing or asset file changes.
   - To change one part later, run just that stage (`--stage narrate | shots | subs | audio | mux | sync`; `--beat <id>` limits `shots` to one beat). The stages are listed at the top of `scripts/build_reel.py`.
   - The build needs `faster-whisper` (`pip install faster-whisper`; or `openai-whisper`) for caption timing. `REEL_WHISPER_MODEL` picks the model (default `small.en`).
   - The build ends with `scripts/check_sync.py`, which measures the finished reel: it finds speech in the reel's own audio (filtering out the music bed) and compares it with the burned-in captions (S1–S4), re-runs Whisper on the reel to check each word's reveal time (S5, 0.3s tolerance), and checks that every caption word keeps one position (S6). A FAIL names the word and how early or late it is: nudge that word only (`caption_nudge`), then `--stage subs` and `--stage mux`. Words it lists as not matched are possible dropped or slurred words to check by ear.

   The script handles:
   - TTS narration, word-by-word captions timed by Whisper and anchored in place, the music bed and loudness;
   - real images placed by their keep box (full-bleed, zoomed or shown whole) below the caption band, full-bleed hook stills, and full-bleed AI images;
   - slow creep on every shot's base layer, with the disinformation tag, headlines and labels locked, and faint grain on graphics (a test build measured 16% still frames);
   - headline cards with the word-by-word highlight sweep;
   - stat shots (`stat`: a figure counting up or popping in on its word, over the blue or an AI motion clip), with a generated low hit as it lands (`"sfx": false` turns that off);
   - graphic wipes (`"wipe": "left"` or `"up"` on a section's first shot);
   - the pace report (`scripts/reel_pace.py`) at the dry run and after the build, and each shot's kind and coverage in `shot_list.json`;
   - the diagram with node reveal and the ✗ snapping on at the denial (`cross_after`);
   - the timeline (`timeline`: events with time, text and source, revealed one at a time);
   - real clips with `clip_mask` delogo boxes, plus AI clips;
   - the end card with pointer and disclosure line;
   - summary panels brought in within the first 40% of the shot, the build stopping if the finished card would show for less than its hold, and `scripts/check_card_hold.py` measuring that hold on the rendered reel;
   - multi-shot beats (`shots`): one narration line cut into several shots, so lines stay whole sentences while shots stay 1–3s;
   - narration silence trimmed and pauses capped, so no gap exceeds 0.3s;
   - diagram nodes timed to the words that name them (the same measured word times as the captions);
   - exact 30 fps frame counts.

   It rejects a manifest that breaks a hard rule: a missing `material`, a beat with no visual, an image it can't read or that is almost blank, a real shot without a source, a status tag (`label`), disinformation material opening the reel or on the end card, or a mask box at the frame edge. It also fails if the total exceeds the length limit; then trim narration, never the denial or distinction beats. It does not generate AI media (the map included) or the slide-ins and particle overlays from the motion table (make those with Muse or as clips, and pass them in), and it does not find a clip's caption or logo bands (measure them from a frame, then set `clip_mask`). Its closing self-check (duration, specs, loudness, contact sheets, caption sync) is a start, not the verification gate.
7. **Verification gate.** See the next section. Mandatory for every build, including small fixes.
8. **Deliver.** Give the file; if the loop-back took the total past the length limit, say so; ask the user for a listen-through, since no agent can hear whether TTS dropped or slurred a word; the verifier's report with measured duration, resolution, audio specs and loudness; a per-shot table (time, visual, material type, source/label); contact-sheet paths; and anything omitted or not fixed, and why.

## Verification gate (independent verifier agent)

The builder never certifies its own reel. After every build, hand verification to a **fresh verifier agent** (a separate subagent or new agent instance) that did not take part in the build.

**Give the verifier only:**
- the rendered reel path (and the reference reel path, if any);
- the manifest or shot list and `facts.md`;
- the assets folder (every image and clip the manifest uses);
- the build workdir (for the narration files B4 measures and the `subs.ass` caption file B9 measures);
- `references/verification-checklist.md`;
- a writable folder for its frames and report;
- from round 2 on: the item IDs and shot IDs in this round's scope (checklist section F), and nothing about what was fixed.

Do not give it your own assessment, the known issues, or what you expect it to find; a primed verifier tends to confirm what it is told.

**The verifier must:**
1. Work from the files it was given; it does not download assets or capture screenshots, and needs no live browser. It may use web search and page-text fetches to check for related images (D4). Run every measurement in the checklist itself on the rendered file (not the planned timeline), extract the contact sheets and per-shot strips, and look at them.
2. Mark each checklist item in its scope (every item in round 1) PASS or FAIL, with evidence: a measured value, a timestamp, or a frame path. "Looks fine" is not evidence.
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
- Any FAIL blocks delivery. The builder fixes the failures, rebuilds, and starts a **new** fresh verifier. Fix a D5 (too much text) FAIL with the text repair steps in "Asset gathering", not by swapping in a headline card. Do not reuse the previous one, and do not tell the new one what was fixed.
- Round 1 runs the whole checklist. Rounds 2 and 3 run only the items the fixes could have changed. Work out the scope with checklist section F: diff the manifest and facts.md against the copies saved for the last round, then look up each kind of change in its impact table. Every round still re-measures the whole rendered file and re-runs every item that has failed before. Any change to the build scripts or the global style, or a change touching more than half the beats, needs the full checklist. The verdict comes from the combined report: the new results plus every other item carried from its latest round.
- After 3 failed rounds, stop. Deliver the latest build to the user clearly marked "not passed", with the verifier's open FAIL items. Never present it as passed.
- No "PASS with note" for a rule breach. A note may record something the spec explicitly allows (a trade-off it names); anything that breaks a rule is a FAIL, and the verifier applies rules as written instead of reinterpreting them (PHP2Shell v1 passed one photo in four shots as "one visual run").
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
- `references/reel-format.md`: the reference reel: its sections, visual grammar, how it moves, and measured benchmarks.
- `references/msci-case-study.md`: the MSCI reel as a worked example: facts sheet, shot list, reusable build settings, and the defect behind each rule.
- `references/php2shell-case-study.md`: a reel that passed every check yet played as a slideshow: what went wrong shot by shot, and what each fix looks like. Read it before planning shots.
