- **`--turn-minutes` lets an operator choose how long one native turn may run.**
  It takes an exact number of minutes, or `none` to run with no Workshop wall
  clock at all, and is available on `workshop wish`, `workshop start` and
  `workshop resume`. Before this, every turn was bounded by whichever frozen
  policy the run materialized, and beneath all of them sat a launcher refusal of
  anything over 3,600 seconds — so a Make turn that genuinely needed 70 minutes
  on a busy host could not be given them, and two timeouts in a row ended the
  command. See ADR 0064.
- **No default moved.** Every `DEFAULT_*_TIMEOUT_SECONDS`, both
  `*_NATIVE_TURN_TIMEOUT_SECONDS` constants and `SPARK_BUDGETED_TURN_SECONDS`
  are unchanged, so a run without the flag — including every frozen older run on
  resume — behaves exactly as it did. Only the ceiling on what may be requested
  moved, from one hour to six (`MAX_NATIVE_TURN_SECONDS`).
- **The selected boundary outranks all three host clamps.** A budgeted run's
  remaining step clock, the launcher's own frozen ceiling and ADR 0023's
  20-minute budgeted-Spark clamp each used to silently shrink a turn. Without
  this the flag would read as accepted and do nothing on exactly the runs most
  likely to need it. The budget clocks still account for what a turn spends.
- **Claude Code and Grok Build learned the untimed path Codex already had.**
  Both adapters now accept `timeout_seconds=None` and wait on the process
  without arming a deadline, rather than with a very large one. Codex keeps its
  refusal to run untimed without a token-budget observer, so an untimed Codex
  turn is still bounded by observed tokens; an untimed Claude or Grok turn is
  bounded by nothing Workshop owns, and the flag's help says so.
- **The boundary is frozen per run and rebindable on an unfinished one.** It is
  an optional `turn_seconds` checkpoint field, so historical checkpoints stay
  valid with no schema bump, and `AgentRun.rebind_turn_boundary` re-selects it
  without touching stage, status, sealed artifacts or history — an operator can
  rescue a run that keeps timing out instead of restarting it.
- `budgets.MAX_TURN_SECONDS` no longer duplicates the launcher literal. It is
  derived as `STEP_BUDGET_SECONDS // 2`, the invariant its comment always
  described, and still evaluates to the same 3,600.
