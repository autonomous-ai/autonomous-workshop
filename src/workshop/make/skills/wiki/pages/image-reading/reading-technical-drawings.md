---
title: Reading technical drawings and conflicting inputs
tags: [drawing, blueprint, dimension, callout, section-view, title-block, conflict]
aliases: [engineering drawing, dimensioned drawing, orthographic drawing, callouts, design intent]
sources:
  - ISO 128 / ASME Y14.5 (technical drawing and dimensioning conventions)
  - skills/cad/references/cad-brief.md
related: [scale-anchors, image-types-and-views]
updated: 2026-09-23
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

## A drawing, systematically

- Read the title block and notes first: units, projection convention (first
  vs third angle), revision, disclaimers, drawing scale. A 1:2 drawing's
  numbers are real-world; a scale bar is not.
- Identify which view is which — front/top/side, sections, details, iso — and
  which model axes each maps to before extracting numbers. Trust callouts and
  view labels, not layout conventions.
- Section views are the source of truth for internal features: bores,
  counterbore and blind-hole depths, wall sections.
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
