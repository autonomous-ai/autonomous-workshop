---
title: Silhouette likeness — what it measures and how it lies
tags: [likeness, silhouette, iou, camera, handedness, mirror, mask, reference-image, scene, landmark]
aliases: [likeness score, silhouette iou, pose search, mirror image model, reference mask, shaded review, board and pieces, tray of parts, populated surface, piece placement, landmark inventory, repeated scene]
sources:
  - skills/image-to-cad/scripts/render_views.py and check_likeness.py (pose search, windowed camera, reflection check, hole filling)
  - skills/image-to-cad/scripts/ref_silhouette.py (flattening rule; border chroma rule for a light ground)
  - "toolchain: fixed orthographic camera 0.865 vs searched camera 0.974 on one perspective reference, same model (reproducible)"
  - "toolchain: chiral fixture — a mirror-image model scores 0.9859 under a free azimuth search (reproducible in the render_views self-check)"
  - "experience: a voxel tree hat posed by matching the lamp head's silhouette"
  - "experience: scenes that matched their archetype while missing most of their defining landmarks"
  - skills/image-to-cad/references/repeated-scene.md
  - "user correction: a hat tipped 9 deg off its pumpkin to match a photo looked lopsided; coaxial was preferred at a lower likeness"
  - "user correction: a pumpkin face aimed at the photo camera showed its side from the lamp's front"
related: [likeness-iteration, measuring-reference-photos, organic-likeness, reference-silhouette-masks]
updated: 2026-10-12
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

## A pose that raises the score can still look wrong

A small tilt of an accessory off its host's axis (a hat tipped on a head) can gain
several points of IoU, because it copies a lean in one photo. Seen in three
dimensions on the host, the same tilt can read as lopsided. A sweep of a pose
angle is not a design decision: show the reviewer a shaded render from more than
the photo's camera before keeping a tilt the sweep found. Prefer coaxial seats
unless the lean is part of what makes the object recognisable. If the reviewer
rejects the tilt, the lower score is an accepted mismatch, not a defect to tune
away. `verify_project --likeness-accept-mismatch` records the acceptance only after
the score has stalled for three rounds.

The same goes for which way an accessory faces. A face turned toward the photo's
camera matches the photo. On the host, the user looks at it from the host's own
front, and from there they see the accessory's side. Aim a face along the host's
front axis and let the camera search find the photo's view.

## A silhouette hides a machine's identity

A machine's identity is interior — slots, pockets, bores, a pin on an arm, one
part seated in another — and a filled outline shows none of it: an assembly
renders as a single blob whose parts cannot be told apart at any resolution.
Review appearance on a shaded render with the same frame and camera, score on
the mask; neither replaces the other, and neither sees colour or material the
way a person does.

## An accessory on a supplied host: find the camera from the host

When the photo shows an accessory on a host you hold as a STEP, paint the
accessory out and match the **host's** silhouette (`render_views --match`).
That fixes the camera independently of the part you are designing, and the
accessory is then scored in the host's world frame. For a host symmetric in
Y, the match `(az, el)` is equivalent to `(-180 - az, -el)`, so choose the
one that puts the camera on the side the photo shows. Decorations on faces
seen edge-on add silhouette bumps that cost IoU; put them on faces seen
face-on.

A free search on a bell-shaped host can land on a mirrored pose from below
and behind that scores higher (0.90 against 0.81) than the true camera.
Window the search to the side the photo shows. When the rim that sets scale
is hidden, a fully visible feature of the same host (a glow ring) measured
in a sibling photo can carry the scale.

If the photo's host is posed differently from the supplied STEP (a
stylised render, or an articulated head), matching the host fails. Read the
camera off the accessory itself, then rotate it through the dock frame into
world coordinates. Keep the search window about +-15 deg, because +-40 let it
turn the face away and look from below. If the host hides the accessory's
bottom in the photo but not in the scored entry, the search settles low, so
treat a thin pass as thin.

Inside a wide window the likeness search can lock onto a poorer local
camera (0.893 where a narrower search found 0.909). Search once, then declare
the camera it found with a tolerance of about +-15 deg, and record both runs.

Fitting an accessory whose image shows a different host, scoring a pair of
pieces, and why a plate's face and side wall look alike to the score:
[[accessory-likeness-on-a-different-host]].

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
*same* pose for viewpoints that are plainly different, inspect the reference
masks as well as the model: the search may be fitting holes instead of the
outline. Nearby cameras alone do not prove a mask defect. A thin plate near
edge-on, an appendage emerging from occlusion, camera roll or perspective can
change the outline sharply within a small angular interval.

A best fit on a declared camera-window boundary is a diagnostic, not a
calibration or proof of wrong geometry. The initial window may itself be an
inference. Check visible planes, facial landmarks and the complete scene
before assigning the cause. In an assembled reference, a support can hide
an underside or socket that appears in an isolated part render. Its absence
from the photograph does not by itself establish positive local camera
elevation. Review both an independent fixed view and the seated assembly,
record the remaining camera uncertainty, and retain the original score
history. Do not enlarge the camera window merely to turn a failure into a pass.

Dissimilar reference outlines at nearby cameras are a contradiction only
when the model's own outlines at those two poses stay similar; if the model's
differ too, the geometry itself changes sharply there (the gate's
`MASK SUSPECT` check, `skills/image-to-cad/references/likeness-gate.md`). That
never excuses a per-view likeness failure or a reference mask that visual
inspection shows to be wrong.

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

## Repeated-piece scenes: the frame dominates the outline

A board and its men, a tray of parts, a rack, a tiled or populated surface can
match its broad archetype while missing most of what defines it, and a single
likeness number will not say so: the outline is dominated by the frame, not by
what sits inside it. So every landmark category is scored on its own; the
inventory and the gate are `skills/image-to-cad/references/repeated-scene.md`.
Three facts behind that gate:

- A grid sampler, farthest-point distribution or random seed with the right
  count creates a conspicuous new composition. Reproduce the observed
  placement unless the reference itself is procedural.
- A visually plausible centroid can still sit in an excluded region or share a
  site. Full-assembly interference finds that late; a placement audit before
  geometry finds it early.
- A full-scene render cannot prove a small feature even when it technically
  exists, so a small landmark needs a local verification target.

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

## An open gap must be empty at every depth

A silhouette sees through the whole model, so a gap the reference shows open —
between a torso and a hanging arm, between the legs, under a wing — is matched
only when nothing at any depth crosses it. A support hidden behind the body in
the shaded view still fills the gap in the outline: a backpack arm running out
to a wing joint, well behind the torso, closed the front view's gap between
torso and arm and cost about 0.005 there. Route hidden structure behind
something the reference's outline already covers at that height (here a pillar
standing behind the forearm), and check every open gap's rows in the overlay
after adding anything behind the body.

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
