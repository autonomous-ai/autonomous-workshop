---
title: Likeness on organic subjects
tags: [organic, figurine, likeness, decoration, loft, station, contact, interference]
aliases: [animal model, character model, figurine, surface decoration, station table, high likeness]
sources:
  - skills/image-to-cad/references/high-likeness-organic.md
  - skills/cad/references/organic-lofts.md
  - "experience: figurines whose decorations, tails and cues passed a side silhouette and failed in 3D or in interference"
  - "experience: a faceted concept sheet rebuilt as a smooth figure, judged not alike until the masses were measured and re-sculpted"
related: [form-to-construction-family, silhouette-likeness, repeated-scene-likeness, low-poly-sculpt-from-a-field, smooth-skin-from-a-field]
updated: 2026-10-05
---

# Likeness on organic subjects

For an animal, figurine, character, toy or any body whose likeness lives in
its silhouette rather than its dimensions, these are the ways a model that
passes the deterministic gates still loses the likeness — or passes the
likeness and fails the gates.

## Silhouette mass first, decoration second

Separate **silhouette mass** from **surface decoration**. Build and validate
the large organic core solids first: torso, head, tail, limbs, perch/base.
Then add colour bands, wrinkles, ridges, scales, spikes, beads and texture as
shallow surface details with bounded penetration, or as separate labelled
visual skins. A full-depth band or spike field cut through a lofted body needs
a named boolean/overlap limit that keeps the solid non-self-intersecting.

## Decorations as separate solids

Place separate decorations as true surface skins: tangent or with a tiny
visible clearance from the core, and non-overlapping with each other.
Grouping them into one "visual module" hides nothing: interference checks walk
leaf solids inside compounds, so a compound of overlapping colour patches,
tail joints, eye discs, mouth beads or bark rings still fails. If a decoration
must overlap to be manufactured as one body, fuse that local group into one
validated solid; otherwise keep it outside the core with clearance.

For bead rows, pupils, nostrils, separate jaw skins, torus tails and other
small cues, use a clearance at least equal to the detail's radius unless the
pieces are locally fused and revalidated. Do not spend a run on a connector
stem, bead row or stripe that is optional for the silhouette until the primary
body, head, perch and tail clear interference.

## Spirals and curls self-intersect

A tube following a small-radius spiral can self-intersect while still looking
like the right construction. Start tight decorative curls with a
collision-safe approximation — a torus or partial ring, a few non-touching
arcs, or an obviously separated raised spiral line — and refine to a real
spiral only after validation and interference pass. When a crest or dorsal
marker's surface height is uncertain, place the first version clearly outside
the core, not "almost embedded". A risky swept feature (tail spiral, curled
tube, horn, crest chain) is trusted only once validated as the actual emitted
part, never because a standalone helper once looked plausible.

## Two wrong ways to clear an interference

- **Exploding the model.** A gap between a cue and its core is a defect for a
  likeness target whether or not a render shows it. A cue that reads as
  floating — eye discs, mouth beads, jaw patches, dorsal spikes, crest,
  stripes, tail curl — is grouped with its local core and proven as a group.
- **Moving a feature along the hidden axis.** A side-view part shifted along
  the unseen depth axis still passes the side silhouette while becoming wrong
  in 3D: a tail no longer rooted in the body, toe pads no longer gripping the
  branch, colour bands standing off the skin as rods. Each defining feature
  needs a maximum visible gap or contact constraint satisfied in the actual
  assembly pose.

## Contacts are declared, not sunk

For every seated module — head into body, tail into body, limb into body, foot
on perch — name whether it is `clearance`, `intentional seated contact` or
`cosmetic near-contact`, with a minimum/maximum contact allowance. If it is
not a real connector, leave a visible air/contact relation rather than sinking
the parts into each other; a visual pose may not rely on large overlaps.

## A station table needs a section vocabulary

Radius-only elliptical stations are insufficient when the reference shows a
flattened flank, keel, cheek, brow or asymmetric belly; record the
cross-section shape and landmark rails at each station. Sparse ruled ellipse
lofts produce a faceted barrel even when their side envelope is correct.

- A defining blade — casque, crest, ear, fin — is not a constant-depth
  extruded side polygon: give it at least three depth stations and loft the
  rounded volume.
- Capsule chains are acceptable only as pose/contact probes for limbs; a
  reviewable limb needs tapered segment lofts and explicit joint transition
  masses.
- Conformal colour shells need measured boundary curves in side/profile space;
  intersecting a shell with repeated full-height slabs gives technically
  conformal but visually uniform bands.

## Safe primitives are probes, not deliverables

A generic safe primitive in place of a defining silhouette is acceptable only
as a temporary gate probe; in the delivered model, defining cues use a form
family that matches the image ([[form-to-construction-family#do-not-downgrade-organic-silhouette-features-to-boxes]]).

## Fitting a posed figure to several silhouettes

A figure whose masses are parameters (joint points, radii, a camera per view)
can be fitted to its reference silhouettes instead of nudged by hand: render
the field's contour with the likeness gate's own rasteriser, normaliser and
IoU, and move one parameter at a time while the score rises, halving the step
when a round buys nothing. Five things decide whether the result is a figure
or a puzzle solution:

- **Bound every parameter to anatomy** (positions within a window of the hand
  read, radii within ±40 %). Unbounded, the fit trades masses the views cannot
  tell apart: a side view cannot separate a thin chest behind a thick upper
  arm from the reverse, and the fit drifted to a 28 mm deep torso with 14 mm
  elbows. Keep asymmetric freedoms explicit and few (one knee lower than the
  other in crossed legs).
- **Score the weakest view, not the mean.** Maximising the mean spends one view
  to buy another; `0.5 * mean + 0.5 * min` balanced three views to within 0.01.
- **Hold a void with a penalty, not a hope.** A gap the pose depends on (air
  between forearm and thigh) is a few hundred pixels and the fit fills it to
  gain elsewhere; add a penalty on the measured clearance.
- **Hold the contact face too.** The silhouette cannot see a 2 mm lift, so the
  fit raised a figure's knees off the desk and left only the seat touching:
  the outline barely moved while pressing the screen's front edge would tip it.
  Give the base its own mass (a low wide pad whose cut face is the contact),
  bound it, and assert the contact area and a tipping margin after every fit.
- **Restart the cameras from where the picture says, not where the last fit
  stopped.** A three-quarter camera that settled at 4 deg elevation on a render
  that plainly looks down held every other parameter in a worse optimum;
  restarted with the elevation bounded at 15 deg and refitted, all three views
  rose by about 0.005-0.01. An interior cue the silhouette cannot see (the dark
  outline of a screen) added as a weighted second overlap keeps the camera and
  the part's orientation honest.

Generated multi-view concept sheets are not one object: the views disagree
(a tray thick as a wedge in profile and thin as a slab in the three-quarter
view; a knee larger in one view than the opposite view allows), so the fit
plateaus near IoU 0.93-0.95 per view however many masses it is given, and the
low-poly reduction then costs about 0.01 on the most curved profile. When the
plateau is reached, compare shaded renders with the references and stop; more
rounds move thousandths. The construction is [[low-poly-sculpt-from-a-field]].

## A silhouette cannot see a limb in front of the body

The fit balances what the outlines show, and an upper arm hanging in front of
the torso in the side view and beside it in the three-quarter view shows
almost nothing: a fit left the upper arm 20 mm thick and the forearm 26 mm at
the elbow, where the side render measured 26 mm and 16 mm (the taper
inverted). A fit also narrows chest and shoulders whenever that buys a few
pixels elsewhere. So:

- **Measure limb thickness where the limb is free** of the body in some view
  (a forearm reaching forward in profile, read on a coordinate grid at the
  view's mm/px) and hold those numbers out of the fit.
- **Judge the masses shaded, beside the reference**, at the reference's own
  camera: a smooth-shaded render of the field next to each crop, seconds per
  round, where a B-rep review render costs minutes.

## A faceted reference built smooth

When the reference is faceted and the delivery is a smooth surface, the facets
are not the likeness to chase; the masses they describe are. Ellipsoids and
round cones blended into one field read as a mannequin beside such a render.
What made the smooth version read like it:

- **Soft boxes for planar masses**: superellipsoids (`(|x/a|^n + |y/b|^n +
  |z/c|^n)^(1/n) = 1`, first-order distance `(s - 1) / |grad s|`, the ellipsoid
  at n = 2) with n about 2.8-3.2 for chest and thighs give broad planes,
  square shoulders and blunt knees; keep the waist near n = 2 or the trunk
  becomes a barrel. Limbs get the same with a superelliptic section.
- **The breaks between planes as grooves and cones**: a sternum valley, a
  spine groove and a glute cleft carved by a smooth subtraction along a
  polyline set into the field's own surface (found by bisection from inside),
  and breasts as a cone from a point merged into the chest to the apex,
  giving a defined underside and no crease on top.
- **Small relief blobs make it lumpy**, not defined: separate collarbone,
  trapezius and shoulder-blade primitives read as straps and pads. Broad
  changes of form carry the read; a narrow blend radius on a small mass does
  not.
- Raising n grows a mass at the same radii; refit the radii to the
  silhouettes after each change of form.

The smooth surface itself is [[smooth-skin-from-a-field]].
