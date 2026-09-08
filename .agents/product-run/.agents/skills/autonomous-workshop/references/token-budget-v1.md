# Product token budget v1

The Codex host enforces one input-plus-output token allowance for the entire
product, default thirty million (30,000,000). Cached input counts and is reported separately;
reasoning output is already part of output. Children, retries and resumes share
the allowance. Explicit resume never resets usage. The host may explicitly
authorize a different total limit; only the host changes the private budget.

This supersedes aggregate clocks and native-turn counts. The routine twenty-
minute split is removed for this capability; every native turn, in every
stage and for Spark as well as Forge and Quest, launches with one 60-minute
emergency execution watchdog. The frozen economics profile's per-stage minute
figures (20/10/16/15/30 for deep runs, 20 for Spark) and its "at most eight
turns per invocation" cap are superseded: they are pacing targets only, and the
host no longer cuts a turn at them. The same profile's per-stage reasoning
levels are also shadowed by the one Wish-wide effort frozen in `MANAGER.json`.
Automatic context compaction (64k Spark, 256k deep) still applies. Missing initial usage has a bounded startup grace period,
and lost or inconsistent observed accounting stops work. Usage covers completed
requests in discovered native root/child records; in-flight requests can
overshoot a limit. This is neither an exact billing limit nor permission to
drop required evidence. Every existing finalizer and product gate still applies.

Finish the same product from its existing artifacts. Report concrete failed
checks and the repair performed; do not restart broad exploration on resume.
Other Manager adapters retain their frozen policies until equivalent measured
usage enforcement is implemented.
