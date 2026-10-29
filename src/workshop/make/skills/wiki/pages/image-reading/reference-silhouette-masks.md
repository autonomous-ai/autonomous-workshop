---
title: Reference masks — making a reference the likeness gate can read
tags: [likeness, silhouette, mask, reference-image, shadow, background, flatten]
aliases: [reference silhouette, flatten reference, ref_silhouette, light ground, cream on cream, drop shadow mask, concept sheet silhouette, contact shadow, relative saturation, tint hue, neutral frac, contact crease]
sources:
  - skills/image-to-cad/scripts/ref_silhouette.py (flattening rule; border chroma rule for a light ground)
  - skills/image-to-cad/scripts/measure_image.py (the gate's own mask; vertical-gradient backdrop)
  - "experience: flattened references scored 0.945 / 0.916 / 0.890 where raw masks scored 0.78-0.85, geometry unchanged"
  - "experience: silhouettes cut from a generated ten-object concept sheet, texture mask against tint mask"
  - "experience: a hat on a lamp shade scored from a cropped, tint-tuned photo against a view-only dressed entry"
  - "experience: a grey voxel plinth on a grey shade"
  - "experience: a cream egg on a cream ground defeated both toolchain masks; red-minus-blue after a median filter separated it"
  - "experience: a brown token's dark contact shadow kept by every mask until a relative-saturation rule"
  - "experience: white, cream and two-hue pixel keys on a cream sweep that no single ground rule held; a top face swept down by the wall did"
  - "experience: a dark cat over a dark lamp shade: an orange-only mask capped likeness near 0.88; a band-rule mask with the host painted out scored the whole hat above the floor"
related: [silhouette-likeness, measuring-reference-photos, likeness-iteration]
updated: 2026-10-12
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
that one colour becomes background — pale parts near the top go, and even the
designer's own geometry, drawn straight from its source file, scores far below
the gate. The flattener cannot help (its ground must be unsaturated). The mask
now recognises a vertical-gradient backdrop — the two side columns agree row by
row, the top and bottom bands are each flat across the width, and top and
bottom differ — and measures each pixel against its own row's backdrop colour;
a flat ground and a radial vignette fail the test and keep the single-colour
path.

Two things that look like a shape problem on such a reference and are not:

- **An off-axis pose for an orthographic view.** A CAD screenshot is taken
  along an axis. When the camera search returns az −91.88 for a view that is
  plainly −90, it is fitting the mask's losses, not the model — the fixed mask
  brought the search back to −90.00 exactly. Check the mask before editing.
- **A clipped extremity after cleaning.** Paint out a logo or a ground line by
  its own pixels (its connected blob, the line's own rows), never by a whole
  band of columns or rows: a band clips the subject's tip, and because the gate
  normalises by the bounding box, 3 px off the feet (under 1 % of the height)
  rescales the whole silhouette and costs points of IoU on a lacy outline.
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

**A dark subject on a near-white ground** is the case the border rule gets
wrong: its soft contact shadow runs more than 60 darker than the border, so the
border rule keeps the shadow as object and fattens the outline on the shadow
side. Luminance is what separates them, so raise the band to the ground
instead: `--ground band --lum-band 110,255` keeps a black print (luma ~40-80)
outside the band and puts the ground and the grey shadow inside it, while a
cream stripe or dot on the subject stays object through its saturation. The
tell is the diff of render against reference: a band of reference-only pixels
along one side of every edge, the side away from the light.

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

A saturated accessory photographed on a **dark host** in front of a cream
ground needs the tint band narrowed by hand: plain `--ground tint` dropped the
lit side of green coils. Measure hue and saturation of ground, host and
subject first (cream 0.17 at 37 deg, charcoal 0.09-0.17 at 35 deg, green
0.33-0.41 at 65-69 deg), then set `--tint-sat` between host and subject and
`--tint-hue` off the ground's hue. Crop the photo to the accessory and score
it against a view-only entry holding only that accessory
(`--likeness-entry`), posed in the host's world frame: the pose search reaches
only about 15 deg of roll, so an upright accessory frame cannot find a leaning
photo.

A neutral subject sitting on a neutral host (a grey plinth on a grey lamp
shade) defeats the band, border and tint rules alike. Paint out the host below
the subject's bottom edge along a polyline read off a coarse pixel grid. Keep
the script that does it in `measure/`, and record the polyline in the README.

A black accessory over a dark host defeats every colour rule. Connectivity
can still separate them when a light gap divides the two: drop the dark
regions that touch the crop's bottom edge.

When there is no light gap but the accessory's top stands against a light
backdrop, score the whole accessory instead of its coloured part. Flatten with
the band rule, raising the band to the backdrop (for a cream sweep,
`--lum-band 140,256 --sat-max 55`), so the backdrop is ground and everything
dark or coloured is object. Then paint out the host below a polyline read off
the photo along the accessory's lower outline, keep the largest blob and fill
holes. Score a dressed entry with every visible part. A mask of only the
coloured body, notched where dark parts stand in front of it, caps the score:
its own convex hull covers it at well under 1.0. After such a paint-out,
`ref_silhouette`'s outline-agreement check can exit 1 on a good file. Judge the
overlay, not the exit code.

## Subject and ground colour choose the ground rule

Measure relative saturation `(max − min) / max` and tint direction (R−G, B−G)
on subject, shadow and ground before choosing a `--ground` mode; the modes
themselves are in `skills/image-to-cad/references/likeness-gate.md`.

- **A coloured subject in its own dark contact shadow** (brown, red, green
  under a key light). The shadow is neutral at every brightness and the
  subject is not: a tinted subject reads about 0.45 or more from lit face to
  deepest groove, its shadow about 0.3 or less. That is the `--ground tint`
  rule; band, border and the gate's default mask all keep the crescent.
- **A neutral subject on a tinted ground** (grey on cream) is the tint rule
  inside out: grey lit faces read 0.02–0.06, the cream ground about 0.10, its
  warm contact shadow 0.13–0.30, so the stock mask sees almost none of the
  subject and the border rule keeps the whole shadow. Colour alone still loses
  every wall facing away from the light, whose lower edge, bounce-lit by the
  warm ground, matches the shadow beside it at the same luminance. What
  separates them is the thin **contact crease** where wall meets ground,
  darker than both: a black top-hat finds it, and as a barrier it stops the
  border flood at the true base. `--ground neutral` does exactly that. Check
  its overlay along the shadow side, where a faint crease lets the flood leak,
  and sweep `--neutral-frac` (default 0.8) against the overlay: too high lets
  the warm shadow bleed in, too low eats the far edge.
- **A pastel subject in a shadow just as unsaturated.** The shadow keeps the
  *direction* of the ground's tint, the pastel points another way:
  `--ground tint --tint-sat 0.25 --tint-hue 30` calls a pixel ground only when
  it is both unsaturated and tinted near the border's direction. A part tinted
  the ground's own way survives only by being too saturated to be ground.
- **A pale or two-hue flat plate on a cream sweep.** Shaded white, cream or
  pastel walls and the warm shadow beside them have the same saturation and
  luminance, JPEG chroma subsampling blurs what difference there is, and a
  subject with one colour near the ground's hue and one far from it fails
  every single rule: `tint` drops the near-hue part, `neutral` and `border`
  keep the shadow. For a constant-thickness plate lying flat, build the
  outline geometrically: take each lit top face by its own colour rule
  (saturation for yellow and red, blue minus green for lavender, luminance for
  white), fill enclosed holes, then sweep the mask straight down the image by
  the wall height, read as the distance from the top edge to the contact
  crease (the luminance minimum). Keep the largest blob and write the
  holes-filled mask the gate reads.
- **A cream subject on a cream ground.** Neither luminance nor saturation
  separates them; warmth does — red minus blue after a 7 px median filter
  (the median removes print-line texture): a neutral ground reads near 10, a
  cream or tan subject 15–40. The contact shadow picks up warm bounce light
  from the subject and reads 16–26, so give the shadowed band under the
  subject a higher threshold than the lit side, and cut below the lowest point
  the grid overlay shows. Keep such a probe as a documented script beside the
  reference. On a warm ground (a pink-beige sweep) red minus blue stops
  separating, both reading 25–45; the hue ratio (G−B)/(R−B) still does — an
  ivory or yellow subject about 0.45 at every brightness, the ground about
  0.35 — and an Otsu split of its median-filtered map finds the threshold. The
  median pushes that mask's edge 3–5 px outward all round, so re-classify a
  band of about 10 px either side of the edge pixel by pixel against a smooth
  background estimated from the pixels outside the band (normalised
  convolution). A glossy desk still returns a contact shadow and a reflection
  that no colour rule removes: read the top of the dark contact line as a
  polyline and cut there.

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
