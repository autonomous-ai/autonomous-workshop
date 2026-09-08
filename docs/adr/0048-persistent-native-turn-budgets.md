# ADR 0048: Persistent native-turn budgets

- Status: Superseded by ADR 0049
- Date: 2026-09-07

Superseded in part: ADR 0049 replaces these turn counts for new runs; frozen runs that materialized this policy keep it.

Peekabud exhausted two twenty-minute native turns without finishing Make.
Neither turn reported complete terminal token usage. ADR 0049 subsequently
recovered usage from version-bound native rollouts. The earlier forty-minute aggregate deadline
was not calibrated against a completed live product.

New Codex runs freeze six native launches per stage and twelve per product.
Each launch is reserved durably before execution and is never refunded, even
after a crash, timeout or error. Resumes and backward stage edges do not reset
counts. Frozen per-launch timeouts remain watchdogs; Spark retains twenty
minutes. This deliberately allows more work than ADR 0047's aggregate clocks,
but is not a token or dollar ceiling. Lifecycle revision/review limits and
all deterministic gates remain separate and unchanged.

Older runs keep their frozen policy unless the operator explicitly requests
`workshop resume <id> --turn-budget`. This narrow migration accepts only an
active first creative stage with an existing persistent clock budget and exact
host progress proving all prior turns belong to that stage. Missing, ambiguous
or out-of-range history fails closed. The atomic private budget replacement
retains the old clock record and seeds all previous turns. Repeating the flag
does not grant more turns. Frozen session identity and product-run assets are
unchanged; the host supplies the adopted policy in the next native prompt.

Software tests do not establish that the extended product will finish. The
first live trial remains unfinished; preserve its CAD instead of starting over.
