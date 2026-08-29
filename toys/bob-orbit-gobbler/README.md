# Orbit Gobbler

An all-printable hand-cranked desktop automaton in which a geared carrier guides a captive moon through a visible orbit and back through a fixed C-shaped mouth every two crank turns.

[View the verified public product page](https://www.autonomous.ai/factory/product/orbit-gobbler)

## Workflow

Forge: `Wish -> Invent -> Make -> Release`. Inventor selection is folded into Invent.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Bob) |
| Invent | 1 | accepted |
| Make | 1 | accepted |
| Playtest | not run | Forge omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

1. **Wish.** Input: the exact request for an all-printable hand-cranked creature that swallows a moon, carries it through a visible orbit, and pops it back out. Output: the immutable [Wish binding](wish/wish.json).
2. **Invent.** Input: that Wish, the eligible Inventor roster, Taste, and blueprint. Output: Bob was selected and defined *Orbit Gobbler: C-Mouth Lunar Cam*: two crank turns drive a geared carrier once while a captive moon slider follows a fixed cam through swallow, exposed orbit, pop, and pause. Its 22-part concept is preserved in [invented.json](invent/invented.json). Invent was its own native Goal.
3. **Make.** Input: the accepted concept and Bob's bound craft context. Output: the sealed all-printable automaton, with 20 STEP, 21 STL, 1 GLB, 3 standardized [product renders](make/verification/renders/), exact [CAD source](make/source/), [models](make/models/), and [verification](make/verification/), all bound by [made.json](make/made.json).
4. **Playtest.** Input: the sealed Made product. Output: not run on the Forge route, recorded explicitly in [PLAYTEST-NOT-RUN.json](release/PLAYTEST-NOT-RUN.json).
5. **Release.** Input: the sealed product plus the truthful Playtest omission. Output: the hash-bound package and printable [customer manual](release/MANUAL.pdf), bound by [release.json](release/release.json).
6. **Publication.** Input: the exact Release package plus host-held Factory authorization. Output: the verified [Factory product](https://www.autonomous.ai/factory/product/orbit-gobbler) and sanitized [publication readback](publication/PUBLICATION.json).

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
- `invent/` — accepted Invent contract.
- `make/` — the exact sealed Release facts, exact CAD source, models, and verification.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
