# Handoff — Grilling session: speeding up the Workshop "fix flow"

**Repo:** `/home/loginuserxx/harnesses/autonomous-workshop` (branch `main`)
**Date:** 2026-09-22
**Original ask:** "Look for the optimization opportunity in the workshop fix flow in order to speed up the run. As for compromising, go through the grilling with me and I will decide it."

This was a `/grill-with-docs` session (grilling + domain-modeling). It is an
**interview in progress**, not an implementation. No files were modified.
Nothing has been decided beyond the answers recorded below.

---

## How to resume

Re-enter the grilling loop. Questions **Q7–Q12** below are the open frontier and
have *not* been answered. Ask them as one round, wait for answers, then
recompute the frontier. Do not start implementing until the user confirms
shared understanding.

---

## Settled decisions (user answered these directly)

| # | Question | User's answer |
|---|---|---|
| Q1 | Which loop is "the fix flow"? | **(3)** Make Rounds **and** Blind Review cycles — everything in Make after first geometry exists — **(4)** framed as whole-run wall-clock |
| Q2 | What is the actual complaint? | **(1)** Wall-clock |
| Q3 | What may be compromised? | **(3)** Isolation/parallelism **+ (4)** pure waste-removal. Determinism and thoroughness were **withheld**. *(See "Q3 is now partly void" below.)* |
| Q4 | Re-analysis or implementation? | **(2) then (1)** — find what the existing analysis missed, then implement. Explicitly: *"re-analyse the workflow, not only the runs"* |
| Q5 | Persist the timing observer first? | **(1)** Yes, first |
| Q6 | The polling pattern? | **(2)** Give the agent a blocking wait primitive **+ (4)** reduce job durations |

### Q3 is now partly void — read this before proceeding
The user authorised parallelism **before** the evidence against it arrived.
Q12 below re-opens exactly that half. Do not treat Q3=(3) as live authorisation.

---

## Established findings (verified, with the correction history)

Three sub-agent explorations plus direct measurement. Key sources, all in-repo:

- `docs/QUALITY_ECONOMICS.md:745-1007` + `docs/correction-run-trace.html` — a
  **pre-existing forensic trace of two real runs** (ad-astra-antisol v12/v13).
  Read this first; it already answers "where does the time go".
- `src/workshop/make/skills/cad/references/run-cost.md` — per-command costs.
  Treat its numbers sceptically (see corrections).
- `.agents/product-run/.agents/skills/autonomous-workshop/references/make.md:123-205`
  — the native Make work order (the actual loop).
- `src/workshop/make/skills/make-round/scripts/make_round` (1106 lines)
- `src/workshop/make/skills/cad/scripts/verify_project` (2733 lines)

### What is true

1. **Model thinking is only 10–16% of wall clock.** Not the bottleneck.
2. **Turn boundaries are not the problem.** v13 blew the 600s tool ceiling 5×;
   total overshoot was **67 seconds**. Timeouts checkpoint and resume without
   losing work (`src/workshop/runtime/claude.py:456-462`). The one real hole was
   **46.9 min of session teardown** — a crash, not a timeout.
3. **Biggest un-taken win: `verify_project` used as an iteration loop.**
   42m40s over 4 sweeps in v13 (680/547/549/793s), **all four passed**.
   `references/make.md:190` already forbids this and was ignored.
4. **Rasterisation was the largest measured cost (~2h of 5h30m) and is already
   fixed** — batched raster landed 2026-09-21, 37×, pixel-identical,
   `tests/make/test_render_review_raster.py`. Every archived run predates it.
5. **The same solid is rebuilt from source 4× per part per round** — `gen --write`,
   `check_thickness`, `check_overhang`, `render_review` each rebuild rather than
   reading the STEP already written (`printlib.py:216-239`). `--print-gates` adds
   3 more per part (`verify_project:1030-1080`).
6. **`make_round` already has a sound hash-reuse ledger** that `verify_project`
   ignores: `print_context`/`reusable_print`, `make_round:300-347`.
7. **cadgen's incremental fast path is unreachable** — `generation.py:1229-1248`
   is guarded on no-output-override, but `gen --write` always sets one
   (`gen/cli.py:118-128`).
8. **83–92% of run wall-clock leaves no duration record.** `WishRunTimingEvent`
   (`src/workshop/runtime/progress.py:60-200`) has full per-stage/turn/gate
   resolution and is `print()`ed and discarded at `src/cli/main.py:234`. There is
   a `_record_native_token_usage` (`native_run.py:9490`) but no timing twin.
9. **The blind review is NOT on the critical path** — the critic is a background
   subagent; the session is inside other tool calls 87–88% of the review bracket.

### Corrections made during the session — do not regress these

- **`import build123d` is ~1.0s here, not the 5.2s in `run-cost.md:63`.**
  Measured: bare 0.01s / numpy+scipy 0.15s / build123d 1.00s in `.venv`.
  The 5.2s figure is arithmetically impossible against `overhang`'s measured
  3.8s mean. `run-cost.md:38-40` hedges its own numbers.
- **Re-enabling the warm daemon would NOT help the print gates.**
  `run-cost.md:59-61`: the import is what `CADGEN_WARM=1` *"cannot remove from a
  standalone gate"*. Daemon helps the `gen` path only. Demoted to low priority.
- **The concurrency ban is NOT stale — parallelism was the wrong call.** Verified:
  - `nproc = 64`
  - `build123d/topology/shape_core.py:1626-1628` passes OCCT `isInParallel=True`
  - `cadgen/_internal/generation.py:1067` spawns up to 63 subprocesses
  - zero hits for `OMP_NUM_THREADS|OPENBLAS_NUM_THREADS|MKL_NUM_THREADS`
  The toolchain already saturates the machine; an outer layer is oversubscription.
  Concurrency also **changes output bytes unconditionally** (report row order and
  per-command `seconds` at `verify_project:1209-1217`; log hashes embedding
  elapsed time at `make_round:470,806`) and can **flip verdicts** via the shared
  wall-clock geometry deadline (`verify_project:774`, `make_round:42/444`).
- **The "5× inflation" claim is folklore.** `run-cost.md:86-89` attributes it to a
  busy machine, not a daemon queue; it measures a gate the same doc calls
  "since-removed"; vendored from upstream, predates current env forcing.
- **The daemon picture is split:** genuinely dead inside `verify_project` (`:808`
  overwrites `:792`) and `make_round` (`:438`), but **live on the agent-driven
  path** (`SKILL.md:203`, `step-generation.md:53-79`, ~15 toy READMEs). So
  `SKILL.md:197`'s ban is correct; only the docstring rationale at
  `verify_project:5-7` is stale — the true reason is in its own `:806-807`
  comment (process-group ownership).

---

## OPEN FRONTIER — ask these next

**Q7 — `verify_project`-as-iteration-loop is a compliance problem.** The contract
already forbids it and the agent did it anyway, so re-wording won't work.
(1) deterministic refusal when nothing hash-relevant changed — precedent at
`verify_project:2504-2513`; (2) make it cheap instead of forbidden; (3) stronger
skill instruction; (4) host-side accounting only.
*Recommended: (1)+(2).*

**Q8 — Does hash-gated skipping count as compromising determinism?** THE PIVOTAL
QUESTION — it decides whether the two biggest wins are in budget. Candidates:
shared tessellation across the three gates (byte-identical output); having
`verify_project` honour `make_round`'s reuse ledger; skipping rebuilds on
unchanged source closure.
*Recommended: (a) these are waste-removal, not determinism compromise — with a
carve-out keeping ONE full cache-free rebuild at the sealing boundary, because
`AGENTS.md` makes host re-derivation load-bearing.*

**Q9 — Where does persisted timing go?** (1) new `TIMINGS.json` in the toy
archive mirroring `TOKENS.json` including its `measured/total/unmeasured` honesty
counter, joined to tokens; (2) extend `TOKENS.json`; (3) host-state only.
*Recommended: (1)+(3), write both. Sanitisation question follows.*

**Q10 — Can blind re-review be scoped without losing thoroughness?** Cost driver
is `make.md:203-205` (any geometry change invalidates the review).
*Recommended: (1)+(3) leave it alone and re-measure — the 87–88% overlap means it
costs almost no wall-clock, and scoping it would gut what ADR 0022/0025 exist for.
This is the one item worth arguing OUT of scope.*

**Q11 — Deliverable?** (1) ADR(s) + plan; (2) implementation; (3) findings doc.
*Recommended: (1) first — the changes meet all three ADR tests and `AGENTS.md`
requires reading the ADR chain before runtime/lifecycle changes.*

**Q12 — What happens to parallelism now?** Replaces the (3) half of Q3.
(1) drop it; (2) cap threads only; (3) run the full 3-arm experiment;
(4) docs-only fix.
*Recommended: (1)+(4).*

### Likely later rounds (blocked on the above)
- Sanitisation policy for `TIMINGS.json` in public toy archives (cf.
  `ATTEMPTS.json`'s `privacy` field) — blocked on Q9.
- Shape and ownership of the blocking wait primitive from Q6=(2): host tool vs
  CAD-skill script, and whether it stays inside `AGENTS.md`'s "no Python agent
  scheduler" boundary — blocked on Q11.
- Which ADRs to write and their numbering (next free number after 0064) —
  blocked on Q11.

---

## Constraints the next agent must respect

- `AGENTS.md` at repo root is binding. **No second Python agent framework**; no
  Python prompt chains, candidate fan-out, model judges, or repair reasoning.
- Read the ADR chain (0012–0064) before changing CLI, runtime, workflow,
  product-run instructions, or lifecycle orchestration.
- Never weaken a production gate to make a test pass. Add contract and
  failure-path tests with every runtime/workflow change.
- `CONTEXT.md` is a glossary only. Relevant terms already defined: **Round**,
  **Make Round**, **Revision**, **Gate**, **Blind Review**, **Print Gate**,
  **Frozen**. Note **"fix flow" is NOT a defined term** — if it survives as a
  concept, it needs a glossary entry or should be dropped in favour of the
  existing ones.

## Suggested skills

Call the Skill tool for:
- `mattpocock-skills:grilling` — **required**; the session is mid-interview
- `mattpocock-skills:domain-modeling` — required for the `CONTEXT.md` glossary
  question above and for any ADR (ADR format lives in that skill's
  `ADR-FORMAT.md`)
- `mattpocock-skills:diagnosing-bugs` — only if Q12 moves toward the perf
  experiment
- `mattpocock-skills:tdd` — only once Q11 resolves toward implementation
