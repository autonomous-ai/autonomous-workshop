---
title: Inflated (puffy) forms
tags: [inflated, puffy, balloon, pillow, poisson, membrane, level-set, loft, organic]
aliases: [puffy star, puffy heart, balloon form, balloon shape, pillow shape, inflated shape, cushion form, squishy look, swollen form, inflate a 2d outline]
sources:
  - "physics: a membrane under uniform pressure p and tension T satisfies T * Laplace(w) = -p with w = 0 on its rim (small-deflection membrane equation; the same Poisson problem as Prandtl's torsion stress function)"
  - "experience: inward offsets of a five-point star with an elliptical edge roll left a ridge along each arm; the pressure-field form had none and lofted in 2 s"
  - "toolchain: build123d 0.11 Solid.make_loft through 28 level-set splines, OCP 7.9"
  - "experience: a cloud outline (puffs on a pill) failed the polar grid's monotone check from every trial centre; spheroid puffs on a lofted pill built in 2 s"
related: [loft-pitfalls, loft-organic-bodies, product-aesthetics, fillet-chamfer-pitfalls, printed-part-count]
updated: 2026-10-05
---

# Inflated (puffy) forms

A puffy star or heart is a 2D outline blown up like a balloon: the
centre swells most, narrow lobes swell less, and the edge rolls under with no
crease anywhere. Two constructions look right in a sketch and wrong in a
render; one works.

## Inflate with a pressure field, not with offsets

- **Inward offsets crease.** Lofting offsets of the outline along an elliptical
  edge roll gives a crisp pillow wherever the region is wider than the roll,
  but where a lobe is narrower (every star arm near its tip) the offsets from
  both sides meet on the medial axis at an angle: a roof ridge along the arm.
  Past the tip rounding radius the offset tips also turn sharp.
- **A flat slab with a big fillet** reads as a cookie, and OCC refuses a fillet
  larger than a convex corner's plan radius.
- **Solve the membrane.** Solve `Laplace(u) = -1` inside the outline with
  `u = 0` on it (a membrane under pressure) and set `z = T * (u / u_max) ** p`.
  The surface is smooth everywhere, its rim meets the base plane with a
  vertical tangent for any `p < 1`, and narrow regions get small `u`, so tips
  come out thinner than the middle with no ridge.
- `p = 0.5` gives an elliptical edge and thin, pinched tips (about a quarter
  of the centre thickness on a fat star). `p = 0.33` keeps the tips chunky;
  smaller still squares the edge off.

## Solve it on a normalised polar grid

For a star-shaped outline `r = R(theta)`, map `rho = r / R(theta)`: the outline
becomes exactly `rho = 1`, so no staircase boundary feeds noise into the low
contours (a Cartesian grid does, and the first stations wobble at grid pitch).
With `q = R'/R`:

```text
R^2 Laplace(u) = (1 + q^2) u_rr + (1 + q^2 - q') u_r / rho - (2 q / rho) u_rt + u_tt / rho^2
```

- Take `R`, `R'`, `R''` spectrally from the sampled outline with a gentle
  low-pass so polygonisation noise does not reach `q'`.
- The centre is one node: `sum_j (u_1j - u_0) / h_j^2 = -M / 4` (the average of
  directional second derivatives over `M` spokes is half the Laplacian).
- Check that `u` falls monotonically along every spoke; then every level set
  is star-shaped and can be read per spoke by a 1D root find.
- A harmonic series (`r^n cos(n theta)` plus `-r^2/4`) is not a substitute: on
  a star it converges slowly at the tips and left 0.2 mm wobble at `n = 80`.

160 rings by 720 spokes solves in about a second with a sparse direct solver.

## Loft through the level sets

- Stations at equal steps of `phi` along `z = T sin(phi)` are evenly spaced in
  arc length along the profile, so a smooth loft does not overshoot (check
  `bbox.max.Z <= T`). 28 stations matched the field to 0.0004 mm.
- Sample every station at the same spoke angles: the angle is the rail
  ([[loft-pitfalls#sections-match-by-index]]), and give every station the
  same spline parameters
  ([[loft-pitfalls#sections-need-one-parametrisation-or-the-knots-multiply]]).
- Start the periodic splines at an angle another body covers (where a stick
  or handle joins) so the loft seam hides.
- End at `phi` near 86 degrees with a small planar cap; it is flat to a
  hundredth of a millimetre and invisible. A vertex end puckers
  ([[loft-pitfalls#closing-a-loft-a-vertex-puckers-a-fused-cap-poisons]]).
- A faceted shading ring near the crown in a render is tessellation, not the
  surface; measure the surface against the field before chasing it.

## A cloud is not star-shaped: build it from puffs

The polar grid needs one centre from which `u` falls along every spoke. A
cloud — puffs along a long base — has none: 126 trial centres over one cloud
outline all failed the monotone check. Build it the way 3D weather icons are:

- **A pill for the base**, lofted through stadium sections whose inset follows
  a quarter ellipse (`inset = w (1 - cos t)`, `z = H sin t`): vertical at the
  outline, level on top. A filleted slab reads as a plate.
- **A half spheroid per puff** (`scale(Sphere(r), by=(1, 1, h / r))` split at
  z = 0), its crown `h` growing with `sqrt(r)` so big puffs stand tallest.
  Each meets its footprint with a vertical tangent, like the pill, and the
  creases where puffs meet are where a real cloud has them.
- **Every puff must own a stretch of the outline.** A puff wholly inside the
  footprint reads as a bubble on a plate, ringed by its crease.
- Build the plan face from the same circles and stadium (`Circle`,
  `SlotCenterToCenter`) so the dome's base and the flat parts under it are
  flush; the valleys between puffs stay crisp, which OCC chamfers and tapers
  refuse ([[operation-families#tapered-extrude]]).

## Split and print

Build one half (`z >= 0`) and mirror it. The split lands on the equator,
where the rim is vertical, so each half prints split face down with no
supports, the domes are top surfaces, and the seam sits on the silhouette
edge. A rod or handle unions on and blends with an ordinary `fillet` on the
intersection edges (found by testing which edges lie on the rod's surface);
a 2 mm blend worked on the lofted skin.
