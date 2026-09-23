# ADR 0070: A redundant final sweep reuses its verdict and exits zero

- Status: Proposed
- Date: 2026-09-22
- Owners: CAD skill (`verify_project`), Make round contract
- Relates to: ADR 0068 (content-bound measurement cache, host re-derivation),
  ADR 0069 (corrections carry byte-identical parts forward), ADR 0061
  (Make-owned verification)

## Context

`references/make.md` step 8 says to run the integrated final verifier once and
not to use it as an iteration loop. Agents use it as an iteration loop anyway.
The Antisol correction measured in ADR 0069 called it 33 times for 2,410
seconds; an earlier run spent 42m40s on four full sweeps that all passed. The
instruction is not ambiguous, so restating it more firmly is not a remedy — it
has already failed in the field.

The waste is specifically re-verification of a project that has not changed
since the last verdict. ADR 0068 already established that measurements bind to
exact content — B-rep bytes, check options, Python/OCP identity, tool source
bytes — and that the host disables cache reads and writes when it re-derives
the archive. The principle needed here is that one, applied to the sweep as a
whole rather than to individual measurements.

## Decision

When `verify_project` is asked for a full sweep and nothing hash-relevant has
changed since the last recorded verdict for that project, it does not
re-verify. It re-emits the recorded verdict, writes a `status: "reused"` row
with `seconds: 0.0` into `measure/verification-pipeline.md` beside the
preserved prior report, and **exits with the recorded verdict's own exit code**.

A reused PASS therefore exits 0. This is the surprising part and it is
deliberate: refusing with a non-zero exit would convert a wasteful-but-harmless
call on a passing project into a new failure on the critical path. The run that
motivated this ADR passed all four of its redundant sweeps; under a hard
refusal it would have failed four times for doing something that cost only
time. A reused FAIL or UNVERIFIED likewise carries its original exit code, so
reuse never upgrades a verdict.

Hash relevance is the sweep's own input closure: the built STEP bytes for every
part, the verifier's arguments, and the tool source bytes already used as cache
keys under ADR 0068. A changed signature review, a changed README file map, or
any changed argument is a change. When the closure cannot be computed, that is
a miss and the sweep runs in full.

The reuse is a sandbox-side economy only. Sealing is unaffected: the host's
isolated re-derivation continues to run with caches disabled, and remains the
last word on what an archive contains. No second cache-free sweep is added
inside the sandbox, because a sandbox verifying itself twice proves nothing the
host does not already prove once.

## Alternatives considered

**Refuse with a non-zero exit.** The precedent is `verify_project`'s existing
`refuse` path, which leaves an auditable `status: "refused"` row. Rejected for
the verdict-carrying case: it turns wasted time into a run failure on projects
that are passing, which is a worse outcome than the waste.

**Restate the instruction more strongly.** Rejected: it is already
unambiguous and was already ignored.

**Host-side accounting only.** Rejected: it measures a cost that is already
measured and removes none of it.

**Refuse only the second and later consecutive no-change sweep.** Rejected as
needless state: the closure hash answers the same question without tracking
consecutiveness, and the threshold would be arbitrary.

## Consequences

The step-8 instruction stops being load-bearing. It stays in `make.md` as
guidance, but compliance is no longer what protects the run's budget — a
non-compliant agent now pays close to nothing, which is the outcome the
instruction was trying to buy.

The pipeline record gains a category. A reader of
`measure/verification-pipeline.md` will see `reused` rows and must not read
them as verification events; they are evidence that verification was correctly
skipped. Accounting of how often this trips is how we learn whether the
underlying behaviour ever improves.

A verdict can now be reported by a process that did not compute it. The bound
on that is the closure hash: if it is ever wrong — too narrow, or blind to an
input that matters — a stale verdict is reported as current. That failure is
silent by construction, so the closure needs failure-path tests that mutate
each input class and assert a miss, not only tests that assert a hit.
## Compatibility and migration

No option, flag or schema changes. A project with no recorded verdict is a
miss, so the first sweep of every existing run behaves exactly as today.
Frozen runs carrying older tools keep their current behaviour and are not
refreshed for this; the economy is not a correctness fix and does not warrant
the narrow tool-refresh exception ADR 0067 reserves for one.

`--quick`, `--dry-run` and `--no-report` keep their current semantics. Reuse
is not attempted when no report would be written, because the recorded verdict
is what reuse reads.

## Verification

Contract tests: an unchanged project's second sweep records a `reused` row,
re-emits the prior verdict, and exits with the prior exit code; the prior
report survives; a reused FAIL exits non-zero; a reused UNVERIFIED stays
UNVERIFIED.

Failure-path tests, one per input class, each asserting a full re-run rather
than a hit: changed STEP bytes for one part, changed verifier arguments,
changed tool source bytes, changed signature review, changed README file map,
and an uncomputable closure. A test that only proves the hit would let the
closure silently narrow.

Host-side: sealing re-derivation still runs with caches disabled and is
unaffected by any recorded verdict.
