---
title: Drawing projection and view conventions
tags: [drawing, projection, first-angle, third-angle, orthographic, section, view]
aliases: [first angle projection, third angle projection, projection symbol, orthographic views, multiview drawing, section view, auxiliary view]
sources:
  - https://en.wikipedia.org/wiki/Multiview_orthographic_projection
related: [reading-technical-drawings, gdt-basics, iso-2768-general-tolerances, image-types-and-views]
updated: 2026-09-23
---

# Drawing projection and view conventions

A multiview drawing lays out six orthographic views of one object in one of
two arrangements. Read the wrong arrangement and the model comes out mirrored,
with the left and right sides (or the top and bottom) swapped. Settle the
projection before measuring anything off a drawing.

## First angle versus third angle

| | first-angle | third-angle |
|---|---|---|
| picture | the object sits in front of the planes, and each view is pushed *through* it onto the far plane ("an upside-down bowl") | the object sits behind the planes, and each view is pulled onto the near plane ("unfolding a box") |
| top view | **below** the front view | **above** the front view |
| left-side view | **right** of the front view | **left** of the front view |
| used in | Europe and most of the world (ISO) | USA (ASME Y14.3), Japan (JIS B 0001), Canada, Australia (AS 1100.101); the UK (BS 8888) allows both |

Both give the same six views, arranged differently. Third-angle is the
intuitive one: each view sits on the side of the front view it looks at.

## The projection symbol

The title block carries a truncated cone drawn as two views: a trapezoid and
two concentric circles.

- **First-angle:** the trapezoid's short side faces *away* from the circles.
- **Third-angle:** the trapezoid's short side faces *toward* the circles.

With no symbol, infer the projection from the region (a US drawing is almost
always third-angle) *and* check it: a feature visible on one side must appear
on the view drawn on the side that looks at it. A mismatch means the other
convention.

## Other view types

- **Section views**: a cutting plane (a chain line with arrows and letters,
  A–A) exposes the interior. Cut material is cross-hatched. Read internal
  bores, wall thicknesses and pockets from sections, not from hidden lines.
- **Auxiliary views**: orthographic views perpendicular to an inclined
  surface. They are the only views that show that face's true shape and size.
- **Hidden lines** (dashed) show edges behind the visible surface. They are
  unreliable for measuring when many overlap.

## Reading order for modelling

1. The title block: projection symbol, units, general tolerance
   ([[iso-2768-general-tolerances]]), scale ("NTS" means not to scale, so
   never measure it).
2. The front view (the most characteristic outline) and the depth from the
   side/top views.
3. Sections and details for the interior.
4. Datums and feature control frames for what is functional ([[gdt-basics]]).
5. Cross-check the model against every view before trusting any single one
   ([[reading-technical-drawings]]).
