---
title: Print-in-place mechanisms
tags: [print-in-place, clearance, hinge, pin, teardrop, elephant-foot, captive, articulated, ball-joint, chain]
aliases: [pip, print in place, printed assembled, non-assembly mechanism, captive hinge, flexi toy, articulated toy, articulated dragon, flexi rex, fused joint, joint fused, break free, crossed loops, interlocking loops, chain link joint, segment joint, flexi joint]
sources:
  - skills/cad/scripts/cadfits.py
  - https://www.sovol3d.com/blogs/news/print-in-place-3d-printing-how-to-design-hinges-joints-and-moving-parts-that-actually-work
  - https://printstack3d.nl/en/blog/print-in-place-clearance-guide
  - https://3dcentral.ca/articulated-3d-prints-how-flexi-toys-work/
  - https://help.prusa3d.com/article/elephant-foot-compensation_114487
  - "experience: sections of a published print-in-place flexi toy's segment joints, measured along each axis and normal to the faces"
related: [flexi-chain-joints, printed-part-count, joints, fit-derivation, fdm-first-layer-and-warping, fdm-bridging-and-sacrificial-layers, fdm-hole-accuracy, overhangs-and-print-orientation, gears, mechanism-verification, flexures-and-living-hinges, mass-properties-and-measurement]
updated: 2026-09-28
---

# Print-in-place mechanisms

A print-in-place (PIP) mechanism leaves the bed already assembled: a hinge,
a captive gear, a chain or an articulated toy printed in one job. Every
mating face must be separated by an **open gap in the printed part**, not only
in the model — the printer closes model gaps in three predictable places
(the bed, the ceiling of the gap, and support). This page is what to do about
each. Whether to print in place at all is
[[printed-part-count#print-in-place-before-splitting]]; the gap numbers come
from `cadfits.print_in_place_gap()` and are not repeated as literals here.

## The gap is per face and per direction

`print_in_place_gap(fit, layer_height=, material=)` returns three numbers:

| key | what it is | why |
|---|---|---|
| `xy` | gap on each side face, 0.20 / 0.30 / 0.40 mm (`tight` / `sliding` / `loose`), +0.05 for PETG/ABS/ASA | two perimeters squeezed side by side weld below it |
| `z` | gap above/below a horizontal face, `xy + layer_height` | the ceiling of a gap is a bridge and droops by about a layer |
| `bottom_chamfer` | 0.5 mm, 45° | elephant's foot closes gaps that start on the bed |

Published guides agree on the range: 0.20–0.30 mm per side for PLA on a
0.4 mm nozzle, 0.15 mm only on a well-calibrated machine, and 0.05–0.10 mm
more for PETG, which is tackier (Sovol, PrintStack3D). The gap is **radial**
(per side); a pin in a bore is `bore_d = pin_d + 2·xy`. State it once and
derive both mating faces from it ([[fit-derivation]]).

Pick the looser class when the mating area is large or the Z span is tall:
more touching area means more chances for one stray line to weld the joint.

## The bed closes gaps: elephant's foot

The first layer is squashed wider than the model (≈0.2 mm on a 0.4 mm
nozzle, Prusa), which is the same size as the whole XY gap. Any gap whose
bottom sits on the bed is therefore closed at layer one.

- Chamfer 45° every edge of a moving part and its housing that touches the
  bed, by `bottom_chamfer` (guides give 0.5–1.0 mm).
- Better: lift the gap off the bed. Start the moving part one or two layers
  above the plate by a `z` gap under it, so the only bed contact is the fixed
  part. A hinge knuckle that does not need to touch the bed should not.
- Do not rely on the slicer's elephant-foot compensation alone; it shrinks
  the outer contour, not the inside of a gap ([[fdm-first-layer-and-warping#elephants-foot]]).

## The ceiling closes gaps: bridges droop

The top of every horizontal gap is printed over air. A short bridge droops
about one layer; that is why `z > xy`. Beyond that:

- Keep every gap ceiling short, or give it an angle: a ceiling at 45° or
  steeper is an overhang, not a bridge, and does not droop into the gap
  ([[overhangs-and-print-orientation]]).
- A gap ceiling longer than a few millimetres is a real bridge. Size it by
  [[fdm-bridging-and-sacrificial-layers#how-far-a-bridge-can-go]]; the
  `+layer_height` in `z` is sized for a short one, so open `z` further (or
  angle the ceiling) and prove it with a test coupon.
- Never put a flat ceiling directly over a moving face that must stay
  smooth — the droop lands exactly there.

## Pin orientation

| pin axis | what prints | rule |
|---|---|---|
| **vertical (Z)** | round, accurate pin and bore; ceiling only at the pin head | preferred. Cone the pin head and the bore top (45°) so neither needs a bridge; retain with a cone or collar that overhangs ≤ 45° |
| **horizontal (in the bed plane)** | the bore's ceiling and the pin's underside are overhangs | teardrop: point the bore **up** (45° roof), flatten or 45°-cut the pin's **underside**; keep the round bearing surface on the sides that carry load ([[fdm-hole-accuracy#horizontal-holes-teardrops-and-horiholes]]) |

A horizontal round pin in a round bore fuses on both its underside (it sits
on its own sagging layers) and the bore's crown. The teardrop pair keeps the
same `xy` gap everywhere except at the two points, which open wider.

Knuckle faces between hinge leaves are vertical walls when the hinge axis is
horizontal: they take `xy`. When the hinge axis is vertical they are stacked
horizontal faces: they take `z`, and the lower one needs the bottom chamfer
if it is on the bed.

## Captive shapes

- **Hinges and flexi-toy joints.** One flexi pattern is a vertical pin
  (cone-topped) on one segment inside a C-shaped or ring socket on the next,
  the whole toy lying flat; the other is two loops crossed like chain links,
  which has no pin head to overhang
  ([[flexi-chain-joints]]). Each joint's range is set
  by **stops** — a tab on one segment that meets a face on the other — and
  each stop face takes the same `xy` or `z` gap as the bearing, or it welds
  first. Size link necks well above the minimum pin: the neck is what snaps
  when a stiff joint is freed ([[fdm-minimum-feature-sizes#features-pins-and-gaps]]).
- **Ball joints.** A sphere prints its lower half as an ever-steeper
  overhang and its south pole on a point. Put the ball's equator gap in XY
  and give the ball a flat or 45° cone base; truncate the socket lip at the
  equator's 45° line so the lip itself is self-supporting. A socket closing
  more than half the ball cannot be assembled, but printed in place it can —
  that is the reason to print it in place ([[joints#revolute-joints]]).
- **Captive gears.** Gear teeth take `xy` on the flanks **in addition to**
  the gear's own backlash; the face-to-housing gap under each gear takes `z`.
  Print gear axes vertical so teeth are extruded profiles and nothing
  bridges between teeth ([[gears#printed-tooth-choices]]).
- **Chain links.** Each link loop is printed in the plane of the bed or
  stood at 45°; a link crossing over another needs its crossing ceiling to be
  an overhang, not a flat bridge. Two links touching nowhere at rest is the
  condition to check (below), not "they look separate".

## Flexi chain joint: two crossed loops

A segmented flexi toy joins each pair of segments with two closed loops
threaded through each other at right angles, printed in place lying on its
belly. The loops, their gaps and sizes, the end faces that set the yaw range,
and what that range does to legs and to the body's look are on their own
page: [[flexi-chain-joints]].

## Supports are trapped by definition

Support inside a PIP gap cannot be removed; the gap is too thin to reach.
Design every gap self-supporting (≤ 45° overhangs, teardrops, cone heads,
short bridges) and, if the part still needs support elsewhere, block support
in the gap volumes (slicer support blocker). A design that only works with
support in the gap is a two-part design.

## Breaking free

A correctly gapped joint is often stiff off the bed: stringing and a few
touching points. Let the part cool to room temperature first, then work each
joint through a small range with the part supported close to the joint, and
stop if the neck whitens or bends (3DCentral). Design for it:

- give the user something to hold on both sides of each joint;
- no joint whose neck is weaker than the force needed to free a stuck joint;
- a first motion that loads the bearing, not a thin stop.

## Verify in CAD: the minimum distance, not "no interference"

`interfere` passes two bodies that **touch** (zero volume overlap), and a
touching pair is a fused joint. The check a PIP design owes is the minimum
distance between every pair of bodies that must separate:

```python
from itertools import combinations
for (na, a), (nb, b) in combinations(bodies.items(), 2):
    d = a.distance_to(b)              # build123d, BRepExtrema under the hood
    assert d >= GAP_XY - 1e-3, f"{na}/{nb} gap {d:.3f} < {GAP_XY}"
```

The minimum distance does not say *which* direction the gap runs; a
horizontal face pair must meet `GAP_Z`, not `GAP_XY`. Check horizontal face
pairs separately (section each joint at its axis, or measure between the
named faces). Check at the **rest pose** — the pose it is printed in —
not only across the motion ([[mechanism-verification#6-where-to-park-the-rest-pose]]).
Only a print shows whether the joint comes out free.

`distance_to` measures boundary to boundary: a pin that overlaps its bore, or
sits wholly inside the other body, still reports a positive gap. Run the
distance check only after `interfere` (or an intersection volume of zero) has
passed for the same pair ([[mass-properties-and-measurement]]).

## Checks

```python
g = cadfits.print_in_place_gap(FIT, layer_height=LAYER_H, material=MATERIAL)
assert g["z"] > g["xy"], "gap ceiling droops: Z gap must exceed XY gap"
assert BORE_D == PIN_D + 2 * g["xy"], "bore not derived from pin and gap"
assert min_body_distance >= g["xy"] - 1e-3, "bodies touch at rest: joint fuses"
assert all(z0 >= g["z"] or chamfered for z0, chamfered in bed_gaps), "bed-level gap closed by elephant's foot"
assert not supports_in_gap, "support trapped inside a print-in-place gap"
```
