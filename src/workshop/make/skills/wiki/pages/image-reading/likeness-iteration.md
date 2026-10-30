---
title: Converging a likeness loop
tags: [likeness, iteration, sweep, history, regression, stall, cost, camera-replay]
aliases: [likeness loop, parameter sweep, edit loop, best round, stalled out, pose replay]
sources:
  - skills/image-to-cad/scripts/check_likeness.py (history, best-round and stall rules)
  - skills/image-to-cad/scripts/render_views.py (pose replay)
  - "toolchain: search 59.2 s vs replay 7.8 s with identical IoU on a six-part model, three references (reproducible)"
related: [silhouette-likeness, image-types-and-views]
updated: 2026-10-11
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
report records the failure as a failure, and an acceptance is recorded apart
from it.

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

When one-knob sweeps each move a score by almost nothing, label the silhouette
difference instead. Overlay the normalised render on the normalised reference
(the gate's own `normalise`, centred), colour render-only and reference-only
pixels, label connected components and sort them by area: the top blobs name
the feature (a wheel off its station, a drooping tip, an underside that hangs
too low) where a band ratio names only a height. Then sweep the knob the blob
points at; the global length and width are rarely it.

- **Search the lens per view.** A close, low photograph needs a wide lens in
  the search list, and another view of the same subject may prefer a long
  one. One `--search-fov` list serves both; the search keeps the best per
  view.
- **Declare the camera that took the photo, including a negative
  elevation.** A camera below the subject looks up at it; declared with the
  wrong sign, the coarse grid can miss the optimum by a grid step.
- **Pose replay hides what a coarse search misses.** A local refinement
  around a stored pose can score above the full coarse search for the same
  shape; always finish with the full search the gate itself runs.

## Read the reference's pose before reshaping

When the score stalls in the high 0.8s, measure where the model's features
land on the reference before changing any shape. Project model landmarks
(fin tips, antenna tips, chin, fists, knees, toes) through the matched camera
and the gate's own alignment (height-normalised, centred on the bounding box)
onto the reference's pixels, and read the offset of each:

- **Offsets that differ by side are an alignment or extent problem.** When
  every head feature sits 6-12 mm left of the photo's, something at the far
  right of the model (a wing tip) is pushing the box centre; fix that part,
  not the head.
- **Paired features with opposite vertical errors suggest a pose; test it
  before building a joint for it.** Left antenna high and right antenna low
  reads as a tilted head, but roll the head on a surrogate (below) first: a
  flat, symmetric fin plate's blades can lean the other way in the same photo,
  and then every roll angle at every pivot scores lower. Thin features also
  mislead here, because the gate erodes their tips (below).
- **A whole-detent pose can move more than any shape.** Legs one hip detent
  forward and the knees two clicks back (shins upright, soles flat, the figure
  dropped onto them) moved the score more than a dozen stalled shape rounds
  had; a waist twist the photo did not show lowered it.

**Back-project the outline of a flat part.** For a plate (a wing, a fin), take
the reference silhouette's runs row by row, map each edge pixel back through
the alignment to the model's image coordinates, and solve the 2 x 2 system
`O + d D + v V` for the part's in-plane coordinates. The outline then comes
from the photograph, not from guesses: one round of it beat three rounds of
guessed outlines.

**Declare a camera window the photo allows.** A free window let the search
settle at el -8 deg on a figure whose foot tops show: the search buys IoU by
lying about proportions. Read the elevation and roll off the photo (tops of
feet visible, shoulders' tops visible) and keep the window within a few
degrees of it.

**Print repairs cost likeness.** Filling a turned foot down to its print bed,
thickening a snap boss and flattening a knife-edged roof each move the
outline; score again after the print gates pass, not before.

A sweep harness is cheap to write in process: patch the parameter module's text
(a regex per `NAME = value`), purge the project's modules from `sys.modules`,
exec the patched text as `params`, rebuild, tessellate, refine the stored pose
by ±6 degrees and score. Each point costs a full rebuild, tens of seconds on a
large assembly.

## Score candidate edits on a mesh surrogate

When single-knob sweeps around a stalled score all read zero, the model sits
at a local optimum of each knob alone; a joint move of many knobs can still
climb. A full render per candidate (a rebuild and a camera search, about a
minute and a half on a large kit) makes that search impossible; a surrogate
makes it cheap:

- Tessellate every part once, **unposed**, and keep its point and triangle
  arrays under a hash of the source files that part reads (its own module,
  the parameter block, the shared features). Apply the pose in numpy from the
  assembly's own pose rules: a pose sweep then rebuilds nothing, and a source
  edit rebuilds only the parts whose hash moved (about 30 s for a 28-part kit
  from cold, seconds after a one-module edit). Score every view at once.
  A candidate edit is arithmetic on the points: a turn about a joint's axle
  in the pose, a translation, a scale about a datum, an in-plane warp of a
  flat plate (antenna and blade angle, length and width about their centre
  lines), a part dropped out.
- Rasterise with the gate's own rasteriser at the gate's camera and score
  with its own `normalise` and `compare`: about 0.04 s per score.
- **Calibrate first.** At the gate's camera the unedited surrogate must print
  the gate's number; rebuild the cache after every source edit (a stale drop
  or pose in the cache silently shifts every score).
- **Rank regions by an upper bound.** Copy one band of the reference's mask
  into the model's and re-score: the gain is the most any edit in that region
  can buy, and it names where to spend the next round.
- **Coordinate-descend the knobs together,** then ablate: revert one group at
  a time to see what each carried.
- **Distrust a gain that lives at one camera.** Score a candidate at the
  gate's camera and at its neighbours; a knob that wins at one azimuth and
  loses at the next is pixel noise.
- **Warps over-predict.** A CAD edit changes more than the warp that stood
  for it (a narrower helmet also moves its eyes, cheeks and camera box); the
  built model lands below the surrogate's figure, so rebuild and score with
  the real gate after each accepted edit.

## Thin tips vanish in the gate's opening

Both masks pass through a morphological opening before they are compared, so
a tapered tip narrower than about three pixels at the normalised scale
disappears from the silhouette. A thin antenna then reads shorter than it is,
and lengthening it appears to help while the real difference is its width.
Measure a thin feature on the reference's mask column by column (the run of
each column across it) against the model's, set the width from that, and
back-project its tip onto the part's plane for the length.

## The silhouette passes and the figure still does not look like the photo

The gate scores the outline only. A figure reached its floor and was still
called nothing like the reference: the interior read wrong. The eye band was
visor-wide, the chest a flat black slab with a small mark, the fists bricks in
the wrong colour, and the legs striped. None of that moves an outline. After
the gate passes, render the model shaded at the reference camera, crop both to
their silhouettes at one height, set them side by side, and compare region by
region: face, chest, hands, waist, legs, feet, and colour. Fix what reads
wrong, then re-score, because interior edits can still move the outline. Leaning
a hanging part out, or narrowing a part that sets the frame's extent, each cost
about 0.01.

