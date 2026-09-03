# Moonwake Garden

A pocket-sized, three-part ambient-light garden whose single exposed right-edge dial reveals Cassiopeia, Cygnus, and a Little Dipper reading within Ursa Minor at three indexed positions.

[View the verified public product page](https://www.autonomous.ai/factory/product/moonwake-garden)

## Workflow

Quest: `Wish -> Invent -> Make -> Playtest -> Release`. Inventor selection is folded into Invent.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | round 2 accepted (Luma Vale) |
| Invent | 2 | round 1 superseded; round 2 accepted |
| Make | 2 | round 1 invent-revision-requested; round 2 accepted |
| Playtest | 1 | round 2 accepted |
| Release | 1 | round 2 accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

1. **Wish.** Input: a pocket-sized three-part ambient-light garden whose edge dial reveals three indexed constellations. Output: the immutable [sanitized Wish binding](wish/wish.json); its exact wording is withheld.
2. **Invent.** Input: that Wish, the eligible Inventor roster, Taste, and blueprint. Output: Luma Vale was selected and defined *Moonwake Garden*: a chassis with spindle/detent/snap frame, hidden moonlight-sector dial, and fixed constellation garden face that reveals Cassiopeia, Cygnus, and Ursa Minor's Little Dipper at three 120-degree detents. The complete concept is in [invented.json](invent/invented.json). Invent was its own native Goal.
3. **Make.** Input: the accepted concept and Luma Vale's bound craft context. Output: the sealed three-part optical toy, with 4 STEP, 4 STL, 1 GLB, 31 legacy-layout Make evidence PNGs, exact [CAD source](make/source/), [models](make/models/), and [verification](make/verification/), all bound by [made.json](make/made.json).
4. **Playtest.** Input: the sealed Made product and its required evidence checks. Output: **pass** from agent-playtest, mechanical-check, and printability-check; see [playtested.json](playtest/playtested.json) and its evidence tree.
5. **Release.** Input: the sealed product plus passing Playtest evidence. Output: the hash-bound package and printable [customer manual](release/MANUAL.pdf), bound by [release.json](release/release.json).
6. **Publication.** Input: the exact Release package plus host-held Factory authorization. Output: the verified [Factory product](https://www.autonomous.ai/factory/product/moonwake-garden) and sanitized [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | unavailable — this run predates split token telemetry |
| Native Manager output tokens | unavailable — this run predates split token telemetry |
| Wish to verified publication | unavailable — the archived snapshot has no trustworthy Wish-start timestamp |

No dollar cost is inferred.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- `invent/` — accepted Invent contract/source and sealed superseded attempts.
- `make/` — the exact sealed Release facts, exact CAD source, models, product renders, verification, and sealed prior attempts.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.
- `playtest/` — accepted Playtest contract/evidence and sealed superseded attempts.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
