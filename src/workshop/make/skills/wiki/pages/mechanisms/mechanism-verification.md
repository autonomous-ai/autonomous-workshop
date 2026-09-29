---
title: Verifying a mechanism
tags: [verification, motion, manifest, kinematics, sampling, retention, driven, sweep]
aliases: [motion check, check_motion, motion manifest, sweep, clearance check]
sources:
  - skills/cad/references/motion-manifests.md
  - skills/cad/scripts/check_motion
  - "toolchain: a labelled group compound read back as a mover returns an empty boolean where its leaf overlaps (reproducible)"
related: [mechanism-design, joints, mechanism-failures, mass-properties-and-measurement]
updated: 2026-09-23
---

# Verifying a mechanism

What proves a machine runs, in the order the evidence is built. The gate
schema is in `skills/cad/references/motion-manifests.md`; this page is how to
fill it for a mechanism.

## 1. Feasibility asserts

Milliseconds, at import. Put them in the parameter module so a bad number
fails the build, not the print: Grashof with margin, transmission angle, slot
holds the stroke, gear body under the teeth, cam pressure angle, rods
quartered, centre distances equal their formulas, shaft deflection at each
gear. Each page of this topic gives its assert.

## 2. One kinematics module

`theta` in → pose of every moving body out, as rotation (axis point,
direction, angle) and/or translation from the assembly pose. The combined
assembly entry places parts at `theta_rest`; the motion manifest samples the
same functions. Nothing else computes a pose.

## 3. The manifest is generated, never edited

`measure/make_motion.py` imports the parameters and kinematics and writes
`measure/motion.json`. Change a parameter → regenerate → rerun. A hand-edited
pose table is a second guess at the kinematics, and a table describing parts
drifting past each other sweeps perfectly clear.

## 4. What the manifest must contain

| condition | why |
|---|---|
| **full coupled cycle** (`coupled_motion_collision`, one input turn, every mover) | proves the parts clear each other through the whole cycle |
| every output marked **`driven: true`** | proves the drive actually touches each output; a follower nobody pushes fails |
| **`obstacle_parts`** listing the frame/body (or an explicit `[]`) | omitted = inconclusive; the frame is what a mechanism is guaranteed to hit |
| **fine sweep of the fastest contact** (one tooth pitch, pin through a Geneva slot) with `maxStepMm` | a coarse sweep steps over a tooth passing through a tooth |
| per joint: assembly direction **`clear`**, capture direction **`blocked`** | a joint only checked for coming apart passes as a plain pocket |
| **assembly order** (`assembly_sequence`), each part on its real insertion axis | final-pose clearance does not prove a shaft can enter its frame |
| **`retention`** proofs down to a genuine fixed root | a blocked sweep freezes its obstacles; a loose gate is not a root |

## 5. Sampling

The step that matters is the fastest point, not the input:

```text
step_mm   = radius_of_fastest_point × Δθ (radians)
steps     = ceil(sweep_angle_rad × radius / max_step)
```

A foot 30 mm from the axle moves about 0.5 mm per crank degree, so a
half-turn at 48 steps is a bulk-clearance sweep of several millimetres per
step; the mesh needs its own one-tooth sweep at a fraction of a millimetre.
Geneva and cam outputs peak mid-stroke at several times their average rate:
sample for the peak. Every table holds exactly `steps + 1` absolute values
from the assembly pose.

Split a full turn into halves if one sweep gets slow; keep the tables
continuous across the split.

## 6. Where to park the rest pose

Mid-stroke for every output. At a travel end the drive only ever falls away
from the output, so the `driven` pass calls a working part undriven. With
several outputs pick a phase where none is at an extreme.

"Rest pose" here means **sample 0 of the table**, not the middle of it. The
`driven` pass freezes its part at sample 0 and runs the rest, so a table that
sweeps a whole revolution still reports no transmission when it happens to
*start* at a dwell. Rotate the table until its first sample is mid-stroke; the
cycle it covers is unchanged.

A dwell is a travel end. On a one-sided drive — a cam with an elastic or
gravity return, a ratchet, a slot that only pushes one way — both ends are
travel ends in opposite senses, and only one of them shows contact. If the
`driven` pass insists a working pair transmits nothing, read the drive's own
boolean before rewriting the table: a cam built by intersecting a disc with the
half-space *above* a tilted plane has its working face on the **underside** and
pushes its follower away in −Z, which is the opposite of what its render
suggests.

## 7. Movers are leaf parts

Name the leaf solids that move, not a labelled group compound: a group
compound read back from the assembly returns an empty boolean (0 mm³) where
its leaf shows the real overlap. A dotted path to a leaf is fine.

## 8. Allowances are declared, not hidden

A detent or snap overlaps by design. Give that condition a `maxOverlapMm3`
equal to the bump band and write in its description why (for example
"8 lip spans × 0.1 × ~2 mm"). Any other collision still fails.

`distance_to` measures between boundaries only, so a body buried inside
another reports a positive gap: [[mass-properties-and-measurement]].

## 9. What nothing here proves

Band or spring torque, friction and friction retention, press-fit force,
snap compliance, elastic recovery, whether a gait actually walks, whether a
print-in-place joint frees, wear. List them as open items in the README/spec
and in the final report; a passing sweep never implies one of them.
