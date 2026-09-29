---
title: Latches, detents and ratchets
tags: [latch, detent, ratchet, pawl, catch, indexing, push-push, draw-latch, bistable, retention]
aliases: [ball detent, spring plunger, ball plunger, index plunger, click stop, detent torque, ratchet wheel, pawl pivot, push latch, touch latch, heart cam, heart-shaped cam, draw latch, cam latch, over-centre catch, magnetic catch, two-position switch]
sources:
  - https://www.swmanufacturing.com/resources/design-guidelines-for-ball-plungers/ (side force FS = FE / tan(θ/2); 90° countersink seat; use the mid-range end force)
  - https://www.firgelliauto.com/blogs/mechanisms/detent (F_release = F_spring · tan(α/2 + φ); notch depth 25–30 % of ball diameter; 5–15 N at the ball for hand controls)
  - https://www.firgelliauto.com/blogs/mechanisms/pawl (contact normal 2–3° on the engaging side of the pivot; back flank 80–90° from the tangent; pivot force formula; seat in 1/3 of a tooth period)
  - https://patents.google.com/patent/US20100288593A1/en (rake angle; engagement held by contact geometry rather than by spring and friction)
  - https://patents.google.com/patent/US4916276A/en (heart-shaped cam push-push lock: pin rocks on a holder, spring-biased into the groove)
  - https://www.kjmagnetics.com/blog/testing-magnet-strength (any gap or coating cuts pull force; steel plate should be about twice the magnet's diameter wide)
related: [joints, snap-fit-design, cams-intermittent, clutches-and-freewheels, springs, flexures-and-living-hinges, straight-line-and-toggle-linkages, magnets-and-strap-slots, mechanism-verification, creep-and-stress-relaxation, hinges-and-pin-joints]
updated: 2026-09-23
---

# Latches, detents and ratchets

Everything here holds a part in a chosen position until a deliberate force
moves it: a detent holds by a spring and a ramp, a ratchet holds one way by
geometry, a latch holds until released. Choose which kind of hold is wanted,
then size the force. The snap-hook calculation is on [[snap-fit-design]];
the one-line catalogue rows are in [[joints#latching-and-holding]].

## Which hold

| need | device | holds by | releases by |
|---|---|---|---|
| click-stops at positions, either direction | **detent** (ball, plunger, flexing finger) | spring force on a ramp | any force above the release force |
| one direction free, the other locked | **ratchet and pawl** | contact geometry | lifting the pawl |
| closed until a button or lever is worked | **latch** (snap hook, cam/draw latch, push-push) | geometry or over-centre | a separate release motion |
| closed with no wear part, pulls itself shut | **magnetic catch** | magnet pull | pull above the magnet force |
| two stable states from one flexing part | **bistable flexure** | stored strain energy | pushing over the energy peak |

## Detent holding force

A spring presses a ball (or rounded plunger, or bump on a flexing finger)
into a notch with seating force `F_s`. The side force to push it out:

```text
θ   = included angle of the notch or countersink
β   = 90° − θ/2   flank angle measured from the direction of travel
φ   = atan(μ)     friction angle
frictionless      F_side = F_s / tan(θ/2)  = F_s · tan β      (plunger makers' form)
with friction     F_side = F_s · tan(β + φ)
rotary detent     T = F_side · r_detent
```

A shallower notch (larger θ) releases more easily; a steeper one holds harder.
At the common 90° notch both forms give `F_s · tan(45° + φ)`: with μ = 0.15
that is 1.35 × the seating force. One published guide writes the friction
form with θ/2 in place of β; that only agrees at 90°, so write β explicitly
in the parameter block.

- **Notch depth** about 25–30 % of the ball diameter; deeper wedges, shallower
  skips.
- **Seat**: a 90° countersink is the plunger makers' default. Opening the
  notch releases more easily; closing it holds harder.
- **Seating force** for a hand-operated control: about 5–15 N at the ball.
- Friction is in every contact (ball–notch, ball–bore, ball–spring), so the
  measured force comes out above the frictionless estimate.
- Printed notches wear and creep: a steel ball in a printed notch indents it
  over cycles. Put the notch in the harder part or use a bought spring plunger
  (`$step-parts`), and plan a test coupon.

A **flexing-finger detent** replaces the coil spring with a cantilever: its
seating force is the snap beam's `P` at the bump height
([[snap-fit-design#cantilever]]) and its strain must stay inside the
repeated-use limit ([[flexure-materials-and-snap-strain]]). A spring sized
for a ball detent: [[springs#helical-compression-spring]].

A rigid sweep reads the bump as a collision; declare the overlap allowance
([[mechanism-verification#8-allowances-are-declared-not-hidden]]).

## Indexing detents

A dial or knob that stops at `n` positions has `n` notches at `360°/n`.

- Resolution and holding torque trade off: more notches means smaller ones
  at the same radius, and a smaller notch depth holds less.
- Put the notches on the largest radius the part allows: holding torque is
  force × radius.
- A detent that must also stop the dial at the end of its range still needs a
  hard stop; a detent is not a stop.
- If a position must be found without looking, give the home position a
  deeper or doubled notch.

## Ratchet and pawl geometry

[[cams-intermittent#ratchet-and-pawl]] gives the short rules; this is the
geometry behind them.

- **Pivot on the tangent.** Put the pawl pivot on (or near) the tangent to
  the wheel's tip circle at the contact point, so the line from contact to
  pivot is perpendicular to the wheel radius there. The locking load then
  acts almost through the pivot and puts no moment on the pawl either way.
- **Undercut the locking face.** Tilt the locking face a few degrees past
  radial (back flank about 80–90° from the tangent, 85° a safe default) so the
  contact normal passes on the engaging side of the pivot by at least 2–3°.
  Then load pulls the pawl deeper into the tooth. Hold engagement by this
  geometry, not by the spring and friction alone.
- **Free-side flank** sloped (the short rules give ~60°) so the pawl rides up
  and drops in; the tooth depth is the pawl lift.
- **Spring** only has to return the pawl: it must seat within about a third
  of a tooth period at the fastest free-running speed or the pawl skips.
- **Resolution** is one tooth: a 24-tooth wheel holds every 15°. Two pawls
  offset by half a tooth halve the backlash without smaller teeth.
- **Pivot force** under a reverse torque T on a wheel of radius R, pawl
  length L from pivot to tip:

```text
F_tip   = T / R
F_pivot = (T / R) · sqrt(1 + (L / R)²)
```

The pawl pivot and its pin carry the whole locking load: size them like a
hinge pin ([[hinges-and-pin-joints#pin-and-knuckle-sizing]]) and put the pivot
in the retention chain. A freewheel built from pawls is on
[[clutches-and-freewheels#freewheels-one-way]].

## Latches

- **Snap-hook latch**: a cantilever with a 90° return face is permanent; a
  sloped return face is separable by force; a hook with a release tab is
  opened by moving the tab. Calculation: [[snap-fit-design]].
- **Cam or draw latch**: a lever pulls a hook or loop over centre and
  clamps. It is a toggle: the knee must pass dead centre by a few degrees onto
  a hard stop to hold itself ([[straight-line-and-toggle-linkages#toggle-mechanisms]]).
  The clamping stretch comes from a compliant link or the hook's own
  deflection; with rigid printed links the lever either will not close or
  holds nothing.
- **Push-push (touch) latch**: a pin rides a heart-shaped cam groove. Push
  once and the pin passes the heart's notch and lodges in it under the return
  spring; push again and it is steered round the other side and released. The
  pin sits on a rocking arm (or the groove floor has steps) so it can only
  travel one way round; the spring must return the moving part past the
  heart. The push needs overtravel beyond the latched position so the pin
  can clear the notch. Buy it where possible: the groove is small and a
  printed one wears.
- **Bayonet**: an L-slot turned into a short leg; a detent bump in the short
  leg stops it backing out ([[joints#latching-and-holding]]).

## Magnetic catches

A magnet catch has no wear part and pulls itself shut over the last
millimetre, but its force falls steeply with any gap: every millimetre of
printed skin, paint or clearance between magnet and striker costs pull. Keep
the magnet flush or behind the thinnest skin the print allows, make a steel
striker at least about twice the magnet's diameter wide, and test the
pull on the actual part. Pockets, polarity and embedding are on
[[magnets-and-strap-slots]].

## Bistable positions

A part with two stable positions and a snap between them is either a
flexure whose energy has two minima ([[flexures-and-living-hinges#bistable-mechanisms]])
or a spring-loaded toggle passing dead centre
([[straight-line-and-toggle-linkages#toggle-mechanisms]]). Both need the
peak force reachable by the user and the strain at the peak inside the
material limit. A detent with only two notches is the simplest bistable part.

## Checks

```python
import math
phi = math.atan(MU)
f_side = F_SEAT * math.tan(math.radians(FLANK_DEG) + phi)
assert F_HOLD_MIN <= f_side <= F_USER_MAX, "detent either slips or cannot be worked by hand"
assert 0.25 <= NOTCH_DEPTH / BALL_D <= 0.30, "detent notch depth outside the usual band"
assert PAWL_NORMAL_MARGIN_DEG >= 2.0, "contact normal does not pull the pawl into the tooth"
assert TOGGLE_OVERTRAVEL_DEG >= 1.0 and HAS_STOP, "over-centre latch needs overtravel and a hard stop"
```

Open items: detent force, spring set, notch wear and magnet pull are forces
and life; no rigid gate measures them. Record them and plan a coupon
([[creep-and-stress-relaxation]]).
