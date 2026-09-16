# ADR 0068: Cancellable geometry and disclosed unverified handoff

- Status: Implemented; original reported machine incident remains unverified
- Date: 2026-09-16
- Supersedes: ADR 0067's v1 migration and absence of an inspection deadline;
  ADR 0063's requirement that every Forge/Quest handoff be print-ready, only for
  the explicit unverified-prototype tier described here

## Decision

An unfinished geometry calculation must not keep a Wish waiting indefinitely.
There are three outcomes: passed, measured failure, and unverified. Only the
third may continue as an explicitly unverified prototype. A clash, invalid
solid, malformed request, missing STEP artifact, changed sealed artifact, or
failed non-geometry gate still requires repair. Interrupted work never creates
positive geometry or print-readiness evidence.

Inspection executes in an owned, disposable worker process. The parent enforces
a 600-second batch allowance and a 60-second native measurement allowance,
independently of Python threads or kernel cooperation. Build/loading work uses
the batch allowance. Cancellation kills and reaps the owned process group.
Completed measurements and measured failures are reported over a separate pipe;
heartbeats cannot renew the deadline. A failure found before interruption
remains a failure. `inspect` uses exit 3 for unverified, 2 for failure, and 0
for success; batch JSONL carries the same per-request exit code.

`verify_project` shares a finite analysis allowance across motion, inspection
and print checks. Make rounds also bound their analysis group and reap child
process groups. Generation and other commands are bounded but a missing output
is not waived. `WORKSHOP_GEOMETRY_TIMEOUT` and
`WORKSHOP_GEOMETRY_OPERATION_TIMEOUT` accept finite positive seconds up to
86400. These are deterministic tool boundaries, not new Wish/token/Goal caps.
Warm requests have a total deadline unaffected by heartbeat messages; expiry
returns 124 without restarting the same job cold. An independent watchdog can
kill its own daemon parent even while native code holds the GIL.

## Reuse and cost

Adjacent refs/validity/interference requests share one source build. The
in-memory scene is invalidated by changed input bytes or directory membership,
including captured source dependencies; a large/unreadable input tree disables
reuse. Only one scene is retained. No scene is reused across worker processes.

Completed validity and intersection measurements are stored atomically under
`__cadgen__/inspection-v2`. Keys bind exact binary B-rep content, check options,
Python/OCP identity and geometry-tool source bytes. Proper rigid placements
share validity measurements; interference retains exact world placement.
Unknown results are never cached. Cache corruption is a miss and cache symlinks
are refused. `--fresh` removes generation caches while preserving these
content-bound measurements. Host verification disables disk cache reads/writes.
Final sealing still removes working caches. Native checking must preserve the
shared input geometry. Collision candidates use a sweep over bounding boxes;
all overlapping candidate pairs still receive the same Boolean test.

## Final contract and publication

A successful continuation with incomplete checks writes **UNVERIFIED** in the
final verification record and a structured `geometry-inspection.json` binding
that record's exact SHA-256. Records with measured failures cannot enter this
path. The frozen Make finalizer validates JSON data without executing a helper
from the run workspace. Before sealing, it writes `GEOMETRY-NOTES.md`, appends
the same details to the README, and sets product status `geometry-unverified`,
`print_ready_claim: false`, and a mandatory public limitation. Existing artifact,
source, signature/visual review and external-effect boundaries still apply.

Make rounds label incomplete print/motion measurements UNVERIFIED and can
continue to visual review. Unknown print measurements supply no passing report;
the existing empty signature-review `print_gate_sha256s` no-claim case applies.
The final verifier still records the incomplete geometry explicitly. Harness
reports `ready: false` with a warning, even though the continuation exits zero.

For this tier the Forge/Quest host validates the exact sealed disclosure rather
than retrying the interrupted kernel. Its receipt says `passed: false`,
`failure_code: geometry-unverified`, `print_ready_eligible: false`, with command
`<host> validate-geometry-disclosure`. This is acceptance of a disclosed
prototype, not a geometry pass. Ordinary tiers retain independent verification;
a host replay that becomes unverified requires the product to be finalized
again with its disclosure. Spark retains its existing Make-owned acceptance.
Every Release carrier retains the exact geometry notes and public limitation.
No additional authorization to print or manufacture is created.

## Resume

Explicit resume installs `workshop-geometry-inspection-v2` once for unfinished
CAD runs, including those already migrated to v1. The host refreshes CAD,
Make-round, and only the product-run finalizer through the recorded immutable
input correction mechanism. Lifecycle, review allowance, session id, sources,
sealed work and consumed token budget remain unchanged. Completion follows
session rebinding; interrupted migrations retry safely. Tool updates are not
injected into an already-running process. The updated installation must be
present on the operator's machine.

## Validation boundary

Tests cover forced native hangs, heartbeat deadlines, independent watchdogs,
retention of earlier failures, exact-input reuse and invalidation, spatial-sweep
parity, source-build reuse, final document sealing, host receipts, Release and
same-session resume. Real complex-assembly replay is separate from mocked host
and lifecycle tests. Neither is evidence of a new native Wish, physical
manufacture, or the cause/resolution of the original remote-machine incident.
