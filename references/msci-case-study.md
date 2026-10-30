# Case study: the MSCI disinformation reel

A worked example of the skill: the MSCI reel in its corrected form (48.5s, 720×1280, h264 + AAC 48 kHz stereo). Read it to see the rules applied to a real story, to reuse its settings, or to plan a similar reel. The rules themselves live in SKILL.md.

## Contents
- Files
- Facts sheet
- Shot list
- Build settings worth reusing
- Source limitations
- Defects and the rules that prevent them

## Files

| What | Path |
|---|---|
| Earlier builders with reusable steps | `~/workspace/v4_1_work/build_v4_1.py` (full build), `~/workspace/v4_1_work/make_map.py` (Natural Earth map), `~/workspace/v4_3_work/build_v4_3.py` and `fix_subs.py` (rebuilding single shots with their subtitles) |

`scripts/build_reel.py` now covers the map, the diagram, clip masking and fitted stills, so prefer it for new reels.

## Facts sheet

- **19 Oct (ALLEGATION).** Muhammad Lutfi alleged, without evidence, that Singapore, through GIC and Temasek, pressured index provider MSCI over Indonesia.
- **ALLEGED MEETING.** Posts claimed Dino Patti Djalal and Saiful Mujani met Singapore's ambassador at his residence.
- **DENIED.** Dino, Saiful and the Singapore embassy denied the meeting; the embassy said "no such visit took place" (The Straits Times, 25 Oct 2026). GIC and Temasek rejected the MSCI claim; GIC said "the allegations about GIC and our staff are untrue" (CNA, 21 Oct 2026).
- **Careful distinction.** Indonesia did reduce gas exports on 24 Oct, for domestic supply reasons, and the volume was under 2% of Singapore's daily gas demand per Singapore's Energy Market Authority (CNA, 26 Oct 2026). The cut is real; tying it to MSCI interference is false.
- **Scale.** CNA Verify (29 Oct 2026) found close to 400 posts and nearly 12 million views, but could not establish a single operator behind them.
- **Cut for length:** Rachel Khoo's name, and the individual Sektor Dominus and Heru Prasetya examples (replaced by CNA's aggregate figures).

## Shot list

Times are approximate.

| Time | Shot | Material | Tags / label |
|---|---|---|---|
| 0.0–1.0 | Crashing market chart, "MARKET CRASH" | ai | AI-GENERATED ILLUSTRATION |
| 1.0–1.7 | IDX photo, fitted, "MADE-UP MEETING" | real | BILYONARYO • IDX, OCT 2026 |
| 1.7–3.9 | Headline card: "Coordinated disinformation… made-up meeting" | recreated | CNA VERIFY |
| 3.9–11.8 | Lutfi clip, full frame; a solid header band behind the headline covers the clip's own logo and background lettering, and its caption band is masked ("19 OCTOBER" / "THE CLAIM") | real | ALLEGATION; REAL CLIP • @m.lutfi, 19 OCT |
| 11.8–15.5 | Chain diagram LUTFI → SINGAPORE / GIC / TEMASEK → MSCI → IDX, revealed node by node | diagram | ALLEGATION |
| 15.5–16.5 | Phone scrolling a blurred feed, "SECOND CLAIM" | ai | AI-GENERATED ILLUSTRATION |
| 16.5–20.9 | Meeting-claim composite, fitted, three headline beats (DINO AND SAIFUL / MET THE AMBASSADOR / AT HIS RESIDENCE) | real | ALLEGED MEETING; DISINFORMATION POST — flagged by CNA Verify; CNA • MEETING-CLAIM POSTS |
| 20.9–24.2 | Headline card: "Singapore embassy rejects meeting claim", key sentence "No such visit took place." | recreated | THE STRAITS TIMES |
| 24.2–26.8 | Chain diagram with the red ✗ on SINGAPORE / GIC / TEMASEK → MSCI | diagram | DENIED |
| 26.8–29.4 | GIC and Temasek logos, fitted | real | DENIED; CNA • 21 OCT 2026 |
| 29.4–31.6 | Headline card: "GIC Temasek deny MSCI claim", key sentence "The allegations about GIC are untrue." | recreated | CNA |
| 31.6–34.3 | Natural Earth map: a thick yellow arrow from Sumatra to Singapore that thins over the shot; the SINGAPORE label sits beside its dot, not on it | diagram | MAP: NATURAL EARTH • SCHEMATIC — NOT TO SCALE (shown once) |
| 34.3–39.3 | Gas-cut press photo, fitted, three headline beats: "DOMESTIC SUPPLY" / "NOT THE FALSEHOOD" / large "TYING IT TO MSCI = FALSEHOOD", with the "GAS CUT = REAL" tag on screen throughout, so the real part and the false part are shown together | real | GAS CUT = REAL; CNA • GAS-CUT ARTICLE, 26 OCT 2026 |
| 39.3–42.5 | "SADIS!!" / "RI ANCAM STOP EKSPOR GAS" posters, fitted, "~400 POSTS" | real | DISINFORMATION POST — flagged by CNA Verify; CNA VERIFY • 29 OCT 2026 |
| 42.5–44.2 | Scattered, separate clusters of red dots with no central hub (matching "no single operator"), "~12M VIEWS" | ai | AI-GENERATED ILLUSTRATION |
| 44.2–46.4 | Headline card: "400 posts, 12 million views", key sentence "Could not establish a single operator." | recreated | CNA VERIFY |
| 46.4–48.5 | End card on the background blue: CHECK BEFORE YOU SHARE, a screenshot of the CNA Verify article page (CNA name, headline, byline, date) as the pointer with "READ THE FULL STORY — CNA VERIFY", disclosure line | recreated card; real article screenshot | "AI voice · AI illustrations (Muse) · Sources: CNA, The Straits Times, CNA Verify" |

Five AI clips were generated with Muse: market chart, chain background, feed, network, and end-card background. None contains words or logos; the market clip shows chart numbers only. Every AI shot is under 3s, and real material carries the key claims.

## Build settings worth reusing

- **Lutfi clip masking:** the caption band is masked with delogo `x=80:y=920:w=560:h=120` (in 720×1280 output pixels). It sat higher than first estimated, so measure it from a rendered frame. The clip's logo and background lettering sit in the top of the frame, so they are covered by a solid header band behind the headline rather than a delogo box. A large delogo box there leaves a visible blurred band and fragments of lettering.
- **Meeting composite:** fitted at 649×520 with its top at y=420, so the two-line headline above it does not overlap.
- **Map:** Natural Earth land data framing the Strait of Malacca, Sumatra, the Malay Peninsula, Singapore and the Riau Islands. Markers SINGAPORE and INDONESIA, each labelled beside its dot. A generic arrow, not a pipeline route. One schematic label.
- **Audio:** compression (threshold −28 dB, ratio 12, makeup 12 dB), then loudnorm I=−14, TP=−1.5; AAC 192k 48 kHz stereo. Measured −14.9 LUFS.
- **Exact frame counts:** 1456 frames (48.53s of video) so the 48.50s audio fits without clipping.

## Source limitations

- The meeting-claim composite's own text is truncated at its edges in the source (embassy sign, Indonesian headline band). Fitting shows everything the source contains; it cannot restore what the source cut. Say so in delivery notes.
- Inside the reel, the receipts are article images and thumbnails, and headline wording appears on headline cards. The one full article screenshot is the end card's pointer: the CNA Verify article page, cropped to the CNA name, headline, byline and date.

## Defects and the rules that prevent them

Each row is a defect that reached a render of this reel, the rule that now prevents it, and how to catch it.

| Defect | Rule (SKILL.md) | How to catch it |
|---|---|---|
| Static slideshow: 44.6s of 54s frozen, 5–11s scenes | Shots 1–3s, never over 4s | Cut times, B5 |
| A slow zoom on the whole frame made text swim | Subtitles, tags and labels never move; no zoom or pan on the composited frame | 8 fps per-shot strips, B8 |
| After the zoom was removed, the reel went the other way: 65% of frames fully still | Stillness cap of 50%; slow creep on every base layer, plus the allowed moves | Still %, B8 |
| Landscape screenshots cover-cropped ("SADIS!!" read "IS!!"; Temasek read "MASEI") | Keep box: zoom only as far as the relevant part stays whole; never crop through it | Full-size frames, D2 |
| Punch-ins re-cropped a dense composite and cut its text | No punch-in on stills | D2 |
| Fake gas poster shown under the true "domestic supply" line | Disinformation never sits under a true line | C3 |
| Fake posters with no disinformation tag, on the hook and end card | DISINFORMATION POST tag every time; never opens the reel or appears on the end card | C3 |
| "LUTIFI" in the diagram | Names match the facts sheet | C6 |
| Blob map with the wrong geography, shown twice | Natural Earth map, shown once | D8 |
| Tags on plain blue with no image | Every shot has a representative image | D4 |
| Headlines in the top 120px, under the Instagram UI | Safe area | D1 |
| Paragraph text repeating the subtitle | At most a 2–4 word headline | D5 |
| Subtitles as 3-line blocks, opening mid-sentence or ending on "the" | 2–5 word phrase-boundary chunks | D6 |
| The clip's own captions under ours; a black band below the clip | Mask with measured delogo boxes; real clips full frame | C8 |
| −27 LUFS with dead air; later 96 kHz mono | −14 LUFS, music bed, 48 kHz stereo | B3, B4, B2 |
| Bold "RECREATED HEADLINE CARD" banners, "(MUTED, CAPTIONS MASKED)" labels | Production notes left off the screen | D9 |
| "TYING IT TO MSCI = FALSEHOOD" was a small tag on a very dark AI pipeline shot | The real-vs-false distinction is shown on screen together, on real material | C2 |
| An AI network with a dense central hub sat under "no single operator" | No AI visual contradicts the narration | C7 |
| A large delogo box left a blurred band and a "SEK" fragment on the real clip | Mask a clip's captions and logos so nothing collides with our text; check the rendered frame | C8 |
| A map label covered its own dot, and the schematic label appeared twice | Map labels drawn by the build; shown once | D8 |
| A frame from the previous layout flashed at a cut (a scene assumed to end at 5.0s ran to 5.3s) | Verify cuts on the rendered file | B7 |
| A 48s timeline rendered as a 1s file (single-frame overlay with `-shortest`; `-c copy` across mixed frame rates) | Looped overlays, 30 fps normalisation, duration checked against the shot list | B1 |
| Rebuilt shots lost their subtitles; frame rounding clipped the audio | Burn a rebuilt shot's subtitles onto it; exact frame counts | B1, D6 |
