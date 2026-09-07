# Crosscurrent

![Crosscurrent](make/verification/renders/iso.png)

Steer two shared currents together, carry your rivals into crowded harbors, and cross lanes for the next surprise. A simultaneous tabletop game for family evenings.

[View the verified public product page](https://www.autonomous.ai/toys/product/crosscurrent)

| Frozen on this run | Value |
|---|---|
| Agent | Codex (`--agent codex`) |
| Workflow | Spark (`--workflow spark`) |
| Model | gpt-6-astra (`--model gpt-6-astra`) |
| Effort | High (`--effort high`) |
| Inventor | [Leo](../../inventors/leo/) |
| Factory | https://www.autonomous.ai/toys/product/crosscurrent |

## Workflow

Spark: `Wish -> Make -> Release`. Inventor selection is folded into Make.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Leo) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | 1 | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

### 1. Wish — freeze the request

**Input:** the creator's request. **This toy's input:** Steer two shared currents together, carry your rivals into crowded harbors, and cross lanes for the next surprise. A simultaneous tabletop game for family evenings.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Leo** was selected and produced **Crosscurrent** — A simultaneous family game where everyone steers the same two currents. Carry rival boats, crowd valuable harbors, then cross into tomorrow’s current. **Concept parts:** Shore, Inner carrier, Outer carrier, Player 1 boats, Player 2 boats, Player 3 boats, Player 4 boats, Player 5 boats. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; selection and this compact concept were folded into Make.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** Steer two shared currents together, carry your rivals into crowded harbors, and cross lanes for the next surprise. A simultaneous tabletop game for family evenings. The sealed snapshot contains 9 STEP, 10 STL, 1 GLB and 2 product render PNGs, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the hash-bound Release package, product facts, and printable [customer manual](release/MANUAL.pdf); see [the Release contract](release/release.json).

### 6. Publication — perform and verify the external effect

**Input:** the exact sealed Release package plus host-held Factory authorization; credentials never enter the native session. **Output:** [the public Factory product](https://www.autonomous.ai/toys/product/crosscurrent) and a sanitized, hash-verified [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 4,181,742 (partial; 2/4 turns measured) |
| Native Manager cached input tokens | 3,934,208 (partial; 2/4 turns measured) |
| Native Manager uncached input tokens | 247,534 (partial; 2/4 turns measured) |
| Native Manager cache-write input tokens | 0 (partial; 2/4 turns measured) |
| Native Manager output tokens | 21,682 (partial; 2/4 turns measured) |
| Native Manager reasoning output tokens | 3,740 (partial; 2/4 turns measured) |
| Wish to verified publication | 4h 50m 28s (2026-09-07T05:24:50Z to 2026-09-07T10:15:18.511522+00:00) |

| Stage | Input tokens | Cached input | Uncached input | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---:|---:|---|
| Match | 0 | 0 | 0 | 0 | 0 | folded; economics folded |
| Invent | 0 | 0 | 0 | 0 | 0 | skipped; economics skipped |
| Make | 2,729,610 | 2,655,744 | 73,866 | 8,330 | 3 | partial; economics partial |
| Playtest | 0 | 0 | 0 | 0 | 0 | not-run; economics not-run |
| Release | 1,452,132 | 1,278,464 | 173,668 | 13,352 | 1 | measured; economics measured |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together. Cached plus uncached input equals the input covered by the economic breakdown, while cache writes and reasoning are reported as subsets rather than added again. No dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same agent and workflow. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --agent codex --model gpt-6-astra --effort high --workflow spark 'Steer two shared currents together, carry your rivals into crowded harbors, and cross lanes for the next surprise. A simultaneous tabletop game for family evenings.'
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
