---
title: Measuring reference photos
tags: [measurement, silhouette, mask, shadow, ruler, cross-check, pixel, photo]
aliases: [measure image, silhouette mask, pixel ratios, per-view scale, cast shadow, line art]
sources:
  - skills/image-to-cad/scripts/measure_image.py (mask, shadow rejection, cross_check)
  - "toolchain: a contact shadow inflates every view by the same proportion, so a cross-view check still agrees (reproducible)"
  - "experience: dimensions read on the wrong view's ruler, which no downstream gate caught"
  - "experience: a cream egg on a cream ground defeated both toolchain masks; red-minus-blue after a median filter separated it"
  - "experience: a brown token's dark contact shadow kept by every mask until a relative-saturation rule"
related: [image-types-and-views, perspective-and-hidden-views, silhouette-likeness]
updated: 2026-10-07
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
- **A coloured subject in its own dark contact shadow.** Under a key light a
  brown, red or green part throws a shadow far darker than the ground, so the
  mask and `ref_silhouette.py`'s band and border rules all keep it: a crescent
  along every edge facing away from the light, 10-15 % of the area on one
  oblique shot, scored as "the model is too thin" (IoU 0.807 for a model that
  later scored 0.920). The shadow is neutral at every brightness and the
  subject is not: relative saturation `(max - min) / max` read 0.46-0.77 on
  the subject (lit face to deepest groove) and 0.31 or under on every shadow
  pixel. `ref_silhouette.py --ground tint` flattens by that rule; a grey,
  white or black subject has no tint to keep and needs another rule.
- **Dark object on a dark ground, or light on light.** Symptom: an error or a
  nonsense bbox. Invert, or move the threshold (roughly 12–45 on 8-bit
  luminance).
- **A cream subject on a cream ground.** Neither luminance nor saturation
  separates them: the ground is brighter than a "mid-luminance" band and the
  subject's lit flank is as neutral as the ground. Warmth does -- red minus blue
  after a 7 px median filter (the median removes print-line texture): a neutral
  ground reads near 10, a cream or tan subject 15-40. The contact shadow picks
  up warm bounce light from the subject and reads 16-26, so give the shadowed
  band under the subject a higher threshold than the lit side, and cut below
  the lowest point the grid overlay shows. Keep such a probe as a documented
  script beside the reference.
  When the ground is itself warm (a pink-beige studio sweep), red minus blue
  stops separating: both read 25-45. The hue ratio (G-B)/(R-B) still does --
  an ivory or yellow subject reads about 0.45 at every brightness, a pink-beige
  ground about 0.35 -- and an Otsu split of its median-filtered map finds the
  threshold. The median pushes that mask's edge 3-5 px outward all round,
  which on a figure costs about 3 points of IoU, so re-classify a band of
  about 10 px either side of the edge pixel by pixel against a smooth
  background estimated from the pixels outside the band (normalised
  convolution). A glossy desk still returns a contact shadow and a reflection
  that no colour rule removes: read the top of the dark contact line as a
  polyline and cut there.
- **Line art defeats the mask, and not obviously.** A denoise pass deletes
  1–2 px strokes, so a white-interior sheet reports no object on some panels
  and a plausible bbox on the ones it half-holds. Flood-fill the white
  background so each outline becomes a solid silhouette, then measure the
  filled image with the same tool. Anything about 2 px wide still needs a
  direct read.

## Colour clusters are colour, not parts

Clustering the pixels inside the outline is how to measure a stripe, a cockpit
opening, a tyre against its fender, a lens or a panel line. But gloss splits
one paint into a lit and a shaded cluster — raise the cluster count until the
feature appears — and two unrelated black components land in the same
cluster. Never read a cluster as a part.

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
disagreement is the highest-value number a measurement produces. Under ~5 %
the images share one camera scale and every proportion may be `[observed]`.
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

A hand-written probe re-derives the silhouette with an ad-hoc threshold and may
omit shadow rejection, making ratios across views incomparable. Interrogate
the same mask (row and column runs, a region window, a named colour) first;
if a probe is unavoidable, say in the spec what was measured by hand and why.
Two runs on one row is the fact that the object is two parts there, and the
gap between them is the clearance.
