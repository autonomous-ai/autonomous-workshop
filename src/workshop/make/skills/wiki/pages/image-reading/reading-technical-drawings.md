---
title: Reading technical drawings and conflicting inputs
tags: [drawing, blueprint, dimension, callout, section-view, title-block, conflict, projection, first-angle, third-angle, orthographic]
aliases: [engineering drawing, dimensioned drawing, orthographic drawing, callouts, design intent, first angle projection, third angle projection, projection symbol, orthographic views, multiview drawing, section view, auxiliary view]
sources:
  - ISO 128 / ASME Y14.5 (technical drawing and dimensioning conventions)
  - https://en.wikipedia.org/wiki/Multiview_orthographic_projection (first and third angle, projection symbol, auxiliary views)
  - skills/cad/references/cad-brief.md
related: [scale-anchors, image-types-and-views, iso-2768-general-tolerances, gdt-basics]
updated: 2026-10-10
---

# Reading technical drawings and conflicting inputs

A drawing is a dimensioned contract; a photo without dimensions is design
intent. Treat them differently, and know which wins when inputs disagree.

## Which input wins

- Dimensioned sources win over image proportions.
- When two dimensioned sources conflict — prose says one value, a drawing
  callout another — flag the conflict instead of silently choosing.
- When drawing views disagree, prefer the dimensioned view and flag the
  conflict.

## Settle the projection first

A multiview drawing lays out six orthographic views of one object in one of
two arrangements. Read the wrong arrangement and the model comes out mirrored,
with the left and right sides (or the top and bottom) swapped.

| | first-angle | third-angle |
|---|---|---|
| picture | the object sits in front of the planes, and each view is pushed *through* it onto the far plane ("an upside-down bowl") | the object sits behind the planes, and each view is pulled onto the near plane ("unfolding a box") |
| top view | **below** the front view | **above** the front view |
| left-side view | **right** of the front view | **left** of the front view |
| used in | Europe and most of the world (ISO) | USA (ASME Y14.3), Japan (JIS B 0001), Canada, Australia (AS 1100.101); the UK (BS 8888) allows both |

Both give the same six views, arranged differently. Third-angle is the
intuitive one: each view sits on the side of the front view it looks at.

The title block's **projection symbol** is a truncated cone drawn as two
views, a trapezoid and two concentric circles. First-angle: the trapezoid's
short side faces *away* from the circles; third-angle: *toward* them. With no
symbol, infer the projection from the region (a US drawing is almost always
third-angle) *and* check it: a feature visible on one side must appear on the
view drawn on the side that looks at it. A mismatch means the other
convention.

## A drawing, systematically

- Read the title block and notes first: units, projection convention (first
  vs third angle), general tolerance ([[iso-2768-general-tolerances]]),
  revision, disclaimers, drawing scale. A 1:2 drawing's numbers are
  real-world; a scale bar is not; "NTS" means not to scale, so never measure
  it.
- Identify which view is which — front/top/side, sections, details, iso — and
  which model axes each maps to before extracting numbers. Trust callouts and
  view labels, not layout conventions. The front view carries the most
  characteristic outline; depth comes from the side and top views.
- Section views (a cutting plane drawn as a chain line lettered A–A; cut
  material cross-hatched) are the source of truth for internal features:
  bores, counterbore and blind-hole depths, wall sections. Hidden (dashed)
  lines are unreliable for measuring where many overlap.
- An inclined face shows its true shape and size only in an **auxiliary
  view**, projected perpendicular to it.
- Datums and feature control frames say what is functional ([[gdt-basics]]).
- Every dimension callout becomes a named parameter and a validation target.
  Multiplicity (`4X`), `TYP.`, and thread/counterbore/countersink callouts
  expand into features plus checks.
- Never scale undimensioned geometry off the drawing image. Derive it from
  stated dimensions when constrained; otherwise assume and report.
- Cross-check features across views.
- A drawing-driven model succeeds when every drawing dimension is either
  verified on the generated geometry or explicitly reported as not verified.

## A photo is design intent

- Establish scale from one stated dimension or a known object in frame
  ([[scale-anchors]]); if neither exists and fit matters, that is the one
  question to ask.
- Estimate remaining proportions from the image and record them as
  assumptions like any other inferred value.
- Distinguish reproduction ("model this part") from inspiration ("something
  like this"): reproduction raises fidelity expectations, inspiration leaves
  freedom.
