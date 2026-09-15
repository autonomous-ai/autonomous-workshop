# ADR 0067: Adopt corrected geometry inspection on operator resume

- Date: 2026-09-15
- Status: Accepted
- Adds a one-time carried-CAD refresh on explicit resume; preserves the
  lifecycle, budgets, review policy and Spark acceptance boundary.

## Problem and evidence

A prolonged geometry-inspection delay was reported, but the affected model,
frozen tools and live process were unavailable. Independently, current source
and real-kernel tests establish that
the shape-taking `BRepAlgoAPI_Check` constructor performs the self-intersection
check, and an additional `Perform()` repeats it. Inspection batch stderr was
also buffered by the final verifier until the batch finished. The tool
correction removes that duplicate call and exposes per-request progress without
changing gate flags or result decoding.

Updating installed tools alone leaves existing run-local copies frozen.
ADR 0066 refreshes old runs missing `MAKE-OPTIONS.json`, but runs that already
carry this option can still retain the duplicated check. An operator resuming
the interrupted Wish needs the corrected tools in the same saved session.

## Decision

On explicit `workshop resume`, the host checks active/waiting runs carrying CAD
for the `workshop-geometry-inspection-v1` marker in the hash-bound
`.agents/skills/cad/references/inspection-and-validation.md`. If absent, the host
refreshes the complete carried CAD skill from the current installation through
the existing recorded tool-refresh boundary. This is a narrow exception to
frozen tool retention, not an upgrade on every continuation. It does not
refresh other domain skills, lifecycle instructions or review finalizers.
ADR 0066's separate motion migration continues to apply where needed.

The exact run opens under its mutation lock and immutable-input verification.
The host records the changed paths and checkpoint, then rebinds the saved
native session's constitution hash. Only then does it append a migration
completion record. An interrupted refresh without completion is retried even
when the marker has already been installed. Completion is ordered in the
private ledger; a changed motion choice on retry can move the checkpoint
without creating a second migration. Native agents cannot edit these tools.

The Wish, session id, model configuration, budget and consumed usage, accepted
artifacts, stage and revision history are preserved. The Manager receives a
short instruction to keep existing product work and finish missing checks.
An interrupted check supplies no verdict. A pending unaccepted Make proposal
is quarantined byte-for-byte and must be finalized under the new checkpoint;
it is not rebound as passing evidence. Pending output reconciliation follows
only consecutive host-recorded corrections, as for the motion migration.

New runs already carry the marker. Once migration completes, later resumes
retain the materialized CAD tree; explicit `--refresh-tools` remains available
for subsequent corrections. Read-only status, terminal runs and runs without
CAD do not receive this migration. No running process is modified in place.
The corrected Workshop installation must be present on the operator's machine.

The full installed inventory on the baseline revision contains 257 inputs,
exceeding the previous 256-file host allowance. A separate correction raises
that resource allowance to 512 so initialization and carried-tool refresh can
fit the installed roster. The 4 MiB aggregate input and 256 KiB checkpoint byte
limits remain enforced. Tests cover materializing the complete installed
inventory, reopening and refreshing at the count limit, and refusing an
oversized creation or refresh before mutation.
The existing 64 KiB correction-record allowance is also checked before tool
writes; rejecting a large change list must not leave new tools and a moved
checkpoint without the correction evidence needed for session rebinding.

## Validation and limits

Tests materialize an older tool tree with motion options already present,
exercise plain CLI resume, and use the actual native session rebind with a
deterministic launcher. Coverage includes saved work and budget preservation,
same-session continuation, idempotency, interruption before/after session
rebinding and during completion recording, a changed motion choice on retry,
pending Make output, immutable-tool tampering and read-only/terminal paths.

Real geometry measurements and gate parity are recorded in the CAD skill
provenance. Deterministic launcher tests do not execute a new native Wish.
Neither these tests nor archived-model replay establish the cause or resolution
of the reported delay. Per-request progress cannot expose progress inside one
long-running kernel operation, and this migration adds no inspection timeout.
