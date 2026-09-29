---
title: Image types and view counts
tags: [reference-image, view, orthographic, photo, render, sketch, symmetry, triage]
aliases: [image triage, how many views, hero shot, orthographic views, extra views, bottom view]
sources:
  - skills/image-to-cad/SKILL.md (triage step)
  - skills/image-to-cad/scripts/measure_image.py (cross_check behaviour with 3 vs 4-6 views)
related: [perspective-and-hidden-views, measuring-reference-photos, scale-anchors]
updated: 2026-09-23
---

# Image types and view counts

What a reference can and cannot tell you is decided before any pixel is
measured: by what kind of image it is, and by how many distinct viewpoints the
set really contains.

## What kind of image

| Kind | Consequence |
|---|---|
| **Orthographic / blueprint** | Best case. Dimensions may be `[observed]`. Read the title block for units and scale ([[reading-technical-drawings]]). |
| **Studio render** | Proportions trustworthy; measure it directly. |
| **Photo in the wild** | Perspective distorts every ratio — correct it first ([[perspective-and-hidden-views]]). |
| **Sketch / concept art** | Intent only. Almost every dimension `[assumed]`. Ask for one governing size. |
| **Screenshot of CAD** | Read the orientation cube if present; treat as orthographic. |

## A hero shot is one view

Count distinct viewpoints. One 3/4 hero shot is **one** view — it shows the
front, the side and the top at once and lies about all three, because it
foreshortens both horizontal axes by an unknown amount at an unknown angle.

| views | what they give |
|---|---|
| 1 | two views are `[inferred]`/`[assumed]` — say so first |
| 2 | the third is `[inferred]` |
| 3 aligned orthographic | the outline is solved; nearly every proportion `[observed]` |
| 4–6 | no more outline; you buy **hidden surfaces** and **redundancy** |

**No number of views gives absolute scale** — that comes only from an anchor
([[scale-anchors]]).

## What views four to six buy

- **Redundancy.** With six views each dimension is constrained four times
  instead of twice, so a cross-view closure test becomes a real outlier
  detector — one bad photo is *identifiable*, not just detectable. With exactly
  three views the residual spreads evenly and every view reports the same
  disagreement: the set is known to be bad without saying which member is.
- **Hidden surfaces.** The bottom view is the only sight of the underside; a
  spec written without it has an invented base, sill, chassis and fastener
  pattern. The back view is the only clean read of the rear face and of
  anything the side view showed edge-on.
- **A null result on symmetry.** The opposite side view usually adds nothing to
  a bilaterally symmetric object — a mirror-symmetry measurement already said
  so. Ask for it only to rule out an asymmetric feature you suspect.

## Rank the extra views before asking

**Bottom** almost always; **back** when the rear differs from the front
(usually); **other side** only when asymmetry is suspected. Asking for three
more photos when the bottom view alone would have answered the question wastes
the user's one round.

## Symmetry is the cheapest inference

Mirror symmetry turns half an unobserved view into `[inferred]`; rotational
symmetry turns the whole top view into `[inferred]`. Establish the symmetry
group once and reuse it. A named product or standard outranks anything
measured from pixels: web-search the spec, cite it, and tag it `[observed]`
from the source.

## Using several images together

- Where two images disagree on a feature, the more orthographic one wins. Say
  which was used.
- A detail shot or close-up is worth more than a hero shot for one specific
  feature and worth nothing for overall proportion. Use each for what it
  measures well and say so.
- Averaging two disagreeing images instead of picking the better one is a
  failure: a foreshortened view averaged into a good one gives a spec that is
  confidently, uniformly wrong ([[measuring-reference-photos#cross-view-closure-and-its-blind-spots]]).
