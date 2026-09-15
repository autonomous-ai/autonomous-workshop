# What a B-rep can and cannot give back

Reference for judging a recovery request before starting work.

## Surface kinds and what each one proves

| Face kind in STEP | Recovered exactly | Reads as |
|---|---|---|
| plane | origin, normal | a flat wall, a cap, a sketch plane |
| cylinder | axis, radius, angular span | a bore when it faces inward and closes 360°, a boss when it faces outward, an arc wall when partial |
| cone | axis, half-angle, reference radius | 45° half-angle is a chamfer; 35–45° a countersink; anything else a deliberate taper |
| torus | axis, major and minor radius | a fillet, minor radius **is** the fillet radius |
| sphere | centre, radius | a ball end or a spherical dish |
| bspline / bezier | control net only | a loft, sweep, or organic surface — approximable, never exact |
| surface of revolution / extrusion | the generating curve | a revolve or sweep whose profile survives but whose construction does not |

A part built only from the first five rows can be reproduced to kernel
precision. One spline face anywhere means the answer is now "close", and the
size of "close" has to be measured, not assumed.

## Signals worth reading out of the fact sheet

- **Coaxial bores of differing radius** — a counterbore or a stepped bore, one
  feature, not two.
- **Concentric partial arcs sharing a centre** — an arc slot or arch; the
  radius difference is the wall thickness.
- **A 180° cylindrical band** — the part is half of a mirrored pair and the
  bore is cut at the seam. Whether it faces inward is unreliable there; check
  the mating half before calling it a hole.
- **Two parallel planes with the same normal** — their separation is a wall
  thickness, and it is usually a named constant in the lost source.
- **Equal-area disjoint rings in one section** — separate islands to union,
  not holes to subtract.

## What is gone regardless of surface quality

Recovering geometry perfectly still loses the program:

- **Parameter names.** `27.0`, never `WHEEL_RADIUS`.
- **Derived relations.** `SUPPORT_INNER + SUPPORT_THICKNESS` collapses to a
  literal, so the two no longer move together.
- **Fit intent.** A Ø3.5 bore does not say it was `slot_for(3.0, 0.25)`; the
  clearance and the shaft it mates with are unrecoverable.
- **Boolean decomposition.** Booleans are destructive. Many different
  fuse/cut sequences produce the identical solid, and the solid does not
  record which one ran.
- **Feature order.** Whether a fillet was applied before or after a cut is not
  in the result, and the two orders can give different shapes elsewhere.
- **Module structure and reuse.** One builder called twice with a mirror comes
  back as two unrelated scripts with duplicate geometry.

This is why the honest summary is two numbers, not one: geometric match, and
the fact that the parametric model is not recovered at all.

## When to stop and re-model instead

Re-model rather than recover when any of these hold:

- The analytic fraction is below roughly 90% — too much of the shape is spline.
- No single extrusion direction exists and the shape is not a simple revolve.
- The user's actual goal is to *change* a dimension. A recovered file makes
  that harder than a clean re-model, because every relation must be rebuilt by
  hand anyway.
- The original source still exists. Recovery is for when it does not.
