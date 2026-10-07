---
title: Silhouette likeness — what it measures and how it lies
tags: [likeness, silhouette, iou, camera, handedness, mirror, mask, reference-image]
aliases: [likeness score, silhouette iou, pose search, mirror image model, reference mask, shaded review]
sources:
  - skills/image-to-cad/scripts/render_views.py and check_likeness.py (pose search, windowed camera, reflection check, hole filling)
  - skills/image-to-cad/scripts/ref_silhouette.py (flattening rule; border chroma rule for a light ground)
  - "toolchain: fixed orthographic camera 0.865 vs searched camera 0.974 on one perspective reference, same model (reproducible)"
  - "toolchain: chiral fixture — a mirror-image model scores 0.9859 under a free azimuth search (reproducible in the render_views self-check)"
related: [likeness-iteration, measuring-reference-photos, organic-likeness, repeated-scene-likeness]
updated: 2026-10-06
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

## Reference masks that cannot hold the subject

A luminance threshold around an estimated background, plus a chromatic shadow
test, is defeated from both sides at once by a **multi-colour object on a
neutral ground**, and neither side announces itself:

- at the default threshold the mask punches **holes** in the object — every
  region whose luma sits inside the threshold band goes: a white shaft end, a
  signature, the specular highlight on a bore wall. The reference then
  measures 10–26 % holey and the model is scored against a perforated target;
- lower the threshold and the holes close, but the soft **cast shadow** comes
  in — shadow rejection is chromatic, so on a grey object over a grey ground it
  has nothing to work with, and the shadow adds material that reads as *the
  model is too small*.

On one reference set, geometry unchanged between columns:

| reference | mask @28 | mask @14 | flattened |
|---|---|---|---|
| front | 0.784 | 0.849 | **0.945** |
| hero | 0.787 | 0.787 | **0.916** |
| iso | 0.787 | 0.809 | **0.890** |

That is "20 % wrong" versus "right", about the same solid — and the pose
search had been landing 17° from the true camera throughout. With the raw
images the contradiction check above fired (cameras agreeing to 15° and 18.75°
with silhouette IoU 0.67 and 0.64); the flattened ones passed at cameras 52°
apart.

The remedy: **make the reference measurable, then measure it with the
unchanged instrument.** Flattening treats *ground-like* pixels (low
saturation, mid luminance) **connected to the frame border** as background and
everything else as object, holes filled. A cast shadow is ground-like and
reaches the border, so it goes; a specular highlight is ground-like but
enclosed, so it stays. Nothing is drawn, moved or smoothed. It cannot separate
a subject from a *cluttered* background: the rule rests on the ground being one
flat colour, which a render gives and a photo in the wild does not.

**A CAD screenshot usually sits on a gradient backdrop** — FreeCAD's default
runs blue at the top to teal at the bottom, and many viewers do the same. One
colour for the whole border ring then lands between the two ends, and every
plate near the top or the bottom whose luma and hue fall inside the band around
that one colour becomes background: on a 15-leg linkage screenshot the mask
lost 12 % of the object (every lilac and pale link near the blue top), and even
the designer's own geometry, drawn straight from its source file, scored 0.849.
The flattener cannot help (its ground must be unsaturated). The mask now
recognises a vertical-gradient backdrop — the two side columns agree row by
row, the top and bottom bands are each flat across the width, and top and
bottom differ — and measures each pixel against its own row's backdrop colour;
a flat ground and a radial vignette fail the test and keep the single-colour
path. The same render then scored 0.938 against 0.788, with no model edit.

Two things that look like a shape problem on such a reference and are not:

- **An off-axis pose for an orthographic view.** A CAD screenshot is taken
  along an axis. When the camera search returns az −91.88 for a view that is
  plainly −90, it is fitting the mask's losses, not the model — the fixed mask
  brought the search back to −90.00 exactly. Check the mask before editing.
- **A clipped extremity after cleaning.** Paint out a logo or a ground line by
  its own pixels (its connected blob, the line's own rows), never by a whole
  band of columns or rows: a band clips the subject's tip, and because the gate
  normalises by the bounding box, 3 px off the feet (0.75 % of the height)
  rescales the whole silhouette and cost this lacy subject 1.6 points of IoU.
  Where a line is drawn *over* the subject (a ground plane edge-on across the
  feet), the pixels under it are gone; say so in the README.

The flattener's band rule (luminance 66-212 plus a saturation ceiling,
flooded from the border) finds **no ground on a light studio sweep above the
band** — a concept sheet or a product render at luma ~230 — and returns the
whole frame. `--ground auto` (the default) notices that the border itself
fails the band rule and switches to the **border rule**: ground is any pixel
whose chroma (R−G, B−G) lies within 3.5 of the border's and that is at most 60
darker than the border's darkest. That separates a warm white print from a cool
grey sweep by the *sign* of the tint, which saturation (max − min) discards; a
neutral contact shadow stays ground and a black part stays object. The
tolerance must clear the JPEG chroma step (a flat ground scatters to √10 ≈ 3.16
from its median; 3.0 left a maze of ground standing as object that the closing
glued to the outline), and the chroma must not be smoothed (a 5 px mean grew
the outline 2 px into the ground and pulled the shadow beside it in). The
gate's own mask is blind on such a reference (it saw 12 % of one outline), so
the outline comparison is reported *not comparable* — look at the `-sil.png`
before scoring — and an outline that reaches the frame edge always fails. For
a subject with no tint against its ground, set the band by hand: `--ground
band --lum-band 218,245 --sat-max 9` held a white ghost on a 235 grey ground,
because the drawing's dark outline stroke stops the flood.

**A warm off-white subject on a near-white ground** (ivory at luma ~220,
saturation ~17, on a ground at ~254 with soft grey shadows at saturation
≤ 7) separates by **saturation, not luminance**: `--sat-max 11 --lum-band
120,256`. A luminance band that excludes the subject also excludes the grey
contact shadow, which then joins the feet into one blob and, once holes are
filled, closes the open span under an arch or an A-frame.

Contents are not product. A reference that shows the vessel full — candy
heaped over a bowl's rim — scores the product against its contents. Clear
exactly the contents' window in a copy of the flattened silhouette, from a
script that prints the rows and columns it cleared, and say so in the README;
never add fake contents to the deliverable to match.

## A subject the same colour as its ground

A brushed-metal or white subject on a grey studio ground has no colour or
luminance to separate it, so the flattener returns the whole frame or nothing.
What separates it is its **edges**: Sobel on a lightly blurred luminance,
threshold near 18 of 255, close three iterations, fill holes, open, keep the
largest blob. That recovers the outline against the wall exactly, and the
sky-side and tail-side outline of a vehicle came out within a pixel.

It fails along the **bottom**: the contact shadow and the floor reflection of
the wheels have strong edges too and glue a fringe to the silhouette. Do not
threshold darkness to remove them (the shadow under the body is as dark as the
tyres). Read the lower outline off the image as a short polyline of contact
points, or as circles for round tyres plus a straight sill line, and take each
column from the edge-fill top to that polyline. Check the result by laying it
over the reference in red before trusting a score. All inputs are image pixels
and read-off constants in a script beside the masks; none is a model number.

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
