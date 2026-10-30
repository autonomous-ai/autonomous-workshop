---
title: Diagnosing clashes in an assembled kit
tags: [interfere, clash, diagnosis, assembly, press-fit, snap, reverse-engineering]
aliases: [interference triage, clash classification, locate a clash, brepalgoapi common]
sources:
  - skills/step-to-source/references/assembling.md
  - "toolchain: BRepAlgoAPI_Common on two rebuilt parts locates a clash in ~20 s against ~4 min for a full interfere rerun"
related: [kit-assembly-poses, authoring-from-a-reference]
updated: 2026-10-10
---

# Diagnosing clashes in an assembled kit

`interfere` names each clashing pair and its volume, but not where the clash
is. Read every clash before fixing any of them. Most of a first run's clashes
share a handful of causes, and some are designed fits that should be reported,
not removed.

## What a first run looks like

A first run on carried references reports dozens of clashes that come down to
a handful of causes: a mirrored placement, a converter's growth, many
overlapping shells inside single meshes, and the kit's designed tight fits
(snap lips round a plate, a D-journal in its bores, pin tabs in pockets), each
a few mm³ to tens of mm³. Once parts are re-authored, the overlapping-shell
class disappears, and anything left is a placement to fix.

## Locate a clash without rerunning the assembly

Rebuild just the two parts from their builders and placement matrices in
scratch code, then take `BRepAlgoAPI_Common`. Its volume and bounding box
locate the clash in about 20 s, against about 4 min for an `interfere` rerun.

## Classify it

| symptom | cause |
|---|---|
| clash volume equals one part's whole volume | that part is inside out: a det −1 placement, or a negative `solid.volume` |
| a thin band, about 0.3 mm, on a mating face | a converted reference sits proud of its mesh; measure on the mesh |
| a strip of a few mm³ on a D-flat or a pin tab | a designed press fit, if a caption or the fit says so |
| a spherical shell of a few mm³ round a ball joint or neck knob | a snap cup gripping the ball: every point of the overlap lies between the cup's seat radius and the ball's, measured from the ball centre |
| a perimeter band where a lid seats | snap lips: in a section of the opening, polygon area < bounding-box area, and the difference is the lips |
| many clashes inside single parts | overlapping shells a slicer would union; they vanish once the part is re-authored |

Fix placements and conversion artefacts. Report designed fits as fits. Rerun
`interfere` once, at the end.

The final runner fails any overlap above its contact tolerance (1 mm³) and has
no way to declare a designed one, so an assembled view with a gripped snap or
a press fit bigger than that cannot pass it. Do not move the part off its seat
to get a green run: prove the overlap is the fit (locate it, as above), and
report the gate as failed on that fit and nothing else.

## Search the pose off CAD, build CAD once

Iterate pose solves, phase scans and clash localisation in scratch code
(`skills/step-to-source/references/assembling.md`): an assembled STEP over
carried references runs to hundreds of MB and minutes per `gen`.
