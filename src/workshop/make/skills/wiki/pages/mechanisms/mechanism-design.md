---
title: Designing a mechanism
tags: [mechanism, archetype, design, kinematics, feasibility, system]
aliases: [mechanism selection, type synthesis, motion conversion, drive system, machine layout]
sources:
  - Norton, Design of Machinery, ch. 1-2 (type synthesis, degrees of freedom)
  - skills/cad/references/motion-manifests.md
  - "experience: kinetic machines built in this repository whose gates passed a mechanism that could not run"
related: [joints, shafts-and-bearings, gears, linkages, cams-intermittent, energy-drive, automata-patterns, mechanism-verification, mechanism-failures]
updated: 2026-09-23
---

# Designing a mechanism

Start here whenever a part turns, slides, swings, indexes, latches or is
driven relative to another. This page holds the sequence and the archetype
chooser; every other page in this topic holds the numbers for one archetype.
`$cad` and `check_motion` cannot tell you *which* joint to draw or *which
numbers* make a linkage turn — that is what these pages are for.

## The design sequence

1. **Name the archetype** (table below) and what was rejected. "Runs on a
   rubber band" or "the wings flap" is a requirement, not an archetype.
2. **Lay out the shafts and joints**: every axis, what supports it, what
   locates it axially, how torque gets onto it ([[shafts-and-bearings]],
   [[joints]]).
3. **Parameterise once** — fixed pivots, link lengths, throws, module and
   tooth counts, phase offsets, joint limits — in one block with provenance.
   Mates derive from `cadfits`; standard elements are searched first.
4. **Write the feasibility condition** as an `assert` (each page gives it).
   No geometry gate catches a machine that cannot complete its cycle.
5. **Solve the kinematics once** (input angle → pose of every moving body),
   place the geometry from that solution, rest pose mid-stroke.
6. **Derive the motion checks from the same solution**: one coupled cycle, a
   fine sweep of the fastest contact, both directions of every joint,
   retention closed at a fixed root ([[mechanism-verification]]).

## Archetype chooser

| input → wanted output | first choice | alternatives (when) | page |
|---|---|---|---|
| rotation → oscillating swing | crank-rocker four-bar | cam + oscillating follower (dwell), slider-crank + rack | [[linkages]] |
| rotation → reciprocating slide | slider-crank | cam + follower (custom timing), scotch yoke (compact, pure harmonic) | [[linkages]], [[cams-intermittent]] |
| rotation → rise / dwell / fall with timing | cam + follower | Geneva (indexed steps) | [[cams-intermittent]] |
| rotation → step-and-hold indexing | Geneva | ratchet + pawl (one-way, rocker-driven) | [[cams-intermittent]] |
| rotation → walking gait | crank + guide pin, Jansen / Klann | cam-lifted legs (automaton) | [[linkages]], [[automata-patterns]] |
| rotation → flapping / undulating panels | crank pins + links to hinged panels | cam shaft + push rods | [[automata-patterns]] |
| speed / torque change, parallel shafts | spur pair | belt (long centres), compound train (> 1:6) | [[gears]] |
| turn the axis 90° | bevel / face gear | worm (big reduction, may self-lock), crossed helical | [[gears]] |
| rotation → straight travel | rack + pinion | lead screw (slow, self-locking) | [[gears]] |
| one-way / hold against return | ratchet + pawl | self-locking worm | [[cams-intermittent]] |
| store and release energy | rubber band on a wound axle, spring | falling weight, clockwork | [[energy-drive]] |
| electric drive | motor / servo + reduction | — | [[energy-drive]] |
| carry a turning part | shaft on two supports | stub axle, shoulder pin | [[shafts-and-bearings]] |
| hinge, pivot, slide, lock | joint catalogue | — | [[joints]] |

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

## Where the other skills take over

Electrical drives: `$electromechanical-integration`. Purchased parts:
`$step-parts`. Standard elements (fasteners, bearings, gears, snap rings):
`skills/cad/scripts/stdpart`. Motion-manifest schema:
`skills/cad/references/motion-manifests.md`. This topic links to those rather
than repeating them.
