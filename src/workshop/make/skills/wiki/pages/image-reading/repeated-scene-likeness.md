---
title: Likeness on scenes of repeated pieces
tags: [scene, repeated, landmark, placement, layout, likeness]
aliases: [board and pieces, tray of parts, populated surface, piece placement, landmark inventory]
sources:
  - skills/image-to-cad/references/repeated-scene.md
  - "experience: scenes that matched their archetype while missing most of their defining landmarks"
related: [silhouette-likeness, organic-likeness]
updated: 2026-09-23
---

# Likeness on scenes of repeated pieces

A board and its men, a tray of parts, a rack, a tiled or populated surface: a
scene like this can match its broad archetype while missing most of what
defines it, and a single likeness number will not say so — the outline is
dominated by the frame, not by what sits inside it.

## Score landmarks by category

Inventory the visible landmarks by category and give each a count, placement
rule or ratio where the image supports one:

- outer silhouette and frame tiers;
- region boundaries and their layers;
- repeated-site density and exclusion zones, measured as rows/columns or
  occupied area rather than described as "many";
- repeated-piece count and distribution — regular, sparse, clustered or
  deliberately irregular;
- one silhouette checklist per defining module;
- rule- or prose-required accessories absent from the hero image.

A single overall likeness number means nothing until every defining category
has its own finding.

## Reproduce an irregular layout, do not resample it

With a manageable number of individually visible pieces (up to roughly 50),
record their observed normalised centroids or a traceable placement table. A
grid sampler, farthest-point distribution or random seed with the right count
creates a conspicuous new composition. A procedural distribution fits only
when the reference itself is procedural, or when the user asked for a new
setup rather than a reproduction — and then it is `[assumed]`.

## Snap observed centroids to legal sites

When pieces must occupy legal sites, observed centroids are evidence, not
final coordinates. Map each centroid to one **unique** valid site, enforce
every exclusion zone, and record the displacement or a maximum snap distance.
A visually plausible centroid can still sit in an excluded region;
full-assembly interference catches that late, a placement audit (count,
uniqueness, site membership, exclusion clearance) before geometry.

## Small landmarks need their own target

Any defining landmark whose bbox is under roughly 15 % of the whole scene
needs a local verification target. A full-scene render cannot prove a small
feature even when it technically exists.
