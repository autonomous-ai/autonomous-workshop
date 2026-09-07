# Product token budget v1

The Codex host enforces one input-plus-output token allowance for the entire
product, default ten million. Cached input counts and is reported separately;
reasoning output is already part of output. Children, retries and resumes share
the allowance. Explicit resume never resets usage. The host may explicitly
authorize a different total limit; only the host changes the private budget.

This supersedes aggregate clocks and native-turn counts. The routine twenty-
minute split is removed for this capability; one hour remains an emergency
execution watchdog. Missing initial usage has a bounded startup grace period,
and lost or inconsistent observed accounting stops work. Usage covers completed
requests in discovered native root/child records; in-flight requests can
overshoot a limit. This is neither an exact billing limit nor permission to
drop required evidence. Every existing finalizer and product gate still applies.

Finish the same product from its existing artifacts. Report concrete failed
checks and the repair performed; do not restart broad exploration on resume.
Other Manager adapters retain their frozen policies until equivalent measured
usage enforcement is implemented.
