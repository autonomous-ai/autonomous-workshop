# ADR 0051: Sixty-minute emergency watchdog per native turn

- Status: Accepted
- Date: 2026-09-03 (decision, commit 63604455); recorded 2026-09-08
- Owners: Workflow and Runtime
- Relates to: ADR 0023 and ADR 0046 (twenty-minute Spark boundary), ADR 0049
  (product-wide token budget)

## Context

Healthy Spark Make turns took 17 to 35 minutes on a quiet machine and timed
out whenever several native sessions shared one host; two timeouts in a row
stopped the command. Commit 63604455 raised the native turn boundary to 60
minutes for new Spark runs (was 20) and for the normal Forge and Quest turn
(was 30), leaving the short first-turn handoffs (Invent 20/10, Make proof 16,
final Make 15) and the 15-minute Daydream turn unchanged
(`changes/turn-boundary-60-minutes.changed.md`).

ADR 0046 then reintroduced an explicit twenty-minute ceiling for budgeted
Spark v3, and ADR 0049 replaced per-turn and aggregate time limits for
token-budgeted products with one product-wide token budget while keeping "a
one-hour per-launch emergency watchdog". The runtime launchers refuse any
timeout above 3,600 seconds (`budgets.py` `MAX_TURN_SECONDS`).

## Decision

Every native turn of a token-budgeted Codex run is launched with
`timeout_seconds=3600`. That 60-minute boundary is an emergency watchdog, not
a pacing target: the host does not enforce the economics profile's
20/10/16/15/30-minute stage boundaries or its eight-turn command cap for such
runs, which are bounded by the observed token cap and a 200-turn loop guard
(`MAX_BUDGETED_TURNS`). The profile minutes remain in the materialized
instructions as pacing guidance.

Unbudgeted sessions and runs frozen before this change keep their
materialized boundaries, including the twenty-minute ceiling of ADR 0046
where it was materialized.

## Alternatives considered

- Keep the twenty-minute split for budgeted runs: rejected by ADR 0049; it cut
  healthy Make turns short on shared hosts.
- Remove the watchdog entirely once tokens are budgeted: rejected; a hung
  provider connection would otherwise consume no tokens and never end.

## Consequences

- One long healthy turn can finish; a hung turn ends within an hour and the
  same session resumes.
- Each budgeted step keeps 120 minutes and each toy six hours so one
  maximum-length turn cannot exhaust its own step; a step with under ten
  minutes left is treated as spent.
- Documentation that quotes "20m/turn" for current Spark describes frozen
  unbudgeted runs only.

## Compatibility and migration

No durable schema changes. Frozen runs keep the ceilings they materialized.

## Verification

Launcher-path regressions assert the 3,600-second timeout for token-budgeted
Codex runs and the preserved shorter boundaries for frozen unbudgeted
sessions.
