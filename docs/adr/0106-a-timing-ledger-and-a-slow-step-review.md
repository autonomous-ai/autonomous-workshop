# ADR 0106: A timing ledger and a slow-step review

- **Status:** Accepted (builder, 2026-11-17). Implemented with deterministic
  tests; backfilled from the existing `toys-spec/` logs. No live step has
  written to it yet on the owner's machine before this merge.
- **Date:** 2026-11-17
- **Amends:** nothing. It adds a record beside every long-running step.
- **Unchanged:** every gate, verdict, threshold, deadline, reuse key, batch
  record and lifecycle decision. No gate or host decision reads the ledger.

## Context

The Amsterdam kit seal took 12 attempts over more than a day
(`toys-spec/mini-city-organizer/amsterdam-kit/PILOT-B-LOG.md`, L33 onward).
Most attempts spent about 90 minutes on print gates and then failed on a
check that takes seconds: a stale prose name, a stale exported STEP, a
library-size rule, a Proof-local check script, a tool that lacked a snap
joint. None found a product defect. Two were stopped by hand mid-run and one
was refused because the stop had removed a summary. Nobody saw the pattern
until a person read the log, because each tool kept its own timing in its
own words (`date +%s` lines, `EXIT n`, `[verify_project] x: rc=1 in 0.23s`,
`(4.7s, exit 0)`, `measure/seeded-batch.json`, `wish-run-timing.json`), and
nothing joined them.

The owner asked for a mechanism that reviews the process itself and points
at anything that takes too long.

## Decision

1. **One timing ledger, host-side, outside the repository.** Every
   long-running step appends JSONL rows to
   `$WORKSHOP_HOME/timing/ledger.jsonl` (`WORKSHOP_TIMING_LEDGER` overrides
   the path; `off` turns it off). A step writes a `start` row, then one
   `end` row that is its complete record: step and tool, project and toy,
   start, end and wall seconds, exit code, outcome (`pass`, `fail`,
   `unverified`, `killed`), failure class, the reason in the tool's own
   words, `cache_hit`, an input key, the parent step and an evidence path.
   A `start` row whose step never ended and was later superseded is read as
   killed. The module is `workshop.runtime.timing_ledger`, stdlib only.

2. **Where the rows come from.** `seeded_batch.run_batch` writes one row per
   step (the seal's layers and a seeded Make's batch), with the batch's own
   reuse key as the input key, a `cache_hit` row for a reused step, and a
   child row for every `[tool] name: rc=N in Ts` line the step printed
   (verify_project's commands). `seal_proof.py` times each command,
   `make_round` each mode, `kit_sheets`, `kit_tree`, `kit_print` and
   `kit_manual` each run, `tools/publish_direct.py` each publish, and
   `workshop wish`/`fix` each terminal stage-operation event the host
   already records in `wish-run-timing.json`. A child step names its parent
   through `WORKSHOP_TIMING_PARENT`. A run-local script copy with no
   Workshop install on its path records nothing. The vendored `cad` skill
   is not edited: verify_project's commands are read from its output, and
   the print-gate implementation is not touched.

3. **The ledger only records.** Every write is best effort and never raises;
   an unwritable ledger changes nothing. A step's exit code, output, record
   and verdict are identical with the ledger on or off (tested). The test
   suite writes to a throwaway ledger (`tests/conftest.py`).

4. **Failure classes are deterministic.** Killed (a timeout, a signal, a
   kill exit code) beats unverified (a gate not finished), which beats a
   stale input (the tool's words say an input is stale or changed since it
   froze), which beats a tool or harness error (a traceback, a usage error,
   an exit code of 2 or more, a batch harness failure); a plain exit 1 is a
   product defect. When an agent later diagnoses a failure differently, it
   records an annotation (`tools/process_review.py annotate`, in
   `annotations.jsonl` beside the ledger). Rows are never edited.

5. **The slow-step review.** `tools/process_review.py report` ranks, over the
   last N days: the steps with the most total wall time (each row's own
   time, its timed children's taken out); steps rerun on unchanged inputs
   (an equal input key, not after a kill); expensive steps (≥ 10 min) that
   ran before a cheap step (≤ 60 s, or a preflight-group failure) failed in
   the same session; failures that were tool or harness errors, stale
   inputs or kills; and wait time on one toy between a step ending and the
   next starting (gaps over two hours are the owner's or a design agent's
   time and are left out). It writes the top 5 findings, each with
   evidence paths and a fixed-template suggested fix, then the top 5 of
   each ranking, to `docs/research/process-review/<date>.md`. The same
   ledger, annotations and date give the same bytes. No model is called in
   Python (AGENTS.md); proposing and making a fix is agent work.

6. **Backfill.** `tools/process_review.py backfill` reads the logs agents
   already left under `toys-spec/`: logs that follow the step convention
   (`date +%s` lines, `EXIT n`, `rc=` lines) or open with a tool banner;
   make_round's per-gate logs, de-duplicated by content and joined to the
   print-gates run that holds them; `measure/seeded-batch.json` and
   `seal-preflight.json` records, joined to their seal log; and each run's
   `wish-run-timing.json`. Times a log does not state come from the file's
   birth and modification times and are marked `times_estimated`; the time
   a seal spent before final verification is an `inferred` row. A design
   script's own output is never a step. Backfill is idempotent by source.

## Consequences

- One command answers "where did the time go" for any toy or week, with
  file paths an agent can open.
- The first report (2026-11-17) shows the seal's pre-final layers spending
  hours before a check that refuses in seconds, which ADR 0098's 2026-11-17
  fail-fast amendment has started to address, and print gates as the
  largest total.
- Backfilled rows carry no input key, so reruns on unchanged inputs become
  visible only for steps the live ledger records.
- `seeded_batch.py`'s bytes change, so its `module_sha256` changes: a seeded
  run frozen before this merge rebinds through the operator's skill refresh
  as for any batch tool update. `make-round`'s skill-tree hash is
  refreshed in `LOCK.json`.
- The ledger grows without bound; at a few hundred bytes a row this is
  megabytes a year. Rotation is left until it matters.
