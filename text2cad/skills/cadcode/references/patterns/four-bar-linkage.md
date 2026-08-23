# four-bar-linkage

**Trigger:** four-bar / 4-bar linkage, crank + coupler + rocker, Hoeken / Klann
/ Jansen / Chebyshev walking leg, walking robot legs, scissor lift, pantograph,
steering linkage, any two pinned links that share a moving joint, "the joints
must meet", "the pins must coincide", legs hanging disconnected, a mechanism
that came out as separate floating bodies.

## Why this exists

A mechanism's shared joint has exactly one correct position, and it is *solved*,
not guessed. Posing each link by an eyeballed angle ("splay the leg 30°, tilt
the rocker 45°") puts their shared joint **C** in two different places, so the
links never touch — `scripts/cad` reports `disconnected_bodies` and the preview
shows a tangle. Once the two anchored pins (crank pin **B**, ground pivot **D**)
and the two link lengths are fixed, **C is forced**: it is where the coupler
circle (centre B, radius `coupler`) and the rocker circle (centre D, radius
`rocker`) cross. Solve it once, place both links from it, and the loop closes.

This is the closed-loop case of `anchor-to-body` (a joint that must touch its
mate) and the kinematic half of `references/assembly.md`. For the full workflow,
mechanism-frame discipline, and the splay trap, read
`references/kinematic-placement.md`.

## Use the helper

`cadlib.kinematics` owns the loop-closure math — import it, don't re-derive the
circle intersection inline (re-deriving it is exactly the step eyeballing
skips).

```python
import cadquery as cq
from cadlib.kinematics import solve_fourbar, place_two_point

COUPLER, ROCKER = 20.0, 20.0
B = (8.0, -13.0)        # crank pin (eccentric journal) in the X–Z working plane
D = (-16.0, -13.0)      # chassis ground pivot in X–Z
C = solve_fourbar(crank_pin=B, ground_pivot=D,
                  coupler=COUPLER, rocker=ROCKER, branch="right")

w = lambda p: (p[0], 0.0, p[1])          # X–Z plane at one Y station -> 3-D

# Each link built along local +X: first joint at origin, second at (L, 0, 0).
leg = place_two_point(make_leg(),  p0_local=(0, 0, 0), p1_local=(COUPLER, 0, 0),
                      p0_world=w(B), p1_world=w(C))
rk  = place_two_point(make_rocker(), p0_local=(0, 0, 0), p1_local=(ROCKER, 0, 0),
                      p0_world=w(D), p1_world=w(C))
# leg and rocker now share the pin at C — one connected mechanism.
```

- `solve_fourbar(...)` returns the moving joint **C** (2-D); `branch` selects
  the elbow (`"left"`/`"right"` of B→D — flip it if the leg folds the wrong way).
- `place_two_point(part, ...)` poses a link by its two joint points; returns a
  new `cq.Workplane`.
- `circle_intersections(*, c0, r0, c1, r1)` is the raw kernel for loops that
  aren't a four-bar.
- All raise `ValueError` when the links can't span B–D — a wrong length reads as
  a clear message, not an OCCT crash.

## Pitfalls

- **Eyeballing the angle.** The angle is an *output* of the solve, never an
  input. "Splay 30°, tilt 45°" is the bug.
- **Two C's, one loop.** Each link must use the *same* solved C. If the leg and
  rocker each solve their own, they won't match — solve once, share it.
- **Wrong branch.** If the foot points up or the linkage folds inward, switch
  `branch`, don't add a corrective rotation.
- **`union` won't bridge a gap.** Pins that miss stay separate solids. Give each
  pinned end an overlapping boss and assert `len(part.solids().vals()) == 1`.
- **Splay opens the loop.** Tilting one link out of the planar four-bar's plane
  moves its C off the shared point — rotate the whole linkage instead (see
  `references/kinematic-placement.md`).
- **Coincident ≠ free.** The solved point makes the preview meet; the printed
  joint still needs `+0.2 mm/side` slip in the moving eye over the pin.
