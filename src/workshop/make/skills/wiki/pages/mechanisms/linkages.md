---
title: Linkages
tags: [linkage, four-bar, grashof, crank, rocker, coupler, slider-crank, scotch-yoke, dead-centre, walking, kinematics]
aliases: [linkage, bar linkage, crank-rocker, connecting rod, toggle, dead point, walking mechanism, strandbeest]
sources:
  - Norton, Design of Machinery, ch. 2 (Grashof condition) and ch. 4 (position analysis)
  - Theo Jansen, Strandbeest linkage; Klann linkage (US patent 6,260,862)
  - "experience: walkers whose legs were posed once for every phase, and axles driven by one rod"
  - "experience: an eccentric-driven rocker whose pin was placed for a 90 deg mid-swing transmission"
related: [mechanism-design, automata-patterns, mechanism-verification]
updated: 2026-09-28
---

# Linkages

## Four-bar

Links: ground `g` (fixed pivots A→D), crank `a` (A→B), coupler `b` (B→C),
rocker `c` (D→C). Let `s` = shortest, `l` = longest, `p`, `q` the others.

**Grashof condition**: `s + l <= p + q` → at least one link turns fully.

| shortest link | behaviour |
|---|---|
| crank (or rocker) | **crank-rocker** — the usual toy drive: motor/hand turns the crank, the rocker swings |
| ground | **double-crank** (drag link): both side links turn |
| coupler | **double-rocker**: only the coupler turns — useless as a drive |
| `s + l == p + q` | **change-point** (parallelogram, kite): can flip to the other branch at the flat pose — avoid, or guide it through |
| `s + l > p + q` | **triple-rocker**: nothing completes a turn |

Feasibility assert for a driven crank, with margin for FDM clearance:

```python
L = sorted([GROUND, CRANK, COUPLER, ROCKER])
assert CRANK == L[0], "crank must be the shortest link"
assert (L[1] + L[2]) - (L[0] + L[3]) >= 0.5, "not Grashof with 0.5 mm margin"
```

**Rocker swing.** At the two extremes crank and coupler are collinear:
`|DC_ext|` from `|AC| = b + a` and `|AC| = b - a`; the swing angle is the
difference of the rocker angles solved at those two poses.

**Transmission angle** μ (between coupler and rocker) must stay between
~40° and ~140°. Near 0° or 180° the coupler pushes along the rocker's own
length and the linkage stalls or binds. Extremes occur with the crank
collinear with the ground:

```text
cos μ = (b² + c² - (g ∓ a)²) / (2 b c)
```

**Closure at one crank angle** θ: `B = A + a (cos θ, sin θ)`; C is an
intersection of circle(B, b) and circle(D, c). Two solutions = two
**branches** (open / crossed). Pick one and keep it for the whole cycle; if
the circles stop intersecting at some θ the linkage is not a crank-rocker.

### Placing the rocker pin

Given the crank centre O and the rocker pivot D, put the rocker's pin C on the
circle whose diameter is O-D (Thales), at the lever length L from D. There the
coupler O-C is square to the lever D-C when the rocker is mid-swing, so the
transmission angle is 90° in the middle of the stroke and, for a small throw
`a`, stays within about `asin(a / L)` of it at the ends. The coupler length is
`sqrt(OD² - L²)`; cut it to close exactly in the pose the parts are drawn in.

```python
C = thales_point(O, D, L)           # |DC| = L, (C - O) . (C - D) == 0
swing = asin(a / L)                 # each way, small-throw estimate
assert 40 <= min(mu) and max(mu) <= 140   # solved over a full turn
```

**Coupler curves.** A point rigidly on the coupler traces a closed curve —
that curve is what makes a foot walk, a beak peck or a head nod. Design the
output by choosing that point, then check its curve by solving closure over
a full turn.

## Slider-crank

Crank `r`, rod `l`, slider line offset `e`:

```text
sin φ = (r sin θ - e) / l          rod angle
x     = r cos θ + l cos φ          slider position
stroke = √((l + r)² - e²) - √((l - r)² - e²)     (= 2r when e = 0)
```

- `assert l > r + abs(e)`; practically `l >= 3 r` for gentle side load on
  the slider.
- Offset `e ≠ 0` gives a quick return (one stroke faster than the other).
- **Scotch yoke**: pin in a slotted yoke; pure harmonic motion, shortest
  package, but the slot wears and the pin slides.

## Dead centres

A crank driven *through its rod* (slider or coupler pushing the crank) has
two dead centres, where crank and rod are collinear (θ = 0°, 180° in-line).
At a dead centre the crank can go either way. Cures:

- drive the crank itself (motor, hand crank) — then dead centre is only a
  force peak;
- a flywheel to carry through;
- **quartering**: two cranks on the same pair of axles 90° apart (for
  example rods at +45° and -45°), so one is always away from dead centre. An
  axle driven by one rod alone can reverse twice a turn.

```python
d = abs((PHASE_LEFT - PHASE_RIGHT + 180) % 360 - 180)
assert abs(d - 90) <= 20, "coupling rods must be quartered"
```

## Walking linkages

| linkage | links per leg | character |
|---|---|---|
| **crank + guide pin** | 1 leg + crank pin + fixed guide slot/pin | simplest printable walker; leg slides and rotates on the guide; stride ≈ 2 × throw × (foot distance / guide distance) |
| **Jansen** | 8 | flat-bottomed foot path, low lift, many pins |
| **Klann** | 6 | higher step, can climb small obstacles |
| **Chebyshev lambda** | 3 (four-bar) | approximate straight line; good for a single-leg gait |

Gait comes from **phase**, not geometry: a trot puts diagonal legs in phase
(FL 0°, FR 180°, RL 180°, RR 0°). Build every leg in its neutral pose and
place it from its own crank phase; legs built at one pose for every phase
collide with each other and walk a pace, not a trot.

Stance feet must be **lower** than swing feet through mid-stride or the body
rocks instead of walking; set the foot sole so its lowest point lands on
Z = 0 in the reference pose.

Straight-line and toggle linkages (Watt, Chebyshev, Hoecken,
Peaucellier–Lipkin, over-centre latches): [[straight-line-and-toggle-linkages]].

## Solving closure numerically

When a chain is more than one loop (crank pins → links → several hinged
panels), write the constraint as residuals and solve:

- per crank angle, root-find each dependent angle in order with a bracketing
  solver (`brentq` over a grid; take the root nearest the previous pose so
  the branch does not jump);
- links with slack (a loop in a slot) are a range, not a length: solve for
  the shortest length inside `[L, L + slack]` that closes;
- choose the **rest pose** by scanning crank angles and scoring against the
  reference (for example: body level, flattest panels), then assert the rest
  pose closes;
- keep all of this in one algebra-only module (`assemblies/pose.py` or
  `features/kinematics.py`) with 4×4 transforms and `det = +1` asserted.

A linkage posed by hand clashes where the solved one does not: repair a
clash by re-solving the rest pose, never by nudging a part.
