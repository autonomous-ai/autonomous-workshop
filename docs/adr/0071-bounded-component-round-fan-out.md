# ADR 0071: Component rounds fan out, bounded by host width

- Status: Proposed
- Date: 2026-09-22
- Owners: Spark Make (component rounds), CAD skill, Workshop Manager session
- Relates to: ADR 0063 (component-first Make), ADR 0068 (cancellable geometry,
  per-invocation geometry allowance), ADR 0069 (corrections carry byte-identical
  parts forward)

## Context

ADR 0063 requires every printable component to pass an isolated
`make_round --component` loop before any assembled object exists, and the
assembled round refuses to start until they have. `references/make.md` step 2
reads that as a sequence: each component is repaired to a pass, then the next
one starts. Nothing in ADR 0063 requires the sequence. The components are
independent until assembly, write into separate `component-rounds/` subtrees,
and are joined by an existing gate, `--require-component-passes`, which already
verifies both that each component has a passing round and that its built STEP
has not changed since.

The cost is real where the set is large. Fresh `wish` runs carry three or four
components typically and up to nineteen in the tail. ADR 0069 shrank the set
for corrections — a correction now loops only the components it changed — but
did not change the ordering for whatever set remains.

`AGENTS.md` permits this directly: the root session "may use Codex-native
subagents for bounded parallel or specialist work", as children of the one
product-run session. The prohibition at `AGENTS.md:112` is on Python-owned
candidate fan-out and schedulers, which this is not.

## Decision

The Manager runs the component rounds that need a loop concurrently, as
Codex-native subagents under the one product-run session, joined at the
existing `--require-component-passes` gate.

The set is whatever needs rebuilding — every component in a fresh run, only the
changed ones in a correction under ADR 0069, all of them under
`workshop fix --full`. There is no run-type special case: a set of one is a
fan-out of one, which is the serial path.

Width is `max(2, ncpu // 4)`, capped at 4. It is derived at runtime rather than
fixed because the hosts differ by more than six times in core count, and it is
capped at 4 because the common set is three or four components, so extra width
buys nothing on the common case while making the nineteen-component tail
materially riskier.

The width bound exists for a correctness reason, not a politeness one. Under
ADR 0068 each `make_round` invocation holds its own 600-second geometry
allowance, keyed by working directory in a process-local table. cadgen already
spawns up to `ncpu - 1` subprocesses and OCCT runs parallel inside each, so N
concurrent arms oversubscribe by roughly N times, and each arm's own allowance
drains against less completed work. Unbounded width therefore converts a
passing component into an UNVERIFIED one through starvation alone.

Every launched arm runs to its own conclusion. A failure in one says nothing
about the others, and their results are exactly what the repair needs. On
retry, only the failed components rerun; the passing ones are already admitted
by `--require-component-passes` on the strength of a passing round and an
unchanged STEP.

## Alternatives considered

**Widen and raise `WORKSHOP_GEOMETRY_TIMEOUT` to absorb the pressure.**
Rejected outright: it fixes oversubscription by loosening a gate ADR 0068 set
deliberately.

**Cancel sibling arms on first failure.** Rejected: it discards completed work
that the retry would need, to save a resource no other arm is waiting on.

**A fixed width.** Rejected: any constant is wrong on one of the two known
hosts.

**Fan out the blind review or the per-round render work instead.** Rejected:
the critic already runs as a background subagent with the session inside other
calls for 87–88% of the review bracket, and batched rasterisation already took
the render win in 2026-09-21.

## Consequences

Component rounds stop being a readable serial narrative. Interleaved arms make
the transcript harder to follow, and a reader diagnosing a run must attribute
each round to its component rather than to its position in the log.

Reuse does not cross arms. ADR 0068 retains one in-memory scene per worker
process and never shares it across processes, so concurrent arms cannot reuse
each other's builds. Serial rounds in one process could not either, since each
`make_round --component` is already a separate invocation, so nothing is lost.

Wall-clock stops being a stable measure of a component round. A round's
duration now depends on how many siblings were running, which means round
timings are comparable only within a run at the same width. Any timing record
must carry the width that produced it or it will be read wrongly later.

## Compatibility and migration

No option, flag or schema changes, and no change to what a passing component
round means. Frozen runs keep their materialized work order.
`--require-component-passes` is unchanged; this decision relies on the gate
exactly as ADR 0063 specified it.

## Verification

Contract tests: a set of N components yields N passing component rounds and an
assembly round that the gate admits; a set of one behaves identically to the
serial path; width resolves to 2 on a 10-core host and 4 on a 64-core host;
width never exceeds the size of the set.

Failure-path tests: one failing arm does not cancel its siblings and does not
prevent their rounds from being recorded; an assembly attempted while one
component is still failing is refused by `--require-component-passes`; a retry
that reruns only the failed component is admitted; a component whose STEP
changed after its passing round is refused.

Starvation is the risk this ADR bounds, so it needs its own test: a fan-out at
the cap must not produce an UNVERIFIED verdict that the same set produces as
PASS when run serially.
