# ADR 0066: Opt-in Make motion verification

- Date: 2026-09-14
- Status: Accepted
- Supersedes motion requirements for newly created runs in ADR 0047 and
  ADR 0060 (declared-motion reconciliation); other Make checks remain intact.

## Decision

`workshop wish`, `start`, and `fix` accept `--check-motion true|false`, with
false as the default. The host freezes the boolean in read-only root
`MAKE-OPTIONS.json`, covered by the ordinary immutable-input hash manifest.
Resume and explicit domain-tool refresh preserve those bytes.

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
not the copied CAD project or current directory. Existing runs keep their
materialized tools; an explicit refresh of an old run with no options file
retains motion enabled. No checkpoint schema migration or Spark host rebuild
is introduced.

## Evidence and limits

The reported slow CPU-only runs motivated this operator control. Source
inspection confirms repeated OpenCascade Boolean operations in `check_motion`
and NumPy/Pillow software rendering for motion animation. Neither path has a
GPU backend here; adding a GPU alone does not accelerate them. This change
removes optional work, not the cost of any remaining gate. It does not measure
a speedup on the CEO's run or establish physical motion correctness.

Deterministic tests cover default skipping with existing manifests, explicit
opt-in, missing required evidence, failed/inconclusive checks, malformed options,
immutable-input tampering, resume and tool-refresh preservation.
