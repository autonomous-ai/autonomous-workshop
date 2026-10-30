---
title: Accessory likeness when the image shows a different host
tags: [likeness, silhouette, accessory, host, camera, scale, ellipse, pair, blob, plate, yaw]
aliases: [accessory on a different host, relief direction, raised vs recessed, ambiguous relief, hollow-mask illusion, concept host differs from the STEP, drum vs flared shade, fit through the STEP host, two ears two blobs, pair of pieces likeness, plate face vs side wall, square plate distorted to fit, free plane fit]
sources:
  - "experience: cat ears fitted to a concept whose head is a drum, built on a flared shade STEP"
related: [silhouette-likeness, scale-anchors, likeness-iteration, reference-silhouette-masks]
updated: 2026-10-13
---

# Accessory likeness when the image shows a different host

An accessory designed from a concept image is scored against that image, but
built on the user's own STEP host. When the two hosts differ, three things go
wrong that a plain likeness loop does not notice.

## When the image's host is not the STEP's host

A concept or AI edit often shows the accessory on a host that only resembles
the one you hold (a drum shade in the image, a flared one in the STEP). Then
the host's silhouette cannot fix the camera, and an accessory fitted on the
image's host is wrong on the real one: a pair of ears fitted on a drum scored
0.95, and the same plates cut by the real flared shade scored 0.78, because the
shade falls away behind the rim and swallows a different part of each plate.

- Fix the camera and the scale from a **clean feature the two hosts share**,
  fitted as a conic: a lit ring or a centre plate concentric with the rim gives
  the face's tilt and orientation; scale that ellipse out to the rim's outer
  pixel for the size. A conic fitted straight to the host's outer silhouette
  mixed in the flank and read the face 0.94 round against the ring's 0.73.
- Fit the accessory through the **STEP host**: cut each candidate by the real
  host's solid of revolution (or shell) before projecting it, so what is scored
  is the solid the CAD will build. Tie the fit to the image with the anchor's
  ellipse and each piece's tip position as penalty terms, or size and placement
  wander freely under per-piece height normalisation.

## A pair of pieces is two blobs

The gate keeps the largest connected blob of a silhouette, so two ears, two
horns or two handles cannot be scored as one reference. Mask each piece
separately (cut the mask at the occluding edge it shows, hull a convex piece
whose shaded edge drops out of a colour rule) and give each its own view-only
entry that places that one piece in the image's pose; pass both to the runner
with `--likeness-entry`. Gate both: dropping the piece the bead half hides is
dropping evidence, and the half-hidden one still scored 0.92.

## A silhouette cannot tell a face from a side wall

A flat plate is the worst case for IoU. Fitted square to an axis when the image
shows it turned, a fit reshapes the outline until the plate's side wall fills
the silhouette where the image shows its face: it passed at 0.94 and looked
unlike the reference (bulged edges, thick wall, wrong tip). Before trusting a
plate fit, fit once with the plane free to turn; if the free fit scores clearly
higher with a large turn, the fixed plane is the defect, and the choice between
the brief's plane and the image's goes to the user.

## A silhouette cannot see relief, and shaded facets read both ways

Relief inside the outline (a raised pyramid against a hollow, a dome against
flat facets) does not change the silhouette, so the likeness gate passes either
way. Feedback about relief is easy to misread, and every reading passes the gate.
In one case five inserts in a row were rejected: pillow-soft, hard facets, a hollow
with hard creases, a soft pyramid, and a soft pyramid sunk below the face. The user
wanted a soft hollow. The approved concept showed a hollow too, but its three
shaded facets read equally well as a pyramid (the hollow-mask ambiguity: with
the light direction unknown, a light facet and a dark facet fit a recess or a
boss alike). The builder read it raised; the user had meant recessed all along.

- Shaded flat facets with no cast shadow, occluded wall or highlight at a
  crease do not fix their direction. Name the image as ambiguous rather than
  reading a direction off it; look for a cue that does decide it (a wall seen
  inside the rim, a shadow cast by the rim, the user's own photo) or ask.
- When the photo and the concept disagree on a recess or a boss, do not pick one.
  Draw both as sections beside the two images, and ask which direction and which
  softness are meant, before building either.
- A flat-lit render cannot settle the question, because a hollow and a pyramid
  render alike. Show the user a section; "lõm"/"lồi" (recessed/raised) are about
  depth, which only a section shows.
- Do not trust a flat-lit render to show the direction: a hollow and a pyramid
  can render alike. Check it in source with a landmark, for example the facets
  must lie below the rim.
