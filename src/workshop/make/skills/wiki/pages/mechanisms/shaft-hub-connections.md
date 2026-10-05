---
title: Shaft-hub connections
tags: [shaft, hub, key, keyway, spline, polygon, pin, set-screw, clamp, taper, press-fit, torque, phase, indexing]
aliases: [hub fixing, shaft to hub connection, shaft-hub joint, gear on shaft, pulley on shaft, wheel on axle, knob on shaft, crank on shaft, d-flat, d-shaft, double-d, flatted shaft, hex shaft, square shaft, polygon shaft, polygon profile, P3G, P4C, spline shaft, involute spline, straight-sided spline, serration, serrated shaft, parallel key, feather key, sunk key, woodruff key, half-moon key, keyseat, cross pin, taper pin, roll pin, spring pin, coiled pin, grub screw, set screw, setscrew, cup point, clamp hub, split hub, clamping hub, clamp collar, taper lock bush, taper bushing, qd bushing, keyless bushing, locking assembly, shrink disc, press-fit hub, knurled shaft, hirth joint, hirth coupling, curvic coupling, face spline, rosette joint, master spline, mounting hub]
sources:
  - https://www.idc-online.com/technical_references/pdfs/mechanical_engineering/Types_of_fasteners.pdf (IIT Kharagpur lesson 4.1: pin double shear, key shear and bearing, Woodruff keys below about 60 mm)
  - https://www.philadelphia.edu.jo/academics/mgogazeh/uploads/DESIGN%201%20CH7.pdf (Shigley's MED ch. 7 slides: keyseat Kt, keyseat end d/10 from a shoulder, key length at most 1.5 d, setscrew safety factors)
  - https://www.roymech.co.uk/Useful_Tables/Keyways/key_strength.html (key and spline shear and compressive stress)
  - https://www.firgelliauto.com/blogs/mechanisms/spline-mechanical (spline load-sharing factor 0.25-0.75; side fit and major-diameter fit)
  - https://asee-ncs.org/proceedings/2016/student_regular_papers/2016_ASEE_NCS_paper_50.pdf (P3G/P4C profile equation, DIN hub wall formulas, real contact pressure 5-6 x the DIN estimate)
  - http://www.hexagon.de/info182/index.htm (P3G e = 0.036 dm, P4C e = 0.125 dm; reversing torque loosens a self-centring polygon)
  - https://www.safetysocket.com/wp-content/themes/epca/files/parts/bd/Products/setscrewtorque.htm (cup-point axial holding power by size; THP = AHP x R)
  - https://practicalmaintenance.net/?p=397 (point factors; screw about half the shaft diameter)
  - https://catalog.climaxmetal.com/viewitems/set-screw-collars/two-hole-set-screw-collar-c-2h-series (a second screw at 90 deg nearly doubles capacity)
  - https://en.wikipedia.org/wiki/Shaft_collar (set screws raise a burr, flats mitigate it; clamp collars hold about twice as much)
  - https://www.firgelliauto.com/blogs/mechanisms/rigid-coupling (clamp T = mu F d / 2; single set screws back out under reversing load)
  - https://www.brainkart.com/article/Solved-Problems--Design-of-Shafts-and-Couplings_5903/ (clamp coupling T = pi^2/16 mu db^2 sigma_t n d)
  - https://tribology.rs/journals/2024/2024-1/9-1546.pdf (dry static friction of printed PLA and PETG on ground steel)
  - https://en.wikipedia.org/wiki/Machine_taper (self-holding Morse taper, self-releasing 7:24)
  - https://www.thebearingcompany.co.uk/wp-content/uploads/2020/02/Taper-Bushes.pdf (taper bush fitting, jacking holes, retorque after running)
  - https://www.ringfeder.com/products/locking-assemblies/ (tapered rings, no keyway, backlash-free)
  - https://www.ringfeder.com/products/shrink-discs/ (external clamping, not in the load path, shafts from 6 mm)
  - https://www.designworldonline.com/properly-pin-shaft-hub-assembly/ (SPIROL: hole at most D/3, hub wall 1.5 pin diameters, shear-plane gap 0.13 mm)
  - https://en.wikipedia.org/wiki/Hirth_joint (60 and 90 deg profiles, self-centring, axial preload)
  - https://ik.imagekit.io/agmamedia/gt/issues/1186x/Back-to-Basics.pdf (Gleason Curvic: 30 deg pressure angle, separating force, clamp 1.5-2 x)
  - https://en.wikipedia.org/wiki/Spline_(mechanical) (spline forms; a wider master spline fixes orientation)
  - Shigley's Mechanical Engineering Design, ch. 3 (press and shrink fits)
  - skills/cad/scripts/cadfits.py (fit classes)
related: [joints, shafts-and-bearings, shaft-couplings, clutches-and-freewheels, gears, dowel-pins-and-press-fits, heat-set-inserts, nut-traps-and-captive-nuts, fastener-torque-and-stripping, creep-and-stress-relaxation, hobby-servos, layer-anisotropy, bayonet-and-twist-locks, push-pins-and-clip-fasteners]
updated: 2026-10-01
---

# Shaft-hub connections

A hub (gear, pulley, crank, wheel, knob) is held on its shaft by **shape** (a
form lock: the profile cannot turn in its socket) or by **friction** (normal
force times μ). Choose by torque, removal, phase and what prints. Short rules:
[[joints#keyed-joints]], [[shafts-and-bearings#getting-torque-on-and-off]].

## Form lock or friction lock

| form | fits | prints | use when |
|---|---|---|---|
| **single D-flat** | 1 way | yes | any phased part; the printed default |
| **double-D** | 2 ways | yes | unphased parts, and parts symmetric under a half turn (a yoke) |
| **square, hex** | 4, 6 ways | check the crush depth | knobs, wheels, bought hex shafts |
| **polygon P3G / P4C** (DIN 32711 / 32712) | 3, 4 ways | yes; no corners | the most torque in a printed hub; P3G self-centres, P4C slides under torque |
| **straight-sided spline** (ISO 14) | n ways | coarse only | a hub that slides along the shaft |
| **involute spline** (ISO 4156, DIN 5480), **serration** (DIN 5481) | n ways | coarse only | a bought splined output; a servo takes its own horn ([[hobby-servos#horns-and-splines]]) |
| **parallel or feather key** (ISO 773, DIN 6885) | 1 way | seats print; the key is steel | high torque; a feather key lets the hub slide. `stdpart sizes ShaftKey`, `Keyway` |
| **Woodruff key** | 1 way | poor (a half-disc seat) | metal shafts below about 60 mm; sits deep, cannot roll |
| **cross, taper or roll pin** | 1–2 ways | drill on assembly | exact phase, high torque, axial retention too |
| **Hirth or curvic face teeth** | n ways | teeth face up | re-indexing in steps, joining shaft halves |
| **set screw on a flat** | 1 way | needs a metal thread | adjusted and removable hubs |
| **clamp or split hub** | any angle | with a nut or insert | adjustable phase on a round shaft |
| **taper, taper bush, locking assembly, shrink disc** | any angle | bought, metal | metal hubs on metal shafts |
| **press fit, knurled press, glue** | any angle | press fits relax | parts that never come off ([[dowel-pins-and-press-fits]]) |

A friction lock holds only while its normal force lasts, and in plastic that
relaxes ([[creep-and-stress-relaxation#design-rules]]): under sustained or
reversing torque it is a limitation to record.

## Crush depth: why a small hex rounds off

Each flat presses with a pressure rising from zero at its middle to a peak at
its edges, so the hub crushes at the corners and spins free once crushed out
to the shaft's corner radius. That depth is the real engagement (derived):

```text
regular n-flat profile, inscribed radius r_in, per-side clearance c:
    h = r_in · (1/cos(π/n) − 1) − c          D-flat of depth t: h = t − c;  polygon: h = 2e − c
torque before the corners yield (derived; edge pressure p_max, hub length L):
    T ≈ n · p_max · L · w² / 12,   w = 2 r_in tan(π/n);   D-flat: n = 1, w = 2·sqrt(r² − (r − t)²)
```

| 6 mm, `c = mating_clearance("snug")` | D-flat t = D/6 | square | hex | octagon | P3G, DIN e |
|---|---|---|---|---|---|
| h (mm) | 0.90 | 1.14 | 0.36 | 0.15 | 0.33 |
| T / (p_max · L) (mm²) | 1.7 | 12 | 6 | 4.1 | — |

A 6 mm hex engages by under one extrusion width and rounds off in PLA: keep
`h` ≥ the D-flat's, and use a square or polygon for torque.

**Polygon** (dm mean diameter, e eccentricity, n lobes):

```text
x(v) = (dm/2 − e·cos nv)·cos v − n·e·sin nv·sin v
y(v) = (dm/2 − e·cos nv)·sin v + n·e·sin nv·cos v        0 ≤ v < 2π
smooth only while e < dm / (2(n² − 1)): dm/16 for three lobes, dm/30 for four
DIN hub wall, torque T, hub length l, allowable σ:  P3G t = 1.44·sqrt(T/(σ·l)) (dm ≤ 35);  P4C t = 0.7·sqrt(T/(σ·l))
```

DIN P3G uses e ≈ 0.036 dm; P4C's 0.125 dm works only because the outer
circle cuts its curve. A printed three-lobe profile can take e ≈ dm/20 (`h ≈
dm/10 − c`). Measured contact pressure was 5–6 × the DIN estimate: give the
bursting hub wall margin. Under reversing torque a P3G loosens and wears.

## Keys, pins and splines: torque and stress concentration

```text
D shaft, L engaged length, T torque
parallel key b × t, half in the hub:  shear T = τ·b·L·D/2;  bearing T = σ_br·(t/2)·L·D/2
cross pin d, double shear:            τ = 4T / (π d² D)
    hub bearing  p_h = 4T / (d·(D_h² − D²))     shaft bore  p_s = 6T / (d·D²)     (derived)
spline, n teeth, mean radius r_m, depth h:  T = K·n·p·h·L·r_m,  K = 0.25–0.75 (share that bears)
```

- **Keys**: at most 1.5 D long or the key twists; a second key goes at 90°.
  In a printed hub the keyseat crushes before the steel key shears: check
  `σ_br` against the plastic.
- **Pins**: shaft hole at most D/3, hub wall at least 1.5 pin diameters, at
  most 0.13 mm hub-to-shaft gap at the shear planes or the pin bends, so pin
  a `SEAT` length, not `RUN`. The two holes must agree within about 0.05 mm:
  print the cross hole as a pilot and drill both together.
- **Splines**: side fit carries most torque, major-diameter fit centres best.
  A printed spline is a coarse gear profile ([[gears#printed-tooth-choices]]): take K low.

**Stress concentration.** An end-milled keyseat (`r/d = 0.02`) has Kt 2.14
in bending, 2.62 in torsion without the key, 3.0 with it; end it d/10 or more
from a shoulder fillet. A retaining-ring groove: about 5 bending, 3 torsion.
Polygons cut no notch. A printed hub is thinnest over the key or flat.

## Set screws

Cup-point alloy-steel screw on a steel shaft at full seating torque;
torsional holding power is `AHP × D/2`:

| screw (≈ metric) | #4 (M3) | #8 (M4) | #10 (M5) | 1/4 in (M6) |
|---|---|---|---|---|
| seating torque | 0.57 N·m | 2.2 N·m | 3.8 N·m | 8.8 N·m |
| axial holding power | 620 N | 1.6 kN | 2.4 kN | 4.4 kN |

- Against the cup point: cone 1.07, flat 0.92, dog 0.92, oval 0.90. Screw
  about D/2; factors 1.5–2 static, 4–8 dynamic. A second screw at 90° nearly
  doubles capacity; a single one backs out under reversing load.
- **Drive onto a flat.** On a round shaft the cup raises a burr that scores it
  and traps the hub. On a flat the burr stays below the round, and the joint
  is a form lock: the shaft turns only by forcing the screw back up its thread.
- **The printed anchor sets the seating torque**: an M3 thread in plastic
  strips near 1 N·m, a pocketed nut near 2, an insert at 3–4
  ([[fastener-torque-and-stripping#how-much-torque-a-printed-joint-takes]]).
  Use an insert or captured nut ([[nut-traps-and-captive-nuts#where-the-pocket-opens-decides-the-strength]]).
  On a printed shaft the screw indents and creeps: the flat carries the torque.

## Clamp hubs and split hubs

```text
F_s total screw tension across the split, bore d, friction μ
    bore conforming (uniform pressure)   T = μ · π · F_s · d / 2
    oversize bore (two line contacts)    T = μ · F_s · d
```

The uniform form is the textbook clamp coupling, `T = (π²/16)·μ·d_b²·σ_t·n·d`
with n/2 bolts per shaft; a clamp collar holds about twice a set-screw collar.
Printed PLA and PETG on dry ground steel gave static μ 0.2–0.3, falling with
load: design at 0.2. F_s = 1000 N on d = 6 mm gives 1.2–1.9 N·m, before creep.

- Slot the hub along its whole length; the screw crosses the slot tangent to
  the bore into a nut trap or insert. Bore `slot_for(D, "slip")`. Closing the
  slot by Δ shrinks the bore by Δ/π, so the slot is wider than
  `π × (bore − shaft)` or it closes before it grips (derived).
- One M3 at 1 N·m pulls about 1.5 kN; the loss is creep. Washer or sleeve
  under the head, retighten after a day, PETG over PLA, a flat for sustained
  torque ([[fastener-torque-and-stripping#clamp-load-relaxes]]).

## Tapers, locking devices, press fits and glue

- **Taper** of half-angle α holds itself when `tan α < μ` (derived): Morse
  (about 1.5° per side) holds, 7:24 (16.6° included) needs a drawbar, printed
  plastic sticks below about 11–17° per side. A shallow taper turns diameter
  error into axial error, `Δz = Δd / (2 tan α)`: 0.1 mm at 3° moves the hub 1 mm.
- **Bought metal**: a *taper bush* is drawn in by grub screws in
  half-threaded holes and freed by its jacking holes; a *locking assembly*
  presses tapered rings into radial pressure, backlash-free with no keyway; a
  *shrink disc* clamps the hub from outside (from 6 mm shafts). Retighten
  after the first run; round a printed hub all three lose clamp to creep.
- **Press fit**: `T = (π/2)·μ·p·d²·L`, p from the interference; printed fits:
  [[dowel-pins-and-press-fits#the-fdm-fit-ladder]], and heat loosens them
  ([[thermal-expansion-and-hybrid-parts#metal-pressed-into-plastic]]).
- **Knurled press**: a straight-knurled steel end pressed hot into a printed
  bore like a heat-set insert ([[heat-set-inserts]]): a form lock at any angle.
- **Glue**: permanent, phase set by a jig; a bonded seat is a clearance of
  2 × the bondline ([[thermal-expansion-and-hybrid-parts#gluing-plastic-to-metal]]).

## Face teeth: Hirth and curvic

Radial teeth on two end faces pulled together: Hirth teeth straight and
tapered (60° or 90° profile), curvic teeth curved (30° standard pressure
angle). Both self-centre without backlash, but only under axial preload:
torque pushes them apart with `F_a = (T / r_m)·tan φ` (no friction), so clamp
with 1.5–2 × the separating forces, through bolt holes with clearance so the
teeth do the centring. Print teeth face up, every flank facing upward. A
printed rosette under a hand knob indexes an arm in 360°/n steps.

## Printing shaft-hub joints

| situation | do |
|---|---|
| any printed hub | bore axis vertical: socket flats are perimeter walls and hoop tension runs along the layers; bore-horizontal hubs split on a layer ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]) |
| printed hub, steel D-shaft | socket `slot_for(D, SEAT)`, flat at `D/2 − t + mating_clearance(SEAT)`; measure the bought flat, which may be shallower than D/6 |
| printed shaft, printed hub | shaft lying on its D-flat ([[shafts-and-bearings#printed-shaft-or-bought-rod]]), or one part if nothing turns |
| set screw | insert or captured nut, radial, onto a flat; two at 90° for reversing torque |
| motor speed or frequent removal | screw the printed part to a bought metal set-screw or clamp hub |

## Phasing and indexing

A profile fits in as many positions as its rotational symmetry. A single D,
key, off-axis pin, asymmetric screw pattern or **master spline** (one tooth
wider, as on propellers and bicycle cassettes) fits one way. A part symmetric
under a 1/k turn is right in every position of a profile whose position count
divides k: a yoke may use a double-D, a square lets it on 90° wrong
([[shaft-couplings#printing-a-universal-joint]]). An n-position profile also
indexes; set screws and clamps have no phase, so set it with a jig ([[gears#mesh-phasing]]).

## Failure classes

| symptom | rule that prevents it |
|---|---|
| round snug fit spins under load | a form lock or a clamp; no plain round fit for torque |
| hub will not come off, shaft scored | set screw onto a flat |
| hex socket rounds, knob free-wheels | `h` ≥ the D-flat's; square, polygon or metal insert |
| set screw loosens under reversing torque | insert or nut, two screws at 90°, a flat |
| clamp hub slips after a day | washer or sleeve, retighten, a flat for sustained torque |
| split hub will not grip | slot wider than `π × (bore − shaft)` |
| hub splits along a layer | bore axis vertical |
| crank pair 180° out | single D or a pin, never double-D |
| pinned hub loosens, pin bends | `SEAT` fit along the pinned length |

## Checks

```python
import math, cadfits
c = cadfits.mating_clearance(SEAT)
h = R_IN * (1 / math.cos(math.pi / N_FLATS) - 1) - c      # D-flat: FLAT_DEPTH - c
assert h >= SHAFT_D / 6 - c, "profile engages less than a D/6 flat: it will round off"
assert PART_SYMMETRY % PROFILE_POSITIONS == 0, "hub can be assembled out of phase"
assert N_FLATS * P_ALLOW * HUB_L * W_FLAT**2 / 12 >= SF * T_DESIGN, "flat corners crush"
assert KEY_L <= 1.5 * SHAFT_D, "key longer than 1.5 D twists"
assert 4 * T_DESIGN / (math.pi * PIN_D**2 * SHAFT_D) <= TAU_PIN / SF, "cross pin shears"
assert 4 * T_DESIGN / (PIN_D * (HUB_OD**2 - SHAFT_D**2)) <= P_ALLOW / SF, "hub crushes at the pin"
assert PIN_D <= SHAFT_D / 3 and (HUB_OD - SHAFT_D) / 2 >= 1.5 * PIN_D, "pin hole or hub wall"
assert SLOT_W > math.pi * (BORE_D - SHAFT_D), "split-hub slot closes before it grips"
assert MU * math.pi * F_SCREWS * SHAFT_D / 2 >= SF * T_DESIGN, "clamp hub slips"
assert F_PRELOAD >= 1.5 * (T_DESIGN / R_MEAN) * math.tan(PHI), "face teeth separate"
```

Crush, preload loss and friction are not measured by any rigid gate: prove the
hub on a coupon at the design torque ([[dowel-pins-and-press-fits#prove-it-on-a-coupon]]).
