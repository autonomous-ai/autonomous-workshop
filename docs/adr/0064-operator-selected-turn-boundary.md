# ADR 0064: one operator-selected native turn boundary

**Status:** accepted (2026-09-11). Adds an explicit, opt-in override over the
frozen turn boundaries of ADR 0019, ADR 0023 and the deep-economics profiles.
It supersedes none of them: every run that does not ask for the override keeps
the exact boundary it froze.

## Context

Every native turn has a host wall clock. Where it comes from depends on the
run: `SPARK_NATIVE_TURN_TIMEOUT_SECONDS` and `DEEP_NATIVE_TURN_TIMEOUT_SECONDS`
are an hour, the short handoffs are 8 to 20 minutes, ADR 0023's budgeted Spark
boundary is 20 minutes, and a budgeted run's remaining step clock can be
shorter than all of them. Beneath all of that sat a hard refusal in each
launcher: `timeout_seconds` had to be an integer from 1 to 3,600. An hour was
not a policy anyone had chosen for a particular run — it was the ceiling of
what the adapters would accept.

ADR 0049 already removed the wall clock for token-budget products, but only for
Codex, and only through `ProductTokenBudget.turn_timeout_seconds` returning
`None`. Claude Code and Grok Build runs had no equivalent: a Make turn on a
busy host that needed 70 minutes could not be given 70 minutes, and two
timeouts in a row ended the command. The operator had no way to say how long a
turn may take, and the only workaround — switching Manager runtime — is frozen
for the life of a run.

## Decision

Add one CLI flag, `--turn-minutes`, on `workshop wish`, `workshop start` and
`workshop resume`. It takes an exact number of minutes, or `none` to run with
no Workshop wall clock at all. It is the operator's boundary and it outranks
every host-side default and clamp. Raise the shared launcher ceiling to
`MAX_NATIVE_TURN_SECONDS` (6 hours) so a longer boundary is expressible, and
teach the Claude and Grok adapters the untimed path Codex already had.

## Consequences

- **Defaults do not move.** `DEFAULT_CODEX_TIMEOUT_SECONDS`,
  `DEFAULT_CLAUDE_TIMEOUT_SECONDS`, `DEFAULT_GROK_TIMEOUT_SECONDS`, both
  `*_NATIVE_TURN_TIMEOUT_SECONDS` constants and `SPARK_BUDGETED_TURN_SECONDS`
  are unchanged. A run without the flag behaves exactly as it did, including
  every frozen older run on resume. Only the ceiling on what may be *requested*
  moved, from one hour to six.
- **`MAX_NATIVE_TURN_SECONDS` is the single ceiling.** It lives in
  `runtime/managers.py`, which every adapter already imports, because
  `src/workshop/runtime/` may not import `workshop.workflow`. `budgets.py` no
  longer carries a duplicate literal: `MAX_TURN_SECONDS` is now derived as
  `STEP_BUDGET_SECONDS // 2`, which is the invariant its comment always
  described — a step must afford two full turns — and which still evaluates to
  the same 3,600.
- **The boundary outranks all three host clamps.** `_budgeted_turn_launcher`
  applies the override instead of `min(remaining, frozen ceiling)` and instead
  of ADR 0023's 20-minute Spark clamp. Without this the flag would be accepted
  and silently do nothing on exactly the budgeted runs most likely to need it.
  The budget clocks keep accounting for what a turn spends; they no longer cut
  it short.
- **An untimed run still needs a bound.** `--turn-minutes none` removes the
  Workshop wall clock only. Codex keeps its existing refusal to run untimed
  without a token-budget observer, so an untimed Codex turn is still bounded by
  observed tokens. Claude and Grok have no token accounting, so an untimed turn
  there is bounded by nothing Workshop owns. The flag's help says so.
- **The boundary is frozen per run, and rebindable on resume.** It is an
  optional `turn_seconds` checkpoint field — absent means frozen policy, an
  integer means that many seconds, `null` means untimed. Absence keeps every
  historical checkpoint valid with no schema bump, in the same way `manager_id`
  and `needs` were added. `AgentRun.rebind_turn_boundary` re-selects it on an
  unfinished run without touching stage, status, artifacts or history, so an
  operator can rescue a run that keeps timing out instead of restarting it.
- **No gate, review, round or token allowance changes.** This is a wall clock
  and nothing else. Make keeps its own engineering checks and review policy.
