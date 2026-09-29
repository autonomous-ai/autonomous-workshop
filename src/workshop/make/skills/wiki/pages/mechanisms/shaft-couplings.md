---
title: Shaft couplings and universal joints
tags: [coupling, universal-joint, oldham, jaw-coupling, beam-coupling, misalignment, cardan, constant-velocity]
aliases: [u-joint, cardan joint, hooke joint, double cardan, spider coupling, lovejoy coupling, helical coupling, flexible coupling, shaft coupler]
sources:
  - https://en.wikipedia.org/wiki/Universal_joint (output speed equation, cos beta and 1/cos beta limits, double-joint phasing)
  - https://en.wikipedia.org/wiki/Oldham_coupling (three discs, perpendicular tongues, parallel offset, springs against backlash)
  - https://en.wikipedia.org/wiki/Coupling (misalignment accepted per coupling type, flexible couplings up to about 1.5 deg)
related: [shafts-and-bearings, gears, joints, mechanism-design]
updated: 2026-09-23
---

# Shaft couplings and universal joints

A coupling joins two shafts end to end. Pick it from the misalignment the
two shafts will have. Printed parts and hand-assembled frames always have
some.

## Choosing by misalignment

| coupling | accepts | backlash | notes |
|---|---|---|---|
| rigid (sleeve, clamp) | none | none | only if the shafts are exactly aligned; otherwise it loads both bearings |
| beam / helical (one piece, helical slots) | angular, parallel, axial | zero | stiffness set by the helix; common motor-to-screw coupler |
| jaw / spider (Lovejoy) | angular, parallel | minimal | elastomer spider damps shock; printable jaws with a TPU spider |
| Oldham | parallel offset only | small; springs reduce it | three discs, compact |
| disc (metal disc pack) | angular, parallel | minimal | high torsional stiffness |
| gear coupling | angular (4–5° typical) | high, by design | excess backlash causes vibration |
| universal (Cardan) joint | large angles | minimal | speed fluctuates unless paired (below) |
| rag joint (fabric) | angular, parallel | minimal | low stiffness, damps; steering linkages |

Flexible couplings in general handle up to about 1.5° of angular misalignment
with some parallel offset.

## Oldham coupling

Two hubs with slots, and a middle disc with a tongue on each face. The two
tongues are **perpendicular**. The middle disc slides in both slots, and its
centre orbits twice per shaft revolution around the midpoint between the
shaft axes. It transmits constant velocity across a *parallel* offset but not
across an angle. Printed: the tongue-to-slot fit is a running fit from
`cadfits`, and the sliding faces wear, so choose a slippery material pair.

## Universal joint: why one is not enough

With a bend angle `β` and input angle `γ₁`:

```text
ω₂ = ω₁ · cos β / (1 − sin²β · cos²γ₁)
ω₂/ω₁ ranges from cos β (minimum) to 1/cos β (maximum), twice per revolution
```

A single joint at 20° makes the output speed swing between 0.94 and 1.06 ×
input. That is a torque ripple, and vibration in anything driven.

**Constant velocity from two joints.** Put two joints on an intermediate
shaft with:

1. **equal angles** at both joints (a Z or W arrangement), and
2. the intermediate shaft's two yokes **in phase**: the second joint's cross
   is rotated 90° relative to the first, so each joint's fluctuation cancels
   the other's.

```python
assert abs(BETA_1 - BETA_2) < 0.5, "double U-joint angles unequal: output speed fluctuates"
```

## Printed-coupling notes

- Clamp or key the coupling onto each shaft; a set screw needs a flat
  ([[shafts-and-bearings#getting-torque-on-and-off]]).
- A coupling is not a bearing. Support each shaft on its own two bearings,
  and do not let the coupling carry radial load.
- A U-joint cross (spider) on printed yokes wears at the pins. Size the pins
  as shoulder pins with running fits ([[joints#revolute-joints]]).

## Checks

- Asserts: coupling type matches the declared misalignment; equal angles and
  in-phase yokes for a double U-joint.
- Motion: sweep one input turn of the coupled shafts through the joint with
  the frame as obstacle. For a U-joint, drive the output angle from the
  equation above, not 1:1 ([[mechanism-verification]]).
