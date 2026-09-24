# Baseline Correction Run (issue #40)

The reference every later performance claim about a Correction Run is measured
against. One real `workshop fix` Run on current code, its schema 2 timing record
read and interpreted, the stale traces checked against it, and each ticket that
was waiting on it re-justified or recommended for closure.

- Run: `wish-20260923-171926-37a1532f`, 2026-09-23 17:19:26Z → 2026-09-24 00:22:21Z
- Archive: [`toys/ad-astra-antisol-companion`](../toys/ad-astra-antisol-companion/)
  (`TIMING.json` schema 2, `TOKENS.json` schema 3)
- Code: branch `feat/sandcastle` at `a5ecbfa2`, which includes batched
  rasterisation and the carry-forward policy (both landed 2026-09-21), the
  host-state timing recorder (#38) and the published breakdown (#39)

## What was run, and why these choices

```
workshop fix --agent claude --model claude-opus-5 --effort high --no-publish \
  --prompt-file brief.txt toys/ad-astra-antisol-v11
```

- **Runtime.** The Claude Code Manager runtime with `claude-opus-5`, the
  runtime and model both archived traces (`ad-astra-antisol-v12`, `-v13`) ran
  on. The runtime registry marks Claude Code **experimental**
  (`workshop doctor`: "available as an experimental Manager"); read every figure
  here as a Claude-runtime figure, not a Codex one.
- **Effort `high`, not the default.** The Claude runtime defaults to `medium`;
  both archived traces froze `high`, so it is passed explicitly.
- **`--no-publish`.** As v13 did. No Factory effect was performed, so the
  record's completion boundary is the local seal, not a public readback.
- **Source `v11`, not `v13`.** `workshop fix` refuses a source archive over
  128 MiB (`MAX_REVISION_BYTES`, `src/workshop/workflow/revision.py:41`). v13 is
  138.4 MiB and v12 137.5 MiB, so neither can be corrected on current code. v11
  is 126.7 MiB and is the exact source the v12 trace corrected, which makes the
  v12 comparison like-for-like.
- **The brief.** Archives withhold the correction brief, so v13's could not be
  reused. This one has the same scope as v12→v13's Jupiter change, one world
  pair's markings:

  > On both Neptune pieces, add the small bright companion cloud that sits
  > just south of the Great Dark Spot: one white outline oval, about 10 by 5
  > degrees of arc, centred about 8 degrees of latitude south of the Great Dark
  > Spot's centre and at the same longitude. Keep it inside the
  > narrowest-feature limit the set already uses for printable markings.
  > Nothing else on either Neptune piece, and nothing on any other part,
  > changes.

- **Host.** 64 cores, 566 GB RAM, shared with other workloads: two libvirt VMs
  (16 and 8 vCPU) were busy throughout, one using about four cores. Timings
  carry that noise; the archived traces were taken on a different machine.

The Run completed and sealed. Make took **four invocations**: the stage budget
(`STEP_BUDGET_SECONDS`, 120 minutes per `wish`/`resume`) stopped it three times
with "Make used its 120-minute budget", and `workshop resume` continued the same
session each time. Operator latency between invocations was 43 s, 16 s and 29 s.

## The timing record

`TIMING.json` (schema 2), as published:

| | ms | share of total |
|---|---:|---:|
| **total** | **25,266,229** (7h01m06s) | 100% |
| **measured** | **25,137,217** | 99.49% |
| **unmeasured** | **129,012** (2m09s) | **0.51%** |

`elapsed_seconds` is 25,253 (Wish intake to seal).

**Unmeasured share, stated plainly: 0.51%.** It is host bookkeeping between
bracketed operations plus the three gaps between invocations. That number is
honest and it is also nearly useless. The observer brackets only seven host
operations, and one of them, the native session turn, contains the whole of
Make. So 99.35% of the Run is two opaque items. **The record says where the
Run's time is, and nothing about what it was spent on.**

### Largest measured items by stage and operation

| # | stage / operation | count | elapsed | share | states |
|---:|---|---:|---:|---:|---|
| 1 | make / `session.resume` | 7 | 21,332.7 s | 84.4% | 2 completed, 5 failed |
| 2 | make / `session.start` | 1 | 3,769.5 s | 14.9% | 1 failed |
| 3 | make / `outcome.process` | 2 | 31.6 s | 0.13% | 2 completed |
| 4 | wish / `run.initialize` | 1 | 2.2 s | 0.01% | completed |
| 5 | make / `gate.evaluate` | 2 | 0.7 s | — | 1 completed, 1 failed |
| 6 | make / `stage.prepare` | 11 | 0.3 s | — | 11 completed |
| 7 | release / `stage.prepare` | 1 | 0.15 s | — | completed |

Read the states carefully. **None of the six `failed` session turns is a
failure.** Each is a native turn that reached the 60-minute turn boundary
(3,607–3,770 s each) and was checkpointed; the host continued the same session.
The one failed `gate.evaluate` is a real host rejection of Make's first proposal,
repaired in a 73-second turn.

### Four things wrong with the record itself

None of them changes a figure above by more than about three minutes. They
belong in a follow-up to #38/#39, not here.

1. **Release's own operations are missing from the published breakdown.** Host
   state has release `outcome.process` 121.4 s and `gate.evaluate` 75.2 s. The
   archive is sealed from inside that `outcome.process`, before either closes,
   so the published record stops at Release's `stage.prepare`.
2. **`completion_boundary` reads "authenticated Factory public readback" on a
   `--no-publish` Run**, which performed no readback.
3. **A routine turn boundary is recorded as `failed`.** A reader counting
   failures sees six that are not.
4. **`measured_ms` includes `run.initialize`'s 2.2 s, which ends before the
   window `total_ms` opens** (`started_at` is that operation's completion), so
   the counter is not strictly a partition of the total.

## Inside Make: the session transcript

The transcript accounting uses the same method as
[`correction-run-trace.html`](correction-run-trace.html): each tool call is paired
with its result by `tool_use_id`, the gaps between calls are counted as model
time, and calls that hit the 600-second tool ceiling (13 of them) are extended to
their job's real end, read from the background output file's final write.

Session transcript: **7h00m00s** across eight native turns.

| | wall | share |
|---|---:|---:|
| a tool call or background job running | 5h42m25s | 81.5% |
| …foreground tool calls alone | 4h24m51s | 63.1% |
| model generating (nothing running, gap ≤ 5 min) | 1h06m07s | 15.7% |
| silent (nothing running, gap > 5 min) | 11m29s | 2.7% |

Where the running time went, as a union of wall intervals rather than a sum, so
nothing is counted twice:

| work | calls | wall (union) | notes |
|---|---:|---:|---|
| whole-set renders: `snap_frames.py`, `world_views.py`, `corona_views.py` | 16 | **171.6 min** | the toy's own render scripts; three completed `snap_frames` runs at about 45 min each, plus runs the agent killed and restarted |
| `make_round` (component and assembled rounds) | 12 | 64.6 min | 39 component rounds and 3 assembled rounds |
| `verify_project` final sweeps | 5 | 59.6 min | 0.1 s FAIL, 470 s FAIL, 1,069 s UNVERIFIED, 1,071 s UNVERIFIED, 966 s PASS |
| measurement scripts under `measure/` | 38 | ~47 min | Neptune mirror, flush, facing and tone-separation evidence |
| `gen` and `production.py` outside rounds | 14 | ~38 min | |
| renders ∪ `make_round` | 28 | **219.5 min** | **52% of the session** |

### Rendering is still the largest cost, but not because of rasterisation

A profile of one assembled-round render, reproducing the Run's own
`r0003/visual/iso.png` byte for byte (222 occurrences, 3 views, 900 px):

| | from source (what the round does) | from the STEP `gen` already wrote |
|---|---:|---:|
| build or import | 410.0 s | 11.6 s |
| tessellate | 467.4 s | 496.9 s |
| rasterise, 3 views | **3.9 s** | 5.4 s |
| wall | 884 s | 518 s |
| images | reference | differ in 0.07–0.08% of pixels, max channel Δ 167 |

The 37× batched rasteriser did its job: rasterising is 0.4% of a render.
**A render is now half assembly rebuild and half tessellation.** The three
assembled rounds' renders took 864, 898 and 889 s, and the `snap_frames` sheets
(92 min user, 144 min sys for 45 min wall) spend their time the same way.
Reading the STEP instead of rebuilding saves 41% per render, but the image is
not byte-identical.

### Carry Forward was defeated

The correction changed no printed part: the companion cloud is a separate
colour body, and both Neptune STEPs came back **byte-identical** to the source
archive. Even so, **11 of 24 printable parts came back byte-different**. The
generator does not serialise the same shape to the same STEP bytes in a warm
multi-target `gen` as in a single-target one. The largest volume difference is
1.13e-8 mm³, and six parts differ in entity count. The byte comparison could not
clear those parts, so the agent gave **all 24 components fresh isolated rounds**
(39 rounds, as some parts took two). It also declined to carry the source's
round histories, because publication had redacted their paths and they no
longer hash to their own state files. See the run's
`measure/quick-fix-carry.md`.

Measured from their own logs, those 39 component rounds cost only about
**10 minutes**: `gen` 4.1 s, thickness 8.1 s, overhang 3.8 s, render 4.4 s per
part on average.

### The final verifier needs several sweeps on this product

Every geometry step in one `verify_project` sweep shares a single allowance,
`WORKSHOP_GEOMETRY_TIMEOUT`, 600 s by default (`verify_project:887-895`).
Completed inspection measurements survive in `__cadgen__`, so a later sweep
resumes from them. On this 222-occurrence product one sweep could not finish:

| sweep | wall | result | inspection |
|---:|---:|---|---|
| 1 | 0.1 s | FAIL | `check_layout`: `parts/world.py` over 400 lines; split before sweep 2 |
| 2 | 470 s | FAIL | `check_spec_format`: 11 untagged dimensions; tagged before sweep 3 |
| 3 | 1,069 s | UNVERIFIED | 1 of 51 checks complete |
| 4 | 1,071 s | UNVERIFIED | 24 of 51 |
| 5 | 966 s | **PASS** | 51 of 51 |

The project did not change between sweeps 3, 4 and 5. They were resumptions,
not an iteration loop. Each one still repeated the whole-product `gen` of all
25 entries (439 s in sweep 5) before resuming inspection.

### The blind review

The critic ran as a background subagent from +3h27m to +5h29m, two rounds.
Round 1 filed a blocking defect: a reader shown the renders cold saw the new
cloud as "a small grey circle". The marking was repaired, and every canonical
image was re-rendered, including a 45-minute `snap_frames`
run and an assembled round. Round 2 passed. The critic's reading time was off
the critical path, as the stale trace found. **The repair its verdict required
was on it**: roughly an hour of re-rendering followed from one finding.

### Tokens

**The token record is not `unavailable`.** Issue #40 expected it to be, but
Claude Manager usage reporting (a79272c4) had already landed. It is **partial**:
2 of 8 Make turns measured, 6 unmeasured. The six unmeasured turns are exactly
the ones stopped at a turn boundary, which end without the CLI's final `result`
event. For the two measured turns only (about 54 min of the session):

| | tokens |
|---|---:|
| input | 88,720,143 |
| …cached (cache reads) | 88,576,260 (99.8%) |
| …cache writes | 143,655 |
| output | 97,795 |
| …reasoning | 14,003 |

These are **lower bounds on the Run, not its cost**; the other 6h06m of session
is unmeasured, and must not be read as zero. The host has no token *budget* for
a Claude Run. So the timing-to-token join from #39 is exercisable for the first
time, but only over 2 of 8 turns.

## Against the stale traces

| | v12 | v13 | **baseline** |
|---|---:|---:|---:|
| source → result | v11 → v12 | v12 → v13 | v11 → companion |
| host elapsed | 5h29m51s | 4h14m44s | **7h00m53s** |
| model generating | 16% | 10% | **15.7%** |
| silent | 2 min | 47 min (teardown crash) | **11 min** |
| rasterisation | ~2 h | 59 min | **seconds** |
| whole-set render wall | not separated | not separated | **2h52m** (build + tessellate) |
| component rounds carried | — | all byte-identical parts | **none** (all 24 rerun) |
| `verify_project` sweeps | not separated | 4, all PASS, 42m40s | 5: FAIL ×2, UNVERIFIED ×2, PASS, 59m36s |
| stops needing `workshop resume` | — | 1 (crash) | **3** (Make stage budget) |

### Figures the baseline contradicts

1. **"A comparable correction should now spend minutes rather than hours on
   rasterisation"** (`QUALITY_ECONOMICS.md`, correction-run trace). This is true of
   rasterisation (3.9 s per assembled render) and false of rendering. Whole-set
   renders took 2h52m of wall here, more than v13's. The trace's "none of it is
   the picture" still holds, but the mechanism is now assembly rebuild plus
   tessellation, not per-triangle rasterisation.
2. **"v13 keeps the component rounds of every byte-identical part and re-renders
   only the assembly."** The policy depends on unchanged parts reproducing their
   bytes. On this product 11 of 24 did not, and none were carried.
3. **v13's four verifier sweeps as "an iteration loop"** (the premise of #41).
   Here the repeated sweeps were required resumptions of an inspection that
   cannot finish inside one 600-second allowance.
4. **`run-cost.md`: `import build123d` alone is 5.2 s.** Measured 2.53–2.71 s
   on this host (five runs). The grilling handoff's 1.0 s is also not
   reproduced here.
5. **`run-cost.md`: print gates cost 7–12 s per part per gate, ~5 s of it the
   import.** The overhang gate averaged 3.8 s per part, the whole call. That is
   below the stated floor and cannot contain a 5 s import.
6. **"Turn boundaries are not the problem"** (grilling handoff). The 60-minute
   turn boundary itself cost little here. The 120-minute stage budget stopped
   an unattended correction three times, and each stop needs an operator to run
   `workshop resume` before work continues.

Consistent with the stale traces: model generation is 10–16% of wall, so
thinking is not the bottleneck, and the blind critic's own reading time is off
the critical path.

## The blocked tickets, re-justified against this baseline

Savings below are upper bounds from this Run's measured costs. The Run's total
is 421 minutes.

### #41 — Reuse a redundant final sweep's verdict: **do not build as written**

- **Saving on this baseline: 0.** No sweep here was redundant: the one PASS was
  the last sweep.
- **As specified it would have broken this Run.** Its first criterion re-emits
  the prior verdict for an unchanged project, and another keeps "a reused
  unverified verdict unverified". Sweeps 3→4→5 were on an unchanged project with
  an UNVERIFIED verdict, and resuming was the only way to reach PASS. Under #41
  sweep 4 would have re-emitted UNVERIFIED and the product could never have
  verified.
- **Recommendation:** narrow #41 to terminal verdicts only (PASS and FAIL),
  never reusing an UNVERIFIED verdict whose inspection can still make progress.
  Re-justify it on v13-style redundant PASS sweeps, and treat it as low
  priority.
- **A larger lever it does not touch:** each resumed sweep repeats the full
  439-second `gen` of unchanged entries (about 22 min over three resumptions
  here).

### #42 — Build each part once per Make Round: **re-scope, or close as written**

- **Saving as written is at most about 6 minutes (1.4%).** The 39 component
  rounds cost about 10 minutes in total. The per-part rebuilds inside them are
  bounded by three rebuilds × 39 rounds × roughly 3 s each. This Run used no
  `--print-gates`, so the three extra rebuilds per part that #42 cites never
  occurred.
- **Where rebuilding actually costs:** the assembled round's render rebuilds the
  222-occurrence assembly from source, 410 s per round × 3 rounds.
- **That rebuild cannot be swapped for reading the STEP under #42's own bar.**
  The STEP-import render differs in 0.08% of pixels, which fails #42's
  byte-identity requirement.
- **Recommendation:** re-scope to the assembled round, where the saving is about
  20 minutes (410 s × 3). A byte-identical route would reuse the in-process
  build or a content-keyed tessellation. Otherwise close #42.

### #43 — Let the final verifier honour the Make Round reuse ledger: **close as written**

- **Saving on this baseline: 0.** The ledger holds Print Gate results, and this
  Spark correction made no print-ready claim, so `verify_project` ran without
  `--print-gates` and no gate in it had a ledger entry.
- **The verifier's real repeated cost is the 439-second whole-product `gen` per
  sweep**, which is not a Print Gate. Reusing it is hash-gated skipping. Whether
  that counts as compromising determinism is the grilling handoff's open Q8, so
  it is the owner's call, not this ticket's.
- **Recommendation:** reopen only for a print-ready Run, where the ledger
  applies.

### #44 — Name the component-round set explicitly: **defer with #45**

- **Behaviour-neutral by design, so there is nothing for a baseline to save.**
- **Its value is as the enabler for #45**, and #45 does not survive this
  baseline (below).
- **Its own premise failed here.** "A Correction Run under Carry Forward has a
  set of only the changed components" presumes unchanged parts reproduce their
  bytes. This one produced a set of all 24 from a correction that changed zero
  printed parts.

### #45 — Run the component-round set concurrently (blocked on #44, not directly on #40): **recommend closure**

- **Ceiling on this baseline is about 7.5 minutes (1.8%).** Width 4 on this
  64-core host applied to about 10 minutes of component rounds.
- **The risk it names showed up here.** Oversubscription starving a geometry
  allowance happened on this product even serially: two final sweeps went
  UNVERIFIED on allowance exhaustion, at about 55 min user and 110–120 min sys CPU
  for 16–18 min wall per sweep.

### What this baseline says to do instead

Ranked by measured wall time in this Run. None of these is filed as a ticket;
each needs an owner's decision first.

1. **Make STEP serialisation deterministic** across warm multi-target and
   single-target `gen`. Without that, Carry Forward cannot carry an unchanged
   part, and every downstream saving that assumes it (#44, #45, carried renders)
   fails. The ceiling is not known from this Run; its 11 byte-different parts
   are the evidence.
2. **Reuse tessellation and assembly builds across renders.** About 470–500 s
   of tessellation and 410 s of build per assembled render. The toy's own
   render scripts repeat both (171.6 min of whole-set render wall). This is a
   content-keyed cache in the renderer, not a gate change.
3. **Stop resumed `verify_project` sweeps from regenerating every entry.**
   About 7 min per resumption.
4. **Fit a large correction inside one invocation**, or say plainly that it
   will not. Three Make budget stops turn an unattended Run into four
   operator-driven invocations.
5. **Raise or waive the 128 MiB revision cap** for archives that already exceed
   it. v12, v13 and this baseline's archive (129.4 MiB) cannot be corrected, but
   `workshop fix` printed "Correct it again: `workshop fix
   toys/ad-astra-antisol-companion`" anyway.
