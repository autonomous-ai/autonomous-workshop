# Ember Knock

![Ember Knock](make/verification/renders/iso.png)

One-piece table-edge lantern rocker for rigid 18–22 mm edges, with a rounded throat, underside striker, twin return pads, and inboard globe ballast.

[View the verified public product page](https://www.autonomous.ai/factory/product/ember-knock)

| Frozen on this run | Value |
|---|---|
| Manager | Codex (`--manager codex`) |
| Effort | Spark (`--effort spark`) |
| Inventor | [Sonora Reed](../../inventors/sonora-reed/) |
| Factory | https://www.autonomous.ai/factory/product/ember-knock |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Sonora Reed) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

### 1. Wish — freeze the request

**Input:** the creator's request. **This toy's input:** One-piece table-edge lantern rocker for rigid 18–22 mm edges, with a rounded throat, underside striker, twin return pads, and inboard globe ballast.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Sonora Reed** was selected and produced **Ember Knock** — A single-piece camping-lantern rocker that saddles a table edge. One press rolls its rounded throat to tap the underside with a 6 mm nub; release lets the inboard-weighted globe roll home onto two broad pads. **Concept parts:** Lantern cage and saddle, Twin landing pads, Underside striker, Press cap. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; selection and this compact concept were folded into Make.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** One-piece table-edge lantern rocker with an R6 throat, 6 mm underside striker, twin 12 x 8 mm return pads, and inboard globe ballast. Intended for rigid 18–22 mm table edges; acoustic and physical performance remain untested. The sealed snapshot contains 1 STEP, 2 STL, 1 GLB and 2 product render PNGs, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the hash-bound Release package, product facts, and printable [customer manual](release/MANUAL.pdf); see [the Release contract](release/release.json).

### 6. Publication — perform and verify the external effect

**Input:** the exact sealed Release package plus host-held Factory authorization; credentials never enter the native session. **Output:** [the public Factory product](https://www.autonomous.ai/factory/product/ember-knock) and a sanitized, hash-verified [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 1,829,195 (partial; 2/4 turns measured) |
| Native Manager cached input tokens | 1,719,168 (partial; 2/4 turns measured) |
| Native Manager uncached input tokens | 110,027 (partial; 2/4 turns measured) |
| Native Manager cache-write input tokens | 0 (partial; 2/4 turns measured) |
| Native Manager output tokens | 13,814 (partial; 2/4 turns measured) |
| Native Manager reasoning output tokens | 1,183 (partial; 2/4 turns measured) |
| Wish to verified publication | 1h 6m 52s (2026-09-03T02:57:06Z to 2026-09-03T04:03:58.290615+00:00) |

| Stage | Input tokens | Cached input | Uncached input | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---:|---:|---|
| Match | 0 | 0 | 0 | 0 | 0 | folded; economics folded |
| Invent | 0 | 0 | 0 | 0 | 0 | skipped; economics skipped |
| Make | 1,076,357 | 1,007,744 | 68,613 | 6,428 | 2 | partial; economics partial |
| Playtest | 0 | 0 | 0 | 0 | 0 | not-run; economics not-run |
| Release | 752,838 | 711,424 | 41,414 | 7,386 | 2 | partial; economics partial |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together. Cached plus uncached input equals the input covered by the economic breakdown, while cache writes and reasoning are reported as subsets rather than added again. No dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same Manager and effort route. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --manager codex --effort spark 'One-piece table-edge lantern rocker for rigid 18–22 mm edges, with a rounded throat, underside striker, twin return pads, and inboard globe ballast.'
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
