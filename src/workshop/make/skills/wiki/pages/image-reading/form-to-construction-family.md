---
title: From visible form to construction family
tags: [construction-family, extrude, revolve, loft, sweep, shell, silhouette, organic]
aliases: [modeling approach from image, which operation, form family, taper profile, station loft]
sources:
  - skills/image-to-cad/SKILL.md (feature-to-operation step)
  - skills/image-to-cad/references/view-inference.md (profile shape to family)
  - build123d documentation (extrude, revolve, loft, sweep, offset)
related: [perspective-and-hidden-views, organic-likeness, measuring-reference-photos]
updated: 2026-09-23
---

# From visible form to construction family

Pick the construction family from the **form**, not from habit. It is the
highest-consequence decision in an image-derived spec — a form authored in the
wrong family cannot be rescued by parameter edits, only by re-authoring. A
tapering body specified as an extrude is wrong **by construction**, not
"close enough".

## What the image shows, and how to author it

| The image shows… | Author as | build123d idiom |
|---|---|---|
| Constant cross-section (box, tray, bracket, plate) | Extrude | `Box(w, d, h)`, or `extrude(amount=h)` over a `BuildSketch` |
| Constant section + uniform draft | Tapered extrude | `extrude(amount=h, taper=3)` |
| Rotationally symmetric (vase, knob, bottle, dome) | Revolve | `Polyline(...)` → `make_face()` → `revolve(axis=Axis.Z)` |
| Section changes along the length — fuselage, hull, swoosh, grip | **Loft over ≥3 stations** | one wire per station from a shared `section_at(t)` helper → `Solid.make_loft(wires, ruled=True)` |
| Constant-ish section following a curved path (tube, rail, strap) | Sweep | `sweep(is_frenet=True)` |
| Planar arch — roll hoop, handle, bail | Extruded ellipse band | two concentric `Ellipse`s, clipped, `extrude(amount=d)` |
| Hollow shell of uniform wall | Shell | `offset(body, -wall, openings=body.faces().sort_by(Axis.Z)[-1])` |
| Non-trivial 2D outline | Sketch | `Rectangle()` → `fillet(sk.vertices(), r)` → `Circle(mode=Mode.SUBTRACT)` → `extrude()` |
| Repeated feature on a line/grid | Array | `with GridLocations(dx, dy, nx, ny): Hole(r)` |
| Repeated feature around an axis | Polar array | `with PolarLocations(r, n): ...` |
| Painted stripe, inlay, or lens on a sculpted skin | Conformal skin patch | `(inflated_loft - raw_loft) & tool` |
| Blended organic mass | Loft stack, bevels baked into the section | `Solid.make_loft()`; keep 3D `fillet()` off tangent chains |

## Reading the family off the elevation profile

The silhouette's width at each height (the row profile, top to bottom) is the
elevation taper signal:

| Elevation profile | Reads as | Author the body as |
|---|---|---|
| flat | constant width up the height | Extrude |
| wide at one end | linear taper | Tapered extrude if the section stays similar; loft if the section *shape* also changes |
| waisted | narrow in the middle | Revolve (if bilaterally symmetric above 0.95 and the plan is round) or loft |
| bulged | fat in the middle | Revolve or loft |
| irregular | character changes more than once | **Loft over stations placed at the profile's band boundaries** |

A band boundary — where a run of roughly constant width ends — is the image
saying the section changed character: that is where loft stations and height
bands go. A fill ratio (silhouette area ÷ bbox area) near 1.0 means a solid
blocky mass, 0.6–0.85 a tapered or shaped body, below 0.5 an open frame, legs,
a handle or a hollow silhouette; a low fill ratio on an object assumed to be a
solid box means the object was misread.

Two independent readings agreeing is the confirmation: a waisted profile on an
object that also looks rotationally symmetric is almost certainly a revolve.
If they disagree, the silhouette is being confused by the background — say so
and fall back to your eyes ([[measuring-reference-photos#when-the-silhouette-lies]]).

## Do not downgrade organic silhouette features to boxes

On animals, figurines, toys, characters, vehicles and product shells, a crest,
casque, horn, fin, brow, cheek, muzzle, fairing, canopy or raised colour lobe
that is visibly rounded or tapered is part of the reference silhouette —
author it as a loft, sweep, revolved cap or conformal skin patch. Use `Box()`
only where the reference shows hard planar faces and square edges. A simplified
organic feature keeps its silhouette envelope and is marked as a deliberate
simplification. More rules for organic subjects: [[organic-likeness]].

## Mixed objects

Mixed objects decompose naturally: a lofted outer skin carrying the image, with
an extruded and booleaned interior carrying the engineering. Say which is
which.

## Seam or colour change

A stripe through the whole cross-section and a stripe painted on the surface
are identical in a photograph and different solids in CAD; a single view
cannot settle which it is. Record the choice.
