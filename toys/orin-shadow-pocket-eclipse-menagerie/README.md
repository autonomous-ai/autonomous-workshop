# Pocket Eclipse Menagerie

![Pocket Eclipse Menagerie](make/verification/renders/iso.png)

A palm-sized one-piece shadow toy whose broad faces project a horned owl and, after a 90-degree turn, a leaping rabbit under an ordinary external phone flashlight.

[View the verified public product page](https://www.autonomous.ai/factory/product/pocket-eclipse-menagerie)

| Frozen on this run | Value |
|---|---|
| Manager | Codex (`--manager codex`) |
| Effort | Spark (`--effort spark`) |
| Inventor | [Orin Shadow](../../inventors/orin-shadow/) |
| Factory | https://www.autonomous.ai/factory/product/pocket-eclipse-menagerie |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Orin Shadow) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

### 1. Wish — freeze the request

**Input:** the creator's request. **This toy's input:** A palm-sized one-piece shadow toy whose broad faces project a horned owl and, after a 90-degree turn, a leaping rabbit under an ordinary external phone flashlight.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Orin Shadow** was selected and produced **Pocket Eclipse Menagerie** — A single broad crossed-mask sculpture: shallow curled-fox relief sits beneath a bifurcated crescent-like crown; one exact axis projects a horned owl and a 90-degree turn projects a leaping rabbit. **Concept parts:** Unified fox-crescent dual-shadow caster. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; selection and this compact concept were folded into Make.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** A palm-sized one-piece sleeping fox beneath a crescent that reveals an owl shadow, then a leaping rabbit after one quarter-turn. The sealed snapshot contains 1 STEP, 2 STL, 1 GLB and 3 product render PNGs, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the hash-bound Release package, product facts, and printable [customer manual](release/MANUAL.pdf); see [the Release contract](release/release.json).

### 6. Publication — perform and verify the external effect

**Input:** the exact sealed Release package plus host-held Factory authorization; credentials never enter the native session. **Output:** [the public Factory product](https://www.autonomous.ai/factory/product/pocket-eclipse-menagerie) and a sanitized, hash-verified [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 7,957,133 (measured; 2/2 turns measured) |
| Native Manager cached input tokens | 7,764,992 (measured; 2/2 turns measured) |
| Native Manager uncached input tokens | 192,141 (measured; 2/2 turns measured) |
| Native Manager cache-write input tokens | 0 (measured; 2/2 turns measured) |
| Native Manager output tokens | 32,290 (measured; 2/2 turns measured) |
| Native Manager reasoning output tokens | 5,709 (measured; 2/2 turns measured) |
| Wish to verified publication | 22m 59s (2026-08-30T07:38:33Z to 2026-08-30T08:01:32.842637+00:00) |

| Stage | Input tokens | Cached input | Uncached input | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---:|---:|---|
| Match | 0 | 0 | 0 | 0 | 0 | folded; economics folded |
| Invent | 0 | 0 | 0 | 0 | 0 | skipped; economics skipped |
| Make | 3,451,567 | 3,336,704 | 114,863 | 18,962 | 1 | measured; economics measured |
| Playtest | 0 | 0 | 0 | 0 | 0 | not-run; economics not-run |
| Release | 4,505,566 | 4,428,288 | 77,278 | 13,328 | 1 | measured; economics measured |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together. Cached plus uncached input equals the input covered by the economic breakdown, while cache writes and reasoning are reported as subsets rather than added again. No dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same Manager and effort route. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --manager codex --effort spark --github 'A palm-sized one-piece shadow toy whose broad faces project a horned owl and, after a 90-degree turn, a leaping rabbit under an ordinary external phone flashlight.'
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
