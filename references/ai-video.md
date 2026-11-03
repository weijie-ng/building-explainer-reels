# Making AI video with Muse

How to prompt Muse and bring its clips into the build. The limits on AI material (what it may never show, labels, lengths) stay in SKILL.md ("AI material"); read them first.

**Making AI video move with purpose.** Generate the still first, look at it, then animate it with Muse as the start frame. Write the prompt as: start frame, one camera move, one action that acts out the line, and constraints. Ask for at least 1s more than the shot needs (5s for a shot up to 4s) so a clean take can be trimmed with `clip_start`/`clip_end`. Templates:
- Access or breach: "A heavy vault door in a dark server corridor, blue light. Slow dolly forward as the door unlatches and swings open, light spilling out. One motion only. No people, text or logos. Keep the subject centred, no morphing, no scene change. 9:16."
- Chain or spread: "Five identical glass cubes in a row on a dark floor. The first glows red, then a thin beam of light travels to the next and it turns red, one after another. Camera fixed. No text. No morphing. 9:16."
- Defence holds: "Macro shot of a brass pin-tumbler lock. A key slides in and fails to turn, then a second key fails. Camera pushes in slowly. No text. 9:16."
- Money or scale: "Stacks of coins on a flat blue surface. A conveyor carries them left to right into a frosted box where they vanish. Camera locked. No text or currency symbols. 9:16."
- Process paused: "Paper cards on a conveyor belt halt at a barrier; one card is lifted and stamped. One smooth motion. No text. 9:16."

Look at the result: the action must be the one asked for, finish inside the trimmed span, and invent nothing the line doesn't say.

**Bringing in an AI video from Muse.** Muse saves the generated video as an mp4; put it in the assets folder and reference it like any clip: `"clip": "ai_frozen_funds.mp4", "material": "ai"`. Ask Muse for:
- **9:16, 720×1280**, so nothing is cropped. Any other shape is cropped to fill the frame, around the clip's `keep` box (fractions of the frame, as for images), or the centre without one; the build warns when an AI clip isn't 9:16.
- **At least as long as its shot** (up to 6s). A shorter clip would hold its last frame, a freeze, and the build warns; use `clip_start` to pick the best part of a longer one.
- **No text, logos or watermark** in the frame, except post text on a simulated feed (SKILL.md, "AI material"). If one appears anyway, cover it with `clip_mask` or regenerate.
- **For a simulated feed or wall of posts**, still ask for 9:16, with the posts large enough to fill the frame. A 16:9 grid cropped to 9:16 keeps only about two columns and loses the sense of many accounts.

The build handles the rest: any frame rate becomes 30 fps with an exact frame count, the clip's own audio is dropped, and the "AI-GENERATED ILLUSTRATION" label is added. Look at the clip before it goes in the manifest, as with any asset.
