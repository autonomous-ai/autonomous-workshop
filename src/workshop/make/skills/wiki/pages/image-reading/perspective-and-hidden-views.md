---
title: Perspective and the views a photo hides
tags: [perspective, foreshortening, three-quarter, depth, top-view, plan, reconstruction]
aliases: [3/4 view, hero shot depth, vanishing point, recovering the plan, hidden view, occlusion]
sources:
  - skills/image-to-cad/references/view-inference.md
  - "experience: depths read straight off a hero shot that delivered visibly shallow parts"
related: [image-types-and-views, measuring-reference-photos, scale-anchors, form-to-construction-family]
updated: 2026-09-23
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
