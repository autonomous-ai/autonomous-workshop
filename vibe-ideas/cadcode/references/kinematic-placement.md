# Kinematic placement — closing a linkage loop

**Trigger:** load when the design is a **mechanism** — parts that share a
moving joint or form a closed loop: a four-bar/Hoeken/Klann/Jansen walking leg,
a crank + coupler + rocker, a scissor lift, a pantograph, a steering linkage,
windscreen-wiper arms, a robot leg/arm with pinned links. Any time two printed
parts are pinned together at a joint and that joint's position depends on the
mechanism's geometry rather than a fixed offset.

This is the kinematic companion to `references/assembly.md`. Assembly covers
**static** placement — put the lid `gap` above the base, the wheel on the axle.
A mechanism adds one hard constraint static placement doesn't: **a shared joint
must land on the same point for every part that meets there.** Solve for that
point; don't pose each part by eye.

## Why this exists

The most common mechanism defect is each link placed by its **own eyeballed
angle**. The leg is "splayed 30° and hung down"; the rocker is "tilted 45°
forward"; both look plausible alone. But the joint they share (call it **C**)
ends up in two different places — the leg puts it here, the rocker puts it
there — so the two parts never touch. `scripts/cad` then reports
`disconnected_bodies` ("part is N separate solids"), and the preview shows a
tangle of links hanging in space instead of a connected mechanism.

A four-bar is over-determined for a guess and exactly-determined for a solve:
once the two anchored pins (crank pin **B**, ground pivot **D**) and the two
link lengths are fixed, **C is forced** — it's where the coupler circle and the
rocker circle cross. There is nothing to eyeball.

## The one rule

> **A shared joint is ONE point, computed once, used by BOTH parts.**

Never give each link its own guessed rotation. Solve the loop for the joint,
then place every link *by its joints* — the link's pose is whatever makes its
two pins sit on their two solved points. Use the helper:

## Use the helper

`cadlib.kinematics` owns the loop-closure math — import it, don't re-derive
circle intersections inline (that's the step the eyeballing skips).

```python
from cadlib.kinematics import solve_fourbar, place_two_point
```

- `solve_fourbar(*, crank_pin, ground_pivot, coupler, rocker, branch="left") -> (u, v)`
  returns the moving joint **C** in the mechanism's 2-D working plane.
- `place_two_point(part, *, p0_local, p1_local, p0_world, p1_world, roll_deg=0.0)`
  poses a link so its two named local points land on two world points — returns
  a new `cq.Workplane`.
- `circle_intersections(*, c0, r0, c1, r1)` is the raw kernel for non-four-bar
  loops (give it the two pinned centres and the two link lengths).

All three raise `ValueError` when the links can't reach (centre distance
> `coupler + rocker`, or one circle inside the other) — a wrong link length
surfaces as a clear message, not an OCCT crash.

## Workflow

1. **Build each link in its local frame** with its joint centres at known
   coords. Convention: put one joint at the origin and the next along local +X
   (e.g. a coupler-leg: eye at `(0,0,0)`, C-pin at `(coupler, 0, 0)`, foot
   beyond it; a rocker: D at `(0,0,0)`, C at `(rocker, 0, 0)`).
2. **Anchor the fixed pins from params**, not from guesses. The crank pin **B**
   is the eccentric/journal position (crank axis + throw at the crank angle);
   the ground pivot **D** is a fixed post on the chassis. These come straight
   from your `params.py` and the chassis geometry.
3. **Solve the moving joint** in the plane the mechanism moves in:
   `C = solve_fourbar(crank_pin=B, ground_pivot=D, coupler=Lc, rocker=Lr)`.
4. **Place each link by its joints:** the leg by `(B, C)`, the rocker by
   `(D, C)` — both with `place_two_point`. They now meet at C by construction.
5. **Verify connectivity:** `assert len(asm_union.solids().vals()) == 1` for a
   pinned pair, and confirm `scripts/cad` reports **no** `disconnected_bodies`
   warning. (In a `cq.Assembly` the links stay separate solids on purpose —
   check coincidence by unioning a test copy, or compare the two parts'
   C-points: `solve_fourbar` guarantees they're equal.)

## Mechanism-frame discipline

`solve_fourbar` is **2-D**: pick the plane the linkage moves in and map its two
axes to the `(u, v)` tuple. A walker's legs swing fore-aft, so the plane is the
**X–Z sagittal plane** (`u = X`, `v = Z`), one plane per leg station along Y.
Solve in `(X, Z)`, then lift back to 3-D — `w = lambda p: (p[0], y_station, p[1])`
— and hand the 3-D points to `place_two_point`, which carries the out-of-plane
Y offset for free.

A **planar four-bar forces B and D into the same plane.** That's the catch that
breaks naive "splay": tilting just the leg out of the loop plane (to fan the
feet outward insect-style) moves its C off the rocker's C — the loop opens. If
you want real outward splay, rotate the **whole** solved linkage (leg *and*
rocker together, about a fore-aft axis through B and D) — or angle the chassis
D-post so D leaves the plane too and re-solve in the tilted plane. Splaying one
link alone is the bug, not the feature.

## Worked example — one Hoeken leg + rocker

```python
import cadquery as cq
from cadlib.kinematics import solve_fourbar, place_two_point

COUPLER, ROCKER = 20.0, 20.0
B = (8.0, -13.0)      # crank pin (eccentric journal) in X–Z, at this crank angle
D = (-16.0, -13.0)    # chassis ground pivot in X–Z
C = solve_fourbar(crank_pin=B, ground_pivot=D,
                  coupler=COUPLER, rocker=ROCKER, branch="right")

w = lambda p: (p[0], 0.0, p[1])        # X–Z plane at one Y station -> 3-D

# leg built along local +X: eye at origin, C-pin at (COUPLER,0,0), foot beyond
leg = place_two_point(make_leg(),
                      p0_local=(0, 0, 0), p1_local=(COUPLER, 0, 0),
                      p0_world=w(B), p1_world=w(C))
# rocker built along local +X: D at origin, C-pin at (ROCKER,0,0)
rk  = place_two_point(make_rocker(),
                      p0_local=(0, 0, 0), p1_local=(ROCKER, 0, 0),
                      p0_world=w(D), p1_world=w(C))
# leg and rocker now share the pin at C — one connected mechanism.
```

For a multi-station gait, loop over the stations with each crank phase to get
that station's **B**, solve its **C**, and place that station's leg + rocker —
same five steps, once per leg.

## Pitfalls

- **Eyeballing the angle.** "Splay 30°, tilt 45°" is the defect, not a starting
  point. Solve C; the angle is an output, never an input.
- **Placing each link independently.** If the leg and the rocker each compute
  their own C, they won't match. Solve C **once**, place both from it.
- **Trusting `union` to connect them.** `a.union(b)` fuses only solids that
  overlap; links whose pins miss stay two solids. Give each pinned end a boss
  that overlaps its mate at the joint, and check `len(solids().vals()) == 1`.
- **Splaying one link out of the loop plane.** Moves its joint off the shared
  point and opens the loop. Rotate the whole linkage, or re-solve in the tilted
  plane.
- **Wrong elbow branch.** Two valid C's exist (`branch="left"` / `"right"`). If
  the foot points up or the linkage folds the wrong way, flip the branch —
  don't add a corrective tilt.
- **Forgetting joint clearance.** The solved point makes the *preview* meet, but
  a real pin needs slip: bore the moving eye `+0.2 mm/side` over the pin
  (`leg_eye_bore` vs `ecc_dia`). Coincident centres in CAD ≠ a free-moving joint
  in the print.
- **Links that can't reach.** A `ValueError` from `solve_fourbar` means the link
  lengths can't span B–D at this crank angle — fix the lengths or the pivot
  spacing; don't catch and force a pose.
