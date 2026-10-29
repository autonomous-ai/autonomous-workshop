---
title: Spinning toys and flywheels
tags: [spinning-top, yo-yo, fidget-spinner, gyroscope, flywheel, inertia, precession, balance, bearing]
aliases: [spinning top, sleeping top, top tip, ball tip, tippe top, yoyo, yo-yo bearing, yo-yo gap, response pad, fidget spinner, hand spinner, 608 spinner, finger cap, gyroscope, gyro, gimbal, precession rate, flywheel, friction motor, inertia motor, pullback motor, pull-back car, flywheel car, spin time, rim weight, hoop stress, burst speed, rotor balance, static imbalance, dynamic imbalance, couple imbalance, ripcord, rack launcher, top launcher]
sources:
  - https://www.damtp.cam.ac.uk/user/tong/dynamics/three.pdf (D. Tong, Classical Dynamics 3.6: heavy symmetric top, sleeping top stable for ω3² > 4 I1 M g l / I3² with I1 about the pivot; falls once I3 ω3 = 2 sqrt(I1 M g l); steady precession M g l = φ̇ (I3 ω3 − I1 φ̇ cos θ))
  - https://en.wikipedia.org/wiki/Spinning_top (friction brings the top upright and less friction takes longer; more inertia and a lower CoG lengthen spin while the body does not touch the ground; ruby or tungsten-carbide ball tips)
  - https://spintricks.org/?p=3340 (small finger tops leave the fingers at 5,500-7,600 rpm, motor release to 9,600; 1.5 mm fine tip against 5 mm ball tip, ball tips self-right more strongly)
  - https://rmf.smf.mx/ojs/index.php/rmf/article/download/6473/6696/22562 (Tanriverdi 2023: slipping friction at a hemispherical peg raises the top; Fokker found larger peg radii rise faster; spin decays mainly by air skin friction)
  - https://arxiv.org/pdf/0704.1221 (tippe top classes: complete inversion at large spin when 1 − ε/R < A/C < 1 + ε/R; never inverts below that band)
  - https://docs.rs-online.com/bccf/A700000014623443.pdf (NSK 608 datasheet: 8 × 22 × 7 mm, da min 10, Da max 20, 7 balls Ø3.969, 12.1 g, grease 34,000 min⁻¹)
  - https://yoyoexpert.com/products/yoyoexpert-yoyo-bearing (yo-yo bearing sizes C .250 × .500 × .187 in, A 5 × 10 × 4, D 5 × 11 × 5, metric 6 × 13 × 5)
  - https://forums.yoyoexpert.com/t/how-does-gap-size-affect-play/65440 (players' unresponsive gaps 4.15-4.45 mm, about 5 mm called wide; narrow gaps snag thick string)
  - https://yoyoexpert.com/pages/408-maintenance-adjusting-gaps (wider gap spins smoother and is less responsive; adjustable gaps open to about one bearing width)
  - https://arxiv.org/pdf/1903.01343 (yo-yo on its string: α = g r / (r² + I/m), r = radius the string unwinds from)
  - https://ph02.tci-thaijo.org/index.php/JSTNSRU/article/view/262069 (spinner spin-down: exponential at high speed from air and bearing viscous drag, linear at low speed from constant friction torque)
  - https://en.wikipedia.org/wiki/Flywheel (E = ½ I ω²; rim stress ρ r² ω²; E/m = K σ / ρ; burst when hoop stress exceeds tensile strength)
  - https://en.wikipedia.org/wiki/List_of_moments_of_inertia (hoop m r², tube ½ m (r1² + r2²), solid cylinder ½ m r² and m (3 r² + h²) / 12)
  - https://www.codecogs.com/page/1226/v/3876 (rotating disc: stress at the centre (3 + ν) ρ ω² R² / 8; hoop stress at a small bore tends to twice that)
  - https://en.wikipedia.org/wiki/Friction_motor (flywheel geared up from the wheels, pumped up by pushes, optional one-way clutch)
  - https://patents.google.com/patent/US3955429A/en (inertia vehicle: 5:1 × 6:1 = 30:1 train, at least 20:1, iron flywheel 2.6 in and about 14 oz, runs up to about two minutes)
  - https://en.wikipedia.org/wiki/Pullback_motor (flat spiral spring, clutch or ratchet frees the wheels once it has run down)
  - https://www.fabrico.io/blog/iso-21940-balance-quality-grades/ (ISO 21940-11: e_per = 1000 G / ω µm; fans and flywheels G6.3, gyroscopes G0.4-G1)
  - https://law.resource.org/pub/eu/toys/en.71.1.2014.html (EN 71-1 3.71 and 4.24: the 370 mm tether limit is for elastic yo-yo balls)
  - "toolchain: build123d 0.11 topology/shape_core.py (Shape.matrix_of_inertia about the CoM, principal_properties)"
related: [shafts-and-bearings, dowel-pins-and-press-fits, fit-derivation, mass-properties-and-measurement, energy-drive, clutches-and-freewheels, gears, swivels-and-turntables, toy-safety-constraints, filament-properties, printed-fatigue, layer-anisotropy, fdm-surface-finish, perimeters-infill-and-strength, counterweights-and-gravity-balance, noise-and-vibration, seating-bought-parts, stability-and-tipping, launchers-and-projectile-toys]
updated: 2026-10-10
---

# Spinning toys and flywheels

A spinning toy is a rotor that must keep its angular momentum: a top, a yo-yo, a spinner, a
gyroscope, a friction car. Each is designed from four numbers (axial inertia, launch speed, the
speed at which it stops working, the drag between) and a balance check, since the print adds imbalance.

## Inertia is the design variable

| body, about its spin axis | I |
|---|---|
| point mass m at radius r (a rim weight); thin ring of radius r | m r² |
| tube, radii r_i and r_o; solid disc of radius r | ½ m (r_i² + r_o²); ½ m r² |
| solid cylinder, transverse axis through its CoM, height h | m (3 r² + h²) / 12 |

Spin energy is `E = ½ I ω²`. A rim mass works twice as hard as the same mass spread over a disc:
put it in dense, precise bought parts at the rim (608s, nuts, a steel ring; steel 7.85 g/cm³
against PLA 1.17-1.24, [[counterweights-and-gravity-balance#ballast-pockets-and-dense-fills]]),
which then also set the balance, and let the print be the light carrier. build123d gives I with
density 1 about the CoM: × ρ (g/mm³) for g·mm², × 1e-9 more for kg·m²
([[mass-properties-and-measurement#inertia-about-the-centre-of-mass-density-1]]).

## Spin time: inertia over drag

One torque grows with speed (air skin friction, viscous grease) and makes the decay exponential
while the rotor is fast; a constant one (dry friction at a tip or in a bearing) makes it linear
once slow. From launch `ω0` to the speed `ω_end` at which the toy stops working:

```text
I dω/dt = −b ω − τ_f
t = (I / b) · ln((ω0 + τ_f/b) / (ω_end + τ_f/b))      → I (ω0 − ω_end) / τ_f  as b → 0
```

Time scales with I, launch speed only through the log while air dominates: rim mass beats a harder
launch. `ω_end` is a top's critical spin (below), a yo-yo's last climbing speed, zero for a spinner.
Blunt lobes, holes and fins add pressure drag (fair a spinner's lobes); 2RS seal lips rub, ZZ do not.

## A sleeping top: the critical spin

A symmetric top spins upright on its tip ("sleeps") only above a critical rate; below it the
upright state is unstable and the top wobbles, precesses and falls. Friction slows it until
`I₃ω = 2 sqrt(I₁ M g l)`, and then it falls.

```text
ω² > ω_c² = 4 M g l I₁ / I₃²
M mass;  l height of the CoM above the tip contact;  I₃ moment about the spin axis;
I₁ transverse moment about the TIP = I_t + M l²  (I_t transverse moment about the CoM)
```

For a thin disc of radius R at height l (stem mass neglected) the mass cancels:
`ω_c = (2 / R) · sqrt(g l (1 + 4 l² / R²))`. At R = 25 mm, l = 8, 15 and 30 mm need 254, 458
and 1,078 rpm; R = 40 mm, l = 15 mm needs 229. Doubling the CoM height more than doubles ω_c.

## Shape a top: disc-like and low, with rim clearance

- **Disc-like, I₃ > I_t.** I₃ sits squared under ω_c and lengthens the spin. A thin disc has
  I₃ / I_t = 2, a sphere 1, a tall cone less than 1; require I₃ / I_t ≥ 1.2 (a design choice).
- **Low CoM.** `l` enters ω_c directly and through `I₁`: a short, light stem; a steel ball tip.
- **Rim clearance.** Tilted by θ, the top touches the table with its lowest rim point once
  `tan θ = h_r / R_r` (that point's height above the tip over its radius), and the spin dies
  when the rim scrapes. Dome or chamfer the underside to give θ_touch ≥ 15° (a design choice).

## The tip: hard, small, round enough to rise

- Tip friction torque is about μ M g × the contact patch radius. Commercial tops use ruby or
  tungsten-carbide balls; a printed PLA tip wears flat and the top walks. Press a steel or
  ceramic ball, or a steel pin with a ground radius, into a printed socket (`press` from `cadfits`).
- A rounded tip slips while the top is tilted, and that sliding friction raises it to vertical;
  a larger radius rises faster. A 5 mm ball tip self-rights more strongly than a 1.5 mm fine tip
  but rolls, so the top travels and drags more: about 1.5 mm for a quiet sleeper, 5 mm for a
  top that stands itself up. On glass it rises more slowly.

## Launching a top

| launch | spin it gives | design |
|---|---|---|
| finger twist | ω ≈ v_finger / r_stem | small finger tops leave the fingers at 5,500-7,600 rpm on a 3 mm stem; a thin stem gives a heavy rotor little torque |
| string or ripcord on an arbor | ω = v_pull / r_arbor; turns = L / (2π r_arbor) | arbor radius sets the speed, string length the turns |
| rack-and-pinion launcher | ω = N · v_rack / r_pinion | ramped lugs push one way, so the top overruns and drops free when the rack stops ([[clutches-and-freewheels#freewheels-one-way]]) |

Launch at ω0 ≥ 3 ω_c (a design choice). A top launched onto a surface is a ground-based toy;
one a launcher can throw through the air is a projectile
([[launchers-and-projectile-toys#projectile-limits-in-the-toy-standards]]).

## Tippe top

A truncated sphere with a stem, its CoM ε below the sphere's centre. Spun on the ball, sliding
friction at the contact turns it onto its stem, so the ball must be smooth and the table hard.
It inverts fully at a high enough spin only when `1 − ε/R < A/C < 1 + ε/R` (A transverse and C
axial moment about the CoM, R the ball radius); below that band it never flips.

## Fidget spinner on a 608

- **Bearing.** 608: 8 × 22 × 7 mm, 12.1 g, 7 balls Ø3.969, grease limit 34,000 min⁻¹. Shoulders:
  inner ring d_a ≥ 10 mm, outer ring D_a ≤ 20 mm. Build it with `stdpart`
  ([[shafts-and-bearings#bushing-or-ball-bearing]]).
- **Seat.** `press` or `snug` from `cadfits` ([[fit-derivation#the-fdm-clearance-table]],
  [[dowel-pins-and-press-fits#bearings-and-tpu]]); seat axis vertical so the bore is a round XY
  hole, two extrusion widths of wall at least, a backing lip with a bore ≤ D_a.
- **Caps touch the inner ring only:** a land at least d_a across and smaller than the inner
  ring, the rest recessed by a running clearance; the caps join through the bore and clamp it.
- **Weights at the rim**, equal masses at equal radius, equally spaced, every lobe identical:
  three 608s at 30 mm give 3.3e-5 kg·m² (their own spin adds under a tenth). Nuts (`stdpart`)
  and coins (measured) work too. Each pulls out with F = m r ω²: a 608 at 30 mm, 16 N at
  2,000 rpm and 36 N at 3,000. A press fit holds that; capture a coin behind a lip.

## Yo-yo: bearing, gap and response

- **Mass at the rim.** On the string `a = g / (1 + I / (m r²))`, r the radius the string
  unwinds from; the share of the drop that becomes spin is `I / (I + m r²)`. A 65 g yo-yo,
  R = 28 mm, I = 0.6 m R², on a size C bearing (r = 6.35 mm) falls at 0.08 g with 92 % in
  spin. Rim mass raises I without mass, so a throw sleeps longer: thin web, heavy rim.
- **Bearings** (bore × OD × width): size C .250 × .500 × .187 in (6.35 × 12.7 × 4.76 mm, inch
  R188); A 5 × 10 × 4 (MR105); D 5 × 11 × 5; a metric 6 × 13 × 5. Clamp the inner ring between
  the halves on a steel axle; the string loops round the outer ring. Make the halves identical:
  a mass or CoM difference between them is a couple imbalance (vibe).
- **Gap = bearing width + shims.** Wider spins smoother and responds less; narrower catches the
  string and returns. Players run unresponsive gaps of 4.15-4.45 mm and call 5 mm wide.
- **Response.** A fixed axle or narrow gap returns on a tug. An unresponsive yo-yo has a wide gap
  and low-friction pads in a ring groove in each inner wall, and returns by a bind.
- **Safety.** EN 71-1 4.24's 370 mm tether limit covers the elastic *yo-yo ball*, not a string
  yo-yo ([[toy-safety-constraints#other-numeric-limits-in-en-71-1]]); record the rule used.

## Gyroscope: precession and gimbals

```text
Ω ≈ M g r / (I ω)      valid while ω ≫ Ω
M total mass, r CoM distance from the pivot along the axis, I rotor axial moment, ω rotor spin
```

Precession speeds up as spin decays, until it falls (100 g, r 40 mm, 2e-5 kg·m², 500 rad/s: 3.9 rad/s).

- **Rotor and axle.** A heavy rim (brass or steel ring on a printed hub) on a steel axle, never
  printed ([[shafts-and-bearings#printed-shaft-or-bought-rod]]), in two small bearings (MR63,
  623) or on pointed ends in cone cups; press the rotor on a D-flat or knurl.
- **Gimbals.** Each ring pivots on a coaxial pair; the rotor CoM sits where all gimbal axes
  cross, so gravity has no lever arm. Keep the rings light.
- **Balance.** ISO 21940-11 puts gyroscopes at G0.4-G1, beyond any print: balance after printing.

## Flywheel burst speed in printed plastic

```text
thin ring                     σ = ρ v²                      v = ω R, the rim speed
solid disc, at the centre     σ = (3 + ν)/8 · ρ v²  ≈ 0.42 ρ v²   (ν 0.3-0.4)
disc with a bore, at the bore σ → (3 + ν)/4 · ρ v²  ≈ 0.84 ρ v²   (small bore: twice the disc)
```

A rotor bursts when hoop stress passes the tensile strength; a hub bore doubles a disc's peak.
Allow 10 MPa for solid PLA printed flat, axis vertical so hoop stress runs in the layer plane
([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]): a design choice, about
UTS_xy / 5 and under the PLA fatigue curve at 10⁴ spin-ups (13.7 MPa,
[[printed-fatigue#a-design-curve-for-printed-pla]]). At ρ = 1.24 g/cm³:

| rotor | v_max m/s | rpm at R 20 mm | R 30 mm | R 50 mm |
|---|---|---|---|---|
| thin ring | 90 | 42,900 | 28,600 | 17,200 |
| disc with a bore | 98 | 46,900 | 31,200 | 18,700 |
| solid disc | 139 | 66,300 | 44,200 | 26,500 |

A hand spin never gets close; a geared flywheel can, and at the limit a PLA ring holds σ / (2ρ) ≈
4 J/g: enclose it. Never print a rotor on edge (hoop stress crosses the layers); check rim pockets for m r ω².

## Friction motors and pull-back motors

- **Friction (inertia) motor:** a flywheel geared up from the wheels, spun up by pushes, then
  driving the car; a one-way clutch is optional. One patented train is 5:1 × 6:1 = 30:1 (at
  least 20:1) with a 2.6 in, 14 oz iron flywheel, running up to two minutes.
- **Flywheel speed** while the tyres grip is `ω_f = N v / r_w`: N = 30, 10 mm wheels and a
  2 m/s push give 6,000 rad/s, so a PLA ring of R = 15 mm is at 90 m/s, the limit.
- **Reflected inertia** `m_eff = I (N / r_w)²` is the extra mass the car feels: a PLA disc
  Ø50 × 8 at N = 30 on 10 mm wheels feels like 55 kg and the tyres skid; a steel Ø20 × 5 disc,
  5.6 kg. Grip caps spin-up torque at μ m g r_w: size I so a few pushes spin it up.
- **The train must back-drive** ([[energy-drive]]); at flywheel speed use a steel shaft and a
  small module ([[gears#trains-and-ratio-budget]], [[noise-and-vibration]]).
- **Pull-back motor:** a bought module, a flat spiral spring wound by rolling back and a clutch
  that frees the wheels once run down. No standard size: search `$step-parts`, measure the unit
  you buy, seat it with `cadmount` ([[seating-bought-parts]]).

## Balance: static, couple and what the print adds

- **Static imbalance:** the CoM sits e off the axis, a rotating force m e ω² (buzz, a walking
  top). **Couple imbalance:** CoM on the axis but the principal axis tilted, so the products
  I_xz, I_yz about the CoM (z on the spin axis) are non-zero. A thin disc mostly needs static
  balance; a long rotor (gyroscope, two-half yo-yo) needs both.
- **Allowance:** ISO 21940-11 sets e_per = G / ω (mm, G in mm/s); flywheels and fans are G6.3:
  30 µm at 2,000 rpm, 10 µm at 6,000, below FDM's scatter.
- **What the print adds:** sparse or non-axisymmetric infill puts mass on one side; an aligned
  or rear seam stacks its blobs on one radius ([[fdm-surface-finish#seams]]). Print rotors flat,
  solid or concentric infill, random seam ([[perimeters-infill-and-strength]]). Then balance
  statically on knife edges or in its own bearing: add mass opposite the side that settles down.
- **In the model:** check each material group alone, then sum I₃ and I₁ over the groups. If
  each group's CoM is on the axis and its products about its own CoM are zero, the
  parallel-axis terms vanish, whatever sign convention the products use.

## Checks

```python
import math
from build123d import CenterOf
c, I = rotor.center(CenterOf.MASS), rotor.matrix_of_inertia   # density 1, about CoM; spin axis = Z
assert math.hypot(c.X, c.Y) <= 0.01, "CoM off the spin axis in the model (mm)"
assert max(abs(I[0][2]), abs(I[1][2])) <= 1e-4 * I[2][2], "couple imbalance"
assert I[2][2] / I[0][0] >= 1.2, "top is not disc-like (I3 / I_t)"
l = (c.Z - TIP_Z) / 1000                                       # m
M = rotor.volume * RHO / 1000                                  # kg, RHO in g/mm^3
I3, I1 = I[2][2] * RHO * 1e-9, I[0][0] * RHO * 1e-9 + M * l * l
w_c = 2 / I3 * math.sqrt(I1 * M * 9.81 * l)
assert W_LAUNCH >= 3 * w_c, f"launch {W_LAUNCH:.0f} rad/s vs critical {w_c:.0f}"
assert math.degrees(math.atan2(RIM_H, RIM_R)) >= 15, "rim scrapes before the top can wobble"
v = W_MAX * R_RIM / 1000                                       # m/s at the fastest drive
assert K_SHAPE * RHO_SI * v * v <= 10e6, "hoop stress over the PLA allowable"  # 1 ring, 0.42 disc, 0.84 bored
assert M_W * (R_W / 1000) * W_MAX ** 2 <= F_POCKET, "rim weight pulls out of its pocket"
```
