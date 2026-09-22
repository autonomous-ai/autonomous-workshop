---
name: mechanisms
description: Reference knowledge for joints and working mechanisms in printed parametric CAD - pins, axles, hinges, slides, keyed shafts, snap and captive joints, gears (spur, rack, worm, bevel), linkages (four-bar, slider-crank, walking legs), cams and followers, Geneva and ratchet drives, rubber-band, spring and hand-crank drives, and automaton layouts. Consult when choosing a mechanism archetype, sizing a joint that must turn or slide, writing a feasibility condition, or planning the kinematics and motion checks for a machine.
---

# Joints and mechanisms — knowledge base

This is a reference, not a workflow and not a tool. It holds the design
knowledge `$cad` and `check_motion` do not: *which* joint to draw, *which
numbers* make a linkage turn, and *why* a correct-looking printed mechanism
still does not run. It writes no geometry, owns no gate and changes no other
skill. Read the page the task needs; the formulas are written out so they can
be copied into a project's parameter block as asserts.

## When to consult it

- a part turns, slides, swings, indexes, latches or is driven relative to
  another;
- a build spec's mechanism section needs an archetype, parameters and a
  feasibility condition;
- a mate must move (a running fit is not a press fit);
- a motion sweep fails, or passes suspiciously, and you need to know whether
  the mechanism or the check is wrong.

For electrical drives go on to `$electromechanical-integration`; for standard
parts `$step-parts`; for the motion-manifest schema the CAD skill's
`references/motion-manifests.md`. This knowledge base links to those rather
than repeating them.

## The design sequence it assumes

1. **Name the archetype** (table below) and what was rejected. "Runs on a
   rubber band" or "the wings flap" is a requirement, not an archetype.
2. **Parameterise once** — fixed pivots, link lengths, throws, module and
   tooth counts, phase offsets, joint limits — in one block with provenance.
   Mates derive from `cadfits`; standard elements are searched first.
3. **Write the feasibility condition** as an `assert` (each page gives it).
   No geometry gate catches a machine that cannot complete its cycle.
4. **Solve the kinematics once** (input angle → pose of every moving body),
   place the geometry from that solution, rest pose mid-stroke.
5. **Derive the motion checks from the same solution**: one coupled cycle, a
   fine sweep of the fastest contact, both directions of every joint,
   retention closed at a fixed root.

## Archetype chooser

| input → wanted output | first choice | alternatives (when) | page |
|---|---|---|---|
| rotation → oscillating swing | crank-rocker four-bar | cam + oscillating follower (dwell), slider-crank + rack | `linkages.md` |
| rotation → reciprocating slide | slider-crank | cam + follower (custom timing), scotch yoke (compact, pure harmonic) | `linkages.md`, `cams-intermittent.md` |
| rotation → rise / dwell / fall with timing | cam + follower | Geneva (indexed steps) | `cams-intermittent.md` |
| rotation → step-and-hold indexing | Geneva | ratchet + pawl (one-way, rocker-driven) | `cams-intermittent.md` |
| rotation → walking gait | crank + guide pin, Jansen / Klann | cam-lifted legs (automaton) | `linkages.md`, `automata-patterns.md` |
| rotation → flapping / undulating panels | crank pins + links to hinged panels | cam shaft + push rods | `automata-patterns.md` |
| speed / torque change, parallel shafts | spur pair | belt (long centres), compound train (> 1:6) | `gears.md` |
| turn the axis 90° | bevel / face gear | worm (big reduction, may self-lock), crossed helical | `gears.md` |
| rotation → straight travel | rack + pinion | lead screw (slow, self-locking) | `gears.md` |
| one-way / hold against return | ratchet + pawl | self-locking worm | `cams-intermittent.md` |
| store and release energy | rubber band on a wound axle, spring | falling weight, clockwork | `energy-drive.md` |
| electric drive | motor / servo + reduction | — | `energy-drive.md` |
| hinge, pivot, slide, lock | joint catalogue | — | `joints.md` |

## Pages

- `references/joints.md` — revolute, keyed, prismatic, latching joints: fits,
  FDM rules, and the `clear`/`blocked` pair each joint owes.
- `references/gears.md` — spur, internal, rack, worm, bevel: formulas, FDM
  tooth choices, phasing, body under the teeth, measuring a mesh.
- `references/linkages.md` — four-bar (Grashof, transmission angle,
  branches), slider-crank, scotch yoke, dead centres, walking linkages,
  closure solving.
- `references/cams-intermittent.md` — cam laws, base circle and pressure
  angle, follower retention, Geneva, ratchet, escapement.
- `references/energy-drive.md` — rubber band, springs, weight, hand crank,
  motor handoff, ratio budget, drive direction.
- `references/automata-patterns.md` — how toy automata are laid out, with
  `output/trotter` and `output/manta_ray` as worked examples.
- `references/verification.md` — from a kinematics solution to motion checks:
  pose tables, sampling, `driven`, both directions, retention, and what no
  rigid sweep proves.
- `references/failure-catalog.md` — mechanism faults upstream has shipped or
  caught, their symptom and the rule that prevents each. Read before calling a
  mechanism finished.

`output/trotter`, `output/manta_ray` and `trotter-src` are machines in the
upstream `autonomous-product-to-cad` repository. They are not materialized in
a product run: the numbers and file names quoted on these pages are the whole
example, so do not look for those paths.

## Principles that hold across every page

- A mechanism is specified by numbers and an assert, never by a picture.
- One source per number: a pivot in the kinematics and again in a part
  builder is two numbers that drift.
- Place moving bodies by the kinematic solution, never by hand.
- Park the rest pose mid-stroke, away from dead centres and travel ends.
- Every joint has an assembly direction and a capture direction; a pin that
  holds a part is itself a part that can leave.
- Name what a rigid sweep cannot answer — band torque, friction, snap
  compliance, whether a gait walks, whether a print-in-place joint frees.
