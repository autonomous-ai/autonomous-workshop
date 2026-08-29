# Comet Heist: Twin-Pulse Vault Run

A portable, all-printed tabletop dexterity game for one or two players: pulse two gravity gates, flick a comet through both portals, and bank into pip-marked vaults across six shots.

[View the verified public product page](https://www.autonomous.ai/factory/product/comet-heist-twin-pulse-vault-run)

## Workflow

Quest: `Wish -> Invent -> Make -> Playtest -> Release`. Inventor selection is folded into Invent.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Leo) |
| Invent | 1 | accepted |
| Make | 2 | round 1 superseded; round 2 accepted |
| Playtest | 2 | round 1 revision-requested (printability-check); round 2 accepted |
| Release | 1 | round 2 accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

1. **Wish.** Input: the exact request for a portable all-printable dexterity game with captured comets, moving gravity gates, scoring vaults, bank shots, and one- or two-player rules. Output: the immutable [Wish binding](wish/wish.json).
2. **Invent.** Input: that Wish, the eligible Inventor roster, Taste, and blueprint. Output: Leo was selected and defined *Comet Heist: Twin-Pulse Vault Run*: a two-piece starfield, comet discs, two user-cocked oscillating gates, 2/4/6-point vaults, slingshot bank bonus, six mirrored pulse patterns, magazines, and storage locks. The complete concept is in [invented.json](invent/invented.json). Invent was its own native Goal.
3. **Make.** Input: the accepted concept and Leo's bound craft context. Output: a sealed 24-piece STEP-first game package with 10 STEP, 10 STL, 1 GLB, 6 legacy-layout Make evidence PNGs, rules, storage plan, support plan, exact [CAD source](make/source/), [models](make/models/), and [verification](make/verification/), all bound by [made.json](make/made.json).
4. **Playtest.** Input: the sealed Made product and its required evidence checks. Output: **pass** from agent-playtest, mechanical-check, and printability-check; see [playtested.json](playtest/playtested.json) and its evidence tree.
5. **Release.** Input: the sealed product plus passing Playtest evidence. Output: the hash-bound package and printable [customer manual](release/MANUAL.pdf), bound by [release.json](release/release.json).
6. **Publication.** Input: the exact Release package plus host-held Factory authorization. Output: the verified [Factory product](https://www.autonomous.ai/factory/product/comet-heist-twin-pulse-vault-run) and sanitized [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager tokens | unavailable — this run predates token telemetry |
| Wish to verified publication | unavailable — the archived snapshot has no trustworthy Wish-start timestamp |

No dollar cost is inferred.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- `invent/` — accepted Invent contract.
- `make/` — the exact sealed Release facts, exact CAD source, models, and verification.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `playtest/` — accepted Playtest contract and exact evidence.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
