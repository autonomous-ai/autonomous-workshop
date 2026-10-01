---
title: Swivels and turntables
tags: [swivel, turntable, thrust, slewing, ball-race, roller, tipping, moment, friction, slip-ring, display]
aliases: [lazy susan, lazy susan bearing, turntable bearing, swivel plate, swivel base, rotating base, rotating plinth, display turntable, rotating display stand, spinning stand, slewing ring, slew ring, slewing bearing, turntable ring, four-point contact bearing, crossed roller bearing, cross roller ring, thrust bearing, thrust washer, ptfe washer, teflon washer, ball race, ball track, printed ball bearing, airsoft bb bearing, bb bearing, gothic arch groove, race conformity, roller thrust bearing, tapered roller, centre pin swivel, center pin swivel, pivot bolt, snap swivel, snap-on turntable, slip ring, rotary joint, rotating electrical connector, indexing table, rotary table, tipping moment, overturning moment]
sources:
  - https://www.craftparts.com/products/lazy-susan-bearings-4 (4 in square plate, 300 lb, 5/16 in tall, 1/4 in balls, for 12–25 in tops)
  - https://www.rockler.com/learn/how-to-install-lazy-susan-hardware (lower plate first; a hole through the base under the plate's large access hole; upper screws driven through it)
  - https://www.thyssenkrupp-rotheerde.com/en/products/rothe-erde-slewing-bearings/technical-basics/calculation-of-the-frictional-torque (Mr = μ/2 (4.4 Mk + Fa DL + 2.2 Fr DL 1.73); μ 0.003–0.008; ±25 %)
  - Schaeffler (INA) Catalogue 404, Slewing rings (https://www.schaeffler.com/remotemedien/media/_shared_media/08_media_library/01_publications/schaeffler_2/catalogue_1/downloads_6/404_de_en_1.pdf), pp. 1, 22, 37–38 (four-point vs crossed roller, flatness δB, support under the rolling elements)
  - https://docs.rs-online.com/6553/0900766b81406d6a.pdf (igus iglidur PRT data: PRT-01-20 15 kN static, 4 kN dynamic axial, 100 N·m tilting, 300 rpm dry; screws in every hole, 2 d engagement)
  - Zaretsky, Poplawski, Root, Reexamination of Ball-Race Conformity Effects on Ball Bearing Life, NASA/TM-2007-213635 (https://ntrs.nasa.gov/api/citations/20080001446/downloads/20080001446.pdf) (f = r/d, 0.52 reference, 0.505–0.57 range)
  - https://en.wikipedia.org/wiki/Ball_bearing (Conrad, slot-fill, fractured race, cage carries no load)
  - https://en.wikipedia.org/wiki/Tapered_roller_bearing (apexes meet on the axis; rib against the pumpkin-seed force)
  - https://www.nsk.com/eu-en/products/data-sheets/cylindrical-thrust-roller-bearings/ (differential circumferential speed, low speed only)
  - https://www.patrolbase.co.uk/airsoft-0-20g-6mm-bbs (0.20 g BBs 5.95 ± 0.01 mm)
  - https://www.fixsupply.com/zusab-pb-366-ptfe-lined-thrust-washers-14mm-id-x-26mm-od-x-1-5mm-thick (PTFE-lined washer μ 0.02–0.20 dry, PV 1.8 MPa·m/s dry)
  - https://www.calculatoratoz.com/en/radius-of-kern-for-circular-ring-calculator/Calc-3052 (kern of a ring (D² + d²)/(8 D))
  - https://www.moflon.com/pdf/install.pdf (slip ring carries its own weight only; anti-rotation pin not fixed forcibly)
  - https://www.adafruit.com/product/736 (22 mm capsule slip ring, 44 mm flange, 6 wires, 2 A, 300 rpm)
  - https://www.photoworkout.com/best-rotating-stand-for-photography/ (display turntables 8–160 s per turn)
  - https://help.prusa3d.com/article/infill-patterns_177130 (concentric top fill follows the perimeters)
  - Shigley's Mechanical Engineering Design, ch. 3 (Hertz contact of spheres) and ch. 16 (axial disk friction, uniform pressure and uniform wear)
  - K. L. Johnson, Contact Mechanics, ch. 6 (first yield under a sphere at p0 ≈ 1.6 Y)
related: [joints, shafts-and-bearings, automata-patterns, stability-and-tipping, snap-fit-design, latches-detents-and-ratchets, friction-wear-and-lubricants, exact-constraint-and-kinematic-mounts, cams-intermittent, creep-and-stress-relaxation, bayonet-and-twist-locks, shaft-hub-connections, rolling-contact-joints]
updated: 2026-10-01
---

# Swivels and turntables

A swivel turns all the way round one axis, usually vertical, under an axial
load plus a **tipping moment**; radial load is small. The moment, a hand on
the rim or an off-centre figure, decides the design more than the weight does.
Choose the form from the moment, then the friction torque, then the hold-down.
Shaft-supported rotation is [[shafts-and-bearings]].

## Which swivel

| form | carries | use when | build |
|---|---|---|---|
| **centre pin + washer stack** | axial on the washers, moment as a couple in the bore | small tops, knobs, slow stands | pin `D`, bore `slot_for(D, RUN)` ≥ 1.5 D long, PTFE or nylon thrust washer (below) |
| **snap-retained swivel** | axial on a flat face, lift on a lip | one-piece toys, caps, plinths with no screw | annular lip over a rim ([[snap-fit-design#annular-snap]]) |
| **printed ball race** | axial (thrust groove) or axial both ways + moment (four-point groove) | tops wider than a pin can steady; low friction | steel balls or 6 mm BBs in a printed groove |
| **printed roller race** | high axial, low speed | heavy slow tops | short, split or tapered rollers |
| **lazy-susan plate** (bought) | axial, moderate moment | furniture-scale tops, display bases | stamped steel plates around 1/4 in balls |
| **slewing ring** (bought) | axial both ways, radial, moment in one ring | arms, cranes, robot bases | four-point ball, crossed roller, or polymer sliding ring |

**One radial locator.** A centre pin and a grooved race both centre the top,
and two centring features fight every print error. Let one locate: a pin with
a flat-track race, or a four-point race with a clearance hole round the pin
([[exact-constraint-and-kinematic-mounts#joints-and-bearings-are-constraints-too]]).

## The load is a moment

Sum every load into an axial force `Fa` and a moment `M` about the
bearing centre: `M = Σ F_i · e_i`, eccentricity `e = M / Fa`. With `Z`
elements on a pitch circle `Dp` and rigid rings, the element load varies as
`cos ψ` round the circle:

```text
gravity-held race (nothing stops lift):
  all elements stay loaded     e ≤ r_kern ≈ Dp / 4      (kern of a ring: (D² + d²) / (8 D))
  top lifts and tips           e ≥ Dp / 2               (the resultant leaves the circle)
captured race (four-point groove, lip, or hold-down):
  most-loaded element          Q_max = Fa / Z + 4 M / (Z · Dp)
  most-lifted element          Q_lift = 4 M / (Z · Dp) − Fa / Z     (> 0: a hold-down carries it)
```

Rothe Erde weighs a moment as an axial load of `4.4 M / Dp`, close to the
rigid-ring 4: doubling `Dp` halves what the moment does. Worked: a 300 mm top
of 10 N pressed with 20 N at its rim gives `M = 3 N·m`, `e = 3 / 30 = 0.1 m`,
and lifts off any gravity-held race with `Dp` under 200 mm. The lean, not the
weight, is the design case.

A bought plate is rated for a centred load: one vendor sells a 4 in plate
(300 lb) for tops of 12–25 in, three to six times its own size. Whether the
whole object then stands is [[stability-and-tipping]].

## Friction torque

```text
flat thrust face, inner/outer radius Ri, Ro (Shigley ch. 16):
  new (uniform pressure)   T = μ Fa · (2/3) (Ro³ − Ri³) / (Ro² − Ri²)
  worn (uniform wear)      T = μ Fa · (Ro + Ri) / 2
ball slewing ring (Rothe Erde, ±25 %):
  Mr = μ/2 · (4.4 M + Fa · Dp + 2.2 · Fr · Dp · 1.73)      μ ≈ 0.003–0.008 (steel)
clamped stack: add μ · F_clamp · r_mean for every face the clamp loads
```

A printed race rolls with far more hysteresis than steel, and PLA on PLA
slides near the top of [[snap-fit-design#mating-and-separating-force]]:
measure the pair on a coupon. A PTFE-lined thrust washer runs at μ 0.02–0.20
dry up to PV 1.8 MPa·m/s, far above a turntable at a few rpm.

## Centre pin with a washer stack

- **The pin takes the moment as a couple.** A bore of length `L` reacts `M`
  with `M / L` at each end, so the bore length, not the pin diameter, steadies
  the top: `L ≥ 1.5 D` ([[joints#revolute-joints]]), longer for a wide top.
- **Clamp the pin, never the rotor.** Stack: base, washer, turning hub,
  washer, nut. Tighten the nut onto a spacer sleeve, or a shoulder on the pin,
  longer than the hub plus washers by the running play. Otherwise the torque
  follows the nut, then fades as the plastic relaxes
  ([[creep-and-stress-relaxation]]). Use a locking nut.
- **Washer radius trades**: a wider face resists tipping and costs torque in
  proportion to its mean radius. Grease must suit the plastic ([[friction-wear-and-lubricants]]).

## Snap-retained swivel

The top's skirt ends in an inward lip that snaps past a rim on the base.
The flat face under the top carries the load, and the lip carries only lift.

- Derive the lip from the rim: `LIP_ID = slot_for(NECK_D, RUN)`, undercut
  `y = (RIM_D − LIP_ID) / 2`, groove height `slot_for(LIP_T, RUN)`.
- A whole ring opens only by `y = ε · d`; above that, slot the skirt into
  fingers and size each as a cantilever ([[snap-fit-design#cantilever]]).
- A lip under about 1 mm prints as a ledge with a flat return face, which is
  permanent ([[overhangs-and-print-orientation#bridge-ledge-overhang]]). A
  deeper lip needs a 45° underside, which is a separable return face: check
  `μ · tan α' < 1` ([[snap-fit-design#mating-and-separating-force]]). Declare
  the undercut's overlap ([[mechanism-verification#8-allowances-are-declared-not-hidden]]).

## Printed ball race

- **Balls.** Hardened steel balls carry load and stay round. Airsoft BBs are
  cheap, light and quiet, but a "6 mm" BB is **5.95 ± 0.01 mm**. Derive every
  groove from the measured ball, never the nominal one.
- **Conformity** `f = r_groove / d`. Steel bearings sit near 0.52, and life
  falls steeply as f opens (NASA TM-2007-213635 tabulates 0.505–0.57). A
  printed radius is off by a print error `ε_p`, and a groove tighter than the
  ball binds, so keep `f ≥ 0.5 + ε_p / d`. With a 6 mm ball and 0.1 mm, that is
  0.517; design 0.53–0.55.
- **Profile.** A circular thrust groove carries one direction. A Gothic arch
  (two arcs of radius `f d`, centres offset so the ball touches at ±α) or a 90°
  V gives four-point contact: axial both ways and moment in one row, top
  captured. A V holds its angle through print error but contacts like a flat.
- **Contact pressure, not ball strength, sets the load.** Hertz, ball `d`
  on a flat (Shigley ch. 3): `a = (3F/8 · k / (1/d))^(1/3)`,
  `k = (1−ν1²)/E1 + (1−ν2²)/E2`, `p_max = 3F / (2π a²)`. First yield at
  `p_max ≈ 1.6 Y` (Johnson). Worked: a 6 mm steel ball on flat PLA (E 2.3 GPa,
  Y 51 MPa) yields at about 4 N. A groove multiplies that load by about
  `f / (f − 0.5)`, the equivalent-radius gain: ×18 at 0.53, ×11 at 0.55.
  Beyond first yield the race embosses a track and then creeps under a
  standing load. Size on the plastic, keep standing loads low, or let a steel
  wire or ring insert be the track.
- **Count.** Touching balls fill the circle at
  `Z_full = floor(π / asin(d / Dp))` (52 balls of 6 mm on Dp 100). Neighbours'
  surfaces move in opposite directions where they touch, so a full complement
  rubs and squeals. A cage spaces them and carries no load: pockets
  `slot_for(d, "free")`, webs at least `cadprint.min_wall(NOZZLE)`.
- **Loading.** A thrust race needs no loading path: lay the balls, drop the
  top on, retain it at the pin or lip. A captured race either splits at the
  ball equator into two rings that screw or snap together (the printed form of
  a fractured race), or takes a filling slot closed by a plug that carries the
  groove on. The slot is a discontinuity in the track, so put it where the
  load is least.
- **Print.** Thrust rings print flat, groove up, so the groove has no
  overhang. Concentric top fill makes the balls run along the strands instead
  of across 0.4 mm ridges. Keep the seam out of the groove; iron flat tracks
  ([[fdm-surface-finish#ironing]]). A groove in a vertical-axis radial ring
  overhangs above the ball centre, past 45° near the mouth: cap it with a 45°
  flank (a teardrop groove), use the V, or split the ring at the equator.

## Printed roller race

- **Cylindrical rollers scuff.** On a flat thrust race the track speed rises
  with radius, but a roller has one speed. A roller of length `L` at mean
  radius `Rm` slips by about `L / Rm` of the rolling speed, which is why roller
  thrust bearings are low-speed parts (NSK). Keep rollers short, or put two
  short ones per pocket so each turns at its own speed.
- **Tapered rollers roll true** when every cone's apex meets on the axis:
  roller radius `r(R) = R · tan β`. Loaded, a cone is pushed toward its large
  end, so an outer rib or the cage has to hold it.
- **Crossed rollers** alternate their axes at 90° in a square-section V
  groove, with each roller a little shorter than its diameter. One row then
  carries axial load both ways, radial load and moment.
- Print rollers standing (round, loaded in compression) or buy dowel pins ([[dowel-pins-and-press-fits]]).

## Bought turntable bearings

- **Lazy-susan plates.** Screw the lower plate down first, over a hole in the
  base that matches its large access hole; then turn the top until each
  upper-plate hole shows through it and drive that screw from below. No hole
  in the base, no way to fix the top. Seat the thin steel on flat faces.
- **Slewing rings.** A four-point ring with clearance asks little of the
  structure's flatness. A preloaded crossed-roller ring carries more, runs
  smoother and stiffer, and needs a flatter, stiffer seat (Schaeffler).
  Schaeffler's flatness limit is `δB = (DM + 500) / 10000` mm for a four-point
  ring with clearance and `(DM + 1000) / 20000` mm preloaded: about 0.06 mm at
  `DM` 100, tighter than a printed plate holds
  ([[fdm-first-layer-and-warping#why-parts-warp]]). Support the ring all the
  way round, directly under its rolling elements, and screw every hole.
- **Polymer slewing rings** slide on plastic elements and tolerate printed
  structures. igus PRT-01-20: 15 kN static axial, 4 kN dynamic, 100 N·m
  tilting, 300 rpm dry; screw every outer-ring hole with 2 d engagement.

## Rotating electrical passes

- **Slip ring.** A capsule ring (one common one: 22 mm body, 44 mm flange,
  6 wires at 2 A, 300 rpm) sits on the axis. The rotor fixes to the turning
  part, concentric. The stator is stopped by a loose anti-rotation pin or fork
  and is **never bolted** as well: rigid at both ends, its own bearings fight
  the turntable's. It carries only its own weight; its leads take no pull, so
  clamp them both sides ([[electronics-enclosure-design#strain-relief]],
  [[power-path-design#wires-are-solids]]). A capsule on the axis displaces the
  centre pin, so run the top on a ring race or plate, or use a through-bore ring.
- **Limited rotation** (a few turns) needs no slip ring: a slack loop through
  a hollow axle, and a hard stop before the loop is spent.

## Toy turntables, display stands and indexing

- Display turntables run 8–160 s per turn, so a sliding swivel serves a light
  figure. An automaton turntable is driven from below by a bevel, face gear or
  worm ([[automata-patterns#the-common-layouts]]); a friction wheel at the rim
  gives a large reduction in one step.
- A gap between a turning top and its base that a child can reach is under
  5 mm or at least 12 mm ([[toy-safety-constraints#finger-entrapment-and-springs-en-71-1]]).
- **Indexing.** Detent notches on the largest radius
  ([[latches-detents-and-ratchets#indexing-detents]]), a Geneva for driven
  steps ([[cams-intermittent#geneva-drive]]), or a stepper. A detent is not a
  stop.

## Failure classes

| symptom | rule that prevents it |
|---|---|
| top rocks or lifts when pressed at the rim | `e ≤ Dp/4`, or a captured race or hold-down sized for `Q_lift` |
| stiff after the nut is tightened, loose a week later | clamp a sleeve or shoulder, never the turning hub |
| race rumbles or ticks | concentric top fill, seam out of the groove, cage the balls |
| rough after standing loaded | contact pressure under 1.6 Y; steel track insert; lower standing load |
| bought ring has tight spots | four-point or polymer ring on printed plates; support under the rolling row |
| slip ring fails early | stator held by a loose pin, not bolted |

## Checks

```python
import math
e = M / FA
assert e <= DP / 4 or CAPTURED, f"top lifts: e {e:.0f} mm beyond the kern {DP/4:.0f} mm"
q_max = FA / Z + 4 * M / (Z * DP)
assert q_max <= Q_ALLOW, f"element load {q_max:.1f} N over the coupon value"
assert GROOVE_R / BALL_D_MEASURED >= 0.5 + PRINT_ERR / BALL_D_MEASURED, "groove tighter than the ball"
assert Z <= math.floor(math.pi / math.asin(BALL_D_MEASURED / DP)), "balls do not fit the circle"
assert PIN_BORE_L >= 1.5 * PIN_D, "bore too short to steady the top"
assert SLEEVE_L > HUB_L + 2 * WASHER_T, "nut clamps the turning hub"
assert DRIVE_TORQUE >= 2 * T_FRICTION, "drive cannot start the turntable"
```

Motion manifest: a full-turn rotation `clear`, lift `blocked` at the lip or
captured race, retention closed at the base ([[mechanism-verification]]).
Rolling friction, track wear and creep are open items for a coupon.
