# Case study: PHP2Shell v1, a reel that passed every check and played as a slideshow

PHP2Shell v1 (Nov 2026, 48.5s) is about a critical PHP flaw, the attacks on Palo Alto firewalls that followed, and a third, unpatched flaw. The independent verifier passed it in round 3 with no FAILs. The user's verdict was that it played as a slideshow and wasted chances to be exciting. Read this before planning shots. Each lesson below became a rule in SKILL.md and a check in the build (pace report) or the checklist.

## What was on screen

| Time | Visual | What went wrong |
|---|---|---|
| 0–2.5s | Wide server-rack photo (hook), `"full_bleed": false`, keep box = whole image | The hook was a 16:9 strip across the middle of the frame, with blurred blue above and below. The user had asked for the first image to fill the screen. |
| 2.5–5s | AI flat icon: a server with a lever | Clip-art, still; it says nothing the caption doesn't. |
| 5–7.6s | AI flat icon: a shield over servers ("RATED 9.2") | A figure shown as an icon instead of the figure. |
| 7.6–10.1s | The same rack photo again | A picture coming back reads as a loop. |
| 10.1–12.5s | The same shield icon again | The same repeat. |
| 12.5–15.3s | Palo Alto hardware photo | Small on blurred fill. |
| 15.3–18s | Dream's attack-chain figure, shown whole | A thin white strip; the node labels can't be read on a phone. |
| 18–26s | The Palo Alto photo again, 3 shots (super changes) | 8s of one picture; together with 12.5s it is 4 shots, about a quarter of the reel. |
| 26–31s | Tenable article image | Small, dark, centred. |
| 31–33.9s | AI flat icon: five servers, 2 shots | Clip-art again. |
| 33.9–40.4s | PHP and CISA headline cards, with an AI server icon between them | The weakest visual type, back to back with an icon. |
| 40.4–48.5s | Summary card, then end card | Fine. |

Measured: still images held about 82% of the non-end time; video clips 0; built graphics 2 cards. Only 18% of frames were fully still, so the stillness cap (B8) passed: a 2% creep counts as motion.

## Why the gates missed it

- **Hook.** The skill offered `"full_bleed": false` as a way out when a hook still's keep box didn't fit 9:16, and C14 only asked "does it move?". Now the build rejects `full_bleed: false` on the hook, and C14 fails any hook frame showing fill after the inset.
- **No video requirement.** Footage was "first choice" for the hook, but a still with a move counted the same, and nothing asked for video anywhere else. Now the pace report and D12 want at least one video shot per ~15s and stills on at most half the reel's time.
- **Repetition rationalised.** The verifier counted the Palo Alto photo's super-change pair as "one visual run" and passed it. Now every shot counts, a returning picture fails, and "PASS with note" is not allowed for a breach.
- **Small images.** Nothing measured how much of the frame a picture covered. Now `coverage` is in the shot list and below 40% is flagged.
- **Headlines.** The 2–4 word target produced telegraphese ("PHP POWERS WEB", "25 ROOTED", "MOST DID NOT FALL") and names with no identity ("DREAM"). Headlines may now take two lines, and C17 reads them alone.
- **Story.** Each beat was one more fact; the patch came before the damage; "rooted" and "9.2" went unexplained; the ending repeated the hook's question without answering it. Now there's "Story shape" in SKILL.md, C16, and the ask-then-answer loop-back.

## What it could have been (same facts, same hedges)

| Beat | Instead |
|---|---|
| Hook | A Muse video that acts out the line: a vault door in a server corridor unlatching with no key ("without logging in"), filling the frame. Or a 9:16 crop of the rack photo with a push. |
| 9.2 | Headline "FLAW SEVERITY: 9.2 OUT OF 10" and a `stat`: "9.2" counting up on the word, label "severity score, 10 = most severe", source PHP advisory. "9.2 out of 10" without "severity" reads like a good score. |
| Fixes 21 Oct | Moved after the firewall beat ("PHP had shipped fixes on 21 October"), over a tight crop of the advisory's version line. |
| Firewalls (the concrete example) | The longest beat: a tight crop of the hardware photo (the ports), then the chain rebuilt as the reel's own diagram (PHP2Shell → management interface → root → Active Directory), labelled "CHAIN AS DESCRIBED BY DREAM", nodes on the words, with a wipe into the section. |
| 25 firewalls | A `stat` "25" with label "Palo Alto firewalls, per security firm Dream". |
| Tenable 0 of 5 | A `stat` "0 of 5" popping in, then a Muse video of a key failing in a lock ("tuned to each target"). |
| Third flaw | A wipe at the turn, then a crop of PHP's advisory sentence. |
| End | "So what got hacked? The clearest break-ins hit firewalls, and the third flaw is still open." (At the sources' strength: Tenable's five-site test doesn't show that websites in general were spared.) Then the end card. |

## v2: a contrast with no bridge

v2 fixed the slideshow problems, but the user's review flagged a new one. The reel went straight from "25 Palo Alto firewalls taken over" to "Tenable tested 5 vulnerable sites online, and none was hacked". With nothing explaining the switch, the viewer can't tell whether the flaw is dangerous or broken, and the second fact seems to cancel the first. Both facts were sourced and in the right order. What was missing was the reason both were true, said at the turn. Now there's "Bridge every contrast" in SKILL.md's Story shape, a tensions table in facts.md, and a C16 and C17 FAIL for an unbridged contrast.

The review offered a reason: appliances run identical firmware, so memory targets are predictable, while web servers' heap layouts vary. That goes in the reel only if Dream's or Tenable's write-up says so. Otherwise the bridge says only what the sources do say about why the attack failed, or that no source gives a reason.

