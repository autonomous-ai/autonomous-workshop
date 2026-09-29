---
title: Likeness on organic subjects
tags: [organic, figurine, likeness, decoration, loft, station, contact, interference]
aliases: [animal model, character model, figurine, surface decoration, station table, high likeness]
sources:
  - skills/image-to-cad/references/high-likeness-organic.md
  - skills/cad/references/organic-lofts.md
  - "experience: figurines whose decorations, tails and cues passed a side silhouette and failed in 3D or in interference"
related: [form-to-construction-family, silhouette-likeness, repeated-scene-likeness]
updated: 2026-09-23
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
