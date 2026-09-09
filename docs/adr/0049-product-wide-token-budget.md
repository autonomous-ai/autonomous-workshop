# ADR 0049: Product-wide native token budgets

- Status: Implemented; one live Spark acceptance passed
- Date: 2026-09-07

New Codex products freeze `token-budget-v1.md`. `workshop wish` and each product
created by `workshop start` default to `--max-tokens 30000000`. The allowance
includes every enabled stage, revision, native child and explicit resume. It
does not include the separate daydream selection loop. Input plus output is
counted, including cached input once and reasoning as part of output. No
pricing table or dollar estimate participates in enforcement.

The default was raised from 10M to 30M on 2026-09-07 after Crosscurrent's
verified digital package used 17,724,704 tokens before publication. This gives
complex products repair headroom; it is a ceiling, not a target. Existing runs
retain their persisted limits, including explicit 10M and 100M runs, unless
the operator explicitly changes the total cap on resume.

`workshop resume ID --max-tokens N` sets the total allowance, not an increment
or reset. Supported older persistent-budget products may adopt it explicitly
only when their complete observed native history can be recovered. Previous
accounting remains preserved. Other runtimes retain their frozen policies.

The trusted host reads bounded native rollout records using a compatibility
adapter validated specifically for Codex 0.153.4. It binds root identity and
workspace to private host state, follows native parent ancestry, deduplicates
cumulative notifications and sums explicit task resets across process resumes.
Continued tasks in the same process, including native child follow-ups, retain
cumulative counters. At each task boundary, the adapter accepts only a reset
whose cumulative counters equal the latest request, or continuation whose
counters exactly equal the previous observation plus the latest request for
every counter. It preserves prior consumption in either case.
This case was missed by the first acceptance: Crosscurrent stopped when Leo
received a follow-up task. Regression tests cover child follow-ups, subsequent
process resets, duplicate notifications, and unexplained boundary counters.
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

Crosscurrent subsequently completed Spark/Codex/Astra/high with an explicit
100M cap and 17,724,704 observed tokens across the root and four native
descendants. The follow-up accounting fix preserved the same root session and
all prior usage. Make and Release passed independent host CAD verification;
the six-page manual passed PDF checks. After the operator configured Dee as
the shared host publisher, an effect-only resume reused the existing package
and completed verified public readback on 2026-09-07. No additional native
turn was needed for publication. The sanitized archive is
`toys/leo-crosscurrent/`; credentials and raw run state remain private. Its
rules simulations do not constitute physical testing or proof of family fun.

## Large native compaction records (2026-09-08)

The normal 4 MiB record bound also rejected a valid native `compacted` record
that copied a large history. The host then stopped on lost accounting while
still below the token allowance. The adapter now validates oversized compaction
records in bounded chunks and retains only their type marker. Embedded historic
token notifications are not new consumption. Subsequent top-level usage records
remain subject to the existing counter, ancestry and task-boundary checks.

The 128 MiB file bound and 4 MiB bound for other record types remain. The streaming
validator rejects malformed JSON, duplicate keys and unsupported record kinds,
and bounds nesting to 64, keys per object to 4096, encoded key size to 4096 bytes,
and numeric/retained type atoms to 128 bytes. A trailing partial append whose type
is already known to be `compacted` preserves only earlier completed usage. These bounds keep unexpected formats
fail-closed; they are not a claim of arbitrary-length session support.

Synthetic tests cover large root and descendant compactions, duplicated historic
usage, partial appends, corrupt records, persistent budget reload and unchanged
cap enforcement. Private retained telemetry was recovered through the new reader
without changing its aggregate counters. The failed native attempt is preserved;
this recovery does not establish product completion or repair quality.


## Bound discovery by metadata (2026-09-09)

Product ancestry discovery reads one complete metadata record, bounded to
4 MiB, from each candidate. It does not apply the selected rollout's 128 MiB
body limit before membership is known. Previously an unrelated session above
that limit could stop accounting for a smaller product even though none of
the unrelated body was needed. A bounded identity read removes that coupling.

The root and every discovered descendant retain the full 128 MiB file bound,
counter checks, workspace binding and ancestry requirements. Malformed,
partial, oversized or duplicate-key identities remain unavailable; ambiguous
identities and linked paths are not skipped. Discovery still has its candidate
count bound. This does not support arbitrarily large selected product sessions.

Regression controls cover an oversized unrelated body, unchanged root and child
file rejection, metadata framing and the exact metadata byte boundary. An
offline replay against retained product usage recovered the same aggregate
counters after excluding an unrelated large body from discovery's size check.
The failed attempt remains failed; accounting recovery is not Make completion.
