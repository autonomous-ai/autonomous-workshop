---
title: Measuring reference photos
tags: [measurement, silhouette, mask, shadow, ruler, cross-check, pixel, photo]
aliases: [measure image, silhouette mask, pixel ratios, per-view scale, cast shadow, line art]
sources:
  - skills/image-to-cad/scripts/measure_image.py (mask, shadow rejection, cross_check)
  - "toolchain: a contact shadow inflates every view by the same proportion, so a cross-view check still agrees (reproducible)"
  - "experience: dimensions read on the wrong view's ruler, which no downstream gate caught"
related: [image-types-and-views, perspective-and-hidden-views, silhouette-likeness, reference-silhouette-masks]
updated: 2026-10-10
---

# Measuring reference photos

Do not eyeball ratios; measure them. But a silhouette measurement sees an
outline, not an object, and each way it misleads is silent and plausible.
Reconcile every measurement against what you see; when the numbers contradict
the image, trust your eyes and say the tool disagreed.

## When the silhouette lies

- **The background is busy.** A cluttered photo yields a mask full of
  background. Symptom: fill ratio near 1.0 with a bbox covering most of the
  frame. Crop to the object and re-measure. Using a fill ratio from an
  uncropped photo is a defect.
- **A hole reads as solid.** A through-hole is inside the silhouette, so a
  silhouette tool cannot see it, nor tell a hole from a notch. Holes always
  come from your eyes.
- **A shadow joins the object.** Dimming a surface scales all three colour
  channels together and leaves its chromaticity untouched, so a shadow can be
  rejected by requiring an object pixel to differ from the background in
  chromaticity, or to be far too dark or too bright for a shadow to explain.
  That still fails on a subject whose colour genuinely matches its ground and
  on a coloured bounce-light spill. Symptom of a miss: the bottom band is wider
  than the object visibly is, mirror symmetry well below what the object looks
  like, and the widest point dragged toward the base. Crop above the shadow;
  turning shadow rejection off out of habit lets a contact shadow back in.
- **The subject's colour matches its ground or its shadow** — a tinted
  subject in its own dark contact shadow, a neutral subject on a tinted
  ground, a pastel, a cream subject on cream, a two-hue flat plate. Each needs
  its own mask rule, measured on subject, shadow and ground first:
  [[reference-silhouette-masks#subject-and-ground-colour-choose-the-ground-rule]].
- **Dark object on a dark ground, or light on light.** Symptom: an error or a
  nonsense bbox. Invert, or move the threshold (roughly 12–45 on 8-bit
  luminance).
- **Line art defeats the mask, and not obviously.** A denoise pass deletes
  1–2 px strokes, so a white-interior sheet reports no object on some panels
  and a plausible bbox on the ones it half-holds. Flood-fill the white
  background so each outline becomes a solid silhouette, then measure the
  filled image with the same tool. Anything about 2 px wide still needs a
  direct read.

## Colour clusters are colour, not parts

Clustering the pixels inside the outline (`measure_image.py --palette K`,
`skills/image-to-cad/SKILL.md`) measures a stripe, an opening or a panel line,
but gloss splits one paint into lit and shaded clusters and two unrelated
black components land in the same cluster. Never read a cluster as a part.

## Every view carries its own ruler

A studio pack crops and frames each render to look good, not to share a scale,
so the subject can stand a fifth taller in one elevation than in the next. Pick
one length of the subject that both views show whole — its overall height is
usually the only one — and divide each view's pixel counts by it before
reading anything else off that view. Then every ratio is in units of that
length and views can be compared.

A dimension read on the wrong view's ruler is wrong by the ratio between the
rulers and **by nothing else**, so it stays plausible: a real measurement of a
real feature, just scaled. Nothing downstream catches it — a whole-silhouette
cross-check compares outlines rather than one feature across views, and a
likeness score still sees the right shape in a uniformly mis-scaled member.
Only re-deriving the ruler does. Keep each view's readings in their own block,
name the ruler in the block's header, and never take a width from an elevation
that cannot see widths.

## Cross-view closure and its blind spots

Solving L : W : H over every named view at once and reporting each view's
disagreement is useful only after the ratios have enough independent
constraints. Repeated front/back views measure W:H and leave L unknown;
repeated top/bottom views leave H unknown, and repeated left/right views
leave W unknown. Least squares still returns numbers for such a deficient
system, but its unconstrained values are arbitrary. The measurement tool
reports `UNDERCONSTRAINED` and no solved ratio in this case.

Two views spanning all three axes solve the ratios exactly and leave no
redundant equation with which to detect perspective distortion. Their verdict
is `SOLVED ONLY`. A consistency claim needs redundant constraints and views
already justified as orthographic; assigning two oblique photographs the same
canonical label does not make them orthographic.

With sufficient constraints, under ~5 % disagreement is consistent with one
orthographic set; it does not prove that the camera model is correct.
Above it, at least one view is foreshortened — find the bad view and drop it.
**Do not average**: averaging a foreshortened view into a good one produces a
spec that is confidently, uniformly wrong.

What closure cannot see:

- **Which view is bad, with exactly three views** — the residual spreads evenly
  ([[image-types-and-views#what-views-four-to-six-buy]]).
- **Shadow inflation** — a contact shadow enlarges every view in the same
  proportion, so the views agree with each other while all of them are wrong.
- **Orientation mistakes** — a closure that reads a plan view's width as the
  object's length reports a disagreement that is not there if the plan image
  is not rotated to the expected orientation first.

## Mirror symmetry versus camera rotation

A low left-right mirror score means the object is genuinely asymmetric **or**
the shot has a strong 3/4 rotation. Above 0.95 treat bilateral symmetry as
observed and mirror the unobserved half; 0.8–0.95 is usually a symmetric
object shot slightly off-axis. Check which before concluding "asymmetric".
A top-bottom mirror score is rarely 1.0 for a real object; a high value
suggests a revolve about a horizontal axis, or a cropped symmetric detail.

## A probe script changes the instrument

A hand-written probe re-derives the silhouette with its own threshold, so its
ratios are not comparable across views. Interrogate the measurement tool's own
mask first (`skills/image-to-cad/SKILL.md`, "Interrogate the mask").
