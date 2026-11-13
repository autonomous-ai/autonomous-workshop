---
title: Reviewing a character against its concept
tags: [character, likeness, critique, review, face, mask, ear, neck, figure]
aliases: [feature measures, side-by-side numbers, patch outline, camera-traced cut, concept checklist, trait checklist, two judges, likeness review, hood face, buried ears, neck stub, character critique]
updated: 2026-11-02
sources:
  - "toolchain: concept-only trait checklist judged by a critic and an independent reviewer over five render rounds at the concept camera (measured)"
  - "toolchain: owner-named features measured on concept and render at the concept camera; 33 of 45 measures out before, all in after, patch IoU 0.65 -> 0.92 (measured)"
  - "toolchain: spheroid head 1.36 wide - ear spheres at a fixed radius buried, chest top grown past the head section read as a collar, inset 0.3 left an open mesh, 0.8 printed (measured)"
---

# Reviewing a character against its concept

How to judge whether a modelled character looks like its concept art, and
the face, ear and neck faults that review found. Proportion rules are in
[[character-proportions-and-appeal]]; outline scoring is in
[[likeness-iteration]].

## A concept-only checklist and two judges

Before any critique round, have an agent that sees only the concept write a trait
checklist: 8–12 traits, each with a measured ratio and a pass/fail
test. Then loop with two judges, the critic and the independent reviewer,
until both agree on every trait. Disagreement is the useful signal. One
judge shown the figure without its base failed "floats low in the water",
so give every judge the full scene as well as the figure crop and a head
close-up.

## Faults the judges found, and their fixes

- **A light mask that wraps the whole front reads as a hood.** With the mask
cap's edge all round the head's silhouette, brown showed as a ring at the
chin and cheek too: a balaclava, not an otter. Lower the mask and make it
smaller, so the cream reaches the chin and the lower outline and brown is
left only as a crown cap. Then set the eyes about 0.35–0.4 head widths
apart, just under the mask's top edge; at 0.2 they crowd the nose.
- **Place ears on the surface, not at a radius.** On a head wider across
than it is tall, ears at a fixed distance from the centre sink inside the
wide side and vanish from the outline. March to the surface along each
ear's direction and centre the ear there, so half of it shows. Hang a 45°
teardrop cone under an ear that sticks out sideways, or its lower half
needs support.
- **A neck reads as a stub when its top is wider than the head.** A chest
ellipse grown past the head's section, to carry the underside, showed as
a straight-walled collar beside the head. Take the chest top from the
head's own horizontal section, inset 0.8 mm (an inset of 0.3 left an open
mesh at the seam), at or just below the height where the head's flank reaches 45°. For
a spheroid w times wider than tall that height is 1/sqrt(1 + w²) of the
radius below the centre. Then bulge the flank as a rounded shoulder down
to the foot.

- **A mouth crease is a dark inlay, not a groove.** The review renders
have no cast shadows. A V-groove cut in the cream lit up as a pale ribbon at
0.6 mm deep and vanished at 1.2 mm deep. A rib of the brown head pushed
through a slot in the mask hung out sideways in the print pose. Print the
line as its own dark strip glued flush into a groove. Extrude the strip
along the mean surface normal over the traced line from one flat floor, so
it prints flat; extruded along the mask's own normal, its top edge was a
0.2 mm knife. At a 0.4 mm nozzle the strip cannot be narrower than 0.9 mm,
so it reads heavier than a sculpted crease. Size the groove from the strip
with `cadfits`, and give the strokes round ends, or the ends read as square
stubs.
- **A cupped ear reads as a C only when the cup breaks the rim.** A centred
cup reads as a button. With a cup offset 0.35 of the ear radius, a thin rim
still closed it into an O. At 0.7, toward the face and down, it opened as the
concept's C-shell. Cut the cup from the head as well, or the head's surface
shows inside it as a pale lens. Make the far ear smaller (0.8 here) rather
than turning it edge-on: at 0.3–0.45 of the turn it read as a thin brim
along the outline. Set the ear's support strut back behind the disc's
camera face and narrow it (0.85 of the chord), or the strut shows as a lip
under a disc that leans toward the camera.
- **Make a pad proud of the surface it sits on.** On a head wider than it
is round, a pad placed at the nominal radius plus 1.1 mm stood only 0.5 mm
proud of the actual cream and did not read as a pad. March to the real
surface along the pad's direction and add the height there.

## When the owner names features, measure them

Two judges agreeing on every trait is not enough when the owner still sees
differences: their verdicts were "agree" while the head tilt, face patch,
eyes, nose and paws were all measurably off. For every named feature,
measure it on the concept and on a model render from the same camera, in a
frame that cancels scale, then fit until each measure is within tolerance:

- **Head frame.** Fit an ellipse to the head outline inside an angular
  sector that skips the ears and the neck. Use its centre as the origin and
  R = sqrt(a·b) as the unit, with x to the right and y up in the image.
  Measure the eye centres, the nose, the eye-line roll, the outline's w/h,
  and the patch edges by marching along the eye-line frame. Workable
  tolerances: positions ±0.06 R, patch edges ±0.07–0.10 R, eye spacing
  ±0.03 W (W = 2R), nose size ±0.02 W, roll ±4°, w/h ±0.08, and patch IoU
  at least 0.80 in the normalised frame.
- **Limb frame.** Use the axis from the body centre to the head centre,
  with its length L as the unit. Fit each paw as a moment ellipse and
  measure position ±0.05 L, size ±15 % and axis angle ±15°.
- **Measure every reading of a vague word.** "Tilted too much" can mean
  the slope of the eye line or the axis of the head outline. An elongated
  outline set diagonally reads as a tipped head even when the eye line
  already matches. Report both, and say which one changed.
  Give the head spheroid its own roll about the face direction, separate
  from the frame that places the eyes and nose. Then the outline's axis can
  move without moving the face. The bounds of the face inlay must turn
  with the spheroid.
- **Do not place geometry by a rendered highlight.** The brightest blob on
a pad follows the light. When the pad moved up, the blob moved down. Draw
the feature itself in a flat marker colour (for example, the part of the
pad more than 0.5 mm above the plain surface) and measure that.
- **Show the numbers with the pictures.** Put concept, before, after and a
  50 % blend side by side, aligned in that frame, next to the table. Then
  have each judge rule on each feature: MATCHES, CLOSE or DIFFERS. In the
  next round the judges named what the numbers missed: outlines that pass
  their position checks but are straight where the concept curves, a
  pointed wedge where the concept's is blunt, toe slits instead of notches.
  Fix those by tracing the concept's measured outline, not by loosening the
  tolerance.

The measuring itself is easy to get wrong:

- **Shadowed fur can segment as black.** Count only the eye and nose blobs
  as part of the patch, not every dark pixel, or the patch grows into the
  shadow under the chin.
- **Close thin grooves before you march.** Close grooves up to about
  0.08 R first. Otherwise a march from the nose down stops at the
  concept's philtrum or mouth line instead of the bottom of the patch.
- **Nudge flat-colour markers toward the camera.** A marker copy of a part
  scaled 1.02 about its centre z-fights with the part. The part showed
  through, and the paw widths read 20 % low. Move each marker 0.4 mm toward
  the camera.

To place a patch edge where the concept puts it, trace the edge as a
polygon in head radii from the eye midpoint. Cast camera rays onto the
head and build a ruled loft along the seat normal. Offset each vertex
along its mitred normal by tan(draft) × its depth, so every wall passes
through its traced point (a tapered extrude drifts off the trace).

- **Cross the cap rim steeply.** A cut that runs along the rim leaves a
  strip on one part or the other.
- **Keep the cut clear of any boss seated on the cap.** If the bare head
  under the cut meets a boss such as the nose, the two parts clash.
- **Choose the wall draft per edge.** On a steep part of the head the
  draft makes one part's edge acute while it opens the other's (see
  [[knife-edges-and-tapers]]).
