# Story background

Details for SKILL.md "Background": the presets, how to pick one, and the custom shape list.

## What it is

Plain blue behind a headline card, a stat or the end card makes the shot read as a slide. So every reel sets one story background in the manifest:

```json
"background": {"preset": "posts"}
```

The build draws it with code; it is not AI. It is made of faint flat shapes in two fixed tints of the reel's blue: about 10% white for bodies (cards, pages, pipes, grid) and 22% for details (bars, avatars, links, flow, the chart line). The tints are set in `scripts/reel_background.py`, so neither a preset nor a custom shape can come out loud enough to compete with the headline. Bars stand in for text, so nothing in it can be read.

It plays behind every shot that would otherwise show plain blue:
- headline cards without an image;
- stat shots without a motion clip;
- the timeline;
- the end card, with or without summary panels;
- the space around an inset while it grows.

Diagrams keep their own AI motion clip, which is planned around where the nodes sit. Photos and clips cover the frame. The wipe stays a solid panel.

It moves on reel time, so it carries on across cuts instead of restarting, and keeps moving through a shot that holds. Headlines, captions and labels never move with it.

## Pick the preset by what the story is about

Choose by the story's subject, not by what happened in it. The background sets the scene; the headline and narration carry the claim.

| Preset | What it shows | Fits |
|--------|---------------|------|
| `posts` | Blank post cards (avatar, name bar, text bars) in staggered rows, drifting up in step and lighting together every few seconds | Social media, disinformation, coordinated campaigns, influencers, platform policy |
| `network` | Points on a loose grid joined to their neighbours, with small pulses travelling along the links | Cyberattacks, data breaches, telecoms, AI and tech companies |
| `pipeline` | Pipe runs with flanges and a slow flow inside, and a tanker outline crossing on a waterline | Oil and gas, energy supply, shipping, commodities, sanctions on exports |
| `ticker` | A chart line scrolling slowly over a faint grid, with a dot riding the line like a live price | Stock markets, company results, currencies, inflation, the economy |
| `papers` | Document outlines at slight angles drifting up, and a stamp ring pressing onto one of them every few seconds | Policy, laws and courts, regulation, official reports, investigations by a regulator |

When a story spans two subjects, pick the one the reel spends the most time on. A disinformation campaign about a stock index is a `posts` reel if it's about the campaign and a `ticker` reel if it's about the market move.

Never force a preset that points at the wrong subject (a pipeline behind a cyber story, a stock chart behind an election). Use `custom` instead.

`"seed": 3` (any whole number) changes the layout of `network`, `pipeline`, `ticker` and `papers` while keeping the style.

## Custom shapes

For a story none of the presets fits, list a few simple shapes that stand for its subject:

```json
"background": {"preset": "custom", "shapes": [
  {"shape": "doc", "x": 0.25, "y": 0.35, "w": 200, "h": 260, "angle": -6, "drift": [0, -10]},
  {"shape": "doc", "x": 0.72, "y": 0.75, "angle": 5, "drift": [0, -12]},
  {"shape": "ring", "x": 0.7, "y": 0.42, "r": 60},
  {"shape": "bar", "x": 0.5, "y": 0.9, "w": 420, "h": 14, "drift": [12, 0]}
]}
```

- **Shapes:**
  - `card`: a blank post card;
  - `doc`: a page with a folded corner and text bars;
  - `circle`: a filled circle;
  - `ring`: a circle outline;
  - `bar`: a rounded bar;
  - `line`: a straight line, from `x`, `y` to `to: [x, y]`.
- **Fields:**
  - `x`, `y` place the shape's centre as fractions of the frame;
  - `w`, `h`, `r` and `width` are sizes in pixels;
  - `angle` turns it, in degrees;
  - `tone` is `"shape"` (bodies) or `"detail"` (bars and outlines). There is no other colour.
- **Motion:** `drift: [dx, dy]` moves a shape in pixels per second, up to 40px/s, and wraps it around the frame. Give a few shapes the same slow drift rather than many shapes different ones.
- **Limits:** at most 40 shapes.

Examples of what custom shapes can stand for:
- **An election:** `doc` shapes as ballot papers, with a `ring` or two as stamped marks.
- **A health story:** `bar` shapes with round ends as capsules, and `circle` shapes as tablets.
- **A transport story:** long `line` shapes as tracks or roads, with `bar` shapes drifting along them.
- **A weather or climate story:** `ring` shapes as rings of rain on water, and `line` shapes as wind streaks.

## What it never shows

The background is scenery, so it makes no claim. That means:
- no readable words, numbers or logos;
- no faces, and no real platform's interface;
- no real place, map or route;
- nothing that could read as an extra box or link in the diagram;
- no suggested scale the sources don't give. A few faint cards in a feed is fine; a screen filling with thousands of posts, behind a line about a few accounts, is not.

It is drawn, not generated, so it needs no AI label and doesn't count as an AI shot.

## Check it

- The dry run warns when shots would sit on plain blue and the manifest has no `background`, listing them.
- It stops on an unknown preset or a malformed custom shape.
- Look at one frame of each graphic shot: every headline, caption, card line, stat label and timeline event must read clearly over the shapes (verifier D11).
