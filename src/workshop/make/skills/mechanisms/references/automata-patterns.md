# Automaton patterns

A toy automaton is a box of mechanism under a figure. The figure is what the
reference image shows; the box is what makes it move. Decide the box first,
then fit the figure over it.

## The common layouts

| layout | how it works | good for |
|---|---|---|
| **cam shaft box** | one horizontal shaft through a box, cams on it, push rods rise through the lid into the figure | several independent up/down motions with set timing (heads, arms, bobbing) |
| **crank-and-link** | crank pins on a shaft, links up to hinged panels or limbs | flapping, undulating, waving (manta_ray) |
| **walker** | cranks on two axles tied by coupling rods, legs on the crank pins with a guide (trotter) | anything that walks |
| **turntable** | vertical output via bevel/face gear or worm under the figure | spinning, dancing |
| **Geneva / ratchet stage** | indexed output under a figure | clocks, conveyors, turn-taking scenes |

Rules shared by all of them:

- **Input shaft level and accessible**: a hand crank on a keyed end, or a motor
  on a reduction; both variants can share one frame (manta_ray builds a motor
  and a manual entry from the same parts).
- **Lid or plate carries the guides**, the box carries the bearings. Guides
  for push rods are bushings ≥ 2 × rod diameter long.
- **The mechanism assembles as a cassette** where possible: shaft, cams or
  cranks, and rods pre-assembled, then dropped into the box in one move
  (trotter `cassette-lowers-into-tub`, checked as one coupled translation).
- **Phase every repeated element deliberately** — cams at staggered angles
  for a wave, cranks at 180° for alternating wings, diagonal legs in phase for
  a trot. Phase is a parameter with a recorded reason.
- **Figure parts hinge on pins, not glue**, when they move; glue only what
  never moves and say so.

## Worked example: `output/trotter` (walker)

- Two crank axles, continuous keyed spines, coupled by two rods **quartered**
  90° apart (+45° / -45°) — no dead centre.
- Right-angle drive: 4-start worm (60°) on a 12-tooth helical wheel (30°),
  3:1, worm axis above the axle; the tail knob is on the worm shaft.
- Legs: one flat leg per corner on a crank pin (throw 3 mm) with a guide pin
  14.5 mm below the axle → 33 mm stride, 6 mm lift. Each leg is built in the
  neutral pose and placed from its own crank phase by
  `features/kinematics.py`.
- Retention: shoulder pins (integral head) for both crank and guide joints;
  the head held down by the lid; the lid held by lip detents. The chain closes
  at the tub.
- Motion manifest generated from the kinematics (`measure/make_motion.py`):
  two half-cycle coupled sweeps against the body and guide pins, one
  fine tooth-pitch sweep, a band-corridor clear path, the full assembly order,
  and three `blocked` captures.

## Worked example: `output/manta_ray` (crank-and-link)

- TT motor (TT gear → back wheel) or hand crank turns the drive shaft; its
  pinion meshes the left front gear, which meshes the right one, each on its
  own crankset; the right crank is set half a tooth pitch ahead, so the two
  sides differ by a few degrees.
- Crank pins lift links hooked into staples on the ray body and on three
  hinged wing panels per side; each link hooks in a loop slot, so it is a
  **range** of lengths `[L, L + slack]`, not a length.
- The rest pose is solved, not posed: scan crank angles, keep those where the
  whole linkage closes, pick the one with the body level and the flattest
  wings (`assemblies/pose.py` `solve_pose`), and `audit()` every datum pair —
  centre distances `m (z1 + z2) / 2`, bearings over bearings, every link inside
  its slack, left/right wings mirroring within the crank advance.
- Clashes found by `interfere` (8 link × staple) were repaired by re-solving
  the rest pose, not by nudging parts.

## Reading a mechanism off a picture

A photo shows the shell over the mechanism. Recover the mechanism from the
motion the object must make, the visible pivots and slots, and the input
(crank handle, motor box, key). If the choice changes the outline and the
image cannot settle it, that is a question for the user; otherwise pick the
simplest archetype that makes the motion and record what was rejected.
