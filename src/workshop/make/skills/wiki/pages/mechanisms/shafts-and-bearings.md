---
title: Shafts and bearings
tags: [shaft, axle, bearing, bushing, deflection, stress, collar, circlip, support, axial-location]
aliases: [spindle, journal, plain bearing, ball bearing, sleeve bearing, retaining ring, e-clip, set screw, beam deflection, segmented axle, axle too long to print]
sources:
  - Shigley's Mechanical Engineering Design, ch. 4 (beam deflection) and ch. 7 (shafts and shaft components)
  - ISO 15 (radial bearing boundary dimensions)
  - Roark's Formulas for Stress and Strain, beams table (simply supported and cantilever cases)
  - skills/cad/scripts/stdpart (bearings and snap rings from bd_warehouse)
  - "experience: walker hip journals that were a thin body wall, hung from a teardrop roof, with a key flat running in the bearing"
related: [joints, gears, mechanism-design, beam-and-plate-stiffness, exact-constraint-and-kinematic-mounts, noise-and-vibration, shaft-hub-connections, rod-ends-and-clevises, swivels-and-turntables]
updated: 2026-10-07
---

# Shafts and bearings

A shaft layout answers four questions for every axis before any part around
it is drawn: what the shaft is made of, what supports it, what stops it
sliding along its axis, and how torque gets onto and off it. Each answer is a
parameter and most of them owe an `assert`.

## Printed shaft or bought rod

| shaft | use when | notes |
|---|---|---|
| **printed, lying flat** | slow toy drives, short spans, parts keyed to the shaft | strong along the extrusion lines; print with a D-flat on the bed so it is not a round overhang ([[joints#keyed-joints]]) |
| **printed, standing up** | never for a shaft that carries a bending load | its layers are cross-sections: it snaps at a layer line under bending |
| **steel rod / dowel pin** | long spans, motor speeds, anything that must stay straight | about 60–80 × stiffer than printed PLA at the same diameter; buy standard diameters (2, 3, 4, 5, 6, 8 mm) and derive the printed bore with `cadfits` |
| **brass / aluminium tube** | light, long, or wiring through the axis | check the wall against the set screw or pin that drives it |

Printed shafts below about 5 mm are fragile; below 3 mm use metal.

A shaft longer than the bed is not a reason to buy a rod: segment it
([[#an-axle-longer-than-the-bed]]).

## An axle longer than the bed

A fixed axle carrying a row of pivots (the ground pivots of a linkage walker,
a comb of levers) is often longer than any bed. A bought rod solves it, but
then the kit does not come off the printer. Segment the axle at the pivots it
carries:

- **Bodies between the pivots, a pin through each.** Each body fills the gap
  between two pivot stacks and prints standing, its end faces on the bed. A
  separate pin runs through the pivot stack into a socket in the body each
  side, and is that pivot's journal. Both halves have their joint face on the
  bed, which is the case for a dowel rather than a plug
  ([[fdm-joining-split-prints#connectors]]).
- **The pin prints lying on a deep D-flat.** It is the only part bending
  across the gap, and standing it breaks at a layer line. The curve must leave
  the flat steeper than 45°: flat depth `r (1 − cos θ)` with θ about 50°, a
  third of the radius. A shallow flat leaves a down-facing band under 45° that
  runs the whole length of the pin; that is an overhang, not a ledge, and
  `check_overhang` fails it (a 0.6 flat on an 8 mm pin did).
- **A deep flat costs little.** In a round running hole the hole's curve
  catches on the flat's two edges, so the flat side runs only about 0.1 mm
  looser than the round side, not the flat's depth looser. Turned sideways to
  the load, the flat removes material near the neutral axis and keeps about
  94 % of the round section's `I`; turned toward the load it loses about a
  third. Put it where the pivot is loaded least: sideways under a vertical load.
- **Key the socket with the flat.** A D-socket locates the pin; in a round
  socket it floats by the flat's depth, and a chain of floating joints no
  longer meets the far frame.
- **The pin bottoms in both sockets.** Its length, printed in XY, then sets the
  pivot's running play; glue cannot. One pin diameter of engagement per side.
- **The end bodies sit in pockets in the frames.** The pocket, not a pin,
  carries the end moment.
- **The bare pins decide the sag.** A pin through a pivot stack is bounded by
  the hole the plate end can take, and the pins near mid-span sit where the
  moment is largest, so they carry most of the deflection while being a small
  part of the length. Compute it with the section changing along the span,
  `δ = F ∫ m(s)² / (E I(s)) ds` with `m` the moment of a unit load at the
  point, not with one diameter. A thicker body buys little; a larger pin, or
  fewer and shorter gaps, buys most.

## Stiffness: deflection decides before strength does

A printed shaft almost always bends too much long before it breaks. Model it
as a beam, `I = π d⁴ / 64`:

```text
simply supported, load F at mid-span L:    δ = F L³ / (48 E I)
cantilever (overhung) load F at length a:  δ = F a³ / (3 E I)
```

Elastic modulus `E` (order of magnitude — printed parts vary with infill,
orientation and temperature): printed PLA ≈ 2.5–3.5 GPa, printed PETG ≈
1.8–2.2 GPa, aluminium ≈ 69 GPa, brass ≈ 100 GPa, steel ≈ 200 GPa.

Where a gear sits on the shaft, the deflection under the tooth load
separates the mesh and eats backlash. Keep deflection at a gear under half the
designed backlash ([[gears#printed-tooth-choices]]):

```python
import math
I = math.pi * SHAFT_D**4 / 64
delta = F_TOOTH * SPAN**3 / (48 * E_SHAFT * I)
assert delta <= 0.5 * BACKLASH, f"shaft bends {delta:.3f} mm at the gear"
```

Deflection scales with `L³ / d⁴`: halving the span buys 8×, one size up in
diameter buys ~2× — shorten the span first.

Other load cases and sections, plates, torsion and buckling:
[[beam-and-plate-stiffness]].

## Strength

Bending stress `σ = 32 M / (π d³)`, torsion `τ = 16 T / (π d³)`, combined
(von Mises) `σ' = sqrt(σ² + 3 τ²)`. For printed shafts use the strength
*across* layers when the layers are not along the axis, and a safety factor
of 3 or more: printed strength scatters and creeps under a steady load.

## Supports and spans

- **Two supports, spaced apart.** Space them at least 2–3 × the shaft
  diameter; one long bore is a worse bearing than two short ones far apart.
- **Each support ≥ 1.5 d long** for a printed journal ([[joints#revolute-joints]]).
- **Keep overhung loads short.** A gear or crank outboard of the last support
  at distance `a` loads that support by roughly `F (1 + a / span)`; keep
  `a` well under the span.
- **Put loads next to supports**, not mid-span, when the layout allows.

## A journal the load hangs from

When a body hangs from its journals — a walker on its hip axles, a cradle,
a pendulum — each shaft bears **up on the roof** of its bore. A horizontal
hole printed with a 45° teardrop top puts a V-block exactly there: two lines
of contact, `1 / cos 45° = 1.41×` the friction of a round bore.

- Give a printed bore loaded upward a **flat roof just over the circle**
  (`max_z = z + r + 0.05`; a roof tangent to the circle troubles the kernel):
  a bridge of about `0.8 r`, one line of contact. Or print the bearing as a
  standing bushing, whose bore is round.
- **Never run a key flat through a bearing.** Key only the length inside the
  hub; round everywhere the shaft turns. A flat in the journal puts its two
  edges on the loaded roof once a turn.
- **A wall too thin for 1.5 d:** when the wall is the journal and the part
  outboard of it turns, press a printed **bushing** in from outside onto a lip
  left in the wall, standing proud into a cup in the turning part. Print it
  standing; give the cup free clearance so it never becomes a second bearing;
  put the lip on the side the end thrust pushes toward. A fixed boss in the
  same place is a horizontal peg in a belly-down print, and the turning part
  round it leaves no room for a keel.

```python
assert JOURNAL_LEN >= 1.5 * SHAFT_D
assert CUP_R - BUSHING_OD / 2 > (BORE_D - SHAFT_D) / 2, "the cup must not bear"
assert ROOF_Z - (AXIS_Z + BORE_D / 2) < (BORE_D - SHAFT_D) / 2, "the journal bears on the flat roof"
```

## Bushing or ball bearing

| bearing | when | notes |
|---|---|---|
| printed journal (bore `slot_for(d, RUN)`) | hand cranks, automata, tens of rpm, light load | the default for toys; PLA on PLA squeaks and wears — PETG or a steel shaft in a PLA bore runs better |
| bronze / sintered bushing | moderate speed, dirt, higher load | a bought part: search `$step-parts`, seat with `cadmount` |
| deep-groove ball bearing | motor speeds, low friction, precise location | search `stdpart` first: `bd_warehouse` builds it with the housing bore derived, never typed |

Common deep-groove sizes (ISO 15, bore × OD × width, mm): MR63 3×6×2.5,
MR85 5×8×2.5, MR105 5×10×4, 623 3×10×4, 624 4×13×5, 625 5×16×5,
626 6×19×6, 688 8×16×5, 608 8×22×7, 6000 10×26×8. The number is a lookup key
for the catalog, not a dimension to type into the model.

A printed housing for a ball bearing: a `snug` or `press` seat from `cadfits`,
a shoulder on one side for axial location, a chamfered lead-in, and the
housing wall at least 2 extrusion widths — a thin press seat splits along a
layer line.

Bushing squeak and bearing noise: [[noise-and-vibration]].

## Axial location: fixed and floating

Locate the shaft axially at **one** support only (the fixed bearing) and let
the other float. Locating at both supports fights every print error and
thermal change and preloads the bearings or binds the journal.

Ways to stop a shaft (or a part on it) moving along the axis:

| stop | notes |
|---|---|
| shoulder on the shaft | printed shafts; the cheapest and most exact |
| head of a shoulder pin | [[joints#revolute-joints]] |
| e-clip / circlip in a groove | metal shafts; the groove comes from `stdpart` snap rings, never typed; pins and their clips: [[rod-ends-and-clevises#clevis-pins-and-what-holds-them]] |
| collar with set screw | M3 grub screw into a captive nut; tighten on a flat |
| the next part in the stack | legitimate only if that part is itself proven held |

Every axial stop is a `blocked` condition in the motion manifest.

The general rule behind fixed-and-floating — count the constraints:
[[exact-constraint-and-kinematic-mounts]].

## Getting torque on and off

Single D-flat for any phased part; pin through the shaft for high torque with
exact phase; press fit only for parts that never come off. The whole list is
[[joints#keyed-joints]]. A set screw on a round shaft slips — always drive it
onto a flat. Torque capacity of every hub form (keys, splines, polygons, set
screws, clamp hubs, tapers, Hirth teeth) is in [[shaft-hub-connections]].

## Checks

```python
assert SUPPORT_SPACING >= 2 * SHAFT_D, "supports too close: the shaft rocks"
assert JOURNAL_LEN >= 1.5 * SHAFT_D, "journal too short: the shaft wobbles"
assert OVERHANG < SUPPORT_SPACING, "overhung load longer than the span"
assert delta <= 0.5 * BACKLASH  # at every gear, from the section above
```

In the motion manifest: every shaft `clear` along its insertion axis from the
open side and `blocked` at its axial stop, with the retention chain closed at
a fixed root ([[mechanism-verification]]).
