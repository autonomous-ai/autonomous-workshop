---
title: Reference masks — making a reference the likeness gate can read
tags: [likeness, silhouette, mask, reference-image, shadow, background, flatten]
aliases: [reference silhouette, flatten reference, ref_silhouette, light ground, cream on cream, drop shadow mask, concept sheet silhouette]
sources:
  - skills/image-to-cad/scripts/ref_silhouette.py (flattening rule; border chroma rule for a light ground)
  - skills/image-to-cad/scripts/measure_image.py (the gate's own mask; vertical-gradient backdrop)
  - "experience: flattened references scored 0.945 / 0.916 / 0.890 where raw masks scored 0.78-0.85, geometry unchanged"
  - "experience: silhouettes cut from a generated ten-object concept sheet, texture mask against tint mask"
related: [silhouette-likeness, measuring-reference-photos, likeness-iteration]
updated: 2026-10-08
---

# Reference masks — making a reference the likeness gate can read

The likeness gate is only as good as the silhouette it scores against. These
are the ways a reference's mask fails, each silent and plausible, and the rule
that makes each measurable. What the score means once the mask holds:
[[silhouette-likeness]].

## Masks that cannot hold the subject

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

**Texture is no separator on a generated concept sheet.** An image model
renders a printed part with a paper-like grain and its ground smooth, which
looks like a free rule, but its soft drop shadow carries the same grain: a
local-standard-deviation mask (3×3, threshold 1.5) took in the shadow band on
the shadowed sides of every object, and against an exact colour mask on the
saturated ones it scored IoU 0.84–0.89 however far it was eroded. The tint did
separate them: cream objects read R−B 18–27 against 10 for the ground and at
most 14 for the shadow, so `saturated OR dark OR R−B ≥ 16`, then a 3 px
closing, fill and the largest blob, hugged cream and coloured objects alike.
Lay the outline over the image and look before scoring.

On the same sheet `ref_silhouette.py --ground tint` **dropped every neutral
subject and still reported ok**: a cream object came back as its blue scarf
alone (4 026 of about 41 000 px), a charcoal one as its purple emblem. Tint
mode needs a saturated subject. For a dark neutral subject on a light ground,
`--ground band --lum-band 140,255` matched the object to a pixel; the border
rule kept the soft drop shadow, 5–9 % of extra area that caps a perfect model
near 0.92, and the pose search half-hid it by tilting a flat part 6–13° off its
declared top view. Compare the new mask's area with the object's before using
any regenerated silhouette.

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
