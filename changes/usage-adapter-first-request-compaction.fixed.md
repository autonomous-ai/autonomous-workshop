- The native token-usage adapter (`workshop.runtime.codex_usage`) no longer
  stops a run when a saturated thread compacts on the first request of a new
  task. Codex charges that compaction to the response ledger and then emits a
  post-compaction `token_count` whose `last_token_usage` counters are all zero
  and whose `total_token_usage` still excludes the compaction spend. The
  adapter already tolerated that shape, but only against a notification
  covered earlier *in the same task*; a task that opens by compacting has
  none, so the check fell through to the strict path, saw its only uncovered
  response was the compaction, and killed the session (seen on a Wren Coil
  Spark run at 30.1M of a 200M cap: Make attempt 2 spent 215 of its 219
  seconds compacting a 22.9M-token root thread, then died with no
  `turn.completed`, and every later resume replayed the same record).
- The covered snapshot now survives the task boundary, because these counters
  are process cumulative rather than task scoped. The in-task signature is
  still dropped, so an ordinary first-in-task notification must prove
  continuation or a process reset exactly as before. A restored baseline
  cannot match the carried snapshot, a compaction in an earlier task still
  authorizes nothing, a non-zero `last_token_usage` still fails closed, and
  the compaction must remain the current task's only uncovered response.
- Offline replay of the affected run's rollouts recovers 30,339,216 tokens,
  charging the 215,285-token compaction request once, without changing run
  state or resuming work.
