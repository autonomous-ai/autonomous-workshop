# Lunar Relay

A palm-sized, three-part printable desk mechanism whose exposed rocker makes one cratered moon rise when the other is pressed.

[View the verified public product page](https://www.autonomous.ai/factory/product/lunar-relay)

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Bob) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

1. **Wish.** Input: “A palm-sized support-free kinetic desk toy: press one moon and make a second moon rise, with no purchased hardware.” Output: the immutable, exact [Wish binding](wish/wish.json).
2. **Invent.** Input: that Wish, the eligible Inventor roster, Taste, and blueprint. Output: Bob was selected and defined *Lunar Relay*: a three-part 92 × 54 × 25 mm machine whose equal-arm rocker raises one cratered moon 8.35 mm when the other is pressed, captured by a printed quarter-turn keyway axle. Spark folded this compact concept into Make; see [the concept](make/invented.json).
3. **Make.** Input: the accepted concept and Bob's bound craft context. Output: the sealed lunar-well mechanism, with 4 STEP, 5 STL, 1 GLB, 1 legacy-layout Make evidence PNG, exact [CAD source](make/source/), [models](make/models/), and [verification](make/verification/), all bound by [made.json](make/made.json).
4. **Playtest.** Input: the sealed Made product. Output: not run on the Spark route, recorded explicitly in [PLAYTEST-NOT-RUN.json](release/PLAYTEST-NOT-RUN.json).
5. **Release.** Input: the sealed product plus the truthful Playtest omission. Output: the hash-bound package and printable [customer manual](release/MANUAL.pdf), bound by [release.json](release/release.json).
6. **Publication.** Input: the exact Release package plus host-held Factory authorization. Output: the verified [Factory product](https://www.autonomous.ai/factory/product/lunar-relay) and sanitized [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager tokens | unavailable — this run predates token telemetry |
| Wish to verified publication | unavailable — the archived snapshot has no trustworthy Wish-start timestamp |

No dollar cost is inferred.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, and verification.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
