# Starling Gate

![Starling Gate](make/verification/renders/iso.png)

A palm-sized, one-piece rocking arch whose negative space shifts from a perched bird at rest toward a shooting-star streak in motion.

[View the verified public product page](https://www.autonomous.ai/factory/product/starling-gate)

| Frozen on this run | Value |
|---|---|
| Manager | Codex (`--manager codex`) |
| Effort | Spark (`--effort spark`) |
| Inventor | [Pico Press](../../inventors/pico-press/) |
| Factory | https://www.autonomous.ai/factory/product/starling-gate |

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

**Input:** the creator's request. **This toy's input:** A palm-sized, one-piece rocking arch whose negative space shifts from a perched bird at rest toward a shooting-star streak in motion.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Pico Press** was selected and produced **Starling Gate** — A monolithic rocking arch whose void reads as a perched bird at rest and a shooting-star streak while tilted. **Concept parts:** Starling Gate body. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; selection and this compact concept were folded into Make.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** A palm-sized one-piece rocking arch whose cutout changes from a perched bird to a shooting star in motion. The sealed snapshot contains 1 STEP, 2 STL, 1 GLB and 1 product render PNG, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the hash-bound Release package, product facts, and printable [customer manual](release/MANUAL.pdf); see [the Release contract](release/release.json).

### 6. Publication — perform and verify the external effect

**Input:** the exact sealed Release package plus host-held Factory authorization; credentials never enter the native session. **Output:** [the public Factory product](https://www.autonomous.ai/factory/product/starling-gate) and a sanitized, hash-verified [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 7,144,631 (measured; 2/2 turns measured) |
| Native Manager cached input tokens | 6,983,552 (measured; 2/2 turns measured) |
| Native Manager uncached input tokens | 161,079 (measured; 2/2 turns measured) |
| Native Manager cache-write input tokens | 0 (measured; 2/2 turns measured) |
| Native Manager output tokens | 24,291 (measured; 2/2 turns measured) |
| Native Manager reasoning output tokens | 2,884 (measured; 2/2 turns measured) |
| Wish to verified publication | 19m 50s (2026-08-30T06:50:56Z to 2026-08-30T07:10:46.493737+00:00) |

| Stage | Input tokens | Cached input | Uncached input | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---:|---:|---|
| Match | 0 | 0 | 0 | 0 | 0 | folded; economics folded |
| Invent | 0 | 0 | 0 | 0 | 0 | skipped; economics skipped |
| Make | 3,247,116 | 3,142,784 | 104,332 | 12,055 | 1 | measured; economics measured |
| Playtest | 0 | 0 | 0 | 0 | 0 | not-run; economics not-run |
| Release | 3,897,515 | 3,840,768 | 56,747 | 12,236 | 1 | measured; economics measured |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together. Cached plus uncached input equals the input covered by the economic breakdown, while cache writes and reasoning are reported as subsets rather than added again. No dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same Manager and effort route. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --manager codex --effort spark --github 'A palm-sized, one-piece rocking arch whose negative space shifts from a perched bird at rest toward a shooting-star streak in motion.'
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
- `TOKENS.json` — separate Manager-reported gross/cached/uncached input and output/reasoning tokens by stage; no combined total or dollar estimate.
- `TIMING.json` — Wish intake to authenticated public-readback elapsed time.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
