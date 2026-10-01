---
title: Ball-and-socket joints
tags: [ball, socket, spherical, joint, friction, swing, retention, gooseneck]
aliases: [ball joint, ball and socket, ball-socket joint, spherical joint, spherical pair, socket joint, ball stud, ball link, ball cup, ball end, angle joint, din 71802, ball head, camera ball head, tripod ball head, friction ball joint, snap-in ball joint, split socket, clamped socket, magnetic ball joint, gooseneck, goose neck, loc-line, modular hose, segmented hose, articulated hose, flexible arm, snake arm, dumbbell joint, double ball joint, swing cone, cone angle, pivot angle, swivel angle, gimbal]
sources:
  - https://www.firgelliauto.com/blogs/mechanisms/spherical-pair (a socket wrapping 200–240° of arc retains the ball; rod ends ±13–25°)
  - https://www.igus.com/us/pdf/igubal_rod_end.pdf (plastic ball-and-socket joints WGRM/AGRM: 25° max pivot, 18° recommended; pull-off along the stud axis a fraction of the push; long-term ratings half the short-term)
  - https://www.jwwinco.com/en-us/products/3.6-Moving-transferring-connecting-with-shafts-and-joints/Angled-ball-joints/DIN-71802-Steel-Threaded-Ball-Joints-Linkaged-with-Plain-Stud (DIN 71802 swivel 18°, 15° with safety catch; pull-off 30 N at 8 mm to 100 N at 19 mm ball; snap-ring retainer)
  - https://www.lensrentals.com/blog/2013/04/how-a-ballhead-works/ (ball head: plastic bearing cups, split conical compression ring closed by the knob)
  - https://reality.tf.fau.de/projects/jointfit/jointfit-lowres.pdf (Calì et al. 2012, print-in-place friction ball joints: proud bands in socket grooves; 0.2 mm gap fused, 0.3 held, 0.6 still held; minimum 5 mm radius; SLS and PolyJet)
  - https://patents.google.com/patent/US5449206 (segmented ball-socket hose separates when over-pivoted; an internal stop ring limits the pivot)
  - https://aimsindustrial.com.au/blogs/product-guides/loc-line-modular-hose-guide (segment balls about 12.5, 17 and 23 mm; acetal; friction alone holds; large sizes need pliers)
  - https://www.binder-magnetic.com/en/magnets/7353-kd312.html (magnetic ball joint: 12 mm steel ball, 18 N holding force)
  - https://www.bernstein-werkzeuge.de/en/products/productdetails/9-284-ball-joint-holder-magnetic (degreasing the ball raises the clamp; adjusting screw under the seat)
  - https://revmaterialeplastice.ro/pdf/19%20CHISIU%201%2021.pdf (Chisiu 2021: printed ABS on a metal pin μ ≈ 0.30–0.37; across the print lines higher than along them)
  - https://patents.google.com/patent/US7021989B2/en (toy ball joint: inward socket ribs, separate retaining insert smaller than the ball)
  - https://steemit.com/design/@tara-bich/3d-printing-ball-joints (20 mm ball: difference ≤ 0.1 mm and a 2 mm lip past the equator held best)
  - https://phorm.to/blog/ball-joints-3d-printing-guide/ (maker guide: ±35° exposed, ±15–25° hidden sockets; balls under about 5 mm snap unreliably)
  - https://makeronline.com/en/model/Dummy%2013%20-%20version%201.0!/237622.html?trackModuleType=13 (kit figure designer's notes: compliant swivels instead of tight tolerances)
  - skills/cad/scripts/cadfits.py (seat and slot derivation, print-in-place gaps)
related: [joints, snap-fit-design, print-in-place-mechanisms, exact-constraint-and-kinematic-mounts, kit-assembly-clash-diagnosis, creep-and-stress-relaxation, layer-anisotropy, friction-wear-and-lubricants, shaft-couplings, magnets-and-strap-slots, posable-figure-joints, rod-ends-and-clevises, swivels-and-turntables]
updated: 2026-10-01
---

# Ball-and-socket joints

A ball in a socket is the spherical pair: three turns about one point and no
translation ([[joints#kinematic-pairs-name-the-freedom-before-the-form]]).
Every printed one trades how far it swings, how hard it holds and how firmly
it stays together. This page sizes all three and picks the form. The
one-line row is [[joints#revolute-joints]], the split-cup snap is
[[snap-fit-design#ball-snap-a-split-cup]], a ball printed in its socket is
[[print-in-place-mechanisms#captive-shapes]], and figure articulation is
[[posable-figure-joints]].

## Closure, undercut and swing

Ball centre at the origin, socket axis out of the mouth. `R` ball radius,
`r_m` mouth (lip) radius, `r_n` neck radius where the neck crosses the lip.

```text
lip polar angle      φ_m = asin(r_m / R)           from the mouth axis
undercut per side    y   = R − r_m = R (1 − sin φ_m)
arc wrapped          A   = 360° − 2 φ_m             in a section through the axis
swing half-angle     θ_max = asin(r_m / R) − asin(r_n / R)
swing cone           2 θ_max                         included angle
```

(The neck meets the lip when the lip's distance from the neck axis,
`R · sin(φ_m − θ)`, falls to `r_n`.)

- **Closure buys retention and costs swing.** A smaller `r_m` raises `y` and
  the pull-out force ([[snap-fit-design#annular-snap]]); `θ_max` falls by the
  same angle. A socket wrapping 200–240° of arc retains its ball without a
  clip (Firgelli): `φ_m` = 80–60°, `y` = 0.015–0.13 R.
- **The neck is the other half of the swing.** Size it from the torque it
  carries ([[#the-neck-is-the-fuse]]) and no thicker.
- **Worked.** `R` = 5, `r_m` = 4.6 (`y` = 0.4), `r_n` = 2.5: θ_max =
  66.9° − 30.0° = 36.9°, a 74° cone. A maker guide gives ±35° exposed and
  ±15–25° hidden in a sculpt; bought plastic ball sockets 25° (18°
  recommended), DIN 71802 angle joints 18°. A 20 mm test ball held best with
  its lip 2 mm past the equator (`y` = 10 − √96 = 0.20 mm) and a ball-to-socket
  difference of 0.1 mm or less.
- **More swing one way: notch the rim.** A slot `slot_for(2 · r_n, RUN)` wide
  lets the neck drop to 90° in one plane (a camera head's portrait notch). The
  ball escapes there first: keep the slot narrower than the ball and put it
  where the load presses the ball in.
- **Derive the seat from the ball**: gripping `cadfits.slot_for(D_BALL,
  "press")` or a coupon's negative per-side value, free `slot_for(D_BALL,
  "slip")`, lip `D_LIP = D_BALL − 2 · y`.

## Leaning on the stop pulls the ball out

When the neck lands on the lip and the user keeps pushing with a moment `M`,
the lip's reaction tilts with the neck, and part of it points out of the mouth:

```text
F_out ≈ (M / L_s) · sin θ_max       L_s ≈ R for a lip stop; the ball pops when F_out > W (separation force)
```

A segmented hose fails this way, levering a ball out over the next lip; the
patent's fix is an internal stop ring met first (US5449206). Stop the swing
far from the centre (a limb tab meeting the housing, large `L_s`), flare the
mouth to a cone at `θ_max` so the neck lands on a line, and size `W` for the
worst over-pose moment.

## Holding torque: friction on the ball

Each contact `i` presses on the ball with `N_i` aimed through the centre and
slides at up to `R` from the turning axis:

```text
T ≈ μ · R · k · Σ N_i
k = 2/π ≈ 0.64   equatorial contact ring bent about an axis in its plane; rings nearer the pole give more
k = sin φ_c      the same ring turned about the socket axis (twist), ring at polar angle φ_c
k = 1            upper bound: use it, with the high μ, for the slip torque; size the hold on 2/π and the low μ
```

| form | normal force from | `Σ N` |
|---|---|---|
| split socket, `n` fingers sprung by interference `δ` | finger bending | `n · E b t³ δ / (4 L³)` (flat strip; a curved shell finger is stiffer) |
| two-piece clamped socket | screw preload `F` | `F / cos φ_c` on each seat ring |
| ball pressed into a cone | wedging | `F / sin α`, `α` the cone half-angle |
| magnetic | magnet pull `F_m` | `F_m` on a cup, `F_m / sin α` on a cone |
| strung on an elastic cord | cord tension `F_c` | `F_c` |

- **μ is a range.** Printed ABS and PLA on a metal pin: about 0.30–0.37,
  higher across the print lines than along them (Chisiu 2021). Plastic on the
  same plastic runs higher ([[snap-fit-design#mating-and-separating-force]]).
- **Preload from a long, soft spring, not a thin interference.** A printed
  radius is uncertain by about a tenth of a millimetre, the whole of cadfits'
  snug clearance (0.10 per side). An interference that size comes out
  anywhere from zero to double: floppy or seized. Make the deflection several
  times the print error and soften the spring (longer, thinner fingers, a TPU
  liner, an O-ring, a coil spring). A widely printed kit figure replaced its
  tight-tolerance swivels with a compliant member for exactly this reason.
- **Worked.** 4 PETG fingers, `E` ≈ 2000 MPa, `b` = 4, `t` = 1.2, `L` = 6,
  `δ` = 0.10: 1.6 N each, `ΣN` = 6.4 N; `R` = 5, μ = 0.3, `k` = 0.64 →
  `T` ≈ 6.1 N·mm. A ±0.05 mm print error moves it from 3.1 to 9.2 N·mm.
  Radius buys torque (`T ∝ R` at one `N`, `∝ R³` at one contact pressure): a
  bigger ball beats a tighter one.
- **Seat on rings, not a hemisphere.** A full spherical seat touches wherever
  print error puts the high spots. Relieve it to one or two rings, the
  three-constraint ball in a cone ([[exact-constraint-and-kinematic-mounts#count-constraints-not-features]]).
  A rigid check reads the grip as a spherical-shell overlap: declare it
  ([[kit-assembly-clash-diagnosis#classify-it]]).

## The neck is the fuse

Every pose loads the neck with the slip torque. A joint that grips harder
than its neck can bear breaks at the neck.

```text
σ_neck = 32 · T_slip / (π · d_n³)          solid round neck in bending
d_n ≥ (32 · SF · T_slip / (π · σ_allow))^(1/3)
```

A neck printed along Z bends across its layers: take `σ_allow` from about
0.3 × the X-Y strength ([[layer-anisotropy#how-much-weaker-across-the-layers]]).
Worked: `T_slip` = 6 N·mm, `SF` = 3, PLA across layers at 15 MPa →
`d_n` ≥ 2.3 mm. A child's toy also meets the abuse torque test
([[toy-safety-constraints#use-and-abuse-tests-what-breaks-off-means]]).

## Forms

| form | build | holds by | use when |
|---|---|---|---|
| **snap-in split socket** | cup slotted into 2–4 fingers, hung in a cavity with air outside them | finger interference; the lip retains | figures, toy limbs, small mounts; the grip relaxes |
| **two-piece clamped socket** | two half-cups closed round the ball by screws or a threaded collar | retightenable screw preload | lamps, mounts, joints that must hold for years; may wrap far past the equator, being assembled round the ball |
| **screw-tightened (ball head)** | lower cup, upper pad pressed by a knob; a camera head closes a split conical ring on the ball | knob force through a wedge | camera and phone mounts, heavy loads; printed: a thumb screw in a heat-set insert on a pad |
| **print-in-place ball** | socket printed round the ball with `print_in_place_gap` gaps, ball on a flat or cone base | bands proud of the ball, printed in socket grooves, ride onto the wall once moved | sockets closing past half the ball; Calì's 0.2 mm gap fused, 0.3 mm held (SLS, PolyJet); FDM needs a coupon |
| **magnetic ball** | steel bearing ball on a cup or cone seat, magnet behind it | magnet pull (12 mm ball, 18 N in one catalogue part) | breakaway joints that re-seat; skin costs pull ([[latches-detents-and-ratchets#magnetic-catches]]); degreasing raises the clamp; [[toy-safety-constraints#magnets]] |
| **ball stud and cup (ball link)** | ball on a threaded stud, snap cup on a rod ([[rod-ends-and-clevises#ball-links-angle-joints-and-ball-studs]]) | snap cup, or snap ring plus safety clip (DIN 71802) | linkages, RC steering and suspension, strut ends |
| **ball with a cross-pin, or two crossed hinges (Cardan, gimbal)** | pin through the ball riding a socket slot; or two hinges on crossing axes | friction, detent and stops per axis | twist must not drift (a camera horizon, a level tail tip), or each axis needs its own range or click; costs in-axis rotation, and three serial hinges add gimbal lock (Calì et al.); driving through one: [[shaft-couplings#universal-joint-why-one-is-not-enough]] |

**Load a ball link in push, not pull.** The snap is weakest along the stud
axis: one plastic ball socket rates its smallest (M5) size at 7 lbf pulled
against 45 lbf pushed, long-term ratings half of those. DIN 71802 steel
sockets give 30 N pull-off at 8 mm and 100 N at 19 mm. Turn the stud so the
load presses the cup on, or clip it.

## Printing the ball and the socket

- **Socket mouth up**: a bowl, its lip leaning in at `90° − φ_m` from
  vertical, self-supporting while `φ_m ≥ 45°`. Mouth down traps support.
- **Ball base.** Pole down, a ball passes an overhang limit `α_oh` (from
  vertical) below `z = −R · sin α_oh`. Cut a flat there (radius
  `R · cos α_oh`) or end in a 45° cone tangent 45° below the equator; relieve
  the seat under it: that is the ring seat above.
- **The neck: strength or even grip.** Standing up, the neck bends across
  layers. Lying down it is strong, but the ball's flat lands on its side and
  the grip ring loses contact on it in one swing direction. Lie it down with
  the flat toward the socket's notch, or stand it up and size it for Z. A
  bought steel or POM ball on a pressed pin removes the choice.
- **Fingers.** Slots along a vertical socket axis make fingers that bend
  across the layers: keep their strain under the Z limit, or make the spring
  a split C-shaped lip ring lying in the layer plane, which opens in X-Y.
- **Ridges make friction directional.** Twist about the print Z slides along
  the ridges; bending crosses them, holds more and wears faster. Sand the ball
  or run the joint in before measuring: the design value is
  the run-in value ([[post-processing-and-finishing#fits-threads-and-mating-faces]]).
  Put an aligned seam where nothing grips ([[fdm-surface-finish#seams]]).

## Wear, creep and keeping the grip

- **The grip relaxes, the lip does not.** Fingers held deflected lose force
  over weeks, PLA worst ([[creep-and-stress-relaxation#design-rules]]).
  Design a slack joint to stay together and record the hold as an open item.
- **Faces polish.** Posing smooths the ridges and the hold drops. Build a
  way back: a retightenable clamp, a replaceable soft liner (a TPU cup in a
  rigid housing), an elastic preload, or inward socket ribs (one toy patent)
  that keep the contact where it was designed. Pairs and lubricants:
  [[friction-wear-and-lubricants#design-rules-for-sliding-contact]].

## Chains of balls: goosenecks and double balls

A **gooseneck** (segmented hose) is identical elements, each a ball at one
end, a socket at the other and a bore through both. Commercial coolant-hose
balls are about 12.5, 17 and 23 mm, in acetal; friction alone holds the
shape, and the larger sizes need pliers to assemble. The root holds the whole
arm (`n` elements of mass `m_s`, pitch `p`, horizontal, tip load `F_tip`):

```text
M_root = m_s · g · p · n² / 2 + F_tip · n · p
n_max  = sqrt(2 · T_j / (m_s · g · p))           with F_tip = 0
bend radius ≈ p / (2 · sin(θ_e / 2))             θ_e = bend per element
```

Every element holds the same `T_j`, so the root gives first: taper the arm or
stiffen the root, and keep each element's stop before its pry-out angle
([[#leaning-on-the-stop-pulls-the-ball-out]]).

A **double ball (dumbbell)**, a link with a ball at each end between two
sockets, leaves the end body five freedoms (three turns, two translations on
a sphere of the link's length) plus an idle spin of the link. The swings add
only when both ends are true balls, and every added freedom flops unless
friction holds it ([[exact-constraint-and-kinematic-mounts#count-constraints-not-features]]).

## Failure classes

| symptom | cause | rule |
|---|---|---|
| ball will not go in, socket cracks | undercut over the finger strain; fingers walled in | slot, lengthen fingers, air outside them ([[snap-fit-design#ball-snap-a-split-cup]]) |
| ball pops out when posed hard | lip used as the stop | far stop or cone flare; size `W` for the over-pose |
| floppy from new, or seized | interference the size of the print error | deflection ≫ error, softer spring |
| holds a day, then sags | finger stress relaxation | PETG/ABS/ASA; retightenable or replaceable preload |
| looser after an hour of play | ridges worn | design to the run-in torque; ribs; harder pair |
| neck snaps | neck along Z, or grip over neck strength | size `d_n` from slip torque at Z strength |
| gooseneck droops from the root | `n²` root moment | shorter arm, tapered elements |

## Checks

```python
import math
import cadfits
phi_m = math.asin(R_LIP / R_BALL)
theta_max = math.degrees(phi_m - math.asin(R_NECK / R_BALL))
assert R_LIP < R_BALL, "mouth not closed past the equator: nothing retains the ball"
assert theta_max >= SWING_HALF_DEG, f"swing {theta_max:.1f} deg under the {SWING_HALF_DEG} needed"
assert math.isclose(D_SEAT, cadfits.slot_for(2 * R_BALL, SEAT_FIT)), "seat not derived from the ball"
eps = 1.5 * FINGER_T * (R_BALL - R_LIP) / FINGER_L**2
assert eps <= (EPS_Z if FINGERS_BEND_ACROSS_LAYERS else EPS_XY), "finger strain over the limit for its print direction"
assert DELTA >= 3 * PRINT_ERR, "grip interference within print error: floppy or seized"
n_sum = N_FINGERS * E_MOD * FINGER_B * FINGER_T**3 * DELTA / (4 * FINGER_L**3)
assert MU_LOW * R_BALL * n_sum * 2 / math.pi >= SF * T_LOAD, "joint will not hold its load"
t_slip = MU_HIGH * R_BALL * n_sum
assert 32 * SF * t_slip / (math.pi * (2 * R_NECK) ** 3) <= SIGMA_NECK, "neck breaks before the joint slips"
assert M_OVERPOSE / STOP_LEVER * math.sin(math.radians(theta_max)) < W_SEP, "leaning on the stop pops the ball"
```
