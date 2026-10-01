---
title: Cable, cord and tendon drives
tags: [cable, cord, tendon, capstan, bowden, sheave, pulley, rope, friction, wrap-angle]
aliases: [string drive, rope drive, capstan drive, cable drive, tendon drive, bowden cable, pull cord, pull string, fishing line, dyneema, spectra, uhmwpe, braided line, monofilament, wire rope, sheave, puppet string, marionette, round belt, string loop, crimp sleeve, ferrule, euler eytelwein, antagonistic tendon]
sources:
  - https://en.wikipedia.org/wiki/Capstan_equation (T_load = T_hold e^(μφ); assumes an inextensible, flexurally limp line; modified for stiff cables such as Bowden cables)
  - https://en.wikipedia.org/wiki/Bowden_cable (housing constructions, barrel adjuster, solid inner wire for push, wire-rope D/d 42 minimum and 72 for long life, bicycle cables far below that, folding-bike housing bends to about 4 cm radius)
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC9611146/ (Bowden friction T_out = T_in e^(−μ sgn(v) φ_L) + T_0 with φ_L the total bend of the sheath; μ = 0.5 used for a 2 mm cord in a 3 mm-bore sheath)
  - https://industrialrope.com/wire-rope/sheave-and-drum-ratios/ (suggested / minimum D/d per wire-rope construction; smaller values cost rope life)
  - https://www.samsonrope.com/warning-statement (synthetic rope — a surface deflecting it more than 10° at least 3 × rope diameter; sheave groove at least 10 % over the rope diameter; working load = breaking strength / 5 minimum)
  - https://www.marlowropes.com/news/rope-strength-and-how-retain-it/ (knotted polyester and nylon keep about 50 %, HMPE 40 %, aramid as little as 30 %; a good splice keeps about 90 %)
  - https://christinedemerchant.com/rope_material_hmpe.html (HMPE melts 144–152 °C, work below about 80 °C, creeps under continuous load, slippery so knots slip)
  - https://lifting.com/blp-blog/wire-rope-terminations-efficiency-ratings-how-to-choose/ (swaged sleeve or socket 100 %, Flemish or turnback eye with sleeve 90 % or better, wire rope clips and wedge sockets 80 %)
  - https://www.aaedmusa.com/projects/capstandrive (printed PLA capstan with helical grooves; steel wire failed in hours on a small drum; synthetic lines stretched; Dyneema DM20 chosen after endurance testing; ratio off nominal because of the helix)
  - https://www.firgelliauto.com/blogs/mechanisms/capstan-gear (vendor article: pretension 10–20 % of working load, fleet angle under about 1.5°, 2–3 wraps nominal; treat as rule of thumb)
  - "https://www.emergentmind.com/topics/tendon-driven-anthropomorphic-manipulators (n + 1 and 2n tendon arrangements for n joints; via search excerpt)"
  - "https://usangler.com/best-fishing-line/ (nylon monofilament 25–35 % elongation to break, absorbs water and loses strength wet; braid does not; via search excerpt)"
  - Shigley's Mechanical Engineering Design, ch. 17 (flexible elements; flat and V-belt friction, effective μ of a V groove)
related: [belts-and-pulleys, springs, automaton-craft-practice, friction-wear-and-lubricants, creep-and-stress-relaxation, linkages, energy-drive, overhangs-and-print-orientation, fdm-hole-accuracy, toy-safety-constraints, mechanism-verification, rolling-contact-joints]
updated: 2026-10-01
---

# Cable, cord and tendon drives

A cord pulls, never pushes, and carries force round corners into fingers,
puppet limbs and automaton figures where gears would not fit. Every corner
costs force (capstan relation), every cord creeps, every end needs an anchor
stronger than a knot. Read this before routing a string or sizing a pulley,
drum or channel for one; timing belts are [[belts-and-pulleys]].

## Capstan relation: friction multiplies with wrap angle

A cord sliding (or about to slide) over a curved surface with friction μ and
total wrap angle θ (radians) has

```text
T_tight = T_slack · e^(μ θ)          Euler–Eytelwein
```

It is independent of the drum radius. It assumes a limp, inextensible line; a
stiff cable (steel wire, Bowden inner) loses more. Two consequences pull in
opposite directions:

- **Holding**: a few turns on a post multiply a small holding force enormously.
  At μ = 0.3, half a turn gives 2.6 : 1 and three turns 285 : 1. This is why a
  cord wound 2–3 turns round a drum drives it without slipping, and why a cord
  can be anchored by wraps before the knot.
- **Transmitting**: every bend a cord slides round divides the output by the
  same factor. The tension at the far end of a routed tendon is

```text
T_out = T_in · e^(−μ · Σθ)        Σθ = sum of every bend along the path, in radians
```

Sum the bends *in all planes*: a channel that turns 30° in plan and 30° in
elevation contributes both. Friction also reverses with direction, so the same
tendon needs `T_in · e^(+μΣθ)` to be let out against a load: a routed cord has
hysteresis equal to that ratio squared.

| cord on | μ (order of magnitude) | note |
|---|---|---|
| PTFE (liner or tube) | 0.12–0.22 | PTFE on steel, [[snap-fit-design#mating-and-separating-force]] |
| steel or polished metal, synthetic cord | 0.2–0.35 | vendor rule of thumb (Firgelli), not measured; varies with age and dirt |
| Bowden sheath, as modelled | 0.5 | value fitted in one exoskeleton study |
| printed plastic channel | unknown — assume 0.3–0.5 | layer lines raise it; measure on a coupon |

With μ = 0.4, a tendon through three finger joints each bent 90° (Σθ = 4.7 rad)
delivers e^(−1.9) ≈ 15 % of its input. Three rules follow: keep total wrap
small, put a rotating pulley (with its own bearing, [[shafts-and-bearings]])
at every large bend, and line tight bends with PTFE tube.

## Sheave, drum and channel diameter

A cord bent round a diameter D much smaller than 20–40 times its own diameter
d loses strength at once and fatigue life with every cycle.

| cord | D/d | source |
|---|---|---|
| wire rope 6×19 | suggested 51, minimum 34 | Industrial Wire Rope table |
| wire rope 6×37 | suggested 39, minimum 26 | same |
| wire rope 6×7 (stiff) | suggested 72, minimum 42 | same; also Wikipedia's "absolute minimum" |
| 7×19 aircraft cable | about 20 minimum (vendor calculator, via search excerpt) | the flexible construction for pulleys |
| synthetic rope over a sheave, cyclic | 8 or more; 20–30 for long cyclic life | Samson; HMPE patent literature (via search excerpt) |
| synthetic rope over a fixed surface bent > 10° | 3 or more | Samson |

- **Steel wire** (0.3–1 mm stranded) needs D ≥ 20 d on anything that cycles.
  A 0.5 mm cable needs a 10 mm pulley; a 1 mm cable needs 20 mm or more. A
  printed capstan with steel wire on too small a drum failed in hours.
- **Braided HMPE (Dyneema/Spectra) and polyester** tolerate much tighter
  bends: D ≥ 8 d on a pulley, and a fixed channel turn with bend radius at
  least 1.5 d (D ≥ 3 d). For long life, go larger.
- **Groove width** at least 1.1 d; a groove narrower than the cord pinches it.
  A V groove wedges the cord and raises effective friction to
  `μ' = μ / sin(β/2)` for groove angle β (Shigley ch. 17) — good for a driven
  pulley, bad for an idler.

## Printed channels and guides

- Route a tendon through a channel with a smooth centreline (arcs, not sharp
  corners): the channel wall is a fixed surface, so apply the ≥ 3 d rule to
  the channel's bend diameter and add the friction to Σθ.
- Channel bore = cord diameter + clearance, or room for a PTFE liner tube
  where the bend is sharp. Model the PTFE tube as a purchased part seated in
  a printed bore ([[fdm-hole-accuracy]]), sized from the tube actually bought.
- Horizontal channels print as teardrops ([[overhangs-and-print-orientation]]);
  the teardrop tip is where the cord rides if it pulls upward, so orient the
  pull against the round side.
- Layer steps abrade the cord. Put the exit of every channel on a flared,
  filleted lip (radius ≥ 1.5 d), never a sharp edge; that edge is where
  cords cut through.

## Capstan drives

A capstan drive is a cord wrapped 2–3 or more turns round a small drum and
anchored at both ends of a large sector or drum, giving a reduction
`i = D_out / D_in` (to the cord centreline) with no geometric backlash.

- Wraps: enough that `e^(μθ)` exceeds the ratio of working tension to
  pretension with margin; 2–3 turns is the usual figure, more if μ is low.
- The cord walks along the drum as it turns (one cord pitch per turn), so give
  the drum a helical groove and axial length for the wraps plus the travel.
  The effective diameter follows the cord centreline, so the realised ratio
  differs from the nominal one — compute it from the centreline, not the drum.
- Pretension: roughly 10–20 % of working load (vendor figure). Too little and
  backlash reappears at reversal; too much and the cord creeps.
- Fleet angle (cord entering the drum off the groove plane) under about
  1.5°, or the cord climbs onto itself.
- Anchor both ends on the big drum with a tensioner (screw, lever or spring)
  so creep can be taken up without re-threading.
- Stiffness is the cord, not the drum: low-creep HMPE (DM20 grade) was
  preferred over steel and ordinary synthetics in one printed build.

## Tendon-driven joints and fingers

For a tendon at moment arm r about a revolute joint:

```text
joint torque   τ = T · r
excursion      Δs = r · Δθ          (Δθ in radians, r constant for a pulley joint)
```

- A tendon only pulls, so each joint needs something to pull it back: a
  return spring or elastic cord (one tendon per joint), an antagonistic
  second tendon (2n tendons for n joints), or a shared-tendon layout (n + 1
  tendons for n joints).
- An antagonistic pair stays taut only if both excursions are equal and
  opposite, which holds when both tendons wrap the same joint pulley radius.
  A tendon that passes a joint off-centre changes path length with angle; take
  up the difference with a spring in series.
- Size the return spring against the whole loop: the actuator must supply
  `(F_spring + load) · e^(μΣθ)`, and the spring alone must beat the
  friction of the return path, or the finger stays curled.
- Coupled (underactuated) fingers: one tendon through several joints closes
  them in an order set by the joint stiffness ratios. Treat the springs as
  design parameters, not decoration ([[springs]]).
- Keep tendons away from the joint axis on the side they pull, and route them
  through each hinge at a fixed radius (a printed half-pulley) so the moment
  arm does not collapse as the joint bends.

## Bowden cables

An inner cable slides in a housing that is incompressible along its length.
The housing reacts the pull, so the two ends may move relative to each other.

- Housing types: coiled (flexes, shortens under load — spongy), compressionless
  (longitudinal strands, stiff, for positioning), and liners (PTFE) inside
  either. A solid inner wire can push over a short stroke; stranded wire only
  pulls.
- Friction follows the capstan relation over the **total** bend of the
  housing (sum of every curve in the run), plus a constant term at zero bend.
  Route with the fewest and gentlest bends.
- Adjust with a barrel adjuster at one housing stop: screwing it out
  lengthens the housing and tightens the cable. Model the stop as a seat for a
  purchased ferrule and adjuster, with an M-thread or slot sized from the part.
- Housing stops need a ferrule seat, not a bare hole, and a slot for the inner
  cable so it can be fitted without threading the nipple through. Bend the
  housing no tighter than its maker allows (bicycle housing: about 40 mm
  radius), and leave a straight lead-in to any multi-bend printed channel
  so it can be threaded.

## String loops in automata and pull toys

- A crossed (figure-eight) loop reverses rotation; an open loop keeps it.
  Either slips by design, which suits a toy and spoils timing
  ([[automaton-craft-practice#drives-gears-and-pulleys]]).
- The slip limit is the capstan relation over the wrap on the smaller pulley.
  An elastic cord or O-ring supplies its own tension; a plain string needs a
  sprung idler or it slackens as it creeps. Groove every rim; a flat rim
  throws the loop.
- Pull-string toys: the cord runs through a guide at the housing wall with a
  flared exit, and a stop (bead or knot pocket) stops it retracting into the
  body. Cord length and loops on toys for young children are regulated
  ([[toy-safety-constraints]]).

## Cord materials

| cord | stretch | creep | notes |
|---|---|---|---|
| braided HMPE (Dyneema, Spectra) fishing line | very low | yes, under continuous load; low-creep grades exist | very slippery: knots slip and keep about 40 % strength; melts 144–152 °C, use below about 80 °C |
| braided polyester | low | low | holds knots better than HMPE; about 50 % knotted |
| nylon monofilament | high: 25–35 % to break, several % at working load | yes, and more when wet | absorbs water and weakens wet; springy, holds a set when coiled |
| fluorocarbon monofilament | slightly below nylon | keeps elongation (permanent set) | does not absorb water |
| stranded stainless wire (7×7, 7×19) | lowest | negligible | needs large pulleys (above); ends need crimps |

HMPE for tendons and capstans, steel for a Bowden inner that pushes, nylon
only where spring is wanted; every synthetic cord creeps, so give it a
tensioner ([[creep-and-stress-relaxation]]).

## Anchoring a cord in a print

Termination efficiency (share of the cord's breaking strength the end keeps):

| termination | efficiency |
|---|---|
| swaged sleeve or socket (wire) | about 100 % |
| eye with swaged sleeve (wire) | 90 % or more |
| wire rope clip or wedge | about 80 % |
| splice (synthetic) | about 90 % |
| knot (polyester, nylon) | about 50 % |
| knot (HMPE) | about 40 %, and may slip |

Printed anchors, from weakest to strongest:

- **Knot pocket**: a counterbore behind a small hole; the knot sits in the
  pocket and cannot pull through. Size the hole from the cord plus clearance
  and the pocket from a tied test knot, not from the cord diameter. Use a stopper knot, and for HMPE add wraps round a post before it
  (the capstan relation then unloads the knot) or melt/glue the tail.
- **Wrap post**: 2–3 turns round a printed or steel post, then a knot; the
  knot sees `T / e^(μθ)`.
- **Crimp sleeve or stop** on wire: a purchased ferrule sits against a
  shoulder; the part carries a seat and a side slot for the cable.
- **Clamp screw**: cord pinched under a washer or in a set-screw bore;
  adjustable, and the natural place for a tensioner. The screw must bear on a
  washer or pad, never directly on the cord.
- Rated strength × termination efficiency ≥ 5 × working tension (rope
  makers' minimum working factor).

## Checks

```python
import math
eta = math.exp(-mu * sum(bend_angles_rad))          # every bend, all planes
assert T_in * eta >= T_required, f"tendon delivers {T_in*eta:.1f} N < {T_required:.1f} N"
assert D_pulley / d_cord >= D_OVER_D_MIN, "pulley too small for this cord"   # 20 wire, 8 synthetic
assert all(2 * r / d_cord >= 3 for r in channel_bend_radii), "channel bend tighter than 3 d"
assert math.exp(mu * wrap_rad) > T_work / T_pretension, "capstan will slip"
assert F_return_spring > T_return_friction, "return spring cannot overcome path friction"
assert anchor_strength * termination_eff >= safety * T_work
```
