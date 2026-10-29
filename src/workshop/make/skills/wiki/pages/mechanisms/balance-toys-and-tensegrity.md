---
title: Balance toys, tumblers and tensegrity tables
tags: [balance, center-of-mass, ballast, self-righting, rocking, tensegrity, pendulum, desk-toy]
aliases: [balancing bird, balance bird, balancing figure, balancing toy, balance on a fingertip, centre of mass below the pivot, roly-poly, roly poly, tumbler toy, weeble, wobble toy, self-righting toy, daruma, okiagari-koboshi, nevalyashka, rocking toy, rocker, rocking horse, floating table, tensegrity table, impossible table, floating compression, newton's cradle, collision balls, kinetic desk sculpture]
sources:
  - https://www.physics.unlv.edu/~jeffery/astro/mechanics/center_of_mass_balancing_bird.html (a free pivot above the CoM is stable; the bird's equilibrium is weak, a small push tips it)
  - https://users.rowan.edu/~klassen/dpa/facultyStaff/Docs/physics_demos/mechanics_html/well_balanced.html (lead wingtip weights reach below the beak; a tilt gives a restoring torque; balances on a knife edge)
  - https://en.wikipedia.org/wiki/Roly-poly_toy (hollow, weight in the bottom hemisphere, CoM below the hemisphere's centre)
  - https://van.physics.illinois.edu/ask/listing/26904 (CoG below the centre of rotation is stable, above falls, coincident is neutral)
  - https://scholarworks.iu.edu/dspace/items/f07ec8a4-316c-4e6a-bccf-512a56610d7c (De, Mathematics Magazine 90(2) 2017 99-107: stable when the CoM is below the centre of curvature of the contact point)
  - https://peer.asee.org/27508.pdf (Hayen 2017, rocking half disk: energy method, omega = sqrt(8g/((9 pi - 16) R)); R 47.6 mm gives 0.542 s, measured 0.500-0.543 s at 10-30 deg release; slips at large release)
  - https://www.comsol.com/blogs/modeling-tensegrity-with-a-floating-table (central wire carries the weight; outer wires keep the top from tipping, near zero force under a centred load, low under twist)
  - https://en.wikipedia.org/wiki/Tensegrity (isolated compression in continuous tension; three cables minimum to locate a member; Snelson 1948, Fuller's term)
  - https://www.the-diy-life.com/make-your-own-3d-printed-tensegrity-tables (fishing line glued in 0.5 mm holes drilled out 0.5-1 mm; centre 8-10 cm, three outer 12-13 cm exactly equal; outer lines first, centre last; about 200 g before the outer lines flex; over-tightening bends the plates)
  - https://stirlingengine.co.uk/products/tensegrity-table-with-centre-wire (92 mm plates 8 and 3 mm thick, 0.4 mm 7-strand stainless wire with crimps, 130 mm tall, tensioner in the base)
  - https://gadgetbuilder.com/TensegrityTable.html (0.012 in music wire with soldered stops, 4-40 screw adjusters, three holes 120 deg apart 6 mm from the edge with counterbore and edge slit; arms carry bending; shivers up to 45 s after a flick)
  - https://fab.cba.mit.edu/classes/863.24/people/Shun-YingChen/posts/week9 (outer wires too long made it wobble; centre wire snapped, went to 2 then 6 threads; screws gave little adjustment, turnbuckles suggested; levelling took an hour)
  - https://3dwithus.com/tensegrity-models-designs-for-3d-printing-and-slicer-settings (base at least as wide and deep as the top; anchors must not be thin)
  - https://en.wikipedia.org/wiki/Newton%27s_cradle (equal masses for the simple transfer; steel compresses little, impacts under 200 us; every impact loses energy)
  - https://www.howitworksdaily.com/how-does-newtons-cradle-work/ (two wires per ball keep it in one plane; usually five or seven balls)
  - https://makezine.com/article/craft/designing-modern-newton-cradle-from-scratch/ (1 in steel balls, a bead epoxied on top; slightly touching balls beat a small gap)
  - https://www.scorchworks.com/Blog/?p=366 (5/8 in bearing balls in a moulded ring; each line wound on a screw; alignment is critical)
related: [stability-and-tipping, counterweights-and-gravity-balance, pendulums-and-escapements, mass-properties-and-measurement, toy-safety-constraints, cable-and-tendon-drives, creep-and-stress-relaxation, magnets-and-strap-slots, noise-and-vibration, exact-constraint-and-kinematic-mounts]
updated: 2026-10-10
---

# Balance toys, tumblers and tensegrity tables

Desk toys that look impossible are statics with one number each: where the
centre of mass (CoM) sits against a pivot, a centre of curvature or a tension
member. Flat bases are [[stability-and-tipping]], balanced arms
[[counterweights-and-gravity-balance]]. Weigh every CoM by density, each
ballast its own solid ([[stability-and-tipping#computing-it-in-build123d]]).

## A body balanced on a point hangs from it

A rigid body on a free point pivot is stable only with its CoM strictly
**below** the pivot: it is a pendulum, and a tilt θ returns `m g d sin θ`
(`d` = pivot-to-CoM distance). Above the point it is an inverted pendulum and
falls. A balancing bird is a pendulum whose bob is outside its body.

- **It rests in the modelled pose only if the model's CoM is under the pivot.**
  A plan offset `e` pitches it by `atan(e / d)`.
- **Size `d` from the imbalance you will get.** A mass error `Δm` at lateral
  distance `s` tilts it by `atan(Δm s / (m d))`; pick the tilt you accept
  (3-5° is a design choice) and solve for `d`.
- **`d` sets the swing**: `T = 2π √(I_P / (m g d))`, `I_P` about the pivot
  ([[pendulums-and-escapements#pendulum-period]]). Small `d` swings lazily and
  sags under any error; large `d` is stiff. Even so the equilibrium is weak: a
  small push knocks the bird off its point.

Worked: an 18.2 g bird with 0.2 g of wing imbalance at 70 mm tilts 8.7° at
`d` = 5 mm, 2.9° at `d` = 15 mm; its roll period is 1.43 s and 0.83 s.

## Sizing the wingtip ballast

Two equations fix it: the plan moment `Σ m_i x_i = m x_pivot` and the height
`z_com = z_pivot - d`. Body and tail sit behind and above, so the wings sweep
**forward and down**. Worked: 10 g of body with its CoM 30 mm behind and 5 mm
below the beak, plus two Ø10 steel balls (4.1 g each) at ±70 mm, 36.5 mm ahead
and 27.2 mm below the beak, gives `d` = 15 mm. Re-run it with the printed
wings in the body term.

- Ballast is a catalog part with known mass: steel balls or nuts (coins vary).
  The classic bird carries lead; a toy must not ([[toy-safety-constraints]],
  [[counterweights-and-gravity-balance#ballast-pockets-and-dense-fills]]).
- Seal each weight in during a print pause, or it is a loose small part
  ([[magnets-and-strap-slots#pause-and-embed]]).

## The pivot contact

- A point on a flat support (a beak on a fingertip) holds by friction and
  slides once the support tilts past `atan(μ)`. A **cone seat** on a stand
  captures it; make the seat wider than the point so contact stays at the apex
  ([[exact-constraint-and-kinematic-mounts]]).
- A **rounded tip** of radius `r` rocks about its centre of curvature, `r`
  above the contact, so rounding adds `r` to the margin; it is also the
  toy-safe tip ([[toy-safety-constraints#sharp-points-and-edges]]). A glued
  Ø3-5 steel ball does not wear; a printed point creeps flat.
- Rotate the model ±20° about the pivot: the body must clear the support.

## Self-righting: the CoM below the base's centre of curvature

A roly-poly (tumbler, weeble, daruma) is upright-stable when its CoM lies below
the **centre of curvature of the base at the contact**: coincident is neutral
(a uniform ball), above falls. For a spherical base of radius `R` and CoM
height `h`, the margin is `d = R - h > 0` and the restoring moment
`m g d sin θ`. A uniform solid hemisphere has `h = 5R/8`; ballast makes `d`
large enough to carry the body above it.

The sphere acts only while the contact is on it. A hemisphere ending at its
equator then pivots on the rim and stays restoring to a tilt of
`90° + atan(d / R)`; past that it lands on its face. So the head must touch
the floor first: resting on head and rim, the CoM is outside both contacts on
the base side and it rolls back. The general invariant: it rights itself from
every pose iff the **only stable rest on its convex hull is upright**. For a
body of revolution, over the section outline compute the CoM height above
each support line, `h(φ) = max_i (p_i - G) · n(φ)`; rests are the local minima
of `h(φ)`, and there must be exactly one.

## Ballast for a tumbler, and the lowest fill level

```text
m_b >= m_s (h_s - h_t) / (h_t - h_b)     m_s, h_s: shell mass and CoM height
                                         h_b: ballast centroid, h_t: target CoM height
```

- **Loose fill has an optimum level**: the combined CoM is lowest when the
  fill surface is exactly at the combined CoM; shot added above it raises it.
- Worked: Ø60 base, 2 mm wall, 25 g shell with its CoM at 40 mm. Loose steel
  shot (packing 0.6) bottoms out at `h` = 18.6 mm = 0.62 R with 92 g filled to
  18.6 mm. Lower needs a solid steel slug, tungsten, or a lighter, hollower
  head. A cap of height `c` in inner radius `R_i` holds `π c² (3 R_i - c) / 3`.
- A tumbler is an infant toy: the ballast must survive the drop and abuse
  tests, and released shot is a small part
  ([[toy-safety-constraints#use-and-abuse-tests-what-breaks-off-means]],
  [[toy-safety-constraints#small-parts-the-choke-test]]). Print it in, no lead;
  loose shot rattles ([[noise-and-vibration]]).

## Rocking period of a curved base

Rolling without slip on a circular base of radius `R`, CoM `d` below the
centre of curvature, radius of gyration `k_G` about the CoM:

```text
ω² = g d / (k_G² + (R - d)²)        T = 2π / ω
```

A uniform half disk gives `ω = √(8 g / ((9π - 16) R))`: 0.542 s at
R = 47.6 mm, measured 0.50-0.54 s for 10-30° releases. The period grows with
amplitude, and a smooth table lets it slip at large releases. Small `d` rocks
slowly: a tumbler with R = 30, k_G = 20 mm rocks at 0.49 s with d = 12 mm and
0.81 s with d = 6 mm.

**Rockers** (rocking horse, rocking figure) are the same body: the CoM,
**rider included**, must sit below the rocker's centre of curvature
(`h < R_r`), and the arc must run past the largest rock angle, ending upturned
or in a stop, or it rolls off the end. A desk rocker with `h` = 60,
`k_G` = 40 mm rocks at 0.48 s on R = 150, 0.72 s on R = 100, 1.45 s on R = 70.
Ride-on rockers fall under [[stability-and-tipping#how-much-angle-is-enough]].

## Tensegrity table: how the top floats

Two rigid parts, each a plate with a hooked arm; the arms interlock without
touching. A **central link** hangs from the base arm's tip down to the top
arm's tip and carries the top. The top's CoM is above that link, so alone it
is an inverted pendulum; **three or more outer links**, base edge to top edge,
pull it down and stop it tipping. Shortening the central link raises the top
and stretches the outer links: it sets the pretension.

- The outer anchors must surround the central link in plan; two leave a
  tipping axis through them.
- The central link carries `W + Σ T_outer`; under a centred load the outer
  links carry only their pretension.
- The arms are cantilevers in bending: central tension times the arm's
  horizontal reach is the root moment. PLA under constant load creeps, the
  top sags and the level drifts ([[creep-and-stress-relaxation#design-rules]]),
  so give it an adjuster.
- The base is at least as wide as the top, and the whole thing plus any load
  must stand on it ([[stability-and-tipping]]).

## Sizing the tensegrity pretension

Put the central link in plan **under the top's CoM** (the top arm pulls that
toward the arm root; compute it). An off-centre load `P` at offset `e` adds
`M = P e`; with `n` equal, evenly spaced outer links at radius `r_o`, the link
on the load side loses `2 M / (n r_o)`. It stays taut, and the top stiff, while

```text
T0 >= 2 M / (n r_o)        T_central = W + P + n T0        (vertical links)
```

Worked: a 40 g top, three links at `r_o` = 35 mm, 100 g placed 40 mm off
centre: `T0` ≥ 0.75 N (76 gf) each, central link 3.6 N. A slack link does not
drop the load, it makes the top wobble; too much pretension bends the plates.

## Tensegrity strings, anchors and levelling

- **Members:** 0.3-0.4 mm steel wire with crimped or soldered stops (exact,
  low creep); fishing line glued in drilled 0.5-1 mm holes; chain, which moves
  in link-pitch steps, so adjust elsewhere. Nylon creeps
  ([[cable-and-tendon-drives#cord-materials]]). Use several threads for the
  central link; it carries the most.
- **Level is a length tolerance.** With three outer links, one `ΔL` long tilts
  the top by `atan(ΔL / (1.5 r_o))`: 1 mm at `r_o` = 35 mm is 1.1°. Knots
  cannot hold that: fix the outer links with a printed spacer jig holding the
  top at height, use crimps or hooks, and add an adjuster (screw, tuning peg,
  turnbuckle).
- **Anchors:** a hole with a counterbore for the stop and a slit from the
  plate edge so a made-up wire drops in sideways; keep the lug thick
  ([[cable-and-tendon-drives#anchoring-a-cord-in-a-print]]). Printed sub-mm
  holes come out undersize: drill them.
- **Order:** outer links to equal length first, central link last to tension.
- **Twist is soft.** A single central string has no yaw stiffness and vertical
  outer links resist yaw only by lifting the top, so a flicked table turns and
  shivers. Outer links skewed in opposite pairs stiffen yaw; links all skewed
  one way twist the top until they hang vertical.

Failures seen: outer links too long (wobble), a weak central link (snapped),
knotted lengths (tilt), over-tightening (bent plates), arms touching.

## Newton's cradle: buy equal steel balls

- **Equal masses** make one ball stop and the next take its speed. Steel
  compresses little and impacts last under 200 µs. A printed ball is 6-7 ×
  lighter at the same size, layered and viscoelastic: impact loss, air and
  string drag dominate and the clicks die in a few strikes. Decorative only.
- **Two strings per ball** from two rack points, a V seen from the end, hold it
  in one plane (one string lets it swing any way and spin). Swing axes
  collinear, strings equal, so the centres sit on one line.
- **Balls touching at rest**: rack pitch = ball diameter. Do not drill
  hardened balls: epoxy a bead or eyelet on, or grip the ball in a printed
  collar. Wind each line on a screw or peg to align, then lock it. String
  length sets the period `2π √(L / g)`; a stiff frame keeps the energy in the
  balls. Anything meant to keep moving needs a motor or magnetic kick.

## Checks

```python
d = PIVOT_Z - com.Z                                       # balance on a point
assert d > 0, "CoM above the pivot: it falls off"
assert math.hypot(com.X - PIVOT_X, com.Y - PIVOT_Y) <= d * math.tan(math.radians(POSE_TOL_DEG))
assert math.degrees(math.atan(DM_G * S_MM / (M_G * d))) <= TILT_MAX_DEG, "imbalance tilts it"
assert COM_H < BASE_R - D_MIN, "tumbler CoM not below the base centre"
assert HEAD_TOUCH_DEG <= 90 + math.degrees(math.atan((BASE_R - COM_H) / BASE_R)), "lands on its face"
assert COM_H_WITH_RIDER < ROCKER_R and ROCKER_HALF_ARC_DEG > ROCK_MAX_DEG
assert N_OUTER >= 3 and inside(CENTRAL_XY, OUTER_ANCHORS_XY), "outer links do not surround the centre"
assert T0 >= 2 * P * E_LOAD / (N_OUTER * R_OUTER), "outer link goes slack under the design load"
assert len(set(BALL_D_MM)) == 1 and abs(RACK_PITCH - BALL_D_MM[0]) < 0.1, "cradle balls unequal or apart"
```
