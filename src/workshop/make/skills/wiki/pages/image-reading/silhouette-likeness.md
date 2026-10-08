---
title: Silhouette likeness — what it measures and how it lies
tags: [likeness, silhouette, iou, camera, handedness, mirror, mask, reference-image]
aliases: [likeness score, silhouette iou, pose search, mirror image model, reference mask, shaded review]
sources:
  - skills/image-to-cad/scripts/render_views.py and check_likeness.py (pose search, windowed camera, reflection check, hole filling)
  - skills/image-to-cad/scripts/ref_silhouette.py (flattening rule; border chroma rule for a light ground)
  - "toolchain: fixed orthographic camera 0.865 vs searched camera 0.974 on one perspective reference, same model (reproducible)"
  - "toolchain: chiral fixture — a mirror-image model scores 0.9859 under a free azimuth search (reproducible in the render_views self-check)"
related: [likeness-iteration, measuring-reference-photos, organic-likeness, repeated-scene-likeness, reference-silhouette-masks]
updated: 2026-10-08
---

# Silhouette likeness — what it measures and how it lies

`validate`, `interfere`, `check_fit` and `check_motion` all pass a figure that
is 60 % of the way to its reference. A silhouette score is the only check of
the model against the *photograph*. It is useful exactly as far as its failure
modes are understood.

## What the score is

Both silhouettes are normalised to a common height — height only, so the
aspect ratio stays in the comparison — and compared as IoU per view, plus
horizontal bands giving the model's width as a fraction of the reference's.
**The bands are the point.** An IoU says the model is wrong; a band ratio of
0.39 at 0.83 from the top says the model is 60 % too narrow near its base,
which is one edit, not an afternoon.

Read the score as a **floor on the disagreement, never a ceiling on quality**:
it is blind to colour, and on a multi-material reference colour is much of
what a human compares. Treat 0.90 as the target, not the pass mark for an
unreviewed first attempt.

## A silhouette hides a machine's identity

A machine's identity is interior — slots, pockets, bores, a pin on an arm, one
part seated in another — and a filled outline shows none of it: an assembly
renders as a single blob whose parts cannot be told apart at any resolution.
Review appearance on a shaded render with the same frame and camera, score on
the mask; neither replaces the other, and neither sees colour or material the
way a person does.

## The camera is unknown — search it

A photo has an unknown azimuth, elevation and focal length. An orthographic
render compared against one taken 15° off will miss 0.90 however right the
model is, and what is then measured is how well the camera was guessed. On a
perspective reference the same model scored **0.865 with a fixed orthographic
camera and 0.974 with the camera searched**. Fixed orthographic views are for
the set a human reviews, and for a reference that is itself an orthographic
drawing.

The recovered pose is worth reading. A pose far from the one the photograph
plainly shows is a finding, not a pass: the search found the best fit to a
shape that is wrong somewhere else. And when the search recovers nearly the
*same* pose for viewpoints that are plainly different, the finding is in the
reference, not the model: the search is fitting the reference's holes rather
than its outline. Two references whose cameras agree within ~20° but whose own
silhouettes score below IoU 0.85 against each other are a contradiction — one
camera cannot produce two outlines — so one of the masks is bad.

## A free search cannot see handedness

Seen from behind, an orthographic silhouette is the mirror image of the same
silhouette seen from in front. A search free to try every azimuth therefore
fits a model built **the wrong way round** — a post on the left the photograph
has on the right — by turning the camera to (az + 180, −el). Against an
orthographic reference taken from (30, 20):

| model | free search | inside a declared ±30° window |
|---|---|---|
| right hand | 0.9918 | 0.9918 |
| mirror image | **0.9859** at (−30, −20.6) | 0.6443 |

Nothing else notices: `validate`, `interfere` and a proportion ledger all pass
a mirror-image model whose ledger rows are sizes rather than sides. A
perspective reference breaks the symmetry only partly (the same pair scored
0.99 / 0.87 at 25° FOV), so the near-orthographic case — a telephoto product
shot, a studio render, a drawing — is exactly where it hides.

The cure is to declare each reference's camera window, where the mirror pose
is out of reach, and to score the model's reflections inside that window too.
A reflection that fits better is a source fix — mirror across that axis —
never a shape sweep; no shape edit reaches it. A mirror-symmetric model cannot
trip the check: its reflection is itself (an L-bracket scored 0.9913 against
its own mirror's 0.9918). Cost is roughly neutral: three windowed searches
(model and two reflections, 156 poses each over three FOVs) took 2.37 s
against 2.89 s for one free search of 585 poses. Also give the ledger one row
that states a side — "post on +X", "handle on −Y" — because a count or a bbox
is the same on both hands.

## Reference masks

A reference whose mask cannot hold the subject — a multi-colour object on a
neutral ground, a light studio sweep, a cream subject on a cream sheet, a
subject the same colour as its ground — scores the model against holes or a
shadow. Flatten it first and look at the outline over the image before
scoring: [[reference-silhouette-masks]].

## Fit the profile to the mask before building

The silhouette score is a function of a handful of side-profile numbers
(length, nose height, hood angle, cowl station, roof flat, tail height, ride
height, wheel radius, axle stations). So instead of building and nudging, run
a bounded differential-evolution fit of a rasterised polygon of those numbers
against the normalised reference mask, using the gate's own normalisation
(height-normalised, width centred), with the hard constraints of the brief
(a tilted display, a bed size) as bounds. It takes seconds and showed that a
model at 0.81 would reach 0.94 at a length-to-height ratio the first guess had
missed by 10 percent. Unbounded, the fit wanders to extremes (a 310 mm body
with a 23 mm roof flat): the bounds are the design, so choose them first.
Where a hard constraint contradicts the reference (a screen that forces a
steeper windshield than the picture shows), the fit finds the least damaging
compromise; record that deviation in the spec.

## Filling holes removes through-openings

Enclosure is all the flattening rule can see, so a real opening — a handle
loop, a window in a frame, the gap under an arch — is filled with the
highlights. Scoring an unfilled render against it then counts a correct
opening as missing material: a frame whose window is half its area scored IoU
**0.50**, the same frame with the window deleted **1.00**, and a sweep loop
would have paid for deleting it. So both sides must be filled by one rule, and
then **the silhouette no longer measures enclosed openings — each needs its
own landmark row** (a count, a clear width, a station).

## Clipped references and burnt-in labels

- **A whole-object reference must contain the whole object.** If its
  silhouette touches an image edge, height normalisation turns a clipped top or
  base into a false shape defect, and camera search optimises against the
  crop. Keep that frame as qualitative evidence; score a complete view.
- **Nothing but the object may be in the render.** A burnt-in chip like "ISO"
  is object to any threshold and stretches the bounding box to the frame edge;
  one early front view scored IoU 0.10 with the model blameless. Keeping only
  the largest connected blob is a second line of defence.

What outlines can never determine (hidden concavities, the corners of a
two-view hull): [[silhouettes-and-visual-hull]]. Camera pose from ellipses
and horizons: [[camera-pose-from-a-photo]].
