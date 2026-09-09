- The native token-usage adapter (`workshop.runtime.codex_usage`) no longer
  stops a run when a follow-up task keeps counting from the previous task's
  total. Codex 0.153.4 resets its cumulative counter only on process resume;
  a `followup_task` on a subagent, or the Manager's next turn in the same
  process, continues it, which the adapter had called "ambiguous" and used to
  kill the session (first seen on the pinned Microduck Spark run, 8.5 minutes
  in, at 1.59M of a 10M cap). A task baseline is now either a reset
  (`total == last`) or a continuation (`total == previous total + last`);
  anything else still fails closed.
