---
title: Energy and drive
tags: [drive, energy, rubber-band, spring, motor, hand-crank, flywheel, torque, ratio, efficiency]
aliases: [power source, prime mover, elastic band, clockwork, gearmotor, torque budget, speed reduction]
sources:
  - Shigley's Mechanical Engineering Design, ch. 10 (springs) and ch. 13 (worm efficiency)
  - skills/electromechanical-integration/SKILL.md
  - "experience: band hooks that were unprintable overhangs, and captures aimed away from the drive direction"
  - "experience: a printed walker whose budget priced foot traction through a flat linkage efficiency, and whose motor stalled"
  - https://www.pololu.com/category/60/micro-metal-gearmotors
related: [gears, mechanism-design, automata-patterns, cable-and-tendon-drives]
updated: 2026-10-07
---

# Energy and drive

The power source is not the mechanism. Name both: *what stores or supplies the
energy*, and *which archetype turns it into the motion*.

## Sources

| source | stores by | delivers | design notes |
|---|---|---|---|
| **rubber band** | twisting (wound on a hook/axle) or stretching | falling torque as it unwinds | anchor on a post moulded into the fixed body, not a loose cross pin; leave a corridor for the twisted band and check it as a clear path; the hook needs a barb or notch, not an open U that is an unprintable overhang |
| **stretched band** | extension between two posts | pull along the band | posts carry the full band force as a moment at their root: fillet the root, keep them short |
| **printed spring** | compression, torsion or flexure | small force, creeps | pitch must exceed wire section or coils fuse; PLA recovers poorly — PETG or a catalog spring for anything cyclic |
| **catalog spring** | — | stable | search `$step-parts` by wire, OD, free length; seat it with `cadmount` |
| **falling weight** | lifted height | constant torque | needs a drop height and a line/drum; slow with a governor or escapement |
| **hand crank** | — | whatever the hand supplies | crank radius 20–35 mm for fingers; a knob on a keyed shaft end |
| **pull-back / flywheel** | spin-up through gears | burst | the gear train has to back-drive: no self-locking worm |
| **motor / servo** | electrical | continuous | an electrical load: go to `$electromechanical-integration` for source, switch, wiring and `power.json` before the layout is fixed |

Pulling a joint through a cord or tendon: [[cable-and-tendon-drives]].

## Ratio budget

Work backwards from what the output needs:

```text
output speed  = source speed / total ratio
output torque ≈ source torque × total ratio × efficiency
```

Printed spur stages run ~90 %, a worm pair much less (often 40–60 % for
low starts). A small DC toy motor runs thousands of rpm; an automaton crank
wants 10–60 rpm — two or three reduction stages, or a worm. A rubber band
gives few turns: a step-up to the wheels trades torque for distance.

## A walker's budget: price every joint at the cycle's peak

A printed linkage loses more to its own plain joints than it spends on the
job. Price it quasi-statically over one crank turn, on the mechanism's own
kinematics, and size the motor against the **peak**, not the mean:

- **work**: the body lifted as the stance feet go down (`W × dz/dθ`), plus a
  swing foot dragged over the floor — a diagonal pair alone is a base a foot
  wide, so the body rocks onto a third foot;
- **every plain joint**: `μ × load × pin radius × relative rotation rate`
  (a guide pin also slides: `μ × load × slide rate`). Solve each leg's statics
  for its pin loads; a hip journal carries the leg load times
  `1 + 2 × overhang / span` ([[shafts-and-bearings#supports-and-spans]]);
- **the gear pair**: its efficiency at the same μ, and a worm wheel's end
  thrust ([[worm-gear-efficiency#the-wheels-end-thrust-is-a-friction-loss]]);
- **the source**: stall torque on the cells at mid-life and near empty, from a
  DC model of the motor behind the cells' own resistance — not the datasheet
  stall scaled by voltage, which overstates a 6 V motor on two alkaline cells
  by about a third ([[small-dc-motors#below-the-rated-voltage-a-dc-model-not-a-scale]],
  [[battery-cells-and-packs#an-alkaline-cell-in-a-model]]).

```python
peak = max(worm_torque(theta, MU_WORST) for theta in range(360))
assert stall_nmm(DEPTH_MID) / peak >= 1.5     # dry PLA on PLA, the worst case
assert stall_nmm(DEPTH_EMPTY) / max(worm_torque(t, MU_RUN_IN) for t in range(360)) >= 1.2
```

Weigh the toy rather than guess it: printed mass is the skin (perimeters and
top/bottom layers, `area × skin thickness`) at full density plus the rest at
the infill share, so the slicer settings are part of the budget — three walls
and 20 % infill against two and 15 % moved one walker's mass by a quarter.

A budget of `traction × stride / 2π / linkage efficiency` misses all of
this. It cleared a printed walker's motor at 2.1×; priced joint by joint the
margin was 0.57× at μ 0.35, and the toy stalled. The joints cost four times
the lift, and two single losses each outweighed it: journals the body hung
from, bearing up into a teardrop roof, and a worm wheel's end thrust on a
large face.

**Torque is cheap; power is not.** A brushed motor's best output is
`stall torque × free speed / 4`, whatever the gearbox ratio: a micro metal
gearmotor's MP winding gives about 0.1 W at 2.6 V, the LP winding half that.
Once the joints take most of it, a higher ratio only moves the stall further
off — it does not make the walker faster. Less friction (grease, round
journals, small thrust faces) or more volts does.

## Play the walk out: stance, grip, motor and cells

A budget assumes how the toy stands and how much of it a dragged foot
carries. Playing the cycle out answers both, still quasi-statically (a crank
turn takes seconds, so inertia is a few per cent of the weight):

1. **Stance.** Sample each sole's outline in the body frame at every crank
   angle. The body rests on a facet of the convex hull of all those points —
   the plane a rigid body settles on — and only on one whose triangle has the
   centre of mass straight above it (along the facet's normal). Keep the
   current facet while it stays stable; when it does not, tip to the stable
   facet nearest in orientation. The foot loads are the centre of mass's
   barycentric weights in the triangle. Use the exact rotation, not a small
   angle: a body whose centre of mass sits 0.4 mm off its stance diagonal and
   90 mm up rolls 5° onto its third foot and puts about 12 % of its weight
   there; a linearised stance says 0.6 %.
2. **Grip.** The body's slide over the floor (two translations and a yaw) is
   the one that minimises the friction power `Σ N |v_contact|`: Coulomb's law
   without inertia. A contact slipping faster than a small threshold carries
   `μN` against its slip; the gripping contacts share whatever balances those,
   as the least-norm set that closes force and moment. Giving a gripping
   contact a full `μN` in the direction of its tiny residual slip invents side
   loads that leg statics then multiply into the pins.
3. **Torque.** The crank pays the rise of the centre of mass (a drop when the
   body tips onto a new facet is free), the feet's sliding power, and every
   joint's friction under the loads of 1 and 2.
4. **Motor and cells.** At each crank angle the crank turns where the motor's
   torque meets the demand; integrate a turn in time for its seconds and
   coulombs, then drain the cells turn after turn. Report the advance per turn
   against the feet's stroke, the heading drift, the speed, the running time,
   and the static friction at which a start from rest fails.

## Drive direction

Write down which way the source pulls or turns, in assembly coordinates, and
what it loads:

- a band pulling a part forward loads whatever that part bears on: that
  contact is the `blocked` condition;
- a worm's separating force pushes the worm away from the wheel: something
  (a lid, a keeper) must stop it, and that stop is a `blocked` condition;
- the direction the driven output reverses under load is where a ratchet
  or self-locking stage belongs, if anything should hold.

A `blocked` condition aimed anywhere other than the drive direction proves a
capture nobody needed and leaves the real one untested.

Springs sized from formulas: [[springs]]. Wheels and motor sizing:
[[wheeled-vehicles]]. Slip clutches and freewheels: [[clutches-and-freewheels]].

## Open items this page can never close

Band torque, spring rate after printing, the real friction coefficients,
whether the toy walks on a particular floor. A played-out cycle prices
runtime and margins against assumed friction; it does not measure them.
Record them as open questions; no rigid sweep answers them.
