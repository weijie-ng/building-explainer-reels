# Building explainer reels

An agent skill that builds short investigative explainer reels: vertical videos under a minute that make one argument about a contested or developing story, with every key claim checkable on screen.

Give it a topic or a few article links and the agent writes a facts sheet and a script, gathers real evidence for each shot, builds the reel with the scripts in this repo, and hands it to an independent verifier before delivering it. It can also review an existing reel against the same rules.

The skill was written for Muse, an agent platform that can also generate AI images and video. SKILL.md doesn't name any platform's tools, so any agent that can load a skill folder and run Python and ffmpeg can use it.

## What a reel looks like

- 720×1280 at 30 fps, h264 + AAC 48 kHz stereo, under 60 seconds by default.
- An AI voiceover with no presenter, and burned-in captions revealed word by word as they're spoken.
- A hook in the first 7 seconds that states the story and asks the question the reel answers. Then one chain of cause and effect, what's confirmed next to what isn't, and an end card that answers the hook's question and links to the full article.
- Real receipts as evidence: screenshots, an outlet's own photos, and real clips shown as the posts they are. AI images and video appear only as labelled illustration, never as evidence.
- False or unverified material always carries a DISINFORMATION POST tag.

`references/reel-format.md` describes the reference reel the format is modelled on. The two case studies in `references/` walk through finished reels and what went wrong in them.

## Using it

Ask your agent for a reel in plain words. For example:

- "Make an explainer reel on the Binance hack from these three articles."
- "Investigative reel, neutral tone, about the MSCI disinformation posts."
- "Review this reel against the reference and tell me what to fix."

The agent confirms the topic, length and tone first, and asks whether you want to stay in the loop. In the loop, you approve the plan before any asset is made, then every shot as it's built. Otherwise it runs through to delivery.

Every build goes through these steps (the full workflow is in SKILL.md):

1. **Facts sheet.** `facts.md` lists every claim with its status, source and denial.
2. **Script.** About 130–140 words, checked line by line against the facts sheet.
3. **Assets.** A visual for every shot: a real find first, AI when the real finds can't carry the line.
4. **Manifest and dry run.** The dry run checks timing, headlines, the story's spine and whether the reel plays as video or as a slideshow.
5. **Build.** The hook alone first, then the whole reel. The build ends with a caption sync check.
6. **Verification gate.** Fresh agents that took no part in the build work through `references/verification-checklist.md`. Any FAIL blocks delivery.
7. **Delivery.** The reel, a shot table, the verifier's report, and anything left open.

## Install

Put this folder where your agent platform loads skills from:

```
git clone https://github.com/weijie-ng/building-explainer-reels.git
```

The skill's name, `building-explainer-reels`, comes from SKILL.md, not the folder name.

The build scripts run on Unix (`python3 scripts/...`) and need:

| What | Notes |
|---|---|
| Python 3 with Pillow and numpy | `pip install pillow numpy faster-whisper` |
| ffmpeg and ffprobe, built with libass | on PATH; libass burns in the captions |
| faster-whisper (or openai-whisper) | times every caption word to the voice. `REEL_WHISPER_MODEL` picks the model (default `small.en`) |
| A TTS command | default `/opt/hatch/bin/tts`, Muse's. Override with `--tts` or `REEL_TTS` |
| DejaVu fonts | default `/usr/share/fonts/truetype/dejavu`. Override with `REEL_FONT_DIR` |
| A CJK font | only for Chinese, Japanese or Korean text on the end card. Set `REEL_CJK_FONT` (and `REEL_CJK_BOLD_FONT`) |

Before rendering anything, the build names whatever is missing.

**Outside Muse**, point `--tts` at a command that takes:

```
<tts> speak --text "..." --format mp3 --output out.mp3 [--voice NAME]
```

Or skip TTS and give every beat in the manifest a recorded `audio` file.

The build doesn't generate AI images or video. Make them with your platform's generator and pass the files in.

## Running the build by hand

The agent runs these, but you can too. The manifest's shape is in `examples/sample-manifest.json`.

```
python3 scripts/build_reel.py manifest.json --dry-run                          # check timings, headlines, pace
python3 scripts/build_reel.py manifest.json --stage hook --workdir work/       # build the hook alone
python3 scripts/build_reel.py manifest.json --out reel.mp4 --workdir work/     # build the whole reel
```

Each beat's narration and each shot is cached in the workdir, so a rerun redoes only what changed. To redo one part, run one stage: `--stage narrate | shots | subs | audio | mux | sync`, with `--beat <id>` to re-render one beat's shots. The stages are listed at the top of `scripts/build_reel.py`.

The other scripts:

| Script | What it does |
|---|---|
| `fetch_preview.py <url>` | fills the end card's link preview from an article's metadata and downloads its share image |
| `make_composite.py spec.json` | shows a real posted clip as the post, or tiles 2–4 accounts' clips into one shot |
| `check_sync.py reel.mp4 --subs work/subs.ass` | measures the captions against the voice in the finished reel |
| `check_card_hold.py reel.mp4 --shots work/shot_list.json` | measures how long the finished end card stays on screen |
| `check_ai_animation.py source.png clip.mp4` | measures how long an AI animation of a diagram stays faithful to it |

## What's in the repo

| Path | What it holds |
|---|---|
| `SKILL.md` | the skill: reporting structure, tone and sourcing, visual spec, workflow and verification gate |
| `references/` | detail the agent reads at the step that needs it: asset gathering, AI video, the end card, the story background, diagrams and clips, the verification checklist, the reference format and two case studies |
| `scripts/` | the build (`build_reel.py` and its `reel_*.py` modules) and the standalone checks above |
| `examples/sample-manifest.json` | a manifest showing each kind of shot: clips, images, a headline card, the diagram, a stat, the timeline and the end card |

## Limits

- The build can't hear. Whisper timing catches most dropped or changed words, but listen to the reel yourself before posting it.
- It doesn't find a clip's burned-in caption or logo bands. The agent measures them from a frame and sets `clip_mask`.
- If the platform can't start a separate verifier agent, the gate runs as a clean second pass, and the delivery notes say it was self-run.
