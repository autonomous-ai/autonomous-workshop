# ADR 0049: Product-wide native token budgets

- Status: Implemented; one live Spark acceptance passed
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

Repair note (2026-09-08): token-budget runs stop the current invocation after
three consecutive normally returned native turns without `agent-outcome.json`,
even below the cap. This bounds finalizer retry storms; it does not infer
progress from prose or file timestamps. Explicit resume preserves the session
and charged usage and starts a fresh three-return window. Legacy clock and
turn-budget runs retain their existing behavior. New finalizers accept alternate
absolute Python aliases only when they resolve to the same host executable;
non-normalized requests and different executables remain rejected. Frozen
run-local finalizer bytes are not rewritten on resume.

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
`wish-20260907-033621-fa3c403c` and completed authenticated publication of
[Quiet Arc](https://www.autonomous.ai/toys/product/quiet-arc) on 2026-09-07.

The host fresh rebuild exposed a genuine harness defect: the overhang report
included its working-directory path and failed exact comparison after
relocation, although all source, geometry and measurements were identical.
The builder paused paid execution, reproduced the mismatch, and added a narrow
comparison of the two path-bearing metadata lines. All options, numeric
results, PASS/FAIL status, region data, source, geometry and file modes remain
exact; the report is not exempted as wholly volatile. The CAD gate suite passed
41 tests plus 22 subtests, including regression and failure paths. The same
product then resumed through the normal CLI and passed Make and Release.

The run used 6,893,962 observed input-plus-output tokens (6,525,312 cached input)
across its root and four native descendants, within the unchanged 10,000,000
cap. Four native launches shared one root session; the builder interruption
did not reset consumption. Wish-to-public-readback time was approximately
41 minutes including diagnosis and repair. The normal resume command exited
zero with `status=complete`, `publication.status=public` and `verified=true`.
Legacy terminal-only telemetry remains separately labelled partial and is not
the product-wide budget total. The sanitized public archive is under
`toys/soren-voss-quiet-arc/`; private workspaces and host state remain private.

This is one successful live digital-product acceptance, not a live matrix of
every CLI combination. Spark truthfully records Playtest not run. The object
has not been physically printed, tested, manufactured or delivered.
