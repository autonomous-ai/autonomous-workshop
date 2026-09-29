---
title: Straight-line and toggle linkages
tags: [straight-line, watt, chebyshev, hoecken, peaucellier, toggle, over-center, mechanical-advantage, linkage]
aliases: [watt linkage, chebyshev linkage, hoecken linkage, peaucellier-lipkin, inversor, toggle clamp, over-centre latch, knee joint, approximate straight line]
sources:
  - https://en.wikipedia.org/wiki/Watt%27s_linkage (geometry, lemniscate path, suspension use)
  - https://en.wikipedia.org/wiki/Chebyshev_linkage (ground 4a, side links 5a, coupler 2a, midpoint traces the line)
  - https://en.wikipedia.org/wiki/Hoecken_linkage (crank a, ground 2a, cognate of Chebyshev)
  - https://en.wikipedia.org/wiki/Peaucellier%E2%80%93Lipkin_linkage (six bars, inversion OB·OD = k², exact straight line)
  - https://www.firgelliauto.com/blogs/mechanisms/toggle-mechanism (F_out = F_in / (2 tan theta), 3-7 deg working range, over-centre lock 1-3 deg, tolerance sensitivity)
related: [linkages, automata-patterns, joints, mechanism-verification]
updated: 2026-09-23
---

# Straight-line and toggle linkages

Both families exploit special positions of four-bar-like chains
([[linkages#four-bar]]). A straight-line linkage guides a point along a line
using pins only, with no slide to wear or jam. A toggle multiplies force as
two links approach collinear.

## Approximate straight-line four-bars

| linkage | proportions | straight-line point | path |
|---|---|---|---|
| **Watt** | two equal long arms pivoted on opposite sides, joined by a shorter coupler | coupler midpoint | nearly straight near mid-travel, perpendicular to the line between the fixed pivots; the full path is a figure-eight lemniscate |
| **Chebyshev** | ground 4a, both side links 5a, coupler 2a (crossed) | coupler midpoint | nearly straight, parallel to the ground line; input angle kept roughly between 36.9° and 101.5° |
| **Hoecken** | crank a, ground 2a, a cognate of Chebyshev | a point on the extended coupler | nearly straight over part of the cycle, at a nearly constant speed |

Use: guide a push rod or a slider without a slot, or make a walking foot's
flat stance phase ([[linkages#walking-linkages]]). All are **approximate**:
solve closure numerically and measure the deviation from the line over the
stroke you use. Assert it stays under the running clearance.

```python
dev = max(abs(y(theta) - Y_LINE) for theta in stroke_samples)   # from the closure solution
assert dev <= CLEAR_MIN, f"straight-line error {dev:.2f} mm exceeds the running gap"
```

## Exact: Peaucellier–Lipkin

Six bars: two equal links `OA = OC` from a fixed pivot `O` to a rhombus
`ABCD`, with point `B` driven on a circle **through O** by a seventh link.
`O`, `B` and `D` stay collinear and `OB · OD = k²`, so `D` is the inverse of
`B` and traces an exact straight line. If `B`'s circle misses `O`, `D` traces a
circular arc instead. Historically this was the first planar linkage to make
exact straight-line motion from rotation (1864). It has many pins, so pin
clearance adds up: each printed pin's running fit adds slop to the output.

## Toggle mechanisms

Two links meet at a knee. As the knee angle `θ`, measured from the straight
(180°) dead-centre position, shrinks, the output force grows:

```text
F_out = F_in / (2 · tan θ)
```

| θ | F_out / F_in |
|---|---|
| 10° | ≈ 2.8 |
| 5° | ≈ 5.7 |
| 1° | ≈ 28 |

- The working sweet spot is about 3–7°. Near 0° the gain is swamped by
  elastic deflection, pin clearance and frame stretch: a 0.2° error at
  θ = 1° shifts the force by 20 %.
- **Over-centre lock**: push the knee 1–3° past straight onto a fixed stop and
  the clamp holds itself (toggle clamps, latches, folding legs). Loose knee
  pins let it creep back out under vibration.
- A toggle is the four-bar's dead centre used on purpose. In a drive chain the
  same position is a stall ([[linkages#dead-centres]]).

```python
import math
assert TOGGLE_OVERTRAVEL_DEG >= 1.0 and HAS_STOP, "over-centre latch needs overtravel and a hard stop"
```

## Checks

- Asserts: straight-line deviation under the running gap over the used
  stroke; toggle overtravel onto a modelled stop.
- Motion: sweep the linkage from its closure solution. For a toggle latch,
  add a `blocked` condition that tries to push the latch open against its
  stop, and a `clear` condition for the release path
  ([[mechanism-verification#4-what-the-manifest-must-contain]]).
- Open items: the clamp force and the force needed to release it depend on
  compliance, which a rigid gate cannot measure.
