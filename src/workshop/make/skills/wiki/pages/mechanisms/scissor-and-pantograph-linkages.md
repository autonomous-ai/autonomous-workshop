---
title: Scissor and pantograph linkages
tags: [scissor, pantograph, linkage, lift, extension, slop, pivot, deployable]
aliases: [scissor mechanism, scissor linkage, scissor joint, X-linkage, X linkage, lazy tongs, lazy-tongs, extending tongs, reacher grabber, extending arm, accordion arm, extending mirror arm, Nuremberg scissors, scissor lift, scissor jack, scissor table, scissor stage, pantograph, drawing pantograph, copying linkage, scaling linkage, Hoberman sphere, Hoberman mechanism, expanding sphere, angulated scissor, angulated element, kinked scissor, generalized angulated element, deployable structure, expanding ring, iris ring]
sources:
  - https://arxiv.org/pdf/1611.10182 (Saxena, after Spackman 1989: F = (L + B/2) dh/dl; screw-jack F = (L + B/2) n / tan θ; vertical actuator F = n (L + B/2); half the lift's weight counts as load)
  - https://www.firgelliauto.com/blogs/mechanisms/lazy-tongs (8 pairs reach about 600 mm from 90 mm, 6.7:1; 6:1 to 8:1 typical against 3:1 to 5:1 for telescoping tubes; N ≤ 10 hand-held; tip wobble about 2 N × radial play; hole spacing matched to ±0.1 mm; thin bars buckle out of plane)
  - https://www.firgelliauto.com/blogs/news/scissor-lift-force-calculation-the-complete-engineering-guide (peak force at the lowest position; do not operate below about 10 to 15 deg)
  - https://en.wikipedia.org/wiki/Pantograph (parallelogram copying linkage; fixed point, tracer and pen collinear; arm positions set the scale)
  - https://patents.google.com/patent/US4942700A/en (Hoberman 1990: angulated strut, three pivots not collinear; the angle between a scissor pair's terminal-pivot lines stays constant; hubs join pairs)
  - https://en.wikipedia.org/wiki/Hoberman_mechanism (two identical angulated rods; the coupler curve is a radial straight line; You and Pellegrino's generalized angulated element)
  - Beer and Johnston, Vector Mechanics for Engineers, Statics, ch. 10 (method of virtual work)
  - skills/cad/scripts/cadfits.py
related: [linkages, straight-line-and-toggle-linkages, joints, hinges-and-pin-joints, print-in-place-mechanisms, tolerance-stack-up, arm-and-gripper-sizing, layer-anisotropy, toy-safety-constraints, beam-and-plate-stiffness, rolling-contact-joints, push-pins-and-clip-fasteners, telescoping-tubes-and-locks, lead-screws]
updated: 2026-10-01
---

# Scissor and pantograph linkages

A scissor linkage is a chain of X-shaped cells: two bars pinned at their
middles, joined end to end to the next cell. Squeeze one end across and the
chain extends along its axis. That gives the lazy tongs, the scissor lift
and jack, extending mirror arms, and (with kinked bars) the Hoberman ring
and sphere. A pantograph is one or two parallelograms that copy a motion at
a fixed scale. Both are pure pin-jointed linkages. Their costs are force
that climbs steeply near the closed state, and slop that adds up over many
pins. Four-bar basics are in [[linkages]].

## Scissor chain geometry and extension ratio

```text
a     half-bar: centre pivot to end pivot (bar pivot-to-pivot length 2a = D)
N     cells (X units) in the chain
θ     bar angle from the transverse (input) direction: the base of a lift, the handle squeeze of tongs
w     bar width at the pivots (boss diameter)

extension     L = N · 2a · sin θ            (a lift's height h = n D sin θ)
cell span     s = 2a · cos θ                (transverse width the input moves)
closed        L_min ≈ N · w                 (bars side by side, θ → 0)
ratio         E = L_max / L_min ≈ 2a · sin θ_max / w
```

The closed length is set by the bar width, not by the kinematics. A longer,
thinner bar extends further, but it is floppier and buckles out of plane
([[beam-and-plate-stiffness#buckling-slender-columns-and-thin-walls]]). One
8-pair stationer's tongs goes from 90 to about 600 mm (6.7 : 1). Lazy tongs
typically reach 6–8 : 1, against 3–5 : 1 for telescoping tubes
([[telescoping-tubes-and-locks]]). Hand-held tongs stay at N ≤ 10; beyond
that the bars must be 1.5–2 × thicker.

- **Pivot exactly at mid-length** for a straight chain. An off-centre pivot
  (the "polar" scissor unit) makes the cell's end lines converge, and the
  chain curves into an arc. A set of bars whose hole spacings differ by more
  than about ±0.1 mm curves visibly, so derive every hole from one `A_HALF`
  parameter.
- Every end node of cell j sits at `j · 2a · sin θ`, so node j moves j/N as
  far as the tip. A lazy tongs is an N-stage pantograph.

## Velocity ratio and force: virtual work

Moving the input across by ds moves the output along by
`dL = −(N / tan θ) · ds`. Virtual work (`F_in · ds = W · dL`, frictionless)
gives the force:

```text
input force for an output load W     F_in  = W · N / tan θ
output force for an input force      F_out = F_in · tan θ / N        (tongs tip force from the squeeze)
```

**Near the closed state (θ small) everything on the input side is
amplified.** The output moves N / tan θ times faster than the input, so the
input force, the actuator and the pins next to it all carry W·N / tan θ,
many times the load. A lazy tongs held nearly closed has no grip. A scissor
lift starting from flat needs an unbounded force. Give every scissor a
**minimum working angle**: a hard stop at about 10–15° keeps 1/tan θ below
about 6. The same geometry makes the scissor jack hardest to turn at the
bottom of its travel. The toggle that uses this amplification on purpose is
in [[straight-line-and-toggle-linkages#toggle-mechanisms]].

## Scissor lift: where the actuator goes

For any actuator whose length is l, the virtual work on the whole lift is

```text
F = (W + W_s / 2) · dh / dl          W_s = the scissor's own weight: half of it counts as load
```

| actuator | force | trade-off |
|---|---|---|
| **horizontal at the base**, moving the sliding foot (screw jack) | `(W + W_s/2) · n / tan θ` | the common layout, short stroke; force peaks at the bottom |
| **vertical across one stage**, between that stage's two pins | `n · (W + W_s/2)`, constant | stroke equals one stage height, and it cannot fit when the lift is closed |
| **inclined**, base to a point part-way along an arm | between the two; closed form for any attachment in the source | farther from the arm's pivot and nearer perpendicular to the arm lowers force and lengthens stroke |

- Size the actuator, its mounts and the bottom stage's pins at θ_min, never
  at mid-travel.
- Stacking stages multiplies the actuator force by n for a base actuator.
  The lowest stage carries everything above it.
- Drive a printed toy lift with a lead screw across the base
  ([[lead-screws]]). A screw that does not back-drive holds the load
  wherever it stops, and the high force near the bottom becomes axial load
  on the screw instead of torque on a servo.

## Pantograph: the ratio from the pivot positions

Take a fixed pivot O, a bar O–B–A with joint B on it, a bar A–C–P with
joint C on it, and links B–T and C–T closing the parallelogram A-B-T-C.
Triangles O-B-T and O-A-P are similar, so

```text
k = OP / OT = OA / OB = AP / AC          the pen P moves k × the tracer T
collinearity: O, T and P lie on one line in every pose iff OA / OB = AP / AC
```

- Swap tracer and pen to reduce by 1/k instead of enlarging.
- Moving joints B and C along their bars (a row of holes, both from one
  index) changes k. A mismatched pair of holes breaks the collinearity, and
  the copy distorts instead of scaling.
- Errors scale too: slop and flex at the tracer appear k × larger at the pen.

## Angulated (Hoberman) elements: radial expansion

Bend each bar at its centre pivot, so its three pivots are no longer in line
(a strut angle β between the two halves). For a pair of identical angulated
struts, the angle between the line through one pair of terminal pivots and
the line through the other stays fixed however the pair scissors: it is
`180° − β`. Those lines can then be radii of a ring. With n pairs:

```text
β   = 180° − 360° / n                       strut angle at the centre pivot (n = 12 → 150°)
r_C = r · cos(Δ / 2) / sin(π / n)           ring radius of the centre pivots
      r = half-strut (centre to terminal pivot), Δ = angle between the two struts' bisectors
```

Every terminal pivot slides along its own radial line, so the ring keeps its
shape while it grows or shrinks. In theory the centre-pivot radius spans a
ratio of 1 / sin(π/n). In practice bar widths and hubs collide well before
that. A Hoberman sphere is several such rings on great circles, joined at
hubs that let neighbouring pairs lie in different planes. Every strut
crossing and every hub is a pivot, so slop and friction add up quickly
(next section).

## Slop accumulates with the pin count

Each pin joint lets its bars shift by its clearance. A scissor puts many
joints in series along the load path: about 2 per cell from base to tip.

```text
c        per-side clearance of one pivot = cadfits.mating_clearance(RUN)
k        pins in series along the path (≈ 2 N for lazy tongs)
worst case   Δ ≈ k · c        (one estimate for tongs: tip wobble ≈ 2 N × radial play)
random       Δ ≈ √k · c       ([[tolerance-stack-up#worst-case-and-rss]])
```

Illustrative: 8 cells with slip pins (0.20 per side) gives a worst-case tip
play of about 3.2 mm. With the print-in-place gap
(`print_in_place_gap()["xy"]`, 0.30) it is about 4.8 mm. Play also passes
through the motion lever: a transverse slop in any cell appears along the
axis multiplied by 1/tan θ, so a nearly closed chain is the loosest. Lateral
compliance also grows with N, because every pin adds an out-of-plane
freedom.

- Fewer, longer cells beat many short ones at the same reach.
- Pins in the `snug` class, or bought steel dowels, for every pivot that
  sets accuracy ([[dowel-pins-and-press-fits]]).
- Preload the chain to one side of its clearances (a spring, or gravity on
  a lift) so it does not cross its backlash in use
  ([[arm-and-gripper-sizing#backlash-and-sag-at-the-end-effector]]).
- Double the bars on each side (a sandwich, the pin in double shear) for
  lifts and long tongs ([[hinges-and-pin-joints#pin-and-knuckle-sizing]]).

## Printing scissor links

- **Bars flat on the bed, pin axes vertical.** Layers then run along the bar,
  which carries tension, compression and bending in its plane
  ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]). Pin holes
  come out round ([[print-in-place-mechanisms#pin-orientation]]).
- **Two planes minimum.** Every pivot joins a bar from each plane; the bars
  of one plane never cross each other. Plane pitch = bar thickness + axial
  gap. Pin length = the stack + head. A lift has inner and outer arm pairs;
  keep the inner pair between the outer ones so every pin is in double shear.
- **Assembled pins.** Shoulder pins integral to one bar and snap-headed, or
  push pins and clips ([[push-pins-and-clip-fasteners]]), or screws with
  shoulder spacers. Bore every moving bar with `cadfits.slot_for(PIN_D, RUN)`
  and seat a pin fixed in one bar with `slot_for(PIN_D, "snug")`; never type
  both halves. Retention is its own condition
  ([[hinges-and-pin-joints#pin-retention]]).
- **Print-in-place stack.** Two stacked planes leave the upper bars floating
  wherever no lower bar is underneath. Half-lap every pivot instead. Each bar
  is full thickness between pivots, and at every pivot one bar takes the
  lower half and the other the upper half, so all bars stand on the bed. The
  upper lap is then one short bridge, one boss diameter long, over a `z`
  gap. Pins rise from the lower lap through the upper lap with the `xy` gap
  and end in a 45° cone head
  ([[print-in-place-mechanisms#the-gap-is-per-face-and-per-direction]]).
  Print the chain at mid-travel, where the bars cross near 90° and each
  overlap is only one boss wide. Nearly closed, the overlap lengthens as
  `w / sin 2θ` and the laps no longer cover it.
- **Hard stops** at θ_min and θ_max, on the bars, not on the pins.
- **Fingers.** A scissor is a shear. Keep at least 12 mm of clearance between
  bars that close on each other in a child's toy, or guard them
  ([[toy-safety-constraints#finger-entrapment-and-springs-en-71-1]]).

## Failure classes

| symptom | cause | rule |
|---|---|---|
| lift will not start, actuator stalls at the bottom | force ∝ 1/tan θ | hard stop at θ_min ≥ 10–15°; size at θ_min |
| pins or bosses near the input crack | the same amplification | double shear, larger pins at the base stage |
| tip wobbles, chain sags | k pins × clearance, amplified near closed | fewer cells, snug or steel pins, preload |
| chain curves instead of running straight | pivot off mid-length or unequal hole spacing | one parameter for every hole; check on a flat table |
| bars bow sideways under load | thin bars buckle out of plane | thicker or doubled bars; wider plane spacing |
| pantograph copy distorts | O, T, P not collinear | assert `OA/OB == AP/AC` |
| angulated ring binds | kink angle not `180° − 360°/n`, or bars collide | derive β from n; check bar clearance at both ends of travel |
| print-in-place chain fused | upper plane printed over air, or flat gap ceilings | half-lap pivots, `z` gap, cone heads |

## Checks

```python
import math
import cadfits
c = cadfits.mating_clearance(RUN)
assert THETA_MIN_DEG >= 10, "a scissor near flat needs an unbounded input force"
f_act = (W_LOAD + W_SCISSOR / 2) * N_STAGES / math.tan(math.radians(THETA_MIN_DEG))
assert f_act <= F_ACTUATOR_MAX, f"actuator needs {f_act:.0f} N at the lowest position"
L_max = N * 2 * A_HALF * math.sin(math.radians(THETA_MAX_DEG))
assert L_max >= REACH_REQUIRED and N * BAR_W <= CLOSED_LEN_MAX, "reach or closed length missed"
assert 2 * N * c <= TIP_PLAY_MAX, f"worst-case tip play {2 * N * c:.1f} mm"
assert abs(OA / OB - AP / AC) < 1e-6, "pantograph points not collinear: the copy distorts"
assert abs(STRUT_ANGLE_DEG - (180 - 360 / N_RING)) < 1e-6, "angulated ring will not expand radially"
assert GAP_BETWEEN_CLOSING_BARS >= 12 or not CHILD_TOY, "scissor action is a finger shear"
```
