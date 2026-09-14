- The native token-usage adapter (`workshop.runtime.codex_usage`) no longer
  stops a run when an inter-agent hand-off repeats the previous `token_count`
  notification verbatim. Codex emits one when a `NEW_TASK` message reaches a
  subagent before that task has issued its first request: the record restates
  the prior task's `total_token_usage` *and* `last_token_usage` unchanged, so
  it is neither a process reset (`total == last`) nor a continuation
  (`total == previous total + last`), and the adapter called it "ambiguous" and
  killed the session (seen on the Harley Heritage Spark run at 2.67M of a 30M
  cap, 397s into Make, right after the design subagent's first task completed).
  An exact repeat of both counter sets is now read as the zero-delta echo it
  is: it adds no usage and holds the task boundary open, so the next record
  still has to establish the baseline. A repeat of only one of the two counter
  sets stays ambiguous, and every other shape still fails closed.
