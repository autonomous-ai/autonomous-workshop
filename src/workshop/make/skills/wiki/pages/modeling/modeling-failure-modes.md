---
title: Modeling failure modes and fixes
tags: [failure, repair, diagnosis, build123d, selector, scale, positioning, import]
aliases: [repair loop, failure classes, missing feature, wrong scale, invalid geometry, selector fragility, gen_step error]
sources:
  - skills/cad/references/repair-loop.md (failure classes; before the move)
  - skills/cad/references/build123d-modeling.md (common failure modes; before the move)
related: [loft-pitfalls, boolean-pitfalls, fillet-chamfer-pitfalls, kernel-validity, sketch-and-extrude-direction, build123d-selectors, cad-joint-types]
updated: 2026-10-10
---

# Modeling failure modes and fixes

Classify a failure, then make the smallest responsible source change. The
repair procedure itself is `skills/cad/references/repair-loop.md`; this page
is what each failure class usually means. Specialised classes have their own
pages: lofts [[loft-pitfalls]], booleans [[boolean-pitfalls]], fillets
[[fillet-chamfer-pitfalls]], validity [[kernel-validity]], sketches
[[sketch-and-extrude-direction]].

An import or syntax failure, or an entry whose `gen_step()` is missing or
misnamed, is tool usage: `skills/cad/references/build123d-modeling.md`
("Modeling objective") and `step-generation.md`.

## Invalid or missing geometry

Likely causes: an open sketch; a subtractive profile outside the target; zero
thickness; a failed boolean; construction geometry used as exported geometry.

Fix: close profiles intended to become faces; verify dimensions are positive;
make subtractive tools pass through when through-cuts are intended; simplify
the failing feature and rebuild incrementally.

## Wrong scale or bounding box

Likely causes: a units mismatch; a diameter mistaken for a radius; extrusion
direction or amount wrong; the part not centred as assumed (see
[[sketch-and-extrude-direction#align-none-is-the-raw-occ-datum]]); a directly
imported STEP in unexpected units.

Fix: check parameter values; inspect facts and planes; measure critical
extents; correct source dimensions or import handling.

## Missing feature

Likely causes: the wrong `Mode.ADD`/`Mode.SUBTRACT`; the feature profile not
inside the target; a blind cut too shallow; a selector that changed after a
prior operation; a cut refilled by a later union.

Fix: confirm the feature mode; increase cut length for through-cuts; inspect
topology or planes; regenerate and measure the feature-specific refs.

## Selector fragility

Likely causes: arbitrary index selection; topology changed after a fillet or
boolean; similar faces/edges that are indistinguishable.

Fix: select by axis, plane, position, normal, or an inspected reference
([[build123d-selectors]]); rediscover stable references with
`refs --facts --planes --positioning`; add construction datums or simplify
operations if needed.

## Positioning or joint mismatch

A part in the wrong place is usually a wrong part-local origin, a reversed
fixed/moving order in `connect_to()`, an inverted axis or a symmetric-placement
sign; fix it with one of the source-level corrections in
`skills/cad/references/positioning.md` ([[cad-joint-types]]). A hand-derived
frame carries its inverse and a round-trip assert
([[frames-and-rotations#write-the-inverse-and-assert-the-round-trip]]).

## Lists where a shape was expected

`solid += helper()` where the helper returns a list turns the accumulator into
a `ShapeList`; the failure surfaces much later as an anytree
`Cannot add non-node object` from inside `Compound(children=...)`
([[sketch-and-extrude-direction#2d-unions-decay]]).
