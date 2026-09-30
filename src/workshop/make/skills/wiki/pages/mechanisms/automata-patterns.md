---
title: Automaton patterns
tags: [automaton, layout, cam-box, crank, walker, turntable, cassette, phase, figure]
aliases: [automata, kinetic toy, mechanical toy, cam box, walking toy, flapping toy, nodding head, head bob, eccentric strap, push toy, pull toy, push-along, scotch yoke, wing flap, swinging legs, galloping legs, leg lever]
sources:
  - general automaton practice (cam box, crank-and-link, walker, turntable layouts)
  - "experience: automata built in this repository (rules only, no results)"
  - "experience: a head-and-tail drive added to a finished walker, where the strap's closed ring decided the assembly order"
  - "experience: legs added to a push-along flapper's pushrod inside a carved split body"
related: [mechanism-design, linkages, cams-intermittent, energy-drive]
updated: 2026-09-30
---

# Automaton patterns

A toy automaton is a box of mechanism under a figure. The figure is what the
reference image shows; the box is what makes it move. Decide the box first,
then fit the figure over it.

## The common layouts

| layout | how it works | good for |
|---|---|---|
| **cam shaft box** | one horizontal shaft through a box, cams on it, push rods rise through the lid into the figure | several independent up/down motions with set timing (heads, arms, bobbing) |
| **crank-and-link** | crank pins on a shaft, links up to hinged panels or limbs | flapping, undulating, waving |
| **walker** | cranks on two axles tied by coupling rods, legs on the crank pins with a guide | anything that walks |
| **turntable** | vertical output via bevel/face gear or worm under the figure | spinning, dancing |
| **Geneva / ratchet stage** | indexed output under a figure | clocks, conveyors, turn-taking scenes |

## Rules shared by every layout

- **Input shaft level and accessible**: a hand crank on a keyed end, or a motor
  on a reduction; both variants can share one frame when the motor entry and
  the manual entry are built from the same parts.
- **Lid or plate carries the guides**, the box carries the bearings. Guides
  for push rods are bushings ≥ 2 × rod diameter long.
- **The mechanism assembles as a cassette** where possible: shaft, cams or
  cranks, and rods pre-assembled, then dropped into the box in one move,
  checked as one coupled translation.
- **Phase every repeated element deliberately** — cams at staggered angles
  for a wave, cranks at 180° for alternating wings, diagonal legs in phase for
  a trot. Phase is a parameter with a recorded reason.
- **Figure parts hinge on pins, not glue**, when they move; glue only what
  never moves and say so.

## Pattern: a four-legged walker

- Two crank axles on continuous keyed spines, coupled by two rods
  **quartered** 90° apart — no dead centre ([[linkages#dead-centres]]).
- A right-angle input: a multi-start worm on a helical wheel with the worm
  axis above the axle, the crank knob on the worm shaft; enough lead angle
  that it back-drives if the toy should roll ([[gears#worm-and-crossed-helical-pairs]]).
- One flat leg per corner on a crank pin with a fixed guide pin below the
  axle; stride and lift follow from the throw and the guide distance
  ([[linkages#walking-linkages]]). Each leg built in the neutral pose and
  placed from its own crank phase by the kinematics module.
- Retention: shoulder pins for crank and guide joints, their heads held down
  by the lid, the lid held by detents — the chain closes at the body.
- Motion manifest generated from the kinematics: coupled half-cycle sweeps
  against the body and guide pins, one fine tooth-pitch sweep, a clear path
  for any band corridor, the full assembly order, and a `blocked` capture per
  retained part.

## Pattern: a crank-and-link flapper

- A motor or hand crank turns the drive shaft; its pinion drives one side's
  gear, which drives the other's, each on its own crankset. Setting one crank
  half a tooth ahead makes the two sides differ by a few degrees on purpose.
- Crank pins lift links hooked into staples on the body and on hinged wing
  panels; a link hooked in a loop slot is a **range** of lengths
  `[L, L + slack]`, not a length.
- The rest pose is solved, not posed: scan crank angles, keep those where the
  whole linkage closes, pick the one that best matches the reference, and
  audit every datum pair — centre distances `m (z1 + z2) / 2`, bearings over
  bearings, every link inside its slack, left/right panels mirroring within
  the crank advance ([[linkages#solving-closure-numerically]]).
- A link × staple clash found by `interfere` is repaired by re-solving the
  rest pose, not by nudging parts.

## Pattern: a push-along flapper

The wheels are the crank: one wheel turn, one wingbeat. The classic wooden
version lifts a rod on a cam and lets the wings fall back, and its commonest
complaint is that the wings flap on some pushes and not others.

- **Put the drive axle under the figure's balance point.** The rod rises
  from the drive axle, so the column that guides it stands over that axle.
  With two axles and the drive at one end the figure overhangs the end, and
  a hand pressing on its head tips the toy. Three axles with the drive in the
  middle, set about 0.5 mm lower than the outer two, keep the drive pair
  loaded on any flat floor: the toy rests on four of six wheels and rocks
  about half a degree. O-ring tyres give the drive pair the grip a printed
  rim lacks.
- **An eccentric in a rectangular yoke, not a cam.** It is a Scotch yoke
  whose pin has grown round the axle: the window's height is the disc
  diameter plus a running fit, its width the disc plus twice the throw plus
  clearance, and the axle passes inside the disc, so the throw is free and
  there is no pin joint to retain. Top and bottom of the window both bear:
  the rod is driven down as well as up, with no gravity return.
- **The closed yoke fixes the order.** The disc goes into the window first,
  rod and disc go up the well together, then the axle is pushed through the
  plinth and the disc. A square rod in a square bore is both its guide and
  its anti-rotation.
- **Two wings, one pin.** Hinge each wing either side of the rod and give it
  a tab reaching across the rod to a cross pin through the rod top. The pin
  runs in a radial slot in each tab (pivot to pin is `S / cos θ`), and the
  blade angle is `β = -atan((H0 + e sin φ) / S)`. Stagger the tabs, one in
  front of the rod and one behind, and stop each knuckle short of the other
  wing's tab. Keep blade and tab coplanar, so the wing prints flat on its
  blade, and set the rest angle with the pin's rest height `H0` instead of
  a bend.
- **Close the bottom.** A rod well open underneath is a 5-12 mm finger gap
  ([[toy-safety-constraints#finger-entrapment-and-springs-en-71-1]]): glue a
  keel plate over its mouth once the rod is in.

## Pattern: legs that swing with the wings

A figure already beaten by a vertical pushrod -- the push-along flapper above
-- can swing its legs from the same rod, with nothing showing.

- **A lever per pair, on a shaft through the shoulders or the hips.** Each pair
  of legs turns on the centre of its root (the joint circle it is let into the
  flank by); a D-shaft through both halves there carries the two legs, glued on
  its ends like wheels on an axle, and a lever keyed on it inside the body.
- **A pin in a radial slot drives it.** A leg pin through the rod runs in a
  slot along the lever that points through the shaft, so the lever always
  points at the pin: a pair's turn is the angle between its pivot-to-pin
  vectors, `atan2(a × b, a · b)`, and the slot's reach is the pin's distance
  from the pivot over the stroke. One lever reaching back from the shoulders
  and one forward from the hips turn opposite ways, so the legs gather as the
  rod rises and stretch as it falls; put the wings' top at the rod's bottom and
  the legs are stretched when the wings are raised.
- **The swing is set by the stroke, not the pin's height.** A radial slot turns
  its lever at most one radian per shaft-to-rod distance, so a 7 mm stroke with
  shafts 26-29 mm from the rod swings the legs 14-15°. The pin's height only
  moves where in the arc the swing sits; choose it for what is around the
  levers (a column tenon under them, a printable pocket).
- **The tips pass through the rod, not beside it.** Levers meeting a rod on the
  midplane of a split body turn in pockets that meet the rod's channel, and
  tips beside the rod need a tall, wide room there. Make each lever a flat plate
  on its inner face, thick only along its arm, and pass both tips through a
  window in the rod, one each side of the midplane; the rod well stays narrow and
  the pockets print ([[overhangs-and-print-orientation#pockets-inside-a-split-print-one-ceiling-one-bridge]]).
  The rod's walls beside the window carry the drive: keep them three lines.
- **Then the rod goes in first.** A tip in the rod's window is in the rod's path,
  so the rod cannot be fed up through a glued body any more: it goes up the
  column first, the levers are hung on it by the leg pin, and the halves close
  round them. The pin then needs no way in from outside; the rod well's walls
  keep it in.
- **The legs turn in their counterbores:** sweep each counterbore over its
  leg's swing, with its floor a running gap under the leg's flat face
  ([[carved-figures-on-split-prints#a-limb-that-turns]]).

## Pattern: a nodding head and tail on an existing crank line

For a machine that already turns — a walker whose head and tail should move
with its legs — the drive is taken off its crank line, not added beside it.

- **Find the one exposed stretch.** In a walker most of the crank line is
  inside leg stacks and bearing tubes; there is usually one window where the
  shaft turns in the open. That window, and what hangs under the axis in it
  (a bevel pinion, a motor), fixes everything below.
- **An eccentric, not a crank pin, when the shaft runs on through the link's
  layer.** A crank pin's eye has to clear the shaft beside it, so the throw
  can never be less than shaft radius + eye radius. An eccentric's strap goes
  round the shaft instead, and its throw is free. Its sweep bound is the
  lowest point it reaches under the axis:

```python
assert THROW + STRAP_BORE_D / 2 + STRAP_WALL <= FLOOR_BELOW_AXIS - CLEARANCE
assert DISC_D / 2 - THROW - BORE_D / 2 >= 2 * NOZZLE   # the disc's thin side
```

- **A closed strap fixes the assembly order.** It is threaded on with the
  shaft and afterwards can only turn, so everything it drives has to be
  brought to it, and whatever it drives turns on pins that go in after the
  parts are hung, not on pegs printed onto the frame behind them. Write the
  order down before choosing which part carries which peg.
- **Hold the strap between a flange and a keeper round the shaft's own
  axis**, each reaching `THROW + STRAP_BORE_D / 2 + 1` from it: they hold it
  at every angle without being clocked to the eccentric. That strap is then
  also the only stop along the shaft for everything pinned to it.
- **One rocker, two ends.** Pivot the neck at the withers with the head
  forward of the pin; a parallelogram bar from an arm on the neck to the same
  arm on a tail pivoted at the croup turns the tail through exactly the
  neck's angle, so the head lifts as the tail drops. Put the rod's pin where
  the transmission angle is 90° at mid-swing ([[linkages#placing-the-rocker-pin]]).
- **Keep every new mover in its own flat layer**, turning about axes parallel
  to the crank line. Then no part changes its extent along that axis and a
  band comparison still settles the clearance to the legs for the whole turn.
- **Time it to the gait**: with one nod per turn, the head can peak on one
  forefoot's mid-stance and bottom on the other's.

## Reading a mechanism off a picture

A photo shows the shell over the mechanism. Recover the mechanism from the
motion the object must make, the visible pivots and slots, and the input
(crank handle, motor box, key). If the choice changes the outline and the
image cannot settle it, that is a question for the user; otherwise pick the
simplest archetype that makes the motion and record what was rejected.
