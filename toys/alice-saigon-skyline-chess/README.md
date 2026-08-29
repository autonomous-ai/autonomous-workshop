# Saigon Skyline Chess

![Saigon Skyline Chess](make/verification/renders/iso.png)

A geometry-readable orthodox chess set that turns six Ho Chi Minh City landmarks into a complete 32-piece skyline, with round River and square Grid plinths distinguishing the two sides without relying on color.

[View the verified public product page](https://www.autonomous.ai/factory/product/saigon-skyline-chess)

| Frozen on this run | Value |
|---|---|
| Manager | Codex (`--manager codex`) |
| Effort | Spark (`--effort spark`) |
| Inventor | [Alice](../../inventors/alice/) |
| Factory | https://www.autonomous.ai/factory/product/saigon-skyline-chess |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Alice) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

1. **Wish.** Input: a geometry-readable orthodox chess set built from six Ho Chi Minh City landmarks. Output: the immutable [sanitized Wish binding](wish/wish.json); its exact wording is withheld.
2. **Invent.** Input: that Wish, the eligible Inventor roster, Taste, and blueprint. Output: Alice was selected and defined *Saigon Skyline Chess*: a relief board plus Landmark 81 king, Bitexco queen, Notre-Dame bishop, Independence Palace knight, Bến Thành Market rook, and Central Post Office pawn. Spark folded this compact concept into Make; see [the concept](make/invented.json).
3. **Make.** Input: the accepted concept and Alice's bound craft context. Output: the sealed one-filament landmark chess set, with 14 STEP, 15 STL, 1 GLB, 20 legacy-layout Make evidence PNGs, exact [CAD source](make/source/), [models](make/models/), and [verification](make/verification/), all bound by [made.json](make/made.json).
4. **Playtest.** Input: the sealed Made product. Output: not run on the Spark route, recorded explicitly in [PLAYTEST-NOT-RUN.json](release/PLAYTEST-NOT-RUN.json).
5. **Release.** Input: the sealed product plus the truthful Playtest omission. Output: the hash-bound package and printable [customer manual](release/MANUAL.pdf), bound by [release.json](release/release.json).
6. **Publication.** Input: the exact Release package plus host-held Factory authorization. Output: the verified [Factory product](https://www.autonomous.ai/factory/product/saigon-skyline-chess) and sanitized [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | unavailable — this run predates split token telemetry |
| Native Manager output tokens | unavailable — this run predates split token telemetry |
| Wish to verified publication | unavailable — the archived snapshot has no trustworthy Wish-start timestamp |

No dollar cost is inferred.

## Reproduce

From a checkout of this repository, verify the host and run the same Manager
and effort route. The exact original Wish remains private, so this command uses
the public product summary. A later run follows the same route but does not
replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --manager codex --effort spark --github \
  'A geometry-readable orthodox chess set that turns six Ho Chi Minh City landmarks into a complete 32-piece skyline, with round River and square Grid plinths distinguishing the two sides without relying on color.'
```

If a native turn stops before Release, continue the same Wish with
`uv run workshop resume <wish-id>`.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, product renders, verification, and sealed prior attempts.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
