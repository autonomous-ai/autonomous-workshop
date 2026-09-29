---
title: NURBS and B-spline basics
tags: [nurbs, bspline, spline, knot, degree, continuity, surface, curve]
aliases: [b-spline, knot vector, control points, G1 continuity, G2 continuity, curvature continuity, rational spline, bezier]
sources:
  - https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline
  - https://occt3d.com/dev/doc/refman/html/class_shape_upgrade___unify_same_domain.html
related: [bspline-height-fields, loft-pitfalls, loft-organic-bodies, kernel-validity]
updated: 2026-09-23
---

# NURBS and B-spline basics

Every loft, sweep and freeform face in the kernel is a B-spline or NURBS
surface. Knowing the handful of terms below explains why a loft ripples, why a
fitted surface overshoots, and why two faces meet with a visible crease.

## Degree, order, control points, knots

- **Order = degree + 1.** A cubic curve has degree 3 and order 4.
- **knots = control points + order.** Five control points of a cubic
  (order 4) need 9 knots.
- **Clamped (open) knot vectors** repeat the first and last knots `order`
  times, so the curve starts and ends exactly on its first and last control
  points. This is the usual form in CAD.
- **Local support:** moving one control point changes only the spans where it
  is active. A spline edit is local; a global polynomial's is not.
- **Knot multiplicity lowers smoothness:** each repeat of an interior knot
  drops one level of continuity there. Enough repeats create a corner in an
  otherwise smooth curve.
- **Rational (the R in NURBS):** weights let the curve represent conics,
  including the circle, *exactly*. A non-rational B-spline only approximates a
  circle. So a spline "circle" from a fit is not a true cylinder, and
  cylindrical-face selectors will not find it.

A control polygon is not the curve: an interpolating fit passes *through*
data points and can overshoot between them. Using the data as the control
net instead bounds the surface by the net ([[bspline-height-fields]]).

## Continuity: C versus G

| level | parametric (C) | geometric (G) | you see |
|---|---|---|---|
| 0 | positions meet | positions meet | a crease is possible |
| 1 | first derivatives equal | tangent directions equal | no crease; a reflection line kinks |
| 2 | second derivatives equal | curvature equal | reflection lines flow smoothly ("class A") |

C0/C1 and G0/G1 are, for practical purposes, the same thing. G is the looser
(shape-only) form of each condition. Two consequences in CAD:

- **Lofted segments that only meet at a section are G0** there unless the
  tangents are controlled. The seam shows in shaded renders, which is one reason
  the organic-body rule makes segments *overlap* rather than meet
  ([[loft-organic-bodies#consecutive-segments-must-overlap-not-meet]]).
- **Kernel requirements are stated in C:** boolean arguments need at least C1
  geometry ([[occt-topology-and-tolerance#what-a-boolean-argument-must-be]]),
  and `UnifySameDomain(ConcatBSplines=true)` joins edges only where they meet
  with C1 continuity.

## Practical rules

- Prefer the lowest degree that gives the needed smoothness. Degree 3 is the
  CAD default, and high degrees ring.
- Fewer, well-placed sections beat many noisy ones: every section adds knots,
  and noise between sections becomes ripple ([[loft-pitfalls]]).
- Bounding boxes of spline faces are computed from the control hull and
  over-report ([[kernel-validity#bounding-boxes-over-report-on-b-spline-faces]]).
- A spline face whose control net folds over itself is a self-intersecting
  face. It is valid to `BRepCheck_Analyzer` and invalid to the BOP check.
