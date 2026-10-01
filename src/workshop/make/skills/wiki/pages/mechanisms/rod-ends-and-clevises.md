---
title: Rod ends, clevises and pinned rod joints
tags: [clevis, fork, knuckle, cotter, rod-end, ball-stud, retention, pin, linkage, spherical]
aliases: [knuckle joint, fork and eye, fork joint, clevis joint, clevis fork, fork head, clevis pin, headed pin, ISO 2341, cotter joint, socket and spigot joint, gib and cotter, split pin, cotter pin, ISO 1234, R-clip, R-pin, hairpin clip, hairpin cotter, hitch pin clip, spring cotter, bridge pin, beta pin, linch pin, lynch pin, clevis clip, safety clip, E-clip, circlip, retaining ring, push nut, push-on fix, starlock, rod end, rod end bearing, heim joint, rose joint, spherical plain bearing, spherical rod end, angle joint, ball socket, ball stud, ball link, ball cup, RC ball end, linkage ball joint, gas strut end fitting, gas spring eyelet, turnbuckle]
sources:
  - Khurmi and Gupta, A Textbook of Machine Design, ch. 12 Cotter and Knuckle Joints (knuckle proportions, pin bending assumption, failure equations; read via https://www.rcet.org.in/uploads/academics/rohini_66824744342.pdf)
  - https://extrudesign.com/how-to-design-socket-and-spigot-cotter-joint/ (eleven cotter failure modes; t = 0.31 d proportions; taper ≤ 1 in 24; cotter load distribution)
  - https://coeng.uobaghdad.edu.iq/wp-content/uploads/sites/3/2019/02/KNUCKLE-JOINT.pdf (gib and cotter: the gib holds the strap closed, gives parallel slots and a larger bearing face)
  - https://testbook.com/mechanical-engineering/cotter-joint-definition-diagram-and-applications (taper 1 in 48 to 1 in 24)
  - https://www.designworldonline.com/what-is-a-cotter-joint/ (taper below the friction angle; not on rotating shafts; positive lock under vibration)
  - https://boltport.com/standards/iso-2341/ (ISO 2341 split-pin hole against pin diameter)
  - https://www.stainlessfix.com/iso-2341/ (form A plain, form B with hole; d h11, d1 H13)
  - https://aimsindustrial.com.au/blogs/product-guides/split-pin-cotter-pin-guide (split pin sized to the hole; bend the legs both ways; single use; R-clips hold less)
  - https://www.aspenfasteners.com/content/pdf/Metric_DIN_11024_spec.pdf (DIN 11024 R-clip hole against pin diameter range)
  - https://en.wikipedia.org/wiki/R-clip
  - https://en.wikipedia.org/wiki/Linchpin
  - https://www.jwwinco.com/en-us/products/3.6-Moving-Transferring-Connecting-with-Joints-Couplings-and-Gears/Fork-joints/GN-751-Steel-Clevis-Fork-Joint-with-Circlip-or-Snap-on-Securing-Collar (DIN 71752 fork heads: snap-on collar, single and double clip)
  - https://www.designworldonline.com/1-reason-for-retaining-ring-failure-how-to-overcome-it/ (groove deformation 90 % of failures; edge margin 3 × groove depth; square corner on the retained part)
  - https://www.rotorclip.com/formulas-retaining-ring-load-capacity/ (groove thrust capacity Pg; y/d ≥ 3)
  - https://www.viba.nl/media/files//dw-resources/103682%2020456starlocks_-_metric.pdf (Starlock: plain steel, non-ferrous or plastic shafts; ± 0.05 mm to 16 mm; not removable without destruction)
  - https://www.intafast.com/wp-content/uploads/2019/11/Roundshaft-starlocks_Metric_imp.pdf (Starlock push-on and pull-off forces)
  - SKF, Spherical plain bearings and rod ends, catalogue (https://www.loziska-policka.cz/user/documents/upload/SKF%20-%20Spherical%20Plain%20Bearings%20and%20Rod%20Ends.pdf), angle-of-tilt tables, permissible loads for rod ends, attachment of rod ends
  - https://www.firgelliauto.com/blogs/mechanisms/rod-end-bearing (9–15° per side; shank breaks at the thread root under side load; engagement ≥ 1.5 × thread; left and right hand ends)
  - https://www.designjudges.com/articles/rod-ends-and-spherical-bearings (axial capacity 5–10 % of radial; top-hat high-misalignment spacers)
  - https://www.jwwinco.com/en-us/products/3.6-Moving-Transferring-Connecting-with-Joints-Couplings-and-Gears/Angled-Ball-Joints-Axial-Ball-Joints/DIN-71802-Steel-Threaded-Ball-Joint-Linkages-with-Threaded-Stud (DIN 71802 = DIN 71805 socket + DIN 71803 stud; 15°/18°; balls 8–19 mm; pull-off 30–100 N)
  - https://www.driftmanjirc.com/products/rc-plastic-ball-cup-end-set-4-8mm-yeah-racing (RC ball cups, tight and free fits)
  - https://naughtyboyrc.com/products/naughty-boy-rc-car-turnbuckle-rod-ball-cup-stud-end-remover-tool-4-4-8-5-5-8mm (4, 4.8, 5 and 5.8 mm RC balls; cups overstretch on removal)
  - https://www.stabilus.com/media/default/STABILUS/PDF/Stabilus_Gas_Springs_Dampers_Brochure_EN_2023.pdf (no twist, lateral force or bending on a gas spring; angle joints; rod down)
  - https://www.hinscha.com/en/gas-springs/gas-spring-end-fittings (eye, ball-and-socket, fork-head end fittings, M5–M14)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC10097255/ (printed PLA/ABS pin-loaded holes: bearing failure only at e/D ≥ 3)
  - https://www.igus.com/spherical-bearings/rod-ends (self-lubricating plastic rod ends)
  - skills/cad/scripts/cadfits.py (slot_for, mating_clearance)
related: [joints, hinges-and-pin-joints, hinge-types, ball-and-socket-joints, push-pins-and-clip-fasteners, shafts-and-bearings, dowel-pins-and-press-fits, snap-fit-design, linkages, counterweights-and-gravity-balance, layer-anisotropy, fdm-print-orientation-for-strength, fdm-bridging-and-sacrificial-layers, lead-screws, creep-and-stress-relaxation]
updated: 2026-10-01
---

# Rod ends, clevises and pinned rod joints

How a rod or link meets its pin: fork and eye, wedge through a socket, ball
in an eye, ball stud in a snap socket. Choose by the freedom the rod needs,
size by the failure checks, then pick the retainer. Hinge knuckles:
[[hinges-and-pin-joints]]; posing ball joints: [[ball-and-socket-joints]].

## Which rod joint

| joint | freedom | carries | use when |
|---|---|---|---|
| **knuckle joint / clevis** (fork + eye + pin) | 1 rotation | tension; compression only if the rods are guided | links, tie rods, levers, cylinder ends |
| **cotter joint** (spigot, socket, tapered cotter) | none | tension and compression | coaxial rods taken apart for service; never on a turning shaft (it works loose) |
| **rod end** (spherical plain bearing in an eye) | 3 rotations inside a cone | load along the shank | push rods and links whose pivots are not parallel |
| **angle joint / ball link** (ball stud + snap socket) | 3 rotations inside a cone | light load across the stud | throttle and RC linkages, gas springs |

Parallel pins need knuckles only. A spherical end on one end of a link whose
pins may be out of parallel removes the over-constraint
([[exact-constraint-and-kinematic-mounts#over-constraint-in-printed-assemblies]]).

## Knuckle joint: proportions and failure checks

Rod diameter `d`, pin `d1`, eye outside diameter `d2`, eye thickness `t`,
each fork cheek `t1`, axial load `P`, allowable stresses σt, τ, σc. The
textbook proportions for a steel joint are `d1 = d`, `d2 = 2d`, pin head and
collar `d3 = 1.5d`, `t = 1.25d`, `t1 = 0.75d`, head thickness `t2 = 0.5d`.
Then check each way it can fail:

```text
rod tension        P = (π/4) d² σt
pin double shear   P = 2 (π/4) d1² τ
pin bending        M = (P/2)(t1/3 + t/4),   σb = 32 M / (π d1³)
eye tearing        P = (d2 − d1) t σt
eye shear-out      P = (d2 − d1) t τ
eye crushing       P = d1 t σc
fork tearing       P = (d2 − d1) 2 t1 σt
fork shear-out     P = (d2 − d1) 2 t1 τ
fork crushing      P = d1 2 t1 σc
```

- **The pin bends because it is loose.** Its load is uniform along the eye
  and linear over each cheek, so each half load acts `t1/3` from the cheek's
  inner face. A running gap `c` per side adds `c` inside the bracket;
  `d1 = d` is the textbook margin for this bending.
- Fork gap `t + 2 · mating_clearance(RUN)`, never `t`. Bores
  `slot_for(d1, RUN)`, or `SEAT` in the cheeks when they hold the pin.
- Head at one end, a collar and split pin at the other
  ([[#clevis-pins-and-what-holds-them]]).

## Cotter and gib-and-cotter joints

A tapered cotter driven through slots in a spigot and its socket draws the
spigot in until a collar seats. The cotter stays put because its taper
angle is below the friction angle: `tan(taper) < μ`. Use a taper of 1 in 48
to 1 in 24 (2.4° at 1 in 24); a steeper one needs a locking device.

Symbols: `d2` spigot, `d1` socket outside, `d3`/`d4` spigot/socket collar,
`t` × `b` cotter section, `a`/`c` spigot/socket end beyond the slot, `t1`
spigot collar thickness. Bending assumes uniform load across the spigot,
falling linearly to zero across each socket collar.

```text
spigot across slot   P = ((π/4) d2² − d2 t) σt
socket across slot   P = ((π/4)(d1² − d2²) − (d1 − d2) t) σt
cotter double shear  P = 2 b t τ
crushing on cotter   P = d2 t σc  (spigot)      P = (d4 − d2) t σc  (socket collar)
end shear-out        P = 2 a d2 τ  (spigot)     P = 2 (d4 − d2) c τ  (socket)
spigot collar        P = (π/4)(d3² − d2²) σc,    P = π d2 t1 τ
cotter bending       M = (P/2)(d2/4 + (d4 − d2)/6),   σb = 6 M / (t b²)
proportions (steel)  t = 0.31d, d2 = 1.21d, d1 = 1.75d, d3 = 1.5d, d4 = 2.4d,
                     a = c = 0.75d, b = 1.3d, t1 = 0.45d
```

**Gib and cotter** joins a square rod to a forked strap. Driven alone, the
cotter's friction springs the strap open; a gib (a wedge with lugs) goes in
first, holds the strap shut, and gives parallel slots and a larger face.

## Clevis pins and what holds them

A clevis pin (ISO 2341) is headed; form A is plain, form B has a split-pin
hole of about a quarter to a third of the pin diameter. The pin is h11, so
it runs free. The hole sits just outside the far washer; take the numbers
from the vendor STEP (`$step-parts`).

| retainer | holds by | reuse | rule |
|---|---|---|---|
| **split (cotter) pin**, ISO 1234 | legs bent round the pin | no | ordered by the hole it goes in; legs come out at least one pin diameter, one bent back and one forward |
| **R-clip / hairpin / spring cotter** | straight leg through the hole, belly grips the pin | yes | DIN 11024 sizes by pin range: the smallest is a 2.5 mm hole for 9–11.2 mm pins; holds less than a split pin |
| **linch pin** | pin through the hole, spring bow snaps over the end | yes | wheels and hitches; the bow must clear whatever turns past it |
| **spring clip / snap-on collar** (DIN 71752 fork heads) | wire clip in a groove or hole | yes | single clips hold one side, double clips both |
| **E-clip** (DIN 6799) | pushed on sideways into a groove | yes | light thrust only; not in `stdpart`, so search `$step-parts` |
| **circlip** (DIN 471 / 472) | sprung into a square groove | yes | `stdpart sizes ExternalSnapRing`, groove from `RetainingRingGroove` |
| **push-on fix** (Starlock) | spring teeth bite a plain shaft | no | shaft ±0.05 mm up to 16 mm and softer than the fix; pull-off 2–7 × the push-on force |
| **O-ring or TPU ring in a groove** | friction and elastic grip | yes | rattle-free; low thrust; gland from `stdpart sizes ORing` |

- **A ring fails by its groove** (about 90 % of failures). In a soft groove
  `Pg = Gf · D · d · π · σy / (K1 · Fs)` governs, not ring shear: `D` shaft,
  `d` groove depth, σy the groove's yield. Edge margin ≥ 3 × groove depth;
  the retained part gets a square corner, since a chamfer loads the ring tip.
- A printed groove yields at the plastic's σy, less across layers: groove a
  steel pin or let a head and cap carry thrust ([[hinges-and-pin-joints#pin-retention]]).
- ±0.05 mm is tighter than a printed pin holds: push-on fixes go on steel.
- Axial location of the shaft itself: [[shafts-and-bearings#axial-location-fixed-and-floating]].

## Rod ends: spherical bearings in an eye

A rod end (heim or rose joint) is a spherical plain bearing in an eye on a
threaded shank (ISO 12240-4). The bolt clamps the ball; the eye tilts in a
cone about it.

- **Misalignment.** The angle of tilt α is per side; the total is 2α.
  Small standard series give about 10–16° (SKF GE 4–12 E, SI 6–12 E); larger
  sizes 6–10°; heavy GEH series 15–17°.
- **Let it tilt.** Spacers clamping the ball step down to the inner ring
  (≤ `da max`); a full-width cheek pinches the housing. Top-hat spacers buy
  more cone.
- **Load along the shank.** Keep the side component under 0.1 · C0 (SKF);
  the axial capacity of a spherical bearing is only about 5–10 % of the
  radial. Off-axis load breaks the shank at the thread root.
- **Double shear.** Mount the eye in a clevis, not cantilevered on one bolt.
- **Turnbuckle:** one left-hand and one right-hand end; jam nut on each,
  thread engaged ≥ 1.5 × its diameter. Plastic rod ends (igubal) run dry.

## Ball links, angle joints and ball studs

A DIN 71802 angle joint is a DIN 71805 ball socket on a DIN 71803 ball stud
(balls 8–19 mm), swivelling 15° with its safety catch and 18° without. The
socket is pushed over the ball and a spring ring holds it; the minimum
pull-off is only 30–100 N, smallest to largest. RC models use
plastic ball cups on 4, 4.8, 5 or 5.8 mm balls, sold in tight and free fits.
Prying one off overstretches the cup.

- It is an annular snap: a pull along the stud is the separating force
  ([[snap-fit-design#mating-and-separating-force]]). Load it across the stud,
  or add the safety clip; size cups for repeated use
  ([[snap-fit-design#permissible-strain]]).

## Gas spring end fittings

Eye, ball socket, fork head or angle joint, on M5–M14 threads. A gas spring
must see no twist, side load or bending: a spherical fitting at each end,
rod pointing down. Sizing and anchors: [[counterweights-and-gravity-balance#gas-springs-for-lids]].
The ball centre stands off the printed bracket, so the force also bends the
bracket and pulls on the stud's insert.

## Printing rod joints

- **Eyes and lugs print flat, bore vertical.** The tearing ligaments then
  pull along the layers and the shear-out planes cut across them. With the
  bore horizontal, the eye shears out along a layer line
  ([[fdm-print-orientation-for-strength#orient-by-load]]).
- **Edge distance.** Printed PLA and ABS pin-loaded holes broke by net
  tension or cleavage at `e/D = 1.5` and reached bearing failure only at
  `e/D ≥ 3`. The steel eye (`e/D = 1`) is too lean: `e ≥ 3 · d1`, or bush it.
- **A printed fork** lying flat has its upper cheek overhanging the gap. A
  sacrificial wall across the fork mouth turns that roof into a short bridge
  ([[fdm-bridging-and-sacrificial-layers#design-out-the-bridge]]); or print
  two flat cheek plates. Cheeks standing up print easily, but the bores are
  teardrops and the cheeks shear along layers.
- **Pins** are steel dowels or clevis pins whenever the joint carries load
  ([[dowel-pins-and-press-fits]]); a printed pin lies down and runs in double
  shear ([[hinges-and-pin-joints#pin-and-knuckle-sizing]]).
- **A printed cotter** lies flat: its taper is an X-Y outline, not a layer
  staircase, and its slot through a flat rod is vertical. Plastic creeps out
  of a wedge's preload, so add a positive lock ([[creep-and-stress-relaxation]]).
- **A printed rod end on a bought ball stud** is a split cup
  ([[snap-fit-design#ball-snap-a-split-cup]]) or a housing screwed shut;
  its pull-off must exceed the largest pull along the stud.
- **A printed clip** (R-clip, hairpin) is a cantilever at large strain: size
  it with [[snap-fit-design#cantilever]] for repeated use, or print it in TPU.

## Failure classes

| symptom | cause | rule that prevents it |
|---|---|---|
| eye splits out beyond the hole | steel proportions in plastic, or bore horizontal | `e ≥ 3 d1`; print the eye flat |
| pin bends, the joint binds after a load | pin loose in a wide fork | `d1 = d`; check σb with the gap inside the bracket |
| rod end shank snaps at the thread | load off the shank axis | side component ≤ 0.1 C0; double-shear clevis |
| rod end stiff before its rated tilt | cheek or spacer wider than the inner ring | step down to `da max` |
| ball link pops off | pull along the stud axis | load across the stud; add the safety clip |
| cotter backs out | taper above the friction angle, or creep | taper ≤ 1 in 24 plus a positive lock |
| circlip walks out of a printed groove | groove shoulder yields | steel pin, or edge margin ≥ 3 × groove depth and a square shoulder |
| push-on fix slides | pin diameter outside ±0.05 mm | steel or reamed pin |
| gas spring leaks early | twist or side load through rigid eyes | spherical fittings at both ends |

## Checks

```python
import math, cadfits
c = cadfits.mating_clearance(RUN)
assert FORK_GAP >= EYE_T + 2 * c, "eye has no running clearance in the fork"
assert P <= 2 * math.pi / 4 * PIN_D**2 * TAU_PIN, "pin fails in double shear"
M = P / 2 * (CHEEK_T / 3 + c + EYE_T / 4)
assert 32 * M / (math.pi * PIN_D**3) <= SIGMA_PIN, "pin bends"
assert P <= (EYE_OD - PIN_D) * EYE_T * SIGMA_T, "eye tears across the hole"
assert P <= PIN_D * EYE_T * SIGMA_C, "eye crushes under the pin"
assert EDGE_DIST >= (3 * PIN_D if EYE_PRINTED else PIN_D), "printed eye shears out"
assert COTTER_TAPER < MU, "cotter is not self-locking"            # taper as a slope, 1/24
assert ROD_END_SIDE_LOAD <= 0.1 * ROD_END_C0, "rod end side load bends the shank"
assert REQUIRED_TILT_DEG <= ROD_END_ALPHA_DEG, "linkage tilts past the rod end's cone"
assert MAX_PULL_ALONG_STUD < SOCKET_PULL_OFF or HAS_SAFETY_CLIP, "ball socket can pop off"
```

Open items, coupon results rather than geometry: allowable stresses across
layers, a printed socket's pull-off, a wedge's slip after creep.
