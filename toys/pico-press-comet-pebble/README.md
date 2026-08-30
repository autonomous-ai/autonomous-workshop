# Comet Pebble

![Comet Pebble](make/verification/renders/iso.png)

A palm-size one-piece desk wobbler designed for a sideways flick or gentle roll, with a raised smiling-star home cue.

[View the verified public product page](https://www.autonomous.ai/factory/product/comet-pebble)

| Frozen on this run | Value |
|---|---|
| Manager | Codex (`--manager codex`) |
| Effort | Spark (`--effort spark`) |
| Inventor | [Pico Press](../../inventors/pico-press/) |
| Factory | https://www.autonomous.ai/factory/product/comet-pebble |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Pico Press) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

### 1. Wish — freeze the request

**Input:** the creator's request. **This toy's input:** A palm-size one-piece desk wobbler designed for a sideways flick or gentle roll, with a raised smiling-star home cue.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Pico Press** was selected and produced **Comet Pebble** — A one-piece skew-keel rattleback: rotated elliptical sections and a wandering centerline are designed to couple roll, pitch, and yaw into a comet-like looping wobble, then a filleted 34.4 x 20.4 mm effective landing ellipse establishes the smiling-star-up rest. **Concept parts:** Skew-keel body with smiling-star crown. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; selection and this compact concept were folded into Make.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** A palm-size, one-piece skew-keel rattleback designed to turn a flick into a looping wobble and reveal a smiling star at rest. The sealed snapshot contains 1 STEP, 2 STL, 1 GLB and 1 product render PNG, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the hash-bound Release package, product facts, and printable [customer manual](release/MANUAL.pdf); see [the Release contract](release/release.json).

### 6. Publication — perform and verify the external effect

**Input:** the exact sealed Release package plus host-held Factory authorization; credentials never enter the native session. **Output:** [the public Factory product](https://www.autonomous.ai/factory/product/comet-pebble) and a sanitized, hash-verified [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 5,759,755 (partial; 2/3 turns measured) |
| Native Manager output tokens | 36,146 (partial; 2/3 turns measured) |
| Wish to verified publication | 1h 20m 58s (2026-08-29T21:15:16Z to 2026-08-29T22:36:14.321853+00:00) |

| Stage | Input tokens | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---|
| Match | 0 | 0 | 0 | folded |
| Invent | 0 | 0 | 0 | skipped |
| Make | 913,561 | 7,678 | 2 | partial |
| Playtest | 0 | 0 | 0 | not-run |
| Release | 4,846,194 | 28,468 | 1 | measured |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together and no dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same Manager and effort route. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --manager codex --effort spark --github 'A palm-size one-piece desk wobbler designed for a sideways flick or gentle roll, with a raised smiling-star home cue.'
```

If a native turn stops before Release, continue the same Wish with `uv run workshop resume <wish-id>`.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, product renders, verification, and sealed prior attempts.
- `release/MANUAL.pdf` — the exact sealed printable in-box manual.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `TOKENS.json` — separate Manager-reported input and output tokens by stage; no combined total or dollar estimate.
- `TIMING.json` — Wish intake to authenticated public-readback elapsed time.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
