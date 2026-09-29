---
title: Silhouettes and the visual hull
tags: [silhouette, visual-hull, shape-from-silhouette, concavity, reconstruction, views]
aliases: [shape from silhouette, silhouette cone, space carving, laurentini, outline reconstruction]
sources:
  - https://en.wikipedia.org/wiki/Visual_hull
  - https://www.robots.ox.ac.uk/~lav/Papers/criminisi_etal_ijcv2000/criminisi_etal_ijcv2000.html
related: [silhouette-likeness, image-types-and-views, form-to-construction-family, measuring-reference-photos]
updated: 2026-09-23
---

# Silhouettes and the visual hull

Most of what an agent reads off a reference image is an outline. This page
covers what outlines can and cannot determine, which sets the ceiling on
building from views and on what a silhouette likeness score proves.

## The visual hull

Shape from silhouette (Laurentini, 1994) back-projects each view's binary
silhouette into a cone from its camera. The **visual hull** is the
intersection of those cones. It is an upper bound on the object: the true
object lies inside it, never outside.

- More views, spread around the object, bring the hull closer to the object.
  Its accuracy depends on how many cameras there are and where they stand.
- Extruding a front outline and intersecting it with a side outline is a
  two-view visual hull — the "extrude and intersect" construction.

## What no set of silhouettes can recover

- **Concavities visible in no silhouette**: a dish's hollow, a recessed
  panel, the inside of a cup, a dimple on a face. They never reach the outline
  from any direction, so the hull fills them in.
- **Anything between two silhouettes' outlines**: with front and side views
  only, a round body and a square one with the same outlines give the same
  hull. The corners of a two-view hull are an artefact, not evidence.

Recover those from shading, highlights, texture, section cues or the
object's function, and record them `[inferred]`, never as measured from the
outline ([[measuring-reference-photos]]).

## Consequences for modelling and checking

- Build from the construction family, not by intersecting outlines, unless
  the object really is a prismatic intersection
  ([[form-to-construction-family]]).
- A high silhouette IoU says the model sits inside the same cones as the
  reference from those cameras. It says nothing about concavities, and a model
  that fills them in can score perfectly ([[silhouette-likeness]]).
- When a concavity defines the object (a bowl, a scoop, a socket), ask for
  a view that looks into it, or state it as an assumption
  ([[image-types-and-views]]).
