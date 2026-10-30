---
title: Tracing concept art onto a CAD outline
tags: [image-reading, concept, trace, inlay, colour, registration, multi-colour]
aliases: [trace concept art, trace arms from image, trace colour regions, register concept to outline, polar registration, concept to inlay, image to inlay, decoration from concept, colour segmentation, pastel segmentation, nearest colour]
sources:
  - "experience: four galaxy arms traced from two generated concepts onto a page holder whose ring the concepts drew 1.4x too large"
related: [fdm-multi-material-design, accessory-likeness-on-a-different-host, unmeshable-faces]
updated: 2026-10-28
---

# Tracing concept art onto a CAD outline

When the owner approves a concept image, an inlay (arms, bands, fields) is
traced from it rather than redrawn by eye. Invented shapes that only
resemble the concept get rejected as "not the image". The trace has three
traps: the concept's proportions are not the model's, close colours swap, and
clipping leaves slivers.

## Register by rays, not by one scale

A generated concept rarely keeps the model's proportions: a ring drawn 1.4×
too large, points 2–3 mm too tall, wings short. With one uniform scale, either
the ring fits and the arms run past the tips, or the tips fit and the arms
fall into the socket. Map polar coordinates about the feature both share (a
ring axis):

```text
angle stays the angle
t = (r_px − ring_edge_px) / (outline_px(angle) − ring_edge_px)
r_mm = ring_edge_mm + t · (outline_mm(angle) − ring_edge_mm)
```

The concept's ring edge lands on the model's ring and its outline on the
model's outline, ray by ray. Shapes keep their place relative to the frame
they sit on. Find the ring edge from the radial brightness profile, not by eye.

## Assign each pixel to its nearest colour

Thresholding each colour separately fails on pastels: a mint and a pale blue
36 RGB apart both pass a 40 tolerance, and the "mint" trace came out as the
blue arm. Take the argmin over all sampled colours first, then threshold the
winner's distance. Star dots inside an arm are found as near-white blobs (all
channels > 215). A lower threshold catches the pastel arm itself and
multiplies the star count.

## Resolve the regions before the B-rep

Clipping traced shapes to the inlay zone and to each other leaves strips under
a line wide wherever an edge runs nearly parallel to the zone edge or to the
next field. In shapely, in paint order:
1. clip each field to the zone shrunk by about 0.05 mm, so the kernel's own
   clip never runs edge-on-edge;
2. subtract the fields painted after it;
3. open it by just over half a line (`buffer(-w).buffer(+w)`);
4. drop pieces under about 1 mm².

Only then build each piece as a fine polyline face (0.3 mm steps). OCC's 2D
offset refuses a periodic spline outright, so do the opening in shapely.
Measure the result with an opening test on every colour and on the body
colour over the whole face ([[fdm-multi-material-design#design-rules]]).

## Say what the palette cannot match

Pick each spool as the nearest stocked colour by CIE76 and report the
distance. Two concept colours that share a nearest spool must not both take
it: give the second its next-nearest, and say which one moved.
