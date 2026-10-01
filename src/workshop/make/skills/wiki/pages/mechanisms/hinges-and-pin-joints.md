---
title: Hinges and pin joints
tags: [hinge, knuckle, pin, lid, friction-hinge, detent, stop, retention, print-in-place, revolute]
aliases: [barrel hinge, knuckle hinge, piano hinge, butt hinge, lid hinge, box hinge, door hinge, pin-and-barrel hinge, friction hinge, torque hinge, hold-open hinge, free-stop hinge, detented hinge, hinge pin, filament pin, hinge types, kinds of hinge]
sources:
  - skills/cad/scripts/cadfits.py (print_in_place_gap, slot_for, peg_for)
  - https://3dprintcalcs.uk/mechanical/hinge-calculator/ (hole = pin + 2 c; wall = 3 × nozzle; pin ≥ 6 × nozzle; ≥ 3 knuckles, odd; axial gap ≥ 2 layers when the axis is vertical)
  - https://www.snapmaker.com/blog/3d-printed-hinges/ (0.2–0.3 mm pin-to-barrel gap; lower flow 2–5 % when a hinge fuses)
  - https://www.sovol3d.com/blogs/news/print-in-place-3d-printing-how-to-design-hinges-joints-and-moving-parts-that-actually-work (PLA 0.15–0.40 mm per side by fit; PETG +0.05; 0.5 mm × 45° bottom chamfer; 3–4 perimeters on pins)
  - https://www.sugatsune-intl.com/torque-hinges/torque-calculation/ (door moment = m g x_cg, maximum with the lid horizontal; hinge torque tolerance ±20 %; torque shared equally between hinges)
  - https://en.wikipedia.org/wiki/Hinge (the hinge forms the type catalogue covers)
related: [joints, hinge-types, rod-ends-and-clevises, flexures-and-living-hinges, shafts-and-bearings, dowel-pins-and-press-fits, fdm-minimum-feature-sizes, overhangs-and-print-orientation, mechanism-verification, latches-detents-and-ratchets, snap-fit-design, creep-and-stress-relaxation, counterweights-and-gravity-balance]
updated: 2026-10-01
---

# Hinges and pin joints

A mechanical hinge is a pin turning in alternating knuckles. This page sizes
the pin and knuckles, chooses how the pin is retained, and adds the three
things a lid hinge usually also owes: a stop, a hold-open torque and a swing
that clears the box. The short catalogue rows are in [[joints#revolute-joints]];
a hinge that bends instead of turning is in [[flexures-and-living-hinges]].

## Hinge types

Which hinge form to draw is on [[hinge-types]]: butt, continuous (piano),
strap and T, lift-off (flag), pivot, rising butt and self-closing cam,
spring and double-action, offset (swing-clear, gooseneck), concealed
European cup, invisible (Soss), and the four-bar hinge that moves a lid
clear. Its chooser gives each type's geometry, when to use it and how it
prints; every type still takes its pin, knuckles, retention and stop from
the sections below. A pin that joins a rod or link rather than two leaves
(fork and eye, clevis pin, rod end) is on [[rod-ends-and-clevises]].

## Pin and knuckle sizing

Derive the barrel from the pin, never the other way round, and never type
both:

```text
barrel bore     d_b = slot_for(d_pin, fit)            (assembled pin)
                d_b = d_pin + 2 · gap_xy               (print-in-place, gap from print_in_place_gap)
knuckle OD      D_k ≥ d_b + 2 · w_min,   w_min = 3 × nozzle width (1.2 mm at 0.4)
printed pin     d_pin ≥ 6 × nozzle (2.4 mm); 3–6 mm is the comfortable range
knuckles        ≥ 3, an odd count (2 on one leaf, 1 on the other at minimum)
```

- A printed pin below ~3 mm is weak and its surface is mostly perimeter
  ridges ([[fdm-minimum-feature-sizes#features-pins-and-gaps]]); give it 3–4
  perimeters so the pin is solid shell, not infill.
- Load the pin in **double shear**: a middle knuckle between two outer ones
  halves the shear per section and keeps the leaves from twisting. For a
  printed pin, `τ = F / (2 · π d² / 4)` must stay well under the filament's
  printed shear strength ([[filament-properties]]); a steel pin makes the
  printed knuckle the weak part, so check bearing pressure there instead,
  `p = F / (d_pin · L_knuckle)`.
- Many short knuckles (a piano hinge) spread load and resist leaf twist; few
  long ones are easier to print and clear.

## Print-in-place hinges

Parts printed together in one job take their gaps from
`cadfits.print_in_place_gap(fit, layer_height=..., material=...)`, which
returns `xy`, `z` (= xy + one layer, because a gap's ceiling is a sagging
bridge) and a 0.5 mm `bottom_chamfer`. Use `"tight"` (0.20) for a
pin-in-barrel hinge on a tuned printer, `"sliding"` (0.30) as the default.
Published per-side values agree with that band: 0.15–0.40 mm for PLA by
tightness, with 0.05–0.10 mm more for PETG. Which gap goes where depends on
the axis:

| axis on the bed | radial gap (pin ↔ bore) | axial gap (knuckle ↔ knuckle) | pin form |
|---|---|---|---|
| **horizontal** (hinge lies flat, the common case) | top of the bore is a bridge: use `z`, or make the bore a teardrop/diamond so its ceiling is self-supporting | knuckle faces are vertical walls: `xy` | round or diamond pin; the pin's underside needs the same care as the bore's top |
| **vertical** (hinge stands up) | walls: `xy` | faces are horizontal ledges: `z`, at least two layers | cone-ended pin (45° or steeper) so each knuckle's bore ceiling is a supported cone |

- Every gap that touches the bed gets `bottom_chamfer`: elephant's foot closes
  a plate-level gap first.
- If a tuned hinge still fuses, lower flow 2–5 % before widening the gap.
- A rigid sweep cannot prove a print-in-place hinge breaks free. Declare it an
  open item until a print does ([[mechanism-verification#9-what-nothing-here-proves]]).

## Pin retention

Choose one and write it in the retention chain; a pin held only by friction is
recorded as such.

| pin | build | retained by |
|---|---|---|
| **headed printed pin** | head on one end, `slot_for(d, RUN)` through the moving leaf, `slot_for(d, SEAT)` blind or through in the fixed leaf | head one way, snug friction the other; add a cap or snap nose if it must not work out ([[snap-fit-design#annular-snap]]) |
| **filament pin** | 1.75 mm filament through a bore `slot_for(1.75, "slip")` | ends melted or flattened into a mushroom once inserted: permanent |
| **steel pin (dowel, rod, nail)** | press into one outer knuckle, slip through the others | the press end; derive both bores from the one pin diameter ([[dowel-pins-and-press-fits]]) |
| **screw as pin** | shoulder screw, or a machine screw with a nut on the far side | head and nut; a plain thread running in a bore wears the knuckle, so keep threads outside the moving knuckle |
| **integral (print-in-place)** | the pin is part of the outer knuckles | captive by construction; cannot be serviced |

A pin in a horizontal bore is also axially free in both directions unless
something stops it: every pin gets two axial stops or one stop plus a
friction note ([[joints#revolute-joints]]).

## Stops and opening angle

A hinge without a stop is stopped by whatever collides first — usually the
leaves, the lid edge or a printed snap. Put the stop where it is meant to be:

- **Leaf-back stop**: the leaves meet each other at the design angle. The
  stop angle comes from the leaf thickness and how far the axis sits from the
  leaf plane, so compute it from those parameters rather than reading it off
  the model.
- **Knuckle stop**: a tab on one knuckle strikes a shoulder on the next.
  Short lever arm, so the stop force is high; keep the tab at least 2
  perimeters thick in the layer plane.
- **Strap or link stop**: for a lid, a link or cord from lid to box carries
  the over-opening load away from the hinge.

The stop is a `blocked` rotation sweep at the limit angle, and the free range
is a `clear` sweep ([[joints#the-two-conditions-every-joint-owes]]).

## Lid hinges for boxes

The back edge of a lid swings on a circle of radius `r` = distance from the
axis to the lid's farthest back corner. Anything of the box inside that
circle on the swing side is hit.

- Put the axis at or behind the back face and at or above the lid seam; then
  the lid's back edge rotates away from the wall.
- An axis set inside the wall needs a relief on the wall top: an arc of radius
  `r + gap` about the axis, or the lid binds after a few degrees.
- A lid that opens just past vertical rests by its own weight against a stop;
  one that stops short of vertical falls shut unless the hinge holds it
  (below). Put the stop a few degrees past vertical, and design the stop to
  take the lid's weight moment plus a push.
- Two short hinges near the ends resist racking better than one in the middle.

## Friction and hold-open hinges

A lid that must stay where it is left (a "free-stop" or torque hinge) needs
hinge friction torque above its own gravity moment at every angle.

```text
lid moment       M(θ) = m · g · x_cg · cos θ      (θ from horizontal; maximum when horizontal)
shared torque    T_each = M_max / n_hinges
free stop needs  T_min ≥ M_max / n_hinges,   T_min = T_nominal · (1 − tol)
```

A bought torque hinge is specified with a tolerance of about ±20 %, so size on
its minimum. Worked example (vendor's): 0.8 kg lid, x_cg = 0.20 m →
M_max ≈ 1.57 N·m; two 1.0 N·m hinges give 0.8 N·m minimum each, 1.6 N·m in
total, just enough.

Printed ways to make friction, all of which relax over time
([[creep-and-stress-relaxation]]) and need a test coupon:

- a slotted, slightly undersized knuckle that grips the pin like a spring clip
  — the torque comes from the clip's elastic interference, so size it as a
  snap ring's strain, not from the fit table;
- an O-ring or TPU sleeve on the pin, compressed in the bore;
- a spring washer or wave spring pressing knuckle faces together (face
  friction torque ≈ μ · F_axial · r_mean per face).

A bought torque hinge is the only one whose torque is known before printing;
search `$step-parts` for it.

Springs, gas struts and counterweights that hold a lid:
[[counterweights-and-gravity-balance]].

## Detented hinges

A hinge that should click to rest at chosen angles puts a detent on the
knuckle faces (axial bumps and notches held by a spring washer or a flexing
leaf) or on the knuckle outside (a leaf-spring finger riding a notched
barrel). Size the detent force with [[latches-detents-and-ratchets#detent-holding-force]]
and turn it into torque with the radius of the bumps.

## Checks

```python
import cadfits
bore = cadfits.slot_for(PIN_D, "slip")                       # derived, never typed
assert KNUCKLE_OD >= bore + 2 * 3 * NOZZLE, "knuckle wall under 3 extrusion widths"
assert PIN_D >= 6 * NOZZLE or PIN_IS_METAL, "printed pin too thin"
assert N_KNUCKLES >= 3 and N_KNUCKLES % 2 == 1, "hinge needs an odd count of at least 3 knuckles"
pip = cadfits.print_in_place_gap("tight", layer_height=LAYER, material=MAT)
assert AXIAL_GAP >= (pip["z"] if AXIS_VERTICAL else pip["xy"]), "knuckle faces will fuse"
m_max = LID_MASS * 9.81 * LID_XCG
assert HINGE_T_NOM * (1 - HINGE_TOL) * N_HINGES >= m_max, "lid will not hold open"
assert STOP_ANGLE_DEG < COLLISION_ANGLE_DEG, "something other than the stop stops the lid"
```
