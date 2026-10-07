---
title: Converging a likeness loop
tags: [likeness, iteration, sweep, history, regression, stall, cost, camera-replay]
aliases: [likeness loop, parameter sweep, edit loop, best round, stalled out, pose replay]
sources:
  - skills/image-to-cad/scripts/check_likeness.py (history, best-round and stall rules)
  - skills/image-to-cad/scripts/render_views.py (pose replay)
  - "toolchain: search 59.2 s vs replay 7.8 s with identical IoU on a six-part model, three references (reproducible)"
related: [silhouette-likeness, image-types-and-views]
updated: 2026-10-04
---

# Converging a likeness loop

A rebuild loop that renders many times and scores once cannot say whether any
round helped. These rules are what make a likeness loop converge instead of
wander.

## Score every round and keep the history

The only question between rounds is *did that edit help?* A report rewritten
in full each run erases the previous number, so that question has no answer on
disk. Keep one row per view per run and read the delta before editing again: a
round that moved the number down is a round to revert, and a run of stalled
rounds means the edits are not reaching the shape the score measures.

## The delivered round must be the best round

Against a floor alone every round between the floor and 1.0 prints "ok", so a
loop can wander downhill and deliver a worse shape with a passing gate. A run
scoring below the best that view has ever recorded is a regression, however
far above the floor it lands; overriding it is a recorded decision with a
reason.

## Why the floor does not come down

Below the floor every round fails with the same verdict, so the cheapest way
to change the output is to lower the floor — which measures nothing and reads,
in the record, exactly like a pass. A recorded acceptance is a decision; a
floor of 0.00 is a missing one. An acceptance on the first run is not even
that: nothing had tried to fix the mismatch yet. Rounds count per view,
because rounds spent on one viewpoint say nothing about a viewpoint scored for
the first time. Keep the measurement and the decision separate: the likeness
report records the failure as a failure; the acceptance lives in the pipeline
record, and below 0.90 only an explicit human acceptance of a measured failing
result can ship.

## Stop after three rounds that move nothing

Three stalled or regressing rounds in a row for one view (an improving round
resets the count) means the shape work is not reaching what is measured. Stop
rendering, report how many rounds the view has had, which run holds its best
and what the last three bought, and put the delivery decision to the user.
A stalled loop told to lower its own floor is how the number stops meaning
anything.

## Search once, replay while editing, search again at the end

Replaying each reference's stored camera instead of searching makes the IoU
delta between two runs belong to the shape, because the camera did not move —
and the search is almost the whole cost. On a six-part model with three
references at three FOVs: searching **59.2 s**, replay **7.8 s**, identical
IoU (0.954 / 0.914 / 0.891). Search again at the end: a big shape change moves
the best pose with it.

Other costs worth knowing before a sweep, from the same model:

- the build123d import is 5.2 s of every invocation and a whole render 6.3 s;
  twenty-five separate calls in one sweep spend two minutes on imports — put
  every view and every match in one call;
- searching three FOVs (0, 25, 40°) costs 2.6× one FOV (23.1 s vs 13.1 s for
  one reference); it is for the final measurement against a perspective
  reference, not the loop. A source-vs-STEP comparison adds 5.6 s and belongs
  only in the final run.

## A dimension no view measures can be measured through the score

Three-quarter views constrain depth only weakly and a single front view not at
all, so the axial chain of a reconstruction is usually the one number left
`[assumed]`. Sweeping one parameter with everything else fixed and reading the
searched-camera IoU is a **measurement against the references**, and cheap:
after the first tessellation each searched pose costs ~20 ms. Write the table
beside the value taken:

| `CHAMBER_L` | front | hero | iso |
|---|---|---|---|
| 17.5 | 0.948 | 0.908 | 0.876 |
| 22.5 | 0.951 | 0.913 | 0.882 |
| **26.0** | 0.945 | **0.916** | **0.890** |
| 34.0 | 0.951 | 0.914 | 0.892 |

Read the *shape* of the curve, not only its maximum:

- **A plateau** means the references stop constraining the parameter there.
  Take the low end of the plateau and say the constraint is weak — a value from
  the far end of a flat region is `[assumed]` wearing a measurement's clothes.
- **A flat line** means the feature is invisible from every reference angle —
  then **do not claim it**. On one reconstruction a conical rear from Ø80.5
  down to Ø50 moved the 3/4 silhouettes by 0.4 % of their area and the IoU by
  less than 0.001: other features set the envelope and the rear sat inside it.
  A shape the references cannot see is not evidence for a feature; modelling
  one anyway is invention with a number attached.

## When the sweeps go flat, read the residual blobs

Eleven knob sweeps (wing height, tail, track, tyre width, bumper) moved a
three-quarter score by under 0.003 each; what moved it by 0.03 in total was found
by labelling the silhouette difference. Overlay the normalised render on the
normalised reference (the gate's own `normalise`, centred), colour render-only and
reference-only pixels, label connected components and sort by area: the top
blobs name the feature (a tyre sitting 40 px off, a wing tip drooping, an
underbody that hangs too low) where a band ratio only names a height. Then
sweep the knob the blob points at. On a low, wide car the levers that mattered
were ride height, depth of the skirts, tyre diameter and the shape of the rear
fender; the ones that did not were global length and width.

Three other things the same run taught:

- **Search the lens per view.** A close, low photograph needs a wide lens in
  the search list (an 85 degree cone fitted the front view; the rear view of the
  same truck kept preferring 25 degrees). Passing only the default lenses left
  0.015 on the table. Both views can be given different lenses by one
  `--search-fov 25,85`; the search keeps the best per view.
- **Declare the camera that took the photo, including a negative elevation.**
  A camera at bumper height looks up at the car: `@-132,-10` puts the coarse
  grid on the true optimum, while `@-145,10` missed it by a grid step.
- **Pose replay hides what a coarse search misses.** A local refinement around a
  stored pose scored 0.906 where the full coarse search returned 0.886 for the
  same shape; always finish with the full search the gate itself runs.

A sweep harness is cheap to write in process: patch the parameter module's text
(a regex per `NAME = value`), purge the project's modules from `sys.modules`,
exec the patched text as `params`, rebuild, tessellate, refine the stored pose
by +-6 degrees and score. One point cost 33 s on a 55-part truck.
