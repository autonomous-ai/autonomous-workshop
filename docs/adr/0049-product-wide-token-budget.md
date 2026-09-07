# ADR 0049: Product-wide native token budgets

- Status: Implemented; live acceptance pending
- Date: 2026-09-07

New Codex products freeze `token-budget-v1.md`. `workshop wish` and each product
created by `workshop start` default to `--max-tokens 10000000`. The allowance
includes every enabled stage, revision, native child and explicit resume. It
does not include the separate daydream selection loop. Input plus output is
counted, including cached input once and reasoning as part of output. No
pricing table or dollar estimate participates in enforcement.

`workshop resume ID --max-tokens N` sets the total allowance, not an increment
or reset. Supported older persistent-budget products may adopt it explicitly
only when their complete observed native history can be recovered. Previous
accounting remains preserved. Other runtimes retain their frozen policies.

The trusted host reads bounded native rollout records using a compatibility
adapter validated specifically for Codex 0.153.4. It binds root identity and
workspace to private host state, follows native parent ancestry, deduplicates
cumulative notifications and sums explicit task resets across process resumes.
Unrelated conversation payloads are not read. Unsupported formats, counter
regression, disappearing usage and ambiguous history fail closed. Native
rollouts are not a stable public API; a future supported app-server usage
adapter can replace this bridge with the same accounting contract.

The host samples completed-request usage while the native process runs and
persists each observation. A new thread may have up to three minutes to report
its first usage. Pending usage is explicitly marked, not presented as complete
zero-cost execution. Crossing the cap or losing established accounting stops
the supervised native process. In-flight requests can overshoot the allowance;
this is an observed-usage stop, not provider-side hard preauthorization.

The ordinary twenty-minute split and aggregate time/turn limits no longer
govern marked token-budget products. A one-hour per-launch emergency watchdog
remains. Revision/review limits and all deterministic engineering, artifact,
assembly and publication gates remain unchanged. Python observes, budgets and
supervises; it does not select designs, judge quality or implement repairs.

Peekabud's recovered root-plus-child completed requests total 4,721,922 tokens
across two native tasks. It did not finish Make and remains stopped. Software
tests and recovered usage are not evidence of live product completion.

Validation on 2026-09-07: CLI/accounting/frozen-budget checks passed 124 tests;
host/accounting checks passed 110 tests, with a separate cap-and-resume host
test also passing. Native runtime checks passed 76 tests with one skipped.
The updated product-run skill passed its validator. The requested new
Spark/Codex/Astra/medium/10M trial was prepared as a one-piece Soren balancing
toy. Automatic approval review initially rejected the launch pending explicit
publication approval. After the user granted it, the normal CLI started
`wish-20260907-033621-fa3c403c`; both root and Soren usage are being observed.
Live Make/Release acceptance remains in progress; no publication is claimed.
