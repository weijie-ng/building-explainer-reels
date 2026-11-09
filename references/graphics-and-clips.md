# Diagrams, posts and real-clip composites

Details for three kinds of shot. The rules for what each is for stay in SKILL.md ("Diagram", "Real clips").

## Diagram

**A source's own chain figure is a receipt, not the reel's diagram.** If a source draws the chain (a research firm's attack-path figure), show it as a receipt only when its labels can be read at phone size, cropped to the part the line is about. A wide figure shown whole becomes a thin strip of unreadable boxes. Then rebuild the chain as the reel's own diagram, with nodes revealed on the words and the source in its label ("CHAIN AS DESCRIBED BY DREAM, 26 OCT 2026"), keeping the source's node names and claim status.

**AI motion behind the diagram.** Give every diagram an AI motion clip behind it, because a still blue plate reads as a slide. The only exception is when the nodes fill the frame too tightly for the motion to show. A diagram can move like an AI video without handing the AI anything that must be exact. The words, boxes, arrows and ✗ have to match facts.md and land on the narrated word; AI video can't spell reliably and can't be timed to a word, and an AI-animated diagram has clipped its own labels at the frame edge before. So split the work:
1. Run `python3 scripts/build_reel.py manifest.json --stage diagram-brief --workdir <dir>`. For each diagram shot it writes a text-free start frame (the background blue, a faint guide line where the arrows run, soft glows where the nodes will sit), the length the clip needs (measured from the narration), and a ready Muse prompt, in `<dir>/diagram_brief/`.
2. Generate the clip with Muse from that start frame and prompt (image animation; a text-only prompt also works). Look at it: no words, numbers, shapes or objects the plate doesn't have, nothing pushed off the frame.
3. Set `"diagram": {..., "motion_clip": "chain_motion.mp4"}` (and `clip_start` to reuse one long clip across several shots of the same diagram).

The build plays the clip as the base layer, tinted toward the background blue, and draws the nodes, arrows, labels and ✗ on top at the narrated words, exactly as without it. The label reads "… · AI MOTION". Never ask the AI to draw the diagram itself or its words; if a beat needs a move the plate can't give (a node sliding in, tokens along an arrow), build it in the script.

**AI animation of a finished diagram (image + prompt).** Muse can animate a script-made diagram with its text, but it redraws every frame, so it drifts. In a test on a causation diagram ("keep all text exactly as shown"), it began a slow zoom within 0.3s, cut "FALSE CAUSE" to "ALSE CAUSE" by 2s, invented a dark screen frame, and faded the timeline note it was told to keep. Use such a clip only for the span where it still matches its source:
1. Run `python3 scripts/check_ai_animation.py diagram.png clip.mp4 --strip strip.png`. It compares every frame with the source where the source has text and lines, reports how long the clip stays faithful (`usable_end`) and when new marks appear (a cross being drawn), and PASSes only if at least 1s is usable.
2. On a PASS, use the clip as the shot's `clip` with `"material": "diagram"`, `"clip_end": <usable_end>`, and `clip_start` chosen so the event you need (the cross) lands on the narrated word; the shot holds the last faithful frame after `clip_end`. Look at the strip: an event must be what the narration says, at the place it says.
3. On a FAIL, don't use it. Animate those moves in the build instead (the reveal and the ✗ on the narrated word), with an AI motion clip behind the diagram for movement.

## Someone's post

A clip an account posted (a reel, TikTok, Short or other video the narration attributes to them) is the receipt of what they posted, so it is shown as their post: whole, in its own shape, with their account above it. Filling the frame with it goes wrong three ways:
- the post's own graphics (a logo, a title box, an on-screen button, a cut-out) sit under the reel's source label, headline and caption;
- blurring that text leaves smeared bands;
- the viewer can't tell it from the reel's own footage.

Examples: a minister's TikTok making the claim the reel checks, a viral Short of a deepfake ad, an influencer's reel repeating a rumour, a fact-checker's video quoted as a reaction.

Build it with `python3 scripts/make_composite.py spec.json --out post.mp4 --preview` and one tile in `tiles` (`clip`, `account`, `post_url`, `posted`; optional `avatar`, `start`, `mask`). The source label defaults to "<account> • <posted>". Pass the output as `"clip"` with `"material": "real"`.
- **Where it sits.** The account strip starts below the caption band (y=408), with the clip right under it (y=448), as wide as the headline's column allows (x 40–680). A tall clip runs past y=1030 to the frame's bottom edge: a 9:16 reel is shown whole at 468×832, about 42% of the frame; kept inside the content band it would be 327×582, about 21%. A wider post (square, 16:9) is centred in the content band when it fits there.
- **What's under the platform's UI.** For a tall post the script prints how much of the clip sits below y=1030 (the bottom ~30% of a 9:16 reel), and `--preview` shades it. The platform's caption, name and buttons cover that part, so nothing the line depends on may be there. If the key moment or the claim's own text sits low in the clip, pick another slice, or show a screenshot of the post instead.
- **Its text.** Its logos, title boxes and on-screen graphics stay: inside the post they are part of the receipt and collide with nothing. Mask its running captions (`mask`, fractions of the clip) where they would be read as part of the reel, including below y=1030, where they would stack under the platform's own caption.
- **Behind it** is the reel's blue over a blurred copy of the clip, as behind any image shown whole.
- **Not in the hook.** The hook fills the frame, so the build rejects a post there. Open on footage or an AI video, and show the post after it.
- **Logged** like a composite tile: the account as posted, the post URL and date go in the asset log (the script prints the row).

## Side-by-side composite of real clips

**Side-by-side composite of real clips.** To show the same content posted by several accounts, a script may tile their real clips (2×2 or side by side) into one 9:16 clip. Pass it as `"clip"` with `"material": "real"`. The rules:
- **Unedited tiles.** Each tile is that account's actual clip, changed only by crop, scale, trim and sync.
- **Names copied exactly.** The account name and avatar drawn above each tile are taken word for word from the post.
- **Logged.** Each account, post URL and date goes in the asset log.
- **A label that describes the set.** Use one source label saying what the tiles are, plus the trace date (e.g. "TRACED EXAMPLES • 28 OCT 2026"). If the tiles aren't part of a figure in the reel, say so ("NOT CNA'S 68"). Never imply the tiles are the whole set or a sourced count.
- **Room for the reel's text.** Leave the headline band and the caption band free of account names and other tile text the viewer must read.
- **Burned-in text.** Mask the source clips' running captions (`clip_mask`) wherever they would collide with the reel's headline or captions. Static text (a logo, a title box) may stay unless it makes the reel's text hard to read (SKILL.md, "Real clips").
- **Muted**, like any real clip.

Build it with `python3 scripts/make_composite.py spec.json --out composite.mp4 --preview`:
- **What the script does:**
  - places 2–4 tiles below the caption band and inside the headline's column (x 40–680), 16px apart, with the reel's blue over a blurred fill behind them. Every clip keeps its own shape, shown whole; a clip is cropped around its `focus` only when its shape differs from the other tiles'. Side by side (`row`), the tiles stay inside the content band, narrowing when the band caps their height. A 2×2 `grid` of tall clips runs past y=1030 to the frame's bottom edge like a post (four 9:16 clips at 218×388 each, against 148×263 kept inside the band). Every account name stays above y=1030, and the script prints how much of the bottom row sits under the platform's UI (about 64% of four 9:16 clips), so nothing the line depends on may be in that part of those clips;
  - draws each account's avatar and name exactly as given;
  - masks the source clips' captions per tile;
  - can bring the tiles in one after another (`stagger`).
- **What it refuses:** a tile without its account, post URL and date, or a composite without the set's label.
- **What it prints:** the manifest entry and the asset-log rows.
- **The preview:** shades the header, caption and platform-UI bands, so you can check that nothing readable sits under them.

The spec format is at the top of the script.
