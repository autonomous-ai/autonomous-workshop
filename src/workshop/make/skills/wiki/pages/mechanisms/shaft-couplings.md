---
title: Shaft couplings and universal joints
tags: [coupling, universal-joint, oldham, jaw-coupling, beam-coupling, misalignment, cardan, constant-velocity, yoke, spider]
aliases: [u-joint, universal joint, cardan joint, hooke joint, hooke's joint, double cardan, double universal joint, spider coupling, lovejoy coupling, helical coupling, flexible coupling, shaft coupler, cv joint, constant velocity joint, constant-velocity joint, homokinetic joint, rzeppa joint, birfield joint, tripod joint, tripode joint, tracta joint, weiss joint, bendix-weiss joint, thompson coupling, cross and bearing, u-joint spider, trunnion cross, block and pin universal joint, pin and block u-joint, ball and pin universal joint, print in place universal joint, printed universal joint, drive shaft, cardan shaft, propeller shaft, telescopic drive shaft]
sources:
  - https://en.wikipedia.org/wiki/Universal_joint (output speed equation, cos beta and 1/cos beta limits, double-joint phasing)
  - https://en.wikipedia.org/wiki/Oldham_coupling (three discs, perpendicular tongues, parallel offset, springs against backlash)
  - https://en.wikipedia.org/wiki/Coupling (misalignment accepted per coupling type, flexible couplings up to about 1.5 deg)
  - https://en.wikipedia.org/wiki/Constant-velocity_joint (Rzeppa 45-48 deg and up to 54; tripod 26 deg with 50 mm plunge; double Cardan centring element; Tracta, Weiss and Thompson mechanisms; Thompson 2 deg minimum offset)
  - https://en.wikipedia.org/wiki/Tracta_joint (forks, semi-spherical sliding pieces, tongue and groove a quarter turn out of phase)
  - https://www.firgelliauto.com/blogs/mechanisms/weiss-cv-joint (balls held in the bisecting plane; Weiss limit about 30-32 deg)
  - https://docs.rs-online.com/3d08/0900766b8140fdd3.pdf (industrial U-joint catalogue: +-0.4 % at 5 deg, +-1.5 % at 10 deg; 40-45 deg single, 80-90 deg double; rpm x angle product; inboard lugs in line; no parallel offset with one joint; square-tube telescopes)
related: [shafts-and-bearings, shaft-hub-connections, gears, joints, mechanism-design, hinges-and-pin-joints, print-in-place-mechanisms, ball-and-socket-joints, telescoping-tubes-and-locks]
updated: 2026-10-01
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

One industrial catalogue gives the single-joint swing as ±0.4 % at 5°,
±0.8 % at 7° and ±1.5 % at 10°: below about 10° a single joint is fine for
a slow toy. The same catalogue rates its joints by the product rpm × angle
(one plain-bearing series: 1200 rpm at most, and then only 10°), allows 40–45°
for a single joint and 80–90° for a double, and notes three more rules:

- A single joint is a pivot: it takes an angle but **no parallel offset**,
  and the shaft axes must meet at its centre or it loads the bearings
  radially. Offset shafts need a pair.
- In a pair each joint works at half the total angle, but the **intermediate
  shaft still fluctuates** with the first joint; its inertia sees the ripple.
- A U-joint takes no change of length. A drive whose ends move apart needs a
  telescoping intermediate shaft (spline, or nested square tubes for light
  duty; [[telescoping-tubes-and-locks]]).

## Constant-velocity joints

A joint runs at constant velocity when the points that carry the torque lie
in the plane that **bisects** the angle between the shafts. Every CV joint
is a way of holding its contacts there.

| joint | how it stays in the bisecting plane | max angle | plunge | printed |
|---|---|---|---|---|
| **double Cardan** | two Hooke joints on a short centre yoke, 90° apart; constant only at equal angles, which a centring element enforces | 80–90° in total | none: add a telescope | the practical toy CV |
| **Rzeppa** (Birfield: elliptical tracks) | six balls in grooves of an inner race and an outer bell, steered by a cage | 45–48°, some 54° | none (fixed joint) | a toy at most: printed grooves wear under steel balls |
| **tripod (tripode)** | three trunnions with barrel rollers in three grooves of a cup | about 26° | up to 50 mm | yes, as a small-angle plunging joint |
| **Tracta** | two forks gripping two semi-spherical sliders joined by a tongue and groove a quarter turn out of phase with the forks | no reliable figure | none | possible; the sliding faces wear |
| **Weiss** (Bendix-Weiss) | four balls in curved grooves of two yokes, centred in the bisecting plane: two carry the torque, two preload against backlash | about 30°: the balls leave the grooves at 30–32° | — | yokes print; balls bought |
| **Thompson coupling** | two Cardan joints nested, a control yoke bisecting the angle | — | none | many parts; needs at least 2° offset to spare the control yoke |

Inboard (gearbox-side) joints of a car axle plunge (tripod); outboard
(wheel-side) joints take the steering angle (Rzeppa). A printed toy shaft
that must bend and stretch is a double Cardan plus a telescope, or a tripod
at small angles.

## Printing a universal joint

| build | parts | notes |
|---|---|---|
| **block and pins** | two yokes, a centre block, two pins crossing in it | strongest; steel pins (dowels, screws) through a printed block. One pin passes through a cross hole in the other, or one long pin and two short ones |
| **cross spider** | two yokes and a printed four-arm cross | the cross cannot enter two closed-eye yokes: open one ear into a hook closed by a keeper, or print in place |
| **ball and pin** | a ball with a cross pin on one shaft; a cup with two axial slots on the other | compact; the ball turns on the pin and the pin swings in the slots. Hooke kinematics, same ripple. The cup lip is a ball socket ([[ball-and-socket-joints]]) |
| **print-in-place** | yokes and spider in one job | `print_in_place_gap()` on every face; printed straight, freed by working it ([[print-in-place-mechanisms#breaking-free]]) |

- **Yokes lie on their side**, shaft axis horizontal and the two ears
  standing as walls. Torque then bends each ear along its layers, and the ear
  bores are horizontal teardrops ([[fdm-hole-accuracy#horizontal-holes-teardrops-and-horiholes]]).
  A yoke standing on its shaft end has each ear root in tension across the
  layers, and snaps there. Lying down, the yoke's own bore is horizontal: print
  the yoke and its shaft stub as one part on the stub's D-flat, or give a
  separate hub a thick wall and a cross pin
  ([[shaft-hub-connections#printing-shaft-hub-joints]]).
- **The spider lies flat**, all four arms in the bed plane, with each arm's
  underside flattened or cut at 45° ([[print-in-place-mechanisms#pin-orientation]]).
  The arms are shoulder pins: ear bore `slot_for(arm_d, RUN)`, fork gap
  `slot_for(spider_w, RUN)` ([[joints#revolute-joints]]).
- **The angle is limited by collision**: the ear tips strike the other
  yoke's hub. Sweep it ([[mechanism-verification]]) rather than trusting a
  catalogue figure.
- **Phase the pair.** The two yokes on the intermediate shaft lie in one
  plane ("inboard lugs in line"). A yoke is symmetric under a half turn, so a
  double-D or single D on the intermediate shaft phases it; a square or hex
  lets it on 90° or 60° wrong ([[shaft-hub-connections#phasing-and-indexing]]).
  A square telescope admits the same error. Printing the intermediate shaft
  and both its yokes as one part removes it.
- **Equal angles**: input and output make the same angle with the
  intermediate shaft, in a Z or W layout.

## Printed-coupling notes

- Clamp or key the coupling onto each shaft; a set screw needs a flat
  ([[shaft-hub-connections#set-screws]]).
- A coupling is not a bearing. Support each shaft on its own two bearings,
  and do not let the coupling carry radial load.
- A U-joint cross (spider) on printed yokes wears at the pins. Size the pins
  as shoulder pins with running fits ([[joints#revolute-joints]]).

## Checks

- Asserts: coupling type matches the declared misalignment; equal angles and
  in-phase yokes for a double U-joint:

```python
assert PARALLEL_OFFSET == 0 or N_UJOINTS >= 2, "one U-joint cannot take parallel offset"
assert abs(BETA_1 - BETA_2) < 0.5 and YOKE_PHASE_DEG % 180 == 0, "pair not constant-velocity"
assert 2 % INTERMEDIATE_PROFILE_POSITIONS == 0, "intermediate shaft lets a yoke on out of phase"
assert RPM * BETA_DEG <= RPM_ANGLE_LIMIT, "speed x angle above the joint's rating"
```

- Motion: sweep one input turn of the coupled shafts through the joint with
  the frame as obstacle. For a U-joint, drive the output angle from the
  equation above, not 1:1 ([[mechanism-verification]]).
