---
title: Stability and tipping
tags: [stability, tipping, center-of-mass, ballast, support-polygon, incline, figurine]
aliases: [tip over, tipping angle, topple, overturn, centre of gravity, center of gravity, cog, com, centre of mass, base footprint, standing figure, stands on one foot, wobble, rocking base, anti-tip, weighted base, inclined plane test]
sources:
  - Meriam & Kraige, Engineering Mechanics: Statics, ch. 5 (centre of mass) and ch. 6 (friction, tipping versus sliding)
  - https://law.resource.org/pub/eu/toys/en.71.1.2014.html (EN 71-1:2011+A3 4.15.1.4, 4.16, 8.23.1 (10 ± 1)° with 25/50 kg load, 8.23.2 (5 ± 1)° heavy immobile toys, Figure 26 load)
  - https://www.seguridadelectrica.com/english/inclined-plane.php (IEC 60335-1 cl. 20.1, 10° incline, 15° for heating appliances)
  - https://ahfa.us/article-template/quick-answers-to-key-questions-concerning-f205723 (ASTM F2057-23 tests: 10 lb at ≤ 56 in, 0.43 in block + 60 lb, 27 in scope)
  - https://en.wikipedia.org/wiki/Density (steel 7850, lead 11340, brass 8600, zinc 7000, sand 1600–2000 kg/m³)
  - .venv/lib/python3.12/site-packages/build123d/topology/three_d.py (Solid.center, CenterOf.MASS via GProp, density 1)
  - https://content.iospress.com/articles/work/wor01670 (tablet tilt 0/30/45/60 deg and self-chosen: self-chosen mean about 34 deg preferred, 0 and 60 least; range 20-50 deg at minimum)
  - https://arxiv.org/pdf/2308.15190 (finger swipes on touchscreens held at 0.5-1.5 N normal force)
  - https://www.iplab.cs.tsukuba.ac.jp/~ikeda/pdf/asian_chi_2020_ikeda.pdf (tap normal forces 0.1-0.9 N)
  - .venv/lib/python3.12/site-packages/build123d/topology/shape_core.py (Shape.compute_mass, Shape.combined_center)
related: [filament-properties, toy-safety-constraints, fdm-first-layer-and-warping, perimeters-infill-and-strength, wheeled-vehicles, handheld-ergonomics, perspective-and-hidden-views, exact-constraint-and-kinematic-mounts, counterweights-and-gravity-balance, swivels-and-turntables]
updated: 2026-10-04
---

# Stability and tipping

An object stands while the vertical through its centre of mass (CoM) falls
inside its support polygon. Everything on this page turns that into two
numbers you can assert: the **tipping angle** and the **tipping force**. Read
it for any figure, stand, lamp, vehicle or display piece that must stand
unattended, and before accepting a reference whose pose looks top-heavy.

## Support polygon and centre of mass

- The **support polygon** is the convex hull of the contact points, not the
  footprint outline. Three feet make a triangle; a ring base makes a disc; a
  figure on one foot has only that foot's contact patch.
- The CoM of a composite body is the mass-weighted mean of its parts:

```text
m = Σ ρ_i V_i
c = Σ ρ_i V_i c_i / m          c_i = centroid of part i
```

- Stability margin in plan, `d`, is the shortest horizontal distance from the
  CoM's ground projection to the polygon edge. `d <= 0` means it falls over.

## Tipping angle

Tilt the body about the edge nearest the CoM. It tips when the CoM passes
vertically over that edge:

```text
theta_tip = atan(d / h)        d = plan distance CoM → tipping edge, h = CoM height
```

Worked: a base half-width 30 mm, CoM 80 mm high → atan(30/80) = 20.6°.
The same figure on a single 12 mm-wide foot centred under the CoM → d = 6 mm,
atan(6/80) = 4.3°: it falls over when the shelf is bumped.

Check every edge of the polygon, and use the **smallest** d. On a slope the
body also slides once `tan(theta) > μ`; rubber feet raise μ so it tips instead
of sliding, and a hard, slippery base may slide before it tips.

## Pushed over: force and energy

A horizontal push F at height `h_F` tips a body of weight `W = m g` when its
moment about the edge beats the restoring moment:

```text
F_tip = W * d / h_F                  (it slides first if μ W < F_tip)
E_tip = W * (sqrt(d² + h²) - h)      energy to lift the CoM over the edge
```

Doubling `d` roughly doubles both; halving `h` halves the push height a
child or a sleeve can exert leverage from. A tall, light piece has a tiny
`E_tip`: a light knock topples it even when its static angle looks fine.

## A touch surface on a desk

A screen people tap and swipe is pushed every time it is used, so a desk
touchscreen's case is a stability problem before it is a styling one.

- **Loads.** Taps press 0.1–0.9 N normal to the glass; swipes are held at
  0.5–1.5 N normal, plus fingertip friction along the glass. Design to a 3 N
  firm press at the far edge of the active area, a stated design choice.
- **Tilt.** With the angle free, tablet users pick about 34° from the desk and
  like 0° and 60° least; give at least 20–50° when it adjusts. A fixed tilt
  near 30° serves most desks.
- **Keep the screen's plan inside the support polygon.** A press is mostly
  vertical: if the whole screen projects inside the feet, the vertical part
  can never tip the case, and only `F sin(tilt)` plus the swipe friction act
  as the horizontal push in `F_tip = W d / h_F` above.
- **Hinge a tilting screen at its low edge.** Every press then lands behind the
  hinge and pushes the screen onto its prop or ratchet. A pivot under the
  middle turns every press on the front half into a lever that lifts the
  screen off its support.
- **Capture the edge of a screen that rests on a support.** A slab propped on
  a block, stone or kickstand levers its free edge up when pressed beyond the
  support: with contact at `a` from the edge and a press at `b > a`, the edge
  lifts once `F (b - a)` beats the slab's own weight moment, which for a light
  slab is well under 1 N. Pin the edge to the base.
- **Flush glass.** A raised bezel stops edge swipes. Set the lens flush and keep
  every ledge, lip or tray below the glass plane.
- **A ledge for a device leaning on a face.** Make the ledge floor square to
  the face, so the device's bottom edge sits flat on it (a level floor carries
  it on one corner, and edge contacts cannot touch). A device of thickness `T`
  on a face at `θ` from the desk has its front-bottom edge `T cos θ` above its
  back-bottom edge, so a lip that retains it stands at least `T cos θ` plus the
  lip height above the groove corner: 8.7 mm plus lip for 10 mm at 30°, 5 mm
  plus lip at 60°. Concept renders often draw a 3 mm cradle under a 10 mm
  device; the functional lip then costs side-view likeness, and that is a
  recorded deviation, not a modelling error.
- **Two faces, two tip cases.** A stand with a steep and a shallow face tips
  backward only from the steep one: the press on a steep face is mostly
  horizontal and high, on a shallow face mostly vertical and inside the feet.
  Check each face with the device on it and the press at its far edge.

## How much angle is enough

Published tests, all "must not tip":

| product | test |
|---|---|
| toys that bear a child's mass (EN 71-1 8.23.1) | loaded with 50 kg (25 kg for under 36 months), a Ø150 × 300 mm cylinder with its CoM 150 mm up, on a (10 ± 1)° slope, most onerous position |
| heavy immobile floor toys ≥ 4.5 kg (EN 71-1 8.23.2) | (5 ± 1)° slope, moving parts in the most onerous position |
| household appliances (IEC 60335-1 cl. 20.1) | 10° incline, doors and cord in the worst position, containers empty or full; 15° for heating appliances |
| clothing storage units ≥ 27 in (ASTM F2057-23) | 10 lb horizontal at the highest handhold ≤ 56 in; 60 lb on an open drawer with a 0.43 in block under the rear legs (carpet); plus an anti-tip restraint |

No standard sets an angle for a desk figure or ornament. Treat the 10°
appliance test as the design floor for anything that stands on a table, and
state it in the spec as a design choice. Test the **worst configuration**: arms
raised, drawer or door open, reservoir full or empty, accessory attached.

## Making it stand

In order of cost to the likeness:

1. **Lower the CoM.** Hollow or sparse-infill the upper body, solid-fill the
   base ([[perimeters-infill-and-strength]]). A printed part's CoM is not its
   solid centroid: shell and infill have different densities (below).
2. **Add ballast low.** Steel (7.85 g/cm³) is 6–7 × PLA (1.17), lead 11.3 but
   not in toys ([[toy-safety-constraints]]), brass 8.6, zinc 7.0, dry sand
   1.6–2.0. Steel balls, nuts or washers in a closed pocket in the base are
   cheap and measurable; seal them in so they neither rattle nor escape
   ([[magnets-and-strap-slots]] shows the pause-and-drop pocket).
3. **Widen the polygon.** A plinth, a tail or cloak touching the ground, a
   third point of contact, or an outrigger. A hidden clear acrylic or wire
   stand beats an oversized plinth when likeness matters.
4. **Pin it.** A figure on one foot can carry a pin or magnet into a
   separate base; then the base, not the foot, is the polygon.

Ballast densities and packing: [[counterweights-and-gravity-balance]].

## A base that rocks is not a polygon

A printed flat base warps, and a slightly convex base rocks on one point.
Relieve the centre so only a rim or three pads touch
([[fdm-first-layer-and-warping#design-against-warping]]); three pads define
the plane exactly. Add elephant's-foot allowance on the contact edge, and
place rubber feet at the polygon's corners, not inboard of them.

Four feet are one constraint too many:
[[exact-constraint-and-kinematic-mounts]].

## Computing it in build123d

`Solid.center(CenterOf.MASS)` (the default) returns the **volume** centroid:
OCC's GProp is run with unit density. `Shape.compute_mass(s)` returns the
volume, and `Shape.combined_center(shapes)` is the volume-weighted mean. None
of them know materials, so weight by density yourself:

```python
from build123d import CenterOf, Vector

def com(parts):                      # parts: [(shape, density_g_cm3, fill), ...]
    tot, acc = 0.0, Vector(0, 0, 0)
    for shape, rho, fill in parts:   # fill ≈ solid fraction of a printed part
        m = shape.volume * rho * fill
        acc += shape.center(CenterOf.MASS) * m
        tot += m
    return acc / tot, tot / 1000.0   # mm, grams (mm³·g/cm³ /1000)
```

- A `Compound` of solids that overlap counts the overlap twice; build a
  clean assembly or subtract before weighing.
- For a printed part, split it into shell and core when the distinction
  matters: the shell (perimeters, top/bottom) is ~100 % dense, the core is
  the infill fraction. A single `fill` factor is a first estimate only.
- The support polygon comes from the contact faces: the faces at the lowest
  Z (within a tolerance), their vertices projected to X-Y, their convex hull.

## Checks

```python
import math
d = min_edge_distance(com_xy, support_hull)          # mm, > 0 inside
assert d > 0, "CoM projects outside the support polygon"
theta = math.degrees(math.atan2(d, com_z))
assert theta >= TIP_MIN_DEG, f"tips at {theta:.1f}°, need {TIP_MIN_DEG}°"
F_tip = mass_kg * 9.81 * d / PUSH_H                  # N at push height PUSH_H
assert F_tip >= PUSH_MIN_N, f"topples under {F_tip:.2f} N"
```
