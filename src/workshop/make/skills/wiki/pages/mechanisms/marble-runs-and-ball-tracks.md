---
title: Marble runs and ball tracks
tags: [marble, ball, track, ramp, lift, rolling, gravity, toy]
aliases: [marble run, marble machine, marble track, ball track, ball run, gravity track, rolling ball sculpture, kinetic ball track, marble lift, ball lift, screw lift, auger lift, archimedes screw lift, stair lift, step lift, staircase lift, wheel lift, chain lift, marblevator, gravitrax, kugelbahn, loop the loop, banked curve, vortex funnel, spiral funnel, two rail track, steel ball track]
sources:
  - https://phys.libretexts.org/Courses/Prince_Georges_Community_College/General_Physics_I%3A_Classical_Mechanics/44%3A_Rolling_Bodies/44.01%3A_Velocity (v = sqrt(2gh/(1+beta)), beta = I/(mR^2); solid sphere v = sqrt(10gh/7))
  - https://www.physicsforums.com/threads/what-minimum-height-ensures-a-marble-stays-on-a-loop-the-loop-track.302298/post-2131739 (rolling solid sphere completes a loop from 2.7(R - r); 2.5 when spin is ignored)
  - https://en.wikipedia.org/wiki/Banked_turn (tan theta = v^2/(r g) for a point mass)
  - https://ar5iv.labs.arxiv.org/html/physics/0602160 (sphere rolling on a cone, eq. 23: the circular-orbit condition carries the 5/7 rolling factor and a spin-about-normal term)
  - Meriam & Kraige, Engineering Mechanics - Dynamics, ch. 6 (rolling rigid bodies; angular impulse-momentum about a point, used for the step losses)
  - https://en.wikipedia.org/wiki/Rolling_resistance (hardened steel ball on steel Crr 0.0010-0.0015)
  - https://www.marblecollecting.com/marble-reference/how-to-size-marbles/ (sieve-sized in 1/16 in steps; one size class varies by 3/64 in; machine-made 1/2-3/4 in; tournament targets 5/8 in)
  - https://en.wikipedia.org/wiki/Ball_(bearing) (grade 100 +/-0.0127 mm, sphericity 0.0025 mm; grade 1000 +/-0.127 mm)
  - https://en.wikipedia.org/wiki/Soda%E2%80%93lime_glass (2.52 g/cm3)
  - https://en.wikipedia.org/wiki/Density (mild steel 7850 kg/m3)
  - https://www.instructables.com/Kinetic-Marble-Track-Around-The-Top-Of-A-Room/ (25 mm glass marbles; average slope about 3.5 %; too flat hangs up, too steep jumps at curves and joints; oversize marbles roll faster and leave curves; two-wheel lift with a 3/4 in gap; stair lift tilted 5 deg)
  - https://www.instructables.com/A-Wooden-Marble-Run-in-a-Frame/ (about 17 mm marbles in a 7/8 in channel 1/2 in deep; 2.5 deg chosen as the slowest that never stops; stair steps a little over 2 d long, tops tilted 5 deg, about 1 mm between fixed and moving sets)
  - https://www.nutsvolts.com/magazine/article/the_flying_marbellos (15/16 in marbles sold as 1 in, sorted to 0.2 g; 1/8 in rod rails 3/4 in apart inside; wider spacing slower, banking less critical; hooks on #41 chain at 10 rpm)
  - https://www.instructables.com/Marblevator-Spirals/ (8 mm balls riding rails "over-rotate" and descend slower; inverse auger prints without supports; 100 rpm 6 V N20 gearmotor run from 3 V)
  - https://www.instructables.com/Marble-Machine-40/ (4-step staircase lift with sloped step tops; cams alternate above and below the axle)
  - https://www.printables.com/model/853965-marblevator-self-reversing-screw-lift (N20 70 rpm 6 V gearmotor; screw printed at 0.1 mm layers)
  - https://www.printables.com/model/655763-orbital-rush-marble-lift-and-track (15 mm marbles; smooth build-plate face as the running surface; hand-wheel step lift raising 70 mm)
  - https://woodgears.ca/marbles/modular.html (32 mm plan unit, 20 mm height unit, each ramp-to-ramp transition drops one unit; a marble in matching holes interlocks blocks; loose track shifts after about 20 marbles; crank pump with a flexible coupling as a slip clutch)
  - https://woodgears.ca/mm2/how_it_works/index.html (gear-pocket lift: pockets slope into the wheel at pickup, flare at the leading edge, guard past halfway; flip-flop keeps up with about 6 marbles/s)
  - https://www.printables.com/model/88169-gravitrax-height-stone-10-mm-with-14-mm-diameter-h (GraviTrax standard height stone 10 mm; a 14 mm hole passes the ball)
  - https://www.printables.com/model/1197796-gravitrax-compatible-height-spacer-tile-set-no-sup (original GraviTrax height parts 5 mm and 10 mm)
  - https://www.printables.com/model/392095-marble-run-railscurves-kugelbahn-schienenkurven-gr (compatible slopes named by height change, 10 mm = one large stone; one slope works over 5-15 mm)
related: [toy-safety-constraints, energy-drive, small-dc-motors, overhangs-and-print-orientation, sweeps-and-helices, noise-and-vibration, lead-screws, cams-intermittent, clutches-and-freewheels, wall-thickness-and-hollowing, fdm-surface-finish, fit-derivation, interlocking-joinery-for-prints]
updated: 2026-10-10
---

# Marble runs and ball tracks

A marble run is a budget of height: every metre of track, curve, joint and
bump spends some of the drop, and a lift buys it back. The ball's speed is
set by the height it has fallen since the last thing that took its energy
and by how it touches the track, not by the slope under it.

## Ball choice: measure the batch, not the label

- **Mass** `m = rho pi d^3 / 6`: 8 / 10 / 12.7 mm steel bearing balls 2.1 /
  4.1 / 8.4 g; 14 / 16 / 22 / 25 mm glass 3.6 / 5.4 / 14.0 / 20.6 g. Steel is
  3.1 times as dense: louder landings and heavier lifts, same rolling speed.
- **Glass marbles vary.** Sieve grading leaves 3/64 in (1.2 mm) inside one
  size class; a bag sold as "1 in" measured 15/16 in. Bearing balls hold
  +/-0.127 mm even at grade 1000. Design to the caliper range of the batch:
  `D_MAX` sets clearances, `D_MIN` what must not fall through.
- **Oversize marbles leave curves.** On rails or in a V a bigger ball sits
  higher, rolls faster (next section) and climbs further in a bend. Sort the
  marbles for a tuned run, or design the curves for `D_MAX`.
- **GraviTrax** runs steel balls under 14 mm (a 14 mm hole in a compatible
  height stone passes them) on hex tiles with 10 mm large and 5 mm small
  height tiles. No official dimensions were found: measure an original.
- Marbles are small balls in toy-safety law: state the age grade and the
  warning ([[toy-safety-constraints#small-parts-the-choke-test]]).

## Speed: drop height and contact geometry, not slope

A solid ball (`I = 2/5 m r^2`) rolls about the line through its contact
points, at `r_e = r cos(alpha)` from its centre (`alpha`: contact angle from
vertical). After a net drop `h`:

```text
beta = 0.4 / cos(alpha)^2                v = sqrt(2 g h / (1 + beta))
on a slope theta:  a = g (sin(theta) - Crr_eff cos(theta)) / (1 + beta)
two rails, top radius rho, centre spacing s:  sin(alpha) = (s/2) / (r + rho)
V groove of included angle 2*gamma:            alpha = 90 deg - gamma
```

| contact | alpha | a / (g sin theta) | v / sqrt(g h) |
|---|---|---|---|
| U floor, one contact | 0 | 0.714 | 1.195 (`sqrt(10/7 g h)`) |
| 120 deg V, or rails about one ball radius apart | 30 deg | 0.652 | 1.142 |
| 90 deg V | 45 deg | 0.556 | 1.054 |
| 1/8 in rods 3/4 in apart, 15/16 in marble | 55 deg | 0.451 | 0.950 |
| 60 deg V, or wide-set rails | 60 deg | 0.385 | 0.877 |

Spread contacts put more of the drop into spin: **wide rails are a brake**
(builders: "wider is slower, banking less critical"; balls "over-rotate" on
rails). Design catches and banks for the lossless `v`. **Keep the contact
geometry constant through a joint:** a ball off rails spins at `v / r_e`, too
fast for a U floor, and skids until the spin matches.

## Slope: just above the loss angle

A ball holds its speed where `tan(theta) = Crr_eff`. Hard steel on steel has
`Crr` 0.0010-0.0015 (under 0.1 deg); real tracks lose far more to joints,
ridges, wall scrub and dust, so built runs sit near 2-2.7 deg (3.5 % on
varnished wood with 25 mm marbles; 2.5 deg as "the slowest that never stops"
with 17 mm marbles). A print is rougher: print a straight coupon of the real
profile, find the angle where `D_MIN` balls still roll, never build flatter.

There is no steepest slope, only a fastest arrival: the ball jumps where it
reaches a curve, joint or catch too fast. Put a speed killer (zig-zag,
catch, funnel) before any bend sized for slow balls.

## Channel profile: U, V or two rails

- **U channel.** Floor radius larger than `r`, so the ball touches one line
  at full `r_e`; width `D_MAX` plus a few mm (22 mm for 17-19 mm marbles in
  one build). A channel narrower than the ball is two rails on its edges.
- **Wall height** at least `r` on straights, so a wall touch pushes sideways
  instead of lifting the ball over (12.7 mm, about 0.7 d, in the same build);
  higher on the outside of every curve.
- **V groove** self-centres and is slower (table); its sharp root never
  touches the ball. **Two rails** show the ball and tune the speed; keep the
  gap well under `D_MIN` and round the rail tops.

## Curves: bank for a rolling ball, not a point mass

A point mass rides a curve of path radius `R` at `tan(theta) = v^2 / (R g)`.
A rolling ball with no spin about the surface normal needs side friction to
swing its spin axis with the path, and rides steeper:

```text
tan(theta_ball) = (7/5) v^2 / (R g)        R_min = (7/5) v^2 / (g tan(theta_wall_max))
```

Spin about the normal shifts this either way. Worked: 0.5 m/s at `R` = 50 mm
rides at 35 deg; 1.18 m/s (100 mm lossless drop) needs 76 deg, which no open
channel holds. In a U channel the ball climbs the outer wall, so the wall's
arc must reach past `theta_ball`. On rails, an outer rail above the ball's
centre and an inner one just inside it hold the ball at any speed.

## Joints between pieces: step down, never up

At an up-step `delta` the ball pivots on the edge, keeping its angular
momentum about it, and must then climb `delta`:

```text
v_after / v = 1 - 5 delta / (7 r)        then needs  v_after^2 >= (10/7) g delta
```

A 0.5 mm step under an 8 mm-radius ball takes 9 % of its energy and stalls
any ball under 0.09 m/s. A down-step only drops it (a hop above
`v = sqrt(g r)`, 0.28 m/s at `r` = 8 mm): noise, not a stall. So **every joint
is a shingle**: the upstream floor laps over the downstream one, higher by
the joint's tolerance stack ([[fit-derivation]]), so any error steps down.

## Drops, catches and funnels

- Off a level lip at `v`, from height `H`, the ball lands `x = v sqrt(2H/g)`
  out. Catch the band from the slowest measured to the lossless speed on a
  surface tangent to the path, with a backstop; a flat floor bounces.
- **Vortex funnel.** The banking rule holds at every radius. A hyperbolic
  wall `z = -k / r` (`tan(theta) = k / r^2`) gives `v^2 = (5/7) g k / r`: the
  ball speeds up and its laps quicken as it spirals in. A cone gives
  `v^2 = (5/7) g r tan(theta)`: the whirl fades. Drain hole over `D_MAX`.

## Loop-the-loop

Ball centre on radius `R_c = R_loop - r`; `k` is the margin on the top speed
(`v_top^2 = k g R_c`; `k = 1` just stays on):

```text
h_release >= R_c (2 + k (1 + beta) / 2)     above the loop's lowest centre point
k = 1:  U channel 2.7 R_c,  90 deg V or rails 2.9 R_c
```

Upstream losses come out of this height: take `k` = 1.3-1.5 as a stated
margin and test. Entry and exit cannot share a plane: the loop is one helix
turn pitched past the channel's outer width; rails need a third rail.

## Lifts: screw, stairs, wheel, chain

- **Screw.** A helix turns inside fixed vertical rails that stop the ball
  orbiting (or a fixed helical track around turning rails - the inverse
  auger, which prints without supports). Each turn lifts one pitch:
  `p >= D_MAX + 2 c`, lift speed `p n`, one ball per start per turn. Printed
  lifts run N20 gearmotors at 70-100 rpm with the screw at 0.1 mm layers
  ([[sweeps-and-helices#helix-construction]], [[lead-screws#lead-pitch-starts]]).
- **Stairs.** Interleaved plates, one set fixed and one moving, or both on
  alternate cams 180 deg apart ([[cams-intermittent#cam-follower]]). Tops slope
  toward the next plate (5 deg in two builds) and hold a ball or two (a top
  a little over 2 d long in one); the stroke exceeds the rise per step plus a
  top's own drop; about 1 mm between sets.
- **Wheel.** Pockets in a wheel, or two wheels with a gap under `D_MIN`. Slope
  each pocket into the wheel at pickup, flare its leading edge, and guard the
  ball from about 90 deg to the release, where the pocket tips out.
- **Chain.** Hooks or forks on a chain (10 rpm sprockets in one build); guide
  every free span that can sway.

## Lift power: the marbles are not the load

`P = (sum m) g v_lift`; a screw needs `T = (sum m) g p / (2 pi eta)`: ten
5.4 g marbles on a 20 mm pitch need 1.7 mN m before losses. Friction, a
jammed ball and starting from rest size the drive: give it a slip clutch or
flexible coupling ([[clutches-and-freewheels#torque-limiters]]), then size the
motor ([[small-dc-motors#sizing-rules]]) or hand crank ([[energy-drive#sources]]).

## Printing a track: layer lines are bumps

- **Model pieces level; take the slope from the supports.** A level floor is
  one layer - a top face, or the smoother bed face - with no steps.
- **A sloped top face is a staircase**: a ridge every `h_layer / tan(theta)`
  (5.7 mm for 0.2 mm layers at 2 deg), each a drop and a click, buzzing at
  `v / spacing`. Where the floor must slope (helices, spirals) print 0.1 mm
  layers, or run the ball on vertical faces: rails whose inner walls are
  perimeters along the travel, seam kept off them ([[fdm-surface-finish#seams]]).
- **Helical ramps** joined to both a core and an outer wall bridge their
  radial width each layer; one hanging off a single wall is an overhang
  ([[overhangs-and-print-orientation#bridge-ledge-overhang]]). An inward lip
  over a channel is a ledge: 1 mm, or chamfered under.
- **Walls** from the nozzle ([[wall-thickness-and-hollowing#derive-the-wall-from-the-nozzle]]),
  three lines on the outside of curves and at catches, which take impacts.
- **Noise.** A hard ball clicks at every ridge and joint and thin walls
  radiate it ([[noise-and-vibration#rattles-and-panel-buzz]]): smooth floors
  and joints first, solid floors not shells over air, glancing landings, and
  TPU only where the ball lands - as a running surface its hysteresis drags.

## Modular grid and connectors

- **One plan pitch, one height unit** (a 32 mm plan unit with 20 mm height
  steps, each ramp-to-ramp transition dropping one; GraviTrax: hex tiles,
  10 and 5 mm height tiles). Slopes are quantised: a piece of length `L`
  dropping `n` units runs at `atan(n H_u / L)`.
- **A sloped piece spans a band** (compatible slopes are named by height
  change; one works over 5-15 mm): shape the connector so the floor meets the
  next piece without a hill anywhere in the band.
- **Locate every joint.** A loose track shifted after about 20 marbles until
  a marble in matching holes keyed the blocks; use a pin, a key
  ([[interlocking-joinery-for-prints]]) or a ball in two sockets.

## Parameters and asserts

```python
D_MAX, D_MIN = 16.6, 15.4                    # mm, caliper on the batch, not the label
W_CHAN, H_WALL = D_MAX + 3.0, 0.7 * D_MAX    # U channel width, straight-run wall
assert W_CHAN - D_MIN <= 0.35 * D_MIN        # sits low, does not wander
assert H_WALL >= D_MAX / 2                   # a wall touch pushes sideways
assert SLOPE_DEG >= SLOPE_MIN_DEG            # from the printed coupon, at D_MIN
beta = 0.4 / math.cos(math.radians(ALPHA_DEG)) ** 2
v = math.sqrt(2 * 9.81 * H_DROP / 1000 / (1 + beta))          # m/s, lossless bound
bank = math.degrees(math.atan(1.4 * v**2 / (R_CURVE / 1000 * 9.81)))
assert bank + BANK_MARGIN_DEG <= WALL_ARC_DEG                 # wall reaches past the ride
assert JOINT_TOL <= STEP_DOWN <= 1.0                          # shingle joints, never up
assert H_LOOP >= (R_LOOP - D_MAX / 2) * (2 + K_LOOP * (1 + beta) / 2)  # K_LOOP 1.3-1.5
assert SCREW_PITCH >= D_MAX + 2 * SCREW_CLEAR
assert RAIL_GAP <= 0.8 * D_MIN                                # cannot fall through
```
