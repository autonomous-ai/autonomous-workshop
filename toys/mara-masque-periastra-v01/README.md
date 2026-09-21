# Periastra

![Periastra](make/verification/renders/iso.png)

Lift a telescope-topped observatory roof to reveal English draughts between two comet streams. Distinctive reversible counters become return-orbit kings, and the complete starting position stores inside the board-box.

[View the verified public product page](https://www.autonomous.ai/toys/product/periastra)

| Frozen on this run | Value |
|---|---|
| Agent | Codex (`--agent codex`) |
| Workflow | Spark (`--workflow spark`) |
| Model | gpt-6-astra (`--model gpt-6-astra`) |
| Effort | Medium (`--effort medium`) |
| Inventor | [Mara Masque](../../inventors/mara-masque/) |
| Factory | https://www.autonomous.ai/toys/product/periastra |

## Workflow

Spark: `Wish -> Make -> Release`. The accepted Inventor assignment is preserved under `match/`. Release is host-owned publication of Make output, with no native Release turn or new manual.

| Stage | Attempts | Outcome |
|---|---|---|
| Wish | host | frozen |
| Match | 1 | accepted (Mara Masque) |
| Invent | skipped | Spark pass-through |
| Make | 1 | accepted |
| Playtest | not run | Spark omission |
| Release | host | accepted |
| Publication | host | public |

Counts come from each stage's public `ATTEMPTS.json`. Skipped stages created no turn, artifact, or gate. Private host rejections and native session resumes are not public.

## How this toy was created

### 1. Wish — freeze the request

**Input:** the creator's request. **This toy's input:** Lift a telescope-topped observatory roof to reveal English draughts between two comet streams. Distinctive reversible counters become return-orbit kings, and the complete starting position stores inside the board-box.

**Output:** an immutable, hash-bound Wish plus its frozen effort route. The exact wording is withheld; this is the sanitized public summary in [the Wish binding](wish/wish.json).

### 2. Invent — choose an Inventor and define the concept

**Input:** the frozen Wish, eligible Inventor roster with each bound Taste/skill bundle, and the product blueprint. **Output:** **Mara Masque** was selected and produced **Periastra** — English draughts — binary-star comet encounters: inbound comets scatter rivals and round the opposite star to gain a return orbit. **Concept parts:** Observatory board base, Conical observatory roof with telescope hood, Single comet 01, Single comet 02, Single comet 03, Single comet 04, Single comet 05, Single comet 06, Single comet 07, Single comet 08, Single comet 09, Single comet 10, Single comet 11, Single comet 12, Forked comet 01, Forked comet 02, Forked comet 03, Forked comet 04, Forked comet 05, Forked comet 06, Forked comet 07, Forked comet 08, Forked comet 09, Forked comet 10, Forked comet 11, Forked comet 12. The complete compact concept is in [make/invented.json](make/invented.json). Spark has no separate Invent Goal; the accepted Inventor assignment and compact Make concept are preserved separately.

### 3. Make — turn the concept into exact product bytes

**Input:** the accepted concept, selected Inventor identity/Taste, blueprint, and any bounded revision evidence. **Output:** Lift a telescope-topped observatory roof to reveal English draughts between two comet streams. Distinctive reversible counters become return-orbit kings, and the complete starting position stores inside the board-box. The sealed snapshot contains 6 STEP and 7 product render PNGs, together with [CAD source](make/source/), [models](make/models/), and [deterministic verification](make/verification/). [The Made contract](make/made.json) binds those exact bytes.

### 4. Playtest — challenge the made product

**Input:** the sealed Made product, blueprint-required checks, and exact evidence. **Output:** not run on this effort route; Release preserves the explicit [omission record](release/PLAYTEST-NOT-RUN.json).

### 5. Release — make the customer package

**Input:** the sealed product and the passed Playtest evidence or truthful not-run record. **Output:** the existing Make files and hash-bound publication metadata, with no new manual, PDF, review, or native Release turn; [the existing README](release/README.md) was reused from Make; see [the Release contract](release/release.json).

### 6. Publication — perform and verify the external effect

**Input:** the exact sealed Release package plus host-held Factory authorization; credentials never enter the native session. **Output:** [the public Factory product](https://www.autonomous.ai/toys/product/periastra) and a sanitized, hash-verified [publication readback](publication/PUBLICATION.json).

## Run cost

| Measure | Value |
|---|---|
| Native Manager input tokens | 28,265,556 (measured; 2/2 turns measured) |
| Native Manager cached input tokens | 27,649,920 (measured; 2/2 turns measured) |
| Native Manager uncached input tokens | 615,636 (measured; 2/2 turns measured) |
| Native Manager cache-write input tokens | 0 (measured; 2/2 turns measured) |
| Native Manager output tokens | 65,991 (measured; 2/2 turns measured) |
| Native Manager reasoning output tokens | 11,842 (measured; 2/2 turns measured) |
| Wish to verified publication | 52m 42s (2026-09-14T03:51:15Z to 2026-09-14T04:43:57.771502+00:00) |

| Stage | Input tokens | Cached input | Uncached input | Output tokens | Turns | Coverage |
|---|---:|---:|---:|---:|---:|---|
| Match | 0 | 0 | 0 | 0 | 0 | folded; economics folded |
| Invent | 0 | 0 | 0 | 0 | 0 | skipped; economics skipped |
| Make | 28,265,556 | 27,649,920 | 615,636 | 65,991 | 2 | measured; economics measured |
| Playtest | 0 | 0 | 0 | 0 | 0 | not-run; economics not-run |
| Release | 0 | 0 | 0 | 0 | 0 | pending; economics pending |

Input and output tokens are best-effort separate counts reported by the native Manager; they are not added together. Cached plus uncached input equals the input covered by the economic breakdown, while cache writes and reasoning are reported as subsets rather than added again. No dollar cost is inferred. Elapsed time ends only after authenticated Factory public readback.

## Reproduce

From a checkout of this repository, verify the host and run the same agent and workflow. This command uses the public product summary; a later run follows the same route but does not replay these exact CAD bytes.

```bash
uv run workshop doctor
uv run workshop wish --agent codex --model gpt-6-astra --effort medium --workflow spark 'Lift a telescope-topped observatory roof to reveal English draughts between two comet streams. Distinctive reversible counters become return-orbit kings, and the complete starting position stores inside the board-box.'
```

If a native turn stops before Release, continue the same Wish with `uv run workshop resume <wish-id>`.

## Snapshot contents

- `wish/` — sanitized Wish binding (exact text only with explicit consent).
- `match/` — accepted Match assignment.
- Invent was skipped by this effort route; its sealed compact concept is under `make/`.
- `make/` — the exact sealed Release facts, exact CAD source, models, product renders, verification, and sealed prior attempts.
- `release/README.md` — the existing Make README, reused without rewriting.
- `release/` — accepted Release contract and exact package bytes.
- `publication/PUBLICATION.json` — sanitized public readback identities.
- `TOKENS.json` — separate Manager-reported gross/cached/uncached input and output/reasoning tokens by stage; no combined total or dollar estimate.
- `TIMING.json` — Wish intake to authenticated public-readback elapsed time.
- `MANIFEST.json` — hashes every workflow file except itself and this README.
- `SANITIZATION.json` — source/public hashes for host-local path prefixes replaced by stable placeholders.
- Playtest was not run; Release records that omission explicitly.

This archive contains no agent session, prompt, transcript, chain of thought, host state, credentials, or raw effect receipt. Publication is not proof of physical manufacture, fit, durability, or delivery.
