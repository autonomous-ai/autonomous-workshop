---
title: Height-field solids and cutters revolved from sampled points
tags: [height-field, b-spline, surface, slab, intersect, revolve, spline, sampling, cutter, distance]
aliases: [height field solid, pillow insert, planar facets, pyramid shell, surface to solid, split by surface returned nothing, soft facets, soft minimum crease, revolved envelope, sampled meridian, polyline revolve sliver, negative area face, distance_to returned zero]
sources:
  - "experience: a B-spline height-field insert with soft-blended facets, and a shade envelope revolved from a STEP meridian used as a cutter"
related: [freeform-surfaces-in-build123d, revolve-seam, fuse-pitfalls, kernel-validity]
updated: 2026-10-13
---

# Height-field solids and cutters revolved from sampled points

Two ways to make a solid from numbers rather than from sketches, and the traps
each set: a face whose height is a function over an outline, and a cutter
revolved from a surface read off a STEP.

## A height-field solid: slab the surface, then intersect

A face whose height is a function over a 2D outline (a soft faceted insert, a
domed badge) is a `make_surface_from_array_of_points` grid over the outline's
bounding box, with heights defined everywhere (clip the function rather than
leaving holes). Turning it into a solid: `split(prism, bisect_by=surface)`
returned **no solid** here; extruding the surface into a slab and intersecting
it with the outline's prism worked first time:

```python
prism = extrude(outline_face, base + rise + 2, dir=(0, 0, 1))
under = extrude(surface, amount=base + rise + 4, dir=(0, 0, -1))
part = prism & under
```

For "facets, but soft", choose the blend so that it stays local to the creases:

- **A log-sum-exp soft minimum,** `-log(sum(exp(-k * f_i))) / k`, is not local.
  Every point drops by up to `ln(n)/k` of the rise, so each facet bows and the
  peak rounds over. A user read this as "puffed, like a pillow".
- **Planar facets with small crease fillets** (a `Shell` pyramid, then `fillet`
  on the edges meeting at the apex) stay flat. At 0.8 mm they read as hard, and
  fillets of 1.5 mm and more failed.
- **A polynomial smooth minimum is local:**
  `h = clip(0.5 + 0.5 (b - a) / k, 0, 1)`, `smin = b + (a - b) h - k h (1 - h)`,
  applied pairwise to the facet heights in mm. It equals the hard minimum
  wherever the facets differ in height by more than `k`, so the facets stay
  flat away from the creases.
  - `k` is a height. The band it rounds is about `k / (slope difference)` wide
    in plan, so on shallow facets a small `k` already rounds a wide band.
    Size `k` from the band you want.
  - Check the result as the share of the facet area where the blend equals the
    hard minimum. One build left a quarter of each facet planar and a reviewer
    read it as a mound; flat facets with soft ridges kept about three quarters
    planar.
  - Roll the edge the same way: `smin(u, rise * d / w, k_edge)`, where `d` is
    the signed distance to the outline (`shapely.distance` on vectorized points).
  - Floor it with a smooth maximum, `-smin(-u, 0, k)`, never `clip`. A clip's
    kink makes the B-spline fit ripple along the floor, about 0.15 mm here.
  - Measure the fitted face against the function between the grid samples (ray
    hits). Streaks in a shaded render can be the renderer's tessellation; render
    with a finer tolerance before blaming the surface.
  - The blends lower the peak; raise the nominal rise to make up the measured
    drop.
  - A steep roll right at the outline leaves a feather edge that the slicer
    drops. Start the roll inside a flat land about 0.5 mm wide, and keep the fit
    grid fine enough to resolve it: at 0.42 mm spacing the fit overshot 0.04 mm
    at the land, and at 0.28 mm it did not.
  - Do not read a height field's highest point from a bounding box. A B-spline
    face's box follows its control net, even with `optimal=True`, and read
    0.9 mm high here. Use the maximum Z of a fine tessellation, or ray hits.

If the concept sets a part into a frame (a step down to its edge), copy that step
too. It reads as "recessed" even when the part's face rises.

## Keep a height field's edge out of a neighbour's plane

An insert whose height field starts at exactly the frame's face plane (edge
"flush") meets that plane tangentially along its whole rim. Every boolean
between the two then failed silently once the insert moved sideways: the common
volume came back as the **whole insert** in two directions and **zero** in the
other two, while a plain prism of the same outline gave the right 3-13 mm³ and
a slide square to the face gave the right 110 mm³. Changing the surface's fit
tolerance only changed which directions lied. Lifting the edge 0.2 mm proud
(and seating the insert on a 0.1 mm glue gap rather than on the pocket floor)
made every slide sane. Two checks catch it before a motion gate does:

- a 0.4 mm slide into each wall must overlap a little (0.5-100 mm³ here), never
  zero and never the whole part;
- the left and right slides of a mirrored pair must agree.

A `check_motion` "blocked" result on such a part is not evidence either way
until that check passes: the gate's sweep uses the same booleans.

## A revolved cutter from sampled points: spline it, sample densely

A host surface read by sectioning a STEP and revolved into a cutter has two
traps. Sample every section edge by length (every 0.05 mm, not a fixed count
per edge): with 80 samples on a 50 mm edge, a 0.4 mm z-bin missed the outer skin
and read the radius 0.3 mm low, and the part touched the host it should have
cleared. And revolve **one spline** through the samples, not a polyline: a
revolved polyline makes one cone per segment, the cut left a face of negative
area, and `distance_to` then returned 0 at a point nowhere near either solid.
