---
title: Form class to operation family
tags: [build123d, extrude, taper, revolve, loft, sweep, sketch, operation, form-class]
aliases: [construction family, base solid, which operation, extrude or loft, prismatic, axisymmetric]
sources:
  - skills/image-to-cad/references/build123d-operations.md (before the move; snippets executed on build123d 0.11 / cadgen 0.4.19)
  - skills/image-to-cad/scripts/measure_image.py (row_shape, col_shape, fill_ratio, symmetry signals)
  - "experience: taper extrude of a 550-point spline disc outline did not finish in minutes; the normal-offset ruled loft built in 8 s"
related: [construction-strategy, feature-recipes, loft-pitfalls, revolve-seam, fillet-chamfer-pitfalls, sweeps-and-helices]
updated: 2026-10-06
---

# Form class to operation family

Diagnose the base solid's family from the image and from `measure_image.py`'s
`row_shape`/`col_shape`, then use the family's call. Every snippet was executed
against build123d 0.11 / cadgen 0.4.19. A correct operation run on the wrong
plane or selector compiles, yields a valid solid, and puts the feature in the
wrong face — so name the frame with the call ([[build123d-selectors]]).

## Prismatic

Constant cross-section: the section does not change along the length. Boxes,
trays, brackets, plates, extruded profiles.

```python
body = Box(p.width, p.depth, p.height)          # algebra mode, centred

with BuildPart() as bp:                          # builder mode, non-trivial outline
    with BuildSketch():
        Polygon((0, 0), (p.width, 0), (p.width, p.height), (0, p.height * 0.6))
    extrude(amount=p.depth)
body = bp.part
```

**Signal:** `row_shape: flat` and `col_shape: flat`, `fill_ratio` near 1.0.
**Risk:** none — this is the cheapest family. The risk is choosing it when the
form is *not* prismatic.

## Tapered extrude

Constant section, uniform draft: one angle, section shape unchanged. Stacking
bins, nesting cups, moulded housings.

```python
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(p.base_w, p.base_d)
    extrude(amount=p.height, taper=p.draft_deg)
```

**Signal:** `row_shape: wide_start` or `wide_end`, straight silhouette edges.
**Risk:** `taper` applies the same angle to every side. If one face is vertical
and the opposite face leans, this is a **loft**, not a taper.

**Risk:** `extrude(taper=)` offsets the outline. On a periodic spline outline
it ran for minutes; on a face of arcs that meet at a sharp concave valley (a
cloud's puffs) it returned a null shape, and `fillet`/`chamfer` on the same
edges failed too. For a bevel band, loft (ruled) from the outline to the same
samples moved in along their normals by the bevel, both splines on one
parameter list; it built in seconds. Every convex radius must exceed the
bevel. For a bed edge on such a face, cut a one-layer inset ring instead:
`face - offset(face, -d, kind=Kind.ARC)`, which handles the valleys.

## Revolve

Rotationally symmetric: vases, knobs, bottles, domes, pulleys, anything turned
on a lathe.

```python
with BuildPart() as bp:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline((0, 0), (p.base_r, 0), (p.max_r, p.waist_z),
                     (p.neck_r, p.height), (0, p.height), close=True)
        make_face()
    revolve(axis=Axis.Z)
```

**Signal:** front and side silhouettes match; `symmetry.left_right` > 0.95; any
horizontal feature reads as an ellipse; `row_shape` is `waisted` or `bulged`.
**Risk:** the profile must **touch the axis** and be closed, or the revolve
produces a ring instead of a solid. A 360° revolve also leaves a seam edge at
+X ([[revolve-seam]]).

## Loft

The section changes along the length: fuselages, hulls, swooshes, sculpted
grips, handles, tapering bodies whose section *shape* (not just size) evolves.
**This is the family most often skipped and most often needed.**

```python
def section_at(t: float, p) -> list[tuple[float, float]]:
    """One station, sampled on fixed rails. Same point count at every t."""
    ...

wires = [
    Wire([Edge.make_spline(
        [Vector(p.length * t, y, z) for (y, z) in section_at(t, p)],
        periodic=True)])
    for t in stations
]
body = Solid.make_loft(wires, True)      # True == ruled
```

**Signal:** `row_shape: irregular`, or `row_bands` showing three or more
distinct bands, or a visibly double-curved surface.

Rules that keep it buildable:

- **One `section_at(t)` helper**, parameter-driven. Never hand-place N
  unrelated wires — that is how the next edit becomes impossible.
- **Stations at curvature events** when they are sparse: nose, widest point,
  waist, tail. `row_bands` boundaries are your station list.
- Sample on rails, interpolate with PCHIP, prefer ruled and dense — the
  reasons are in [[loft-pitfalls]].

**Risk:** twisted loft from index-mismatched sections; overshoot from a smooth
loft; a loft that fails to close if the first or last station is degenerate.
If a station must be a point, use a very small finite section instead.

## Sweep

Constant-ish section along a curved path: tubes, rails, straps, handles that
follow a curve, cable guards, pipe runs.

```python
with BuildPart() as bp:
    with BuildLine():
        Spline((0, 0, 0), (p.mid_x, 0, p.mid_z), (p.end_x, 0, p.end_z))
    with BuildSketch(Plane.YZ):
        Circle(p.tube_r)
    sweep(is_frenet=True)
```

**Signal:** a recognisable constant profile visibly following a curve.
**Risk:** without `is_frenet=True` the section can rotate unpredictably along
the path. A path whose radius is tighter than the section is wide will
self-intersect and fail. For a **planar arch** — a roll hoop, a handle, a bail
— a band between two concentric ellipses extruded along the third axis is far
more robust than a sweep, and lands its feet exactly where you put them.

Measured sweep behaviour — profile placement, `is_frenet`, the default
transition dropping material at corners: [[sweeps-and-helices]].

## Sketch-driven

Any outline you would draw with a pencil. Reach for `BuildSketch` whenever the
2D outline is non-trivial: rounded slots, mixed arcs and lines, outlines with
internal cut-outs, profiles that need 2D fillets before extrusion.

```python
with BuildPart() as bp:
    with BuildSketch() as sk:
        Rectangle(p.width, p.height)
        fillet(sk.vertices(), p.corner_r)      # corners FIRST
        Circle(p.hole_r, mode=Mode.SUBTRACT)   # then the hole
    extrude(amount=p.thickness)
```

**The order is the opposite of the 3D rule.** In 3D you fillet last; in a
sketch you fillet **before** the boolean ([[fillet-chamfer-pitfalls#sketch-fillets-go-before-the-boolean]]).
A 2D fillet on the sketch always succeeds where an equivalent 3D fillet on the
extruded solid may fail, so when a corner radius is part of the *profile*, put
it in the sketch. Sketch algebra has its own traps:
[[sketch-and-extrude-direction]].

**Round every corner of a star or snowflake outline with offsets, not vertex
picks.** `offset(face, -r, kind=Kind.ARC)` then `offset(+r)` — an opening —
rounds every convex corner to `r`; `+r` then `-r` — a closing — rounds every
concave one. Both return exact lines and arcs (a six-armed, twelve-branched
outline came back as 145 line and arc edges in hundredths of a second), and an
outline whose every arc is larger than the round still takes a small 3D fillet
on its extruded top edges. **An opening erases anything narrower than `2r`:**
a 3.6 mm hanging-loop ring vanished under a 2.3 mm opening. Fuse such features
after the opening, then close, then cut their holes last.

## Blended organic mass

Loft stack plus generous blends. Expect to spend the modelling effort in the
station function, not in fillets. Do **not** reach for a 3D fillet or chamfer
on a tangent chain or a multi-arc outline
([[fillet-chamfer-pitfalls#tangent-chains-and-multi-arc-outlines]]); bake the
bevel into the lofted section instead. Animals, figures and hulls:
[[loft-organic-bodies]].
