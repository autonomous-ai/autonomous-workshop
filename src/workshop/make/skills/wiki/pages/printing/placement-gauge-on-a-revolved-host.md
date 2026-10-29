---
title: A placement gauge for parts taped to a revolved host
tags: [gauge, jig, placement, locate, taped, adhesive, surface-of-revolution, slot, slide-off]
aliases: [placement jig, positioning gauge, alignment template, taped accessory location, conformal foot rotates freely, gauge slot direction, slide off gauge]
sources:
  - "experience: a strip gauge that set two taped ears at +-36 deg on a flared lamp shade"
related: [knife-edges-and-tapers, fit-derivation, seating-bought-parts]
updated: 2026-10-12
---

# A placement gauge for parts taped to a revolved host

A foot shaped to a surface of revolution (a shade, a dome, a bottle) fixes a
part's tilt and its place along the axis, but not its angle round the axis:
the same foot fits anywhere on the circle. Two parts that must sit symmetric
(ears, handles, fins) then go on by eye unless something locates them. A loose
printed strip lying on the host does it without touching the host's design.

- **Axial stop from the host.** On a cone or a flared shade the strip cannot
  ride over the crest of the rim: end it at the crest and it stops there one
  way and slides off the other way, rearward down the cone, with no lip.
- **Slot direction follows the removal.** Sliding the strip off rearward moves
  each stuck part forward relative to it, so the slots must be open at the
  strip's front edge (an early version opened them rearward and hit both parts
  after 2 mm).
- **Slot size from the swept volume, not the contact layer.** Sliding down a
  cone the strip sweeps every radius up to its front edge's outer radius, so
  clear the whole part inside that cylinder, not just the layer the strip
  touches at rest (the narrower slot collided after 10 mm).
- **Slot walls in planes through the axis** at the part's angular extent plus
  the fit clearance; they locate the angle (±0.5 deg of play here) and stay
  square to the strip ([[knife-edges-and-tapers]]).
- **Prove it with booleans, not a render:** the strip clears the host and both
  parts at rest, clears them at every step of the slide-off, and overlaps a
  part turned ±1 deg round the axis.
- **Projecting a part's footprint:** the convex hull of its edge samples took
  seconds; a union of its tessellated triangles took over 20 minutes.
