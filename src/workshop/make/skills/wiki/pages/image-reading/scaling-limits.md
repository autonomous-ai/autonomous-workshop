---
title: What breaks when you scale a model
tags: [scale, wall, minimum-feature, bed, overhang, fdm, sanity-check]
aliases: [scaling a spec, scale down, scale up, resize a model, enlarge, minimum wall, sanity gates, print bed fit]
sources:
  - skills/cad/scripts/check_fit and check_thickness (bed and wall gates)
  - "experience: scaled specs whose screw bosses and walls scaled with the body"
  - "experience: a finished mesh-carried toy scaled up twice, whose ledge check failed on facets that scaled with it"
related: [scale-anchors, known-object-sizes, print-in-place-mechanisms, overhangs-and-print-orientation, fdm-minimum-feature-sizes, flexure-materials-and-snap-strain]
updated: 2026-09-28
---

# What breaks when you scale a model

Scaling a spec is not multiplying every number. Run these checks whenever a
scale is chosen or changed, and state each finding.

## Sanity gates before the size table

**Bed fit.** Does the largest dimension exceed the print bed? The default
sanity bound to design to is 200 × 200 × 200 mm; common real beds are 220 mm
(Ender 3 class) and 256 mm (Bambu X1/P1 class). If it does not fit, say so and
name the remedy: scale down, split into parts with a stated joint, or print
diagonally.

**Minimum wall.** At the chosen scale, is any wall thinner than 0.8 mm (2 ×
0.4 mm nozzle)? Walls **do not scale**. A model scaled to half size needs its
walls re-thickened to the same absolute minimum, which changes the proportion
the image showed. Say which walls were thickened and by how much — this is a
visible trade, not a silent fix.

**Minimum feature.** Anything below ~1.5 mm will not survive FDM: thin ribs,
fine engraving, sharp text, small pins. In the image these are often the
details that carry the object's character. Name each one and either
deepen/thicken it, or state that it is dropped.

**Overhang.** From the side view, is any surface more than 45° from vertical?
At the chosen scale, does it bridge more than ~10 mm unsupported? Name the
print orientation that avoids the worst of it.

**Order of magnitude.** Check the number against the object's real-world class
([[scale-anchors#check-the-anchor-against-the-objects-class]]).

## Scales and does not scale

| Scales with the model | Does **not** scale |
|---|---|
| Overall envelope, feature positions, cosmetic radii | Wall thickness (nozzle-bound) |
| Cavity sizes for scaled contents | Clearances and tolerances (printer-bound, ±0.2/0.4 mm) |
| Aesthetic proportions | Fastener sizes (M3 stays M3) |
| | Bearing/magnet/insert seats (the component is a fixed size) |
| | Minimum printable feature (~1.5 mm) |

A model scaled down 50 % with its screw bosses scaled too now has M1.5 bosses
holding M3 screws. Keep component-driven dimensions fixed and let the body
absorb the change.

## Scaling a finished model: build in its own frame, scale last

Every observed datum, cached thinning and layout of a finished model is in
the frame it was designed in. Keep building there, and scale each body by
`k = target / design` about the frame's origin as the last step before it
becomes a solid (a mesh: scale the vertices before sewing, so host and inlay
still share every vertex). A placement worked out in that frame keeps its
rotation and scales its translation by `k`: `R·x + t` becomes `R·(k·x) + k·t`.
Assert the built size against the target, so a later edit that moves the
extreme point cannot leave `k` stale.

A value the printer sets is written in printed mm and taken into the build
frame by dividing by `k`: a fit grown in that frame by `c / k` prints as `c`.
Growing a scaled curve by `c` is the same as scaling the curve grown by `c / k`,
so both halves of the mate still come from one curve.

## Scaling up passes every least and can break every most

A minimum (wall, groove width, tip radius, colour depth) only grows with
`k > 1`, so it holds. A maximum grows too, and fails:

- a ledge's reach (about 1 mm, [[overhangs-and-print-orientation#bridge-ledge-overhang]]),
- an emboss height or engrave depth on a top face (< 0.9 mm, [[fdm-minimum-feature-sizes]]),
- a bridge span (a pocket ceiling doubles with the part).

Judge each at its printed size. Surface detail that was sized to the nozzle
rather than to the look (a groove at the finest a nozzle keeps) is held in
printed mm: the part grows, the detail stays as fine as it was allowed to be,
and a finer reference image is matched more closely rather than less.

A rule judged facet by facet (a downward patch under 1 mm passes as a ledge)
reads the tessellation. A mesh thinned to a tolerance in the design frame has
facets `k` times larger once printed, so a patch of two or three facets over
a groove's end outgrows the rule though the groove did not. Thin any body such
a rule reads at `tol / k` in the design frame.

A gate's volume threshold is absolute too. An interference check that calls
anything under 1 mm³ contact reads the faces an inlay shares with its host as
a small overlap; the reading grows as `k³`, and a pair that stayed under the
threshold at one size is reported as a clash at the other. Settle it with an
exact mesh boolean of the pair (zero to rounding when the inlay was cut from
its host), not by raising the threshold.

## Carried print-in-place gaps and snaps scale with the geometry

A gap between two surfaces of a carried mesh scales by `k`. What the joint
does depends on the gap over the joint's radius, the angle it swings free,
and that ratio does not change: the chain moves as the original does. State
the new absolute gap against the usual 0.20–0.40 mm per side
([[print-in-place-mechanisms#the-gap-is-per-face-and-per-direction]]): larger
prints free more easily and plays more.

A snap's interference δ over a cantilever of thickness `t` and length `L`
strains the arm by about `1.5·δ·t / L²`; scaled by `k` together it is
unchanged, so scale the interference with the snap rather than holding it
([[flexure-materials-and-snap-strain#snap-fit-strain]]). Hold it only when the arm is held too.
