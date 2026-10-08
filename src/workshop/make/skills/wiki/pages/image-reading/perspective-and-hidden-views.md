---
title: Perspective and the views a photo hides
tags: [perspective, foreshortening, three-quarter, depth, top-view, plan, reconstruction]
aliases: [3/4 view, hero shot depth, vanishing point, recovering the plan, hidden view, occlusion, pixel art, voxel, rectilinear plan, grid plan]
sources:
  - skills/image-to-cad/references/view-inference.md
  - "experience: depths read straight off a hero shot that delivered visibly shallow parts"
  - "experience: a flat token photographed lying on a table at 45 deg, rectified to its plan and scored 0.920"
  - "experience: a pixel-art key read on a fitted grid from one oblique shot; inlaid squares settled the row/column ratio the outline could not"
related: [image-types-and-views, measuring-reference-photos, scale-anchors, form-to-construction-family]
updated: 2026-10-08
---

# Perspective and the views a photo hides

The failure this page prevents is reading a depth straight off a hero shot,
writing it into the spec as a dimension, and delivering a part that is visibly
too shallow. The missing views are not recovered by looking harder; they are
recovered by **reasoning from symmetry, function, and the one axis the image
measures honestly** — then labelled `[inferred]` or `[assumed]`.

## Diagnose the shot first

| Symptom | Shot type | Correction |
|---|---|---|
| Vertical edges stay parallel; the top face is a thin sliver | Near-orthographic, long lens | None needed. Proportions are trustworthy. |
| Vertical edges converge slightly toward the top | Mild perspective | Measure ratios at the object's **mid-height** where distortion is least. Accept ±10 %. |
| Vertical edges converge strongly; near corner much larger than far | Wide-angle, close | Ratios off the image are unusable for depth. Use function and symmetry instead; tag depth `[assumed]`. |
| Two vanishing directions visible on the top face | 3/4 view | Apply the width/depth split below. |

## The 3/4 width/depth split

In a 3/4 shot the silhouette width is *not* the object's width — it is the sum
of the projected width and the projected depth:

```text
silhouette_width ≈ W·cos(θ) + D·sin(θ)
```

where θ is the rotation away from face-on. θ, W and D are three unknowns in
one equation, so do not solve it. Instead:

1. **Take height as the honest axis.** Height is unaffected by rotation about
   the vertical axis, so the bounding-box height is the most reliable
   measurement and the best thing to anchor scale to.
2. **Read W and D from the visible face edges, not the silhouette.** Find the
   front face's own left and right edges and measure between them; do the same
   for the side face's near and far edges. These are still foreshortened, but
   each is now a single face rather than a sum.
3. **Read the top face's corner angle if visible.** The near corner of a
   rectangular top reads as ~90° only face-on. A visibly obtuse near corner
   means significant rotation — trust the height, tag the depth `[assumed]`.
4. **Round to a plausible proportion.** Most product depths land on a simple
   ratio of the width: 1.0 (square plan), 0.75, 0.6 or 0.5. Pick the nearest
   one the image does not contradict, state the ratio in the ledger, and tag it
   `[assumed]`. A stated ratio the user can correct in one edit beats a false
   precision like "62.4 mm".

## Recovering the top view

The plan is the view a hero shot hides most thoroughly, and the one that
decides whether the body is a plain extrude or a sketched profile. In priority
order:

1. **Rotational symmetry.** If the front and side silhouettes have the same
   outline, and any horizontal feature reads as an ellipse, the plan is a
   **circle** — `[inferred]`, high confidence. Author as a revolve.
2. **Bilateral symmetry.** A mirror-symmetry score above 0.95 gives one mirror
   plane. It fixes the plan's symmetry axis but not the depth.
3. **The visible top face.** If any part of the top is visible, its outline —
   however foreshortened — gives the plan's *shape class*: rounded rectangle
   vs circle vs racetrack vs freeform. Shape class is `[inferred]` with
   confidence; the depth number is not.
4. **Function.** A base must support the mass above it: the plan must be at
   least large enough that the centre of mass sits inside the footprint. A
   shelf's depth is set by what it holds. A grip's plan is set by a hand.
5. **Archetype default.** Failing all of the above, use the archetype's usual
   plan proportion, tag it `[assumed]`, and put it in the Assumptions list.

## A flat part lying on a table shows its whole plan

A constant-thickness plate photographed lying on its back (a token, a
keychain, a cookie-cutter shape) is the one case where an oblique shot gives
the plan as numbers, not a shape class: the top face is the plan, shortened
in depth by `sin(el)`, with the wall hanging under every near edge.

- **Top face = silhouette eroded by the wall, AND the lit top's colour.** A
  pixel is top face when it and the `wall_px` pixels below it all lie in the
  silhouette. Neither half works alone: the colour rule misses gaps where one
  stroke's wall hangs over the next, the erosion fills them.
- **Elevation from strokes of one width.** Tines, letters, spokes drawn with
  one pen show their true width across the image and `width x sin(el)` when
  they run across it: 27 px across, 19 px deep gave 45 deg. 40 and 50 deg
  each cost 0.06 IoU against the same reference.
- **Rectify** rows by `1 / sin(el)`; thickness is `wall_px x mm/px / cos(el)`.
- **Grow the plan back by the edge band.** The lit-colour rule keeps the flat
  top and drops the rounded edge round it, which is plan: about 0.6 mm here.
  The wall read by eye was short as well (22-25 px against 26).
- **Settle wall and edge band by a sweep, without the kernel.** Project the
  extruded plan as the union of the plan scaled by `sin(el)` in depth and
  shifted by `z cos(el)` for z through the thickness, rasterise, and score it
  with the likeness gate's own `normalise`/`compare` against the flattened
  reference: seconds per cell. A 5 x 4 grid moved IoU from 0.870 to 0.920 at
  the declared camera, where the gate then recovered az, el, roll and fov
  exactly.

## A rectilinear plan is read on a grid, not traced

Pixel art, voxel and brick-built plans have every edge on one of two axes. Read
the grid and the cell map, never a traced outline: a trace rounds every step
the design is made of.

- **The outline alone cannot give the plan's aspect.** Any 2 x 2 linear map
  of a plane is some orthographic camera (scale, elevation, azimuth, roll), so
  one oblique outline fits a plan stretched along either axis equally well
  with a different camera. Settle it with a feature known to be square or
  round on that plane (studs, inlaid squares, a hole), or with the wall: at
  zero roll the wall hangs straight down the image. On one generated shot the
  outline's steps read 17.1 x 13.4 px while inlaid squares read 0.81 x 1.05
  of those steps: rows were 1.3 columns tall, and reading the steps as square
  would have needed a 50 deg camera roll.
- **Axes** from the silhouette's gradient-direction histogram; **pitches**
  from the corners of the crisp edges (the ones facing away from the camera
  carry no wall); then fit only the phase. Never fit the pitch by
  quantisation error: a smaller cell always fits better.
- **Widths land on whole counts** once the pitch is right (odd widths for a
  shape on an axis); a run of widths all half a cell short means the pitch is
  a few percent off, not that the shape is.
- **Score every discrete reading** (a notch row, an odd or even width, a
  half-row step) by fitting the whole plan to the flattened silhouette: six
  affine terms plus the wall's height in pixels, maximising IoU, seconds per
  fit. Fit the affine with the wall held first: a free wall from a poor start
  grew to 27 px to cover a misplaced outline, where the staged fit found 11.
- **A generated image is not self-consistent.** Its grid drifts (a centreline
  half a column off over a dozen rows); design on one axis and let the fit
  report the cost. Its pixels need not be square (rows a tenth taller than
  columns on several tiles) nor one size (outline and detail grids differ on
  one tile): fit column and row pitch separately by least squares through the
  measured edges, or transcribe at half pitch, which keeps every edge within a
  quarter cell. A rasterised plan scored with the gate's own
  `normalise`/`compare` predicted the gate within 0.001–0.015 on ten tiles.
- **Compute the likeness ceiling before fitting.** When parts of the object
  are fixed by something other than the image (a family's shared shank, a
  size cap), paste the reference's own outline onto those parts and score it.
  If that is under the floor, no edit of the free part can pass: report it at
  once instead of iterating.

## Write the reasoning, not just the conclusion

An `[inferred]` view presented without the reasoning that produced it cannot
be checked. Example:

> Top view `[inferred]` — front and side silhouettes match to within 4 % and the
> shade's lower rim reads as an ellipse, so the plan is circular. Ø `[inferred]`
> 180 mm from the front view's max width. The base plate's plan is `[assumed]`
> circular and coaxial; nothing in the image contradicts it.

## Occlusion is weak evidence of depth

What occludes what is weak evidence and may conflict across views. Take
lateral placement from near-orthographic elevations where offsets are
measurable, and record unresolved conflicts as assumptions.

Measuring heights and plan ratios from parallel edges and one known length:
[[single-view-metrology]]. How far a close phone shot is from orthographic:
[[camera-model-and-focal-length]].
