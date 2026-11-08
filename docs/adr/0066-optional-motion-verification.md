# ADR 0066: Opt-in Make motion verification

- Date: 2026-09-14
- Status: Accepted
- Supersedes motion requirements for newly created and operator-resumed runs in ADR 0047 and
  ADR 0060 (declared-motion reconciliation); other Make checks remain intact.

## Decision

`workshop wish`, `start`, `fix`, and `resume` accept `--check-motion true|false`, with
false as the default. The host freezes the boolean in read-only root
`MAKE-OPTIONS.json`, covered by the ordinary immutable-input hash manifest.
Each operator resume reselects the boolean with default false, including
previously enabled runs. Explicit domain-tool refresh alone preserves it.
(Superseded for resume by the 2026-11-08 amendment below: an omitted
`--check-motion` now keeps the frozen value.)

Make rounds and the final CAD verifier skip motion sweeps when disabled,
including when a manifest or documented assembly action exists. Coupled-motion
animation generation, reconstruction, and independent motion review are also
optional under this setting, and the Make finalizer does not require them.
A skipped gate is reported as not run/unverified, never as a passing motion
check. Still-image signature review, geometry, fit, and print checks remain.

When enabled, all existing required manifest, sweep, animation and independent
review checks still apply. Tool flags may not contradict a frozen run option.
Standalone tools default off and accept `--check-motion true`. Directly invoking
`check_motion` remains an explicit request to run that diagnostic.

The isolated host verifier resolves options relative to its frozen tool path,
not the copied CAD project or current directory. On the first resume of an
older run without this file, the host refreshes
its carried CAD/Make-round tools and Make finalizer through the existing
recorded tool-refresh operation. It rebinds the saved native session before
adding the selected root option, so a checkpointed migration interrupted before
session rebinding is retried before the next native turn.
It does not import new lifecycle or token-budget instructions, reset usage,
or rebuild sealed Spark assets. The native prompt tells the existing session
to reread this host-owned choice and supersedes older mandatory-motion text.
Completed/failed terminal runs are inspected without changing this option.
Without operator resume, older materialized runs keep their original policy.
No checkpoint schema migration or Spark host rebuild is introduced.

Pending output bindings are reconciled only across consecutive recorded motion
corrections. An unaccepted Make proposal is preserved privately and must be
finalized again under the selected policy; sealed artifacts stay intact.

## Evidence and limits

The reported slow CPU-only runs motivated this operator control. Source
inspection confirms repeated OpenCascade Boolean operations in `check_motion`
and NumPy/Pillow software rendering for motion animation. Neither path has a
GPU backend here; adding a GPU alone does not accelerate them. This change
removes optional work, not the cost of any remaining gate. It does not measure
a speedup on the CEO's run or establish physical motion correctness.

Deterministic tests cover default skipping with existing manifests, explicit
opt-in, missing required evidence, failed/inconclusive checks, malformed options,
immutable-input tampering, resume reselection, legacy migration/interruption,
session and budget preservation, and plain tool-refresh preservation.

## Amendment 2026-11-08: resume keeps the frozen choice (issue #244)

A plain `workshop resume` of the Sunset Slider fix run switched its frozen
`check_motion` from true to false, so a Make that needed its motion gate
lost it without anyone asking. That broke the rule ADR 0049 and ADR 0064
keep for every other frozen option: a flag the operator omits keeps what
the run froze.

`resume --check-motion` now defaults to unset. Unset keeps the run's
`MAKE-OPTIONS.json` byte for byte, with no host correction. An explicit
`true` or `false` rebinds it as before. An older run without
`MAKE-OPTIONS.json` still migrates on any resume, with false unless asked,
which is the policy it ran under. `wish`, `start` and `fix` are unchanged:
a new run still defaults to false.

Tests cover a plain resume keeping a frozen true, an explicit false
rebinding it, and an unset resume migrating an older run to false.
