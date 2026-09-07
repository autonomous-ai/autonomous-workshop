# ADR 0052: Exact thickness readings and host-corrected run tools

- Status: Accepted
- Date: 2026-09-06
- Owners: Make gate, workflow, and product-run protocol maintainers

## Context

`check_thickness`, the wall gate every printable part must pass, measured
walls by marching inward through a voxel grid in half-pitch steps and failed
a sample under `min_wall - pitch / 2`. The allowance was meant to absorb the
grid reading one step low on a wall that does not line up with the grid.

The first Forge run on `gpt-6-astra` (microduck-windup, 2026-09-06) stopped
at Make round 4 with a host need, and its evidence held up: a 0.8 mm axle
shoulder read 0.7333333333333333 mm against a threshold computed as
0.7333333333333334 mm, so 841 samples on a wall drawn at exactly the minimum
failed on their last floating-point digit; a 0.8 mm spring coil read
0.6667 mm over 1,587 samples because the march loses a boundary voxel on both
faces of a curved wall, while exact STEP probes stayed solid at 0.799 mm and
left at 0.801 mm on every sampled ray. The gate was measuring the grid, not
the part, and the Manager could not thicken either feature without changing
a sealed dimension.

Correcting the tool did not by itself reach the run. Domain skills are
materialized into a run at creation and hash-bound in its input manifest,
which the host re-verifies on every checkpoint; the host owned the bytes but
had no operation to change them.

## Decision

1. `check_thickness` keeps the voxel march as its screen and re-measures
   every sample the grid reads under the minimum exactly, by intersecting the
   sample's own inward ray with the mesh triangles near it. The verdict is
   taken on that exact distance with a quarter-pitch allowance for
   tessellation chord error. A wall drawn at exactly the minimum passes; a
   wall a tenth of a millimetre under it fails, and so does a 0.75 mm wall
   the old grid could not tell from 0.80. Its self-check pins all three.
2. `AgentRun.refresh_domain_skill_tools` lets the host rewrite a run's copy
   of a domain skill byte-for-byte from the installed source, rebind the
   input manifest in a new checkpoint revision, and append an owner-only
   record to `host-corrections.jsonl` in host state. Only skills the run
   already carries are refreshed. `workshop resume --refresh-tools` exposes
   it; nothing refreshes implicitly.

## Consequences

- Thin-wall failures now name real thin walls. The exact pass adds seconds
  on a thin part (11 s on the 53,000-sample spring) and nothing on thick ones.
- A run that stopped waiting on a tool defect resumes after the operator
  upgrades Workshop and passes `--refresh-tools`; the native session, round
  budget, and sealed artifacts are untouched, and the ledger shows exactly
  which bytes changed under which checkpoint.
- The Manager sees the corrected tool's new hash on its next verification;
  its earlier evidence manifest still names the old one, which is the point.
- The `cad` skill is vendored from `autonomous-product-to-cad` at the commit
  named in `src/workshop/make/skills/LOCK.json`; this change is a local patch
  on top of that commit, the lock's fingerprint now names the patched tree,
  and the patch should be offered upstream so the next vendored snapshot
  carries it instead of reverting it.
