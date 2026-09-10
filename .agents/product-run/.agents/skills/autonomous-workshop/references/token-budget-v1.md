# Product token budget v1

The Codex host enforces one input-plus-output token allowance for the entire
product, default thirty million. Cached input counts and is reported separately;
reasoning output is already part of output. Children, retries and resumes share
the allowance. Explicit resume never resets usage. The host may explicitly
authorize a different total limit; only the host changes the private budget.

This is the sole Workshop execution budget, superseding aggregate host clocks,
native-turn counts, lifecycle-round limits and proposal retry caps. It does not
replace Make's frozen engineering checks or internal review allowance; current
Make tools permit an initial independent review and three repair-and-rereview
cycles. There is no twenty-minute split or one-hour host execution watchdog.
Continue evidence-driven work within the token allowance and Make's own protocol.
Valid pending initial usage has no elapsed-time limit; lost or inconsistent
observed accounting stops work. Usage covers completed
requests in discovered native root/child records; in-flight requests can
overshoot a limit. This is neither an exact billing limit nor permission to
drop required evidence. Every existing finalizer and product gate still applies.

Finish the same product from its existing artifacts. Report concrete failed
checks and the repair performed; do not restart broad exploration on resume.
Other Manager adapters retain their frozen policies until equivalent measured
usage enforcement is implemented.
