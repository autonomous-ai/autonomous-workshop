# Plan: Review Loop wall-clock

Date: 2026-09-22. Follows the grilling session recorded in
`workshop-fix-flow-grill-handoff.md`. Vocabulary is `CONTEXT.md`.

The goal is whole-run wall-clock for a Correction Run, with isolation and pure
waste-removal available as compromises. Determinism and thoroughness are not.

## Why the order matters

Every measurement this plan could have rested on is stale. The archived
ad-astra-antisol runs predate batched rasterisation (37x, 2026-09-21) and
predate ADR 0069's carry-forward (2026-09-21), and ADR 0069's own transcript
figures disagree with the older trace about where the time went. There is no
baseline that reflects current code.

So step 1 is not preparation for the work; it is what decides whether steps 2
and 3 are worth doing, and the only thing that can show they worked.

## Step 1 — Persist the timing observer

No ADR: this records data that already exists and is currently discarded, which
is a fix, not a trade-off.

`WishRunTimingEvent` (`src/workshop/runtime/progress.py:60-200`) already carries
per-stage, per-turn and per-gate resolution. It is `print()`ed and dropped at
`src/cli/main.py:234`, which is why 83-92% of run wall-clock leaves no duration
record. There is a `_record_native_token_usage` at `native_run.py:9490` and no
timing twin.

- Write `TIMINGS.json` into the Toy Archive, mirroring `TOKENS.json`'s shape and
  joinable to it, including its `measured / total / unmeasured` honesty counter.
- Write the same to host state, which is what a live run can query.
- Archive copy carries durations, not absolute wall-clock timestamps: durations
  are the comparable quantity, timestamps pin a run to a machine and a moment.
  The honesty counter stays public; suppressing it would defeat the file.
- Record the fan-out width alongside round durations, per ADR 0071's
  consequences, or later readings will compare rounds taken at different widths.

Tests: archive contains `TIMINGS.json` with the counter reconciling; durations
present and timestamps absent in the archive copy; host state written
independently of archive sealing; a run that fails mid-way still emits what it
measured.

Then take one Correction Run baseline on current code. Steps 2 and 3 are
re-justified or dropped against it.

## Step 2 — Reuse inside the Review Loop

ADR 0070 covers the surprising part: the redundant-sweep skip that exits zero.
The other two items are applications of ADR 0068's established content-bound
caching and need no ADR of their own.

- **Redundant final sweep** (ADR 0070): re-emit a recorded PASS or FAIL, write
  a `reused` row beside the preserved report, exit with the recorded exit code.
  Never reuse UNVERIFIED: a repeated sweep on an unchanged project is how a
  resumable inspection reaches a verdict (`docs/BASELINE_CORRECTION_RUN.md`).
  Mirror the existing `refuse` path at `verify_project:2382-2420`, which already
  writes `{"status": "refused", "seconds": 0.0}` with `preserve_existing=True`.
- **Shared tessellation across the three Print Gates.** The same solid is
  rebuilt from source four times per part per round -- `gen --write`,
  `check_thickness`, `check_overhang`, `render_review` each rebuild rather than
  reading the STEP just written (`printlib.py:216-239`); `--print-gates` adds
  three more per part (`verify_project:1030-1080`). Output must stay
  byte-identical.
- **`verify_project` honours `make_round`'s reuse ledger**, which already exists
  and is sound at `make_round:300-347` (`print_context` / `reusable_print`) and
  is currently ignored.
- **Polling overshoot falls out of this.** The measured wall-clock cost of
  polling is overshoot: 67 s across v13's four foreground jobs, against about
  12 minutes on the two datable v12 jobs that were backgrounded and polled with
  54 `time.sleep(570)` calls. Commit b70fa1b8 already forbids those sleeps and
  was ignored, the same compliance failure as the step-8 rule; its test pins
  only that the sentence exists in `make.md`. The root cause is job duration
  crossing the 600 s tool ceiling, which is why the agent backgrounds a job at
  all. `verify_project` sweeps at 680/547/549/793 s straddle that line, so
  making them cheap removes the backgrounding and the overshoot with it. No
  separate change.
- **Correct the stale rationale** at `verify_project:5-7`. The docstring's
  reason for the daemon ban is contradicted by the file's own comment at
  `:806-807`, where the true reason -- process-group ownership -- is recorded.
  The ban itself is correct and stays; only the rationale is wrong.

The determinism carve-out needs no new code: ADR 0068 already states that host
verification disables cache reads and writes, so the one cache-free
re-derivation at the sealing boundary is already enforced, outside the sandbox
where it is worth more.

## Step 3 — Bounded component fan-out

ADR 0071. Fan out the component rounds that need a loop, as Codex-native
subagents, joined at `--require-component-passes`. Width `max(2, ncpu // 4)`
capped at 4, derived at runtime. All arms run to conclusion; retries rerun only
the failed components.

Re-justify against step 1's baseline before building: ADR 0069 shrank the set
for corrections, so the remaining value is concentrated in fresh `wish` runs
and `workshop fix --full`.

## Out of scope, with reasons

- **Scoping the Blind Review.** The critic is a background subagent and the
  session is inside other tool calls for 87-88% of the review bracket, so it is
  not on the critical path. Narrowing it would cost what ADRs 0022 and 0025
  exist for and buy time that is not there. Re-measure under step 1 instead.
- **Process and thread parallelism.** The toolchain already saturates the host:
  OCCT runs `isInParallel=True` (`shape_core.py:1626-1628`), cadgen spawns up to
  `ncpu - 1` subprocesses (`generation.py:1067`), and no thread-count
  environment variables are set anywhere. An outer layer is oversubscription. It
  also changes output bytes unconditionally -- report row order and per-command
  `seconds` at `verify_project:1209-1217`, log hashes embedding elapsed time at
  `make_round:470,806`.
- **Re-enabling the warm daemon for the Print Gates.** `run-cost.md:59-61` says
  the import is what `CADGEN_WARM=1` cannot remove from a standalone gate. The
  daemon helps the `gen` path only.
- **Raising `WORKSHOP_GEOMETRY_TIMEOUT`** to absorb fan-out pressure: weakening
  a gate to fit a change.
- **A blocking wait primitive to replace agent polling.** `make_round` already
  blocks, and `yield_time_ms` is a Codex tool parameter, not a Workshop knob.
  The handoff's Q6=(2) assumed a blocking primitive was missing; it is not.

## Stale figures not to carry forward

- `import build123d` is ~1.0s here, not the 5.2s at `run-cost.md:63`. Measured
  in `.venv`: bare 0.01s, numpy+scipy 0.15s, build123d 1.00s. The 5.2s figure is
  arithmetically impossible against `overhang`'s measured 3.8s mean, and
  `run-cost.md:38-40` hedges its own numbers.
- The "5x inflation" claim is folklore: `run-cost.md:86-89` attributes it to a
  busy machine rather than a daemon queue, measures a gate the same document
  calls since-removed, and was vendored from upstream before current env
  forcing.
- The v12/v13 trace in `docs/QUALITY_ECONOMICS.md:745-1007` and
  `docs/correction-run-trace.html` predates batched raster and carry-forward.
  ADR 0069's transcript figures are the more recent reading and disagree with
  it: the integrated verifier was 33 calls over 2,410s, not four sweeps.

## Constraints

`AGENTS.md` is binding: no second Python agent framework, no Python prompt
chains, candidate fan-out, model judges or repair reasoning. Native subagents
for bounded parallel work are explicitly permitted (`AGENTS.md:22-25`). Read the
ADR chain before changing CLI, runtime, workflow, product-run instructions or
lifecycle orchestration. Never weaken a production gate to make a test pass; add
contract and failure-path tests with every runtime or workflow change.
