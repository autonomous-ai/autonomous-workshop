# ADR 0049: Product-wide native token budgets

- Status: Implemented; one live Spark acceptance passed
- Date: 2026-09-07

New Codex products freeze `token-budget-v1.md`. `workshop wish` and each product
created by `workshop start` default to `--max-tokens 30000000`. The allowance
includes every enabled stage, revision, native child and explicit resume. It
does not include the separate daydream selection loop. Input plus output is
counted, including cached input once and reasoning as part of output. No
pricing table or dollar estimate participates in enforcement.

On 2026-09-09 the explicitly selectable maximum was raised to 200,000,000
tokens and later to 1,000,000,000. The default remains 30,000,000 and existing
saved caps do not change. The cap is a guard rail against a runaway product, not
a quota, and it should not be the reason a healthy product cannot continue. The
bound and both of its refusal messages derive from `MAX_PRODUCT_TOKENS`, so
raising it again is a one-line change that cannot leave a stale figure behind.

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
adapter introduced and live-validated with Codex 0.153.4. On 2026-09-10 the
launcher gate was widened to 0.153.4 or newer; the reader continues to validate
the exact identity, task-boundary, model, counter and record shapes, so an
incompatible newer format fails closed instead of becoming zero usage. It binds
root identity and workspace to private host state, follows native parent ancestry, deduplicates
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
persists each observation. A valid pending request has no first-report timer;
the former three-minute grace was removed on 2026-09-10. Pending usage is
explicitly marked, not presented as complete zero-cost execution. Completed
root-turn input/output usage is reconciled with the native terminal event
before accepting a proposal or performing an effect. A private durable record
preserves unresolved completed-turn accounting across resume. Canceled or
in-flight descendants remain pending rather than becoming fabricated completed
usage. Crossing the cap or losing established accounting stops
the supervised native process. In-flight requests can overshoot the allowance;
this is an observed-usage stop, not provider-side hard preauthorization.

The ordinary twenty-minute split and aggregate time/turn limits no longer
govern marked token-budget products. On 2026-09-09 the one-hour per-launch
watchdog was removed, together with native-turn, proposal-rejection and
lifecycle-round host spending caps. An earlier positive-review-count change
was superseded when the team's Make changes were integrated: current Make keeps
its own four-review allowance under [ADR 0060](0060-make-round-visual-feedback-and-three-repairs.md).
Token budgeting does not remove Make-internal checks or review policy.
Existing materialized tools remain frozen
unless explicitly updated with `resume --refresh-tools`; this host operation
records exact allowlisted review-tool changes and preserves the session and
token ledger, including recovery after an interrupted rebind. Token-budget
host CAD verification has no wall-clock deadline; cancellation still reaps its
subprocess tree. Accounting accepts more than 32 ancestry-bound sessions while
retaining input-size and identity checks. Temporary provider service overloads
are eligible for same-session recovery with backoff. Other
host execution budget changes apply on the next launch, not inside an already
running process. Deterministic engineering, artifact,
assembly and publication gates were unchanged by this budget decision; the later
Spark-only orchestration changes are recorded in [ADR 0061](0061-spark-make-owned-verification.md).
Python observes, budgets and
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

## Large native visual-tool records (2026-09-13)

A blind-review subagent can return several rendered images in one
`response_item` / `custom_tool_call_output` record. Base64 image data can push
that otherwise valid record beyond the ordinary 4 MiB line bound and stop a run
after the creative work has finished. The streaming validator now accepts that
exact outer and payload type pair, validates the complete JSON with the same
depth, key, atom, duplicate-key and UTF-8 bounds, and discards the body. The
record cannot contribute usage; later top-level token notifications remain the
only counter source. Other oversized `response_item` payload types and all
other unsupported oversized record kinds still fail closed.

## Replayed follow-up usage snapshots (2026-09-14)

Codex 0.154.0 can begin a subagent follow-up by repeating the preceding task's
final cumulative and last-request counters, then complete without fresh usage.
The adapter previously rejected this snapshot as an ambiguous task baseline.
It now ignores an exact counter replay under the same model when cumulative
usage differs from last-request usage. The first fresh record still must prove
either cumulative continuation or a reset; duplicate snapshots do not consume
that pending boundary or advance the observation timestamp.

`total == last` retains its reset meaning even when it matches an earlier
single-request task. Changed last-request counters, unexplained increments,
regressions, and a replay under a different model remain fail-closed. Synthetic
tests cover root and child tasks, duplicate-only follow-ups, subsequent
continuation and reset, and unchanged product-budget observations. Offline
replay recovered the affected product's same 9,425,297-token observation across
three threads. No private records were edited and no native session resumed;
this accounting recovery is not evidence that Make completed.

## Resume terminal-usage reconciliation (2026-09-13)

Supported Codex resume paths have emitted `turn.completed` usage in two forms:
request-local counters and cumulative root-thread counters. The rollout ledger
remains the accounting authority. Reconciliation now accepts either exact
monotonic relationship: observed root usage must advance beyond the saved
baseline and must cover either the baseline plus the terminal delta or the
terminal cumulative counters themselves. Missing, stale, regressing or
otherwise inconsistent terminal usage still blocks the proposal.


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

## Explicit one-billion-token cap retained (2026-09-14)

The operator-authorized upper bound is 1,000,000,000 tokens, preserving saved
Cratercade usage and its previously selected limit across the team sync. The
default remains 30,000,000; raising the maximum does not reset any usage or
change another run's saved limit. Values above the maximum remain refused.
