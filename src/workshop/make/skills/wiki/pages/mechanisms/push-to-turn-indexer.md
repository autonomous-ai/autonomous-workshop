---
title: Push-to-turn indexer (the click-pen cam)
tags: [indexer, cam, crown, ratchet, detent, push-button, rotary-index, helicoid]
aliases: [click pen mechanism, retractable pen cam, ballpoint click, rotating cam, push to rotate, push button rotary index, push button indexer, pen rotator, crown cam, sawtooth crown, index drum button, mood egg mechanism, turn one step per press]
sources:
  - https://patents.google.com/patent/US3288115A/en (plunger with 8 teeth, rotating ratchet with 4 guides and 8 auxiliary teeth, barrel with 8 slots; the ratchet turns partly when pushed and partly on the plunger's return)
  - https://penvibe.com/how-pens-work/ (a click turns the cam 45 deg on the push and 45 deg on the release)
  - "experience: a five-position crown set proved by a quasi-static walk, then by a coupled check_motion cycle built from the same walk"
  - "experience: sawtooth crown tips read as walls to the thickness gate until given lands"
related: [cams-intermittent, latches-detents-and-ratchets, springs, mechanism-verification, mechanism-design, gears, wall-thickness-and-hollowing]
updated: 2026-09-29
---

# Push-to-turn indexer (the click-pen cam)

A button pushed straight down turns an output one fixed step and leaves it
there: a retractable pen's rotating cam. Three crowns on one axis do it, with
one spring and no flexing part:

| crown | on | faces | moves |
|---|---|---|---|
| **P** (plunger) | the button's rod end | down | down and up, keyed against turning |
| **R** (rotor) | a ring keyed to the output, spring pushed up | up | down, up, and one way round |
| **F** (fixed) | the housing | down | never |

Push: P pushes R down until R's teeth clear F's teeth, then P's ramps turn R
part of a step. Release: the spring lifts R into F, whose ramps turn it the rest
of the step into the next seat. The seat is the detent: forward is blocked by
F's walls, backward only by pushing the spring down. The output turns one way
only. Choose it over a rack-and-pinion with a one-way clutch (five parts, and
the pinion's axis cannot be the button's) or a flexing pawl on a ratchet wheel
(a printed pawl creeps and fatigues).

## Crowns are helicoids, specified in degrees

Every working face is a ramp whose height grows linearly with angle, the same
at every radius, so a profile is fixed by spans in degrees and a rise `s` in mm
per degree; two crowns of the same rise stay in full contact across their
ring. The ramp's steepness is not constant across the ring:

```text
tan α(r) = s / (r · π/180)          steepest at the ring's inner edge
```

Set `s` from the angle wanted at the ring's **outer** edge, where it is
shallowest, and keep that angle at least 20 deg above the friction angle
(`atan μ`, 17 deg for PLA on PLA): both turns are driven by the spring, whose
torque on the rotor is `F · tan(α − φ) · r`.

P sits on the axis inside F, so R carries two rings: R_in under P, R_out under
F. Leave a gap between the bands wider than the plunger rod's radial play, or
P's teeth reach R_out's.

## The tooth forms that give a direction

Symmetric V teeth on all three crowns only rock the rotor back and forth. The
direction comes from walls:

- **F and R_out:** a flat, then a ramp over `W2` rising `W2 · s2`, then a wall.
  At rest they mesh; R_out's tips stand against F's walls.
- **R_in:** a drive ramp over `W1` rising `H1 = W1 · s1`, then a back slope
  down over the rest of the pitch.
- **P:** R_in's profile moved `a1` along its own drive slope (`θ + a1`,
  `z + a1 · s1`). R_in's steepest upward slope is its drive slope, so the moved
  copy lies on or above R_in everywhere and rests on its drive faces.

`a1` is the turn made on the push; the release makes `pitch − a1`. Two limits
hold it, each needing a few degrees of margin:

```python
assert pitch - W2 + land < a1 < W1   # push ends with R_out's tips over F's ramps,
                                      # with P's tips still on R_in's drive ramps
```

Past either limit a tip lands on a flat and the mechanism stalls: a flat
pressed on a flat has no tangential force.

## Stroke

R must drop the height of F's wall to clear it, and while it turns under F's
flat it rises along P's drive ramp, so the push has made its whole turn at

```text
D_turn = wall + (pitch - W2 + land) · s1
stroke to the hard stop >= D_turn + 0.8 .. 1.2 mm
```

For a fixed ramp angle, `s` scales with radius, so the stroke is roughly
`r · pitch · tan α`: a coarse index (five positions, 72 deg) needs small rings
(F out to about 6 mm) to keep the stroke near 5-6 mm. Put the flat on F rather
than widening every ramp: only F's upper ramp is ever contacted, and each
degree of flat costs `s1`, not `s2`.

## The back slope lifts the plunger

On the release R keeps turning under P, so P's tips climb R_in's back slope and
cross its peaks. Only P's weight resists, but the lift force is
`W / (cos β − μ sin β)`, which self-locks near 73 deg for μ 0.3. Keep the back
slope under about 65 deg at P's inner radius, and never rest a finger on the
button's return.

## Lands on the tips

A sawtooth tip is a knife edge, and a knife edge between two flat faces is
always a wall to a thickness gate. Cut R_out's tips (and F's notch tops, the
same shape) level over the last few degrees of the ramp. The land narrows
the first limit above (`a1 − land > pitch − W2`) and lowers the wall, so the
stroke drops by the land's height. Lands on R_in's peaks eat the margin P's
tips land in; leave those sharp, where the ring's small radius makes them read
as tapers.

## The spring and the output's pivot

The spring pushes R up and the output down. Hang the output on a point (an
axle ending in a sharper cone than the bore's roof) so the spring's thrust has
no friction radius, and centre the spring at both ends (a spigot on the floor,
a counterbore in the rotor). Keep the spring index 4-12 and its length at the
stop above solid ([[springs#helical-compression-spring]]).

## Proving it: walk one click

No rigid-body gate can tell whether the teeth stall. Walk the crowns in their
own coordinates, where every ramp is a straight line:

```python
def allowed_by_f(phi):                   # highest rotor datum F allows at rotor angle phi
    return min(F(t) - R_out(t - phi) for t in thetas)
def allowed_by_p(phi, zp):               # ... with the plunger at zp
    return min(P(t) + zp - R_in(t - phi) for t in thetas)
# push: zp from 0 to -stroke; the rotor sits at min(both) and turns whichever way raises it
# release: the plunger floats; the rotor climbs F; the plunger rides at max(R_in - P)
assert abs(end_turn - pitch) < 0.2 and end_z == rest_z and plunger_back == 0
assert allowed_by_f(+0.5) < rest_z and allowed_by_f(-0.5) < rest_z    # the seat is a detent
```

Sample the walk into a coupled `check_motion` cycle (plunger translation;
rotor rotation and translation, driven; output rotation, driven), insert
straight-line states wherever one step moves a part further than the sweep's
declared step (the finger coming off lifts the rotor at once), and leave the
spring out of the obstacles: it is compliant. Add blocked conditions both ways
at rest, the plunger's key, and the rotor's key to the output
([[mechanism-verification]]).

## Showing one face of a drum through a window

A drum of `n` panels behind a window shows its neighbours at the window's
edges: parallel sight lines at half-width `w` see a neighbour from its corner
inward by `(w − c) / sin(90° − 360°/n)` along the panel, where `c` is the
panel's half chord. Marks near a panel's edge then show on both sides. Narrow
the aperture at the drum's depth rather than the window: cheeks inside the
shell, between the drum's swept circle plus clearance and the wall, splayed
toward the window's edge. Where the egg or dome closes in on the drum and the
cheeks run out, roll the drum's corners back first, so the cheeks can follow
up past the highest mark.
