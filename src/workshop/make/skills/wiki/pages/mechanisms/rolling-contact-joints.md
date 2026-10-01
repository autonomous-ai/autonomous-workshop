---
title: Rolling-contact joints
tags: [joint, rolling, band, ligament, hinge, knee, finger, revolute, compliant]
aliases: [rolling contact joint, rolling joint, RCJ, CORE, compliant rolling-contact element, rolling-contact element, D-CORE, XR joint, Xr-joint, cross-strip rolling pivot, crossed-strap hinge, crossed band hinge, rolamite hinge, rolamite, Jacob's ladder, Jacobs ladder toy, flip-flop toy, tumbling blocks, Rubik's Magic, Jacob's ladder hinge, flip-flop hinge, two-way hinge, 360 degree hinge, double-action hinge, rolling knee, condylar joint, cruciate ligament joint, crossed four-bar knee, polycentric knee, ligament joint, robot finger joint, Hillberry joint, geared hinge, geared continuous hinge, gear-constrained rolling joint, noncircular rolling joint]
sources:
  - https://patents.google.com/patent/US3932045A/en (Hillberry and Hall, rolling contact joint: straps keep the surfaces in pure rolling; non-circular contours set the torque)
  - https://patents.google.com/patent/US3945053A/en (straps on smaller shoulders, not sandwiched; non-concentric shoulders strain the bands into a spring; four straps, inner pair spaced so straps never touch)
  - https://patents.google.com/patent/US4558911A/en (Ruoff: band pair one way, single band the other; 1:1 pay-out and take-up; bands may sit in grooves)
  - https://en.wikipedia.org/wiki/Jacob%27s_ladder_(toy) (interlaced ribbons hinge each block at either end)
  - https://patents.google.com/patent/US20100227529A1/en (three ribbons per joint: one one way, the pair the other)
  - https://mathematische-basteleien.de/jacob.htm (one toy: blocks 80 x 47 x 10 mm, 15 mm ribbons, 3 mm between blocks, glued at the short ends only)
  - https://en.wikipedia.org/wiki/Rolamite (S-band between two rollers; friction coefficients as low as 0.0005)
  - https://scholarsarchive.byu.edu/etd/895 (Halverson thesis abstract: CORE, 360 deg deflection, multistability from tension in the bands)
  - https://www.witpress.com/Secure/ejournals/papers/D&NE080302f.pdf (Etoundi et al. 2013, condylar knee: ICR at the crossing of the cruciates, 160 deg, cable tension trade-off, 0.65 mm nylon cable at 3.7 N, slid apart past 60 deg until a compression strut was added)
  - https://arxiv.org/pdf/2308.02453 (tendon hand: rolling joints with a pair of crosswise ligament strings, modelled as two virtual hinges through the cylinder axes rotating together)
  - https://arxiv.org/pdf/2504.04259 (rolling joints dislocate instead of breaking; ligaments can loosen over time)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12890850/ (noncircular rolling joints: equal-arc and tangency conditions, PLA bodies, TPU 85A ligaments printed 20 % short, 1,000 cycles plus 300 impacts)
  - https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2023.1164660/full (rolling knee: equal radii, shin 45 deg gives knee 90 deg; fibre cables creep and need retensioning)
  - https://en.wikipedia.org/wiki/Geared_continuous_hinge (leaves with meshing teeth held under a cap)
  - Norton, Design of Machinery, ch. 6 (instant centres; pure rolling puts the instant centre at the contact point)
  - Shigley's Mechanical Engineering Design, ch. 3 (contact stresses between two cylinders)
  - "Jeanneau, Herder, Laliberte, Gosselin, A compliant rolling contact joint and its application in a 3-DOF planar parallel mechanism, ASME DETC 2004 (the XR name: crossed bands, rolling DOF; via search summary only)"
  - skills/cad/scripts/cadfits.py
related: [joints, hinges-and-pin-joints, flexures-and-living-hinges, cable-and-tendon-drives, gears, print-in-place-mechanisms, creep-and-stress-relaxation, flexure-materials-and-snap-strain, layer-anisotropy, arm-and-gripper-sizing, posable-figure-joints, linkages, latches-detents-and-ratchets, scissor-and-pantograph-linkages]
updated: 2026-10-01
---

# Rolling-contact joints

A rolling-contact joint replaces a pin with two curved surfaces that roll on
each other, held together and kept from slipping by flexible bands, cords or
gear teeth. It has no sliding surface, so friction and wear are low; it can
turn far past 180°, and under overload it dislocates instead of breaking.
The costs are a moving axis, bands that stretch, creep and need tension, and
almost no resistance to being pulled apart. Pinned hinges are in
[[hinges-and-pin-joints]]; joints that bend instead are in
[[flexures-and-living-hinges]].

## Forms

| form | what holds it | use |
|---|---|---|
| **CORE / XR joint** (two cylinders, crossed bands) | ≥ 2 bands crossing at the contact, in opposite senses | compliant revolute joint, robot fingers, parallel stages |
| **Jacob's ladder / two-way hinge** | flat panels, 3 ribbons per joint (1 one way, 2 the other) | toy, a hinge that folds either way through 360° |
| **rolling knee** (convex condyle on a flatter seat) | crossed straps or cords as cruciate ligaments | knees, wide-range limbs carrying body weight |
| **noncircular rolling joint** | crossed ligaments on cam profiles | a programmed speed or force ratio along the stroke |
| **gear-constrained rolling joint** (geared hinge) | meshing teeth plus a link holding the centres | a two-pin hinge that splits the angle; no bands |
| **rolamite** (linear) | an S-band round two rollers in a channel | low-friction linear guide or sensor ([[linear-guides-and-slides]]) |

## Kinematics: the contact point is the instant centre

Rolling without slip means equal arc lengths on both surfaces and a common
tangent at the contact. The instant centre of body 2 relative to body 1 is
then the contact point itself, and it moves along both surfaces.

```text
ρ1, ρ2   rolling radii at the contact (add t/2 when a band of thickness t lies in the contact)
φ        rotation of the line of centres O1→O2 about O1, body 1 held
θ        joint angle: rotation of body 2 relative to body 1
s = ρ1 φ                    arc rolled on each surface
θ = φ (ρ1 + ρ2) / ρ2        equal radii: θ = 2 φ
O1O2 = ρ1 + ρ2              constant
```

With equal radii the joint is exactly **two virtual pins**, one at each
centre, each turning θ/2. One tendon-hand model simulates it that way, and
a humanoid's equal-radius knee reads 90° for 45° of shin rotation. A point
at L beyond O2 sits at `(2ρ sin(θ/2) + L sin θ, 2ρ cos(θ/2) + L cos θ)`
from O1, body 1 along y. At 90° that is `(√2 − 1) ρ ≈ 0.41 ρ` further out
on each axis than a pin at the first contact point would put it, so skins,
covers and tendon paths must let the joint lengthen as it bends.

## The band length condition

A band is anchored on body 1, runs along its surface to the contact, crosses
there, and runs along body 2 to its anchor. As the bodies roll, the band
pays out from one body and winds onto the other by the same arc.

- **Band in the contact** (sandwiched between the surfaces): the length is
  constant for **any** pair of profiles that roll without slip, circular or
  not. The surfaces roll on the band's mid-plane, so the centre distance is
  `R1 + R2 + t`.
- **Band on shoulders** (strap surfaces of radius r beside rolling surfaces
  of radius R, so the bodies touch each other directly): the crossed band's
  length is constant only if `r1 / R1 = r2 / R2` (equal radii: equal
  shoulders, concentric). A shoulder that is not concentric strains the band
  as the joint turns. That makes a return spring, or with several minima a
  multistable joint that clicks into positions without a detent.
- **Range.** A band stops the joint when its anchor reaches the tangent
  point. With `w1` the wrap angle left on the unwinding body,
  `θ_max = w1 (ρ1 + ρ2) / ρ2`, or `2 w1` for equal radii.
- **Both senses.** One band prevents slip in one direction only. Use bands
  of both senses. Split the width symmetrically (one centre band one way,
  two outer bands the other) so that tension does not twist the joint. That
  is the Jacob's ladder's three ribbons and a robot-joint patent's band pair
  plus a single band. Keep bands at separate axial positions so they never
  rub.

## Load paths and band tension

| load | carried by | consequence |
|---|---|---|
| compression across the contact | the surfaces, as a line contact | stiff; the reason a knee rolls |
| tangential force `F_t` at the contact | the bands of one sense, tangent there | `ΣT = F_t`, one to one |
| pull-apart along the line of centres | the bands, nearly perpendicular to it | almost no stiffness until a gap opens |
| moment about the joint | nothing (circular, concentric) | a true revolute joint; non-circular or eccentric straps add torque |

For a pull-apart force `F` on equal radii ρ, virtual work over the crossed
band gives `F = ΣT · √(δ/ρ)` once a gap δ has opened: a 1 % gap needs a
band tension of 10 F. Arrange the working load to press the surfaces
together, and add a hard stop, a compression strut or a preload spring for
the pull-apart case. One prosthetic knee slid apart past 60° until a
compression bar was added across one diagonal of each ligament four-bar.

Contact pressure on two cylinders of face width l pressed by N (Shigley's
line contact; d = 2ρ, negative for a concave seat):

```text
b     = sqrt( (2 N / (π l)) · ((1 − ν1²)/E1 + (1 − ν2²)/E2) / (1/d1 + 1/d2) )
p_max = 2 N / (π b l)
```

Illustrative: two PLA cylinders, ρ = 10 mm, l = 10 mm, N = 50 N,
E ≈ 3.4 GPa → b ≈ 0.13 mm, p_max ≈ 25 MPa, high for a print held under load.
A convex condyle in a nearly matching concave seat (a conformal pair) and a
wide face cut it by a large factor. Check p_max against
[[beam-and-plate-stiffness#safety-factors-for-printed-plastic]] and, for a
held pose, against creep ([[creep-and-stress-relaxation]]).

**Band bending strain.** Every band element that crosses the contact goes
from curvature `+1/ρ1` to `−1/ρ2`. The strain range per pass is

```text
Δε = (t / 2) · (1/ρ1 + 1/ρ2)        equal radii: Δε = t / ρ
```

Keep Δε within the band material's repeated-strain limit
([[flexure-materials-and-snap-strain#flexures-and-printed-springs]],
[[printed-fatigue]]). At 2 % a rigid-plastic band needs ρ ≥ 50 t. This is
why bands are spring-steel shim, cord, cloth or TPU, and why rigid printed
strips are one or two layers thick and wrap large radii.

**Tension is a trade-off.** Too tight and the joint has friction; too slack
and it is unstable and slides. One knee prototype solved this with
compliance: one long 0.65 mm nylon monofilament threaded through the joint
11 times, pretensioned to 3.7 N by threaded bushes, gave 160° of motion and
50,000 loaded cycles.

## Jacob's ladder and the two-way hinge

Each block is tied to the next by three ribbons. The single ribbon runs over
the end of one block and under the next; the pair runs the other way. The
joint can therefore hinge about either end of the gap. Lift the top block,
flip it, and each block in turn falls over onto the next. A pair of flat
panels tied this way folds face to face in either direction: a hinge with
360° of travel and no pin, used in folding wallets and puzzle toys. It is a
CORE whose rolling surfaces are the panel edges. Give each panel end a full
round (radius half the panel thickness) so the ribbon bends over a radius
and not a corner, and glue or clamp ribbons only at the panel ends, never
along the rolling face.

## Rolling knees and finger joints

- **Knee as a crossed four-bar.** The cruciate ligaments and the two bones
  form a crossed four-bar. The instant centre is where the ligaments cross,
  and it travels (about 2 cm in an adult knee) while the condyle rolls and
  slides on the tibia. Shape the condyle profile to match the four-bar's
  moving centre. Put a crossed pair on each side of the joint rather than
  one in the middle, for lateral stability ([[linkages#four-bar]]).
- **Robot fingers.** Two cylinders with crossed ligament strings or bands,
  with tendons routed across the joint
  ([[cable-and-tendon-drives#tendon-driven-joints-and-fingers]]). Under
  overload they dislocate instead of breaking, which is why printed hands
  use them. Their ligaments loosen over time, so give them a tensioner.
- **Noncircular profiles** make the transmission ratio vary along the
  stroke: torque = r_e · F with r_e the instantaneous effective radius. One
  design varied end speed from near 0 to 4 × the mean. Generate the two
  profiles together from the equal-arc and common-tangent conditions; never
  draw them independently.

## Gear-constrained rolling joints

Replace the bands with teeth: two gear sectors whose pitch circles are the
rolling circles, and a link (side plates or a cap with two pins) holding the
centres at the pair's centre distance. The kinematics are those above, with
ρ the pitch radii. Each body turns θ/2 about its own pin for equal gears, so
a 180° geared hinge turns each leaf only 90°. A geared continuous door hinge
is this joint along a whole edge. The teeth carry the tangential load and
the link carries separation and compression, so it holds pull-apart better
than any banded joint. Mesh backlash `b_t` at the pitch circle becomes
angular play of about `b_t / ρ`, added to the link's pin clearances.

Build the sectors from `stdpart` (`stdpart sizes` for the gear family) so
that the centre distance comes from the gear pair and is never typed. Bore
the link with `cadfits.slot_for(PIN_D, RUN)`. Printed tooth limits are in
[[gears#printed-tooth-choices]].

## Printing rolling joints

| band | how | rule |
|---|---|---|
| **TPU strip** | printed flat, strands along the band, ≥ 2 layers | it stretches; print it short so it is prestrained when fitted (one study printed TPU 85A ligaments 20 % short); anchor by a loop over a pin or a clamp, never by glue alone |
| **cord, fishing line** | through holes, crossing at the contact; knots or crimps ([[cable-and-tendon-drives#anchoring-a-cord-in-a-print]]) | braided HMPE stretches least; nylon creeps and wants a tensioner ([[cable-and-tendon-drives#cord-materials]]) |
| **PLA/PETG strip** | one or two layers, printed flat | only with ρ ≥ 50 t (Δε above) and few cycles |
| **spring-steel shim** | bought, clamped under a printed plate | the classic band: no creep, highest life |
| **print-in-place band** | vertical walls interleaved along a vertical joint axis | each band is printed off its surface by the print-in-place xy gap ([[print-in-place-mechanisms#the-gap-is-per-face-and-per-direction]]), so it is slack by about gap × total wrap angle (rad); add a tensioner |

- **Joint axis vertical (Z).** The rolling surfaces are then perimeters,
  smooth along the rolling direction, and the contact line rests on every
  layer. With the axis in the bed plane the profile is stair-stepped where
  it rolls and its underside is an overhang ([[layer-anisotropy]]).
- Set the band into a groove of depth ≈ t, or onto shoulders, when the
  bodies themselves should touch. Radius every edge where a band leaves an
  anchor: a sharp exit is where bands tear.
- Print TPU bands and rigid bodies separately, and fit them mechanically. A
  bonded multi-material interface peels under band tension.

## Failure classes

| symptom | cause | rule |
|---|---|---|
| joint clunks, bodies slide | band slack: creep, anchor slip, TPU stretch | prestrain, tensioner, low-creep cord; re-tension on a schedule |
| pops apart under a pull | pull-apart carried only by band tension | keep the load compressive; add a stop, strut or preload |
| stiff, gritty | over-tension | add compliance to the band system; adjustable anchor |
| prefers one angle | a flat spot from creep under a held pose, or an eccentric shoulder | conformal contact, wide face, low p_max; or make the detent deliberate ([[latches-detents-and-ratchets]]) |
| band tears at the anchor or crossing | strain range too high, sharp exit | Δε rule; radius every exit |
| joint twists out of plane | bands of one sense on one side | split widths symmetrically about the mid-plane |

A rigid-body sweep can pose the two virtual pins, but it proves nothing
about band tension, slip or life. Record those as open items
([[mechanism-verification#9-what-nothing-here-proves]]).

## Checks

```python
import math
rho1, rho2 = R1 + T_BAND / 2, R2 + T_BAND / 2            # band in the contact
theta_max = math.radians(BAND_WRAP_DEG) * (rho1 + rho2) / rho2
assert theta_max >= math.radians(JOINT_RANGE_DEG), "band unwinds to its anchor inside the range"
if BANDS_ON_SHOULDERS:
    assert abs(R_STRAP1 / R1 - R_STRAP2 / R2) < 1e-6 or SPRING_INTENDED, "band length changes with angle"
assert N_BANDS_SENSE_A >= 1 and N_BANDS_SENSE_B >= 1, "bands of one sense only: the joint slips one way"
d_eps = T_BAND / 2 * (1 / rho1 + 1 / rho2)
assert d_eps <= EPS_REPEATED[BAND_MATERIAL], f"band strain range {d_eps:.2%} per pass"
k = (1 - NU**2) / E_BODY
b = math.sqrt(2 * N_LOAD / (math.pi * FACE_W) * 2 * k / (1 / (2 * R1) + 1 / (2 * R2)))
assert 2 * N_LOAD / (math.pi * b * FACE_W) <= P_ALLOW, "contact pressure flattens the printed surface"
assert LOAD_PRESSES_SURFACES or HAS_PULL_APART_STOP, "a banded joint barely resists being pulled apart"
```
