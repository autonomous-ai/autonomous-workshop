# ADR 0059: See a pale subject on a white ground, and re-search a stale camera

- Status: Accepted
- Date: 2026-09-08
- Owners: Make gate and image-to-cad skill maintainers

## Context

The second goose run (wish-20260908-111111-9bb86530) used an image-to-image
product photo as its Wish reference: a cream goose on a white sweep. Its
Make Manager ran fifteen rounds with the likeness IoU pinned between 0.47
and 0.58, then parked with a need for a "host-qualified reference
silhouette": its bounded probes showed the mask dropping the pale head and
torso (fill 0.30), and its own flattening tool filling the real wing and
inter-leg openings. The probes were right on both counts.

Two host tools caused it. `measure_image.py`'s mask is a luminance threshold
around the background plus a shadow test in normalised rgb; cream sits
inside the band and only ~0.02 off the ground in normalised rgb, below the
0.045 the shadow test needs, so lit cream reads as ground and shaded cream
as shadow. And `make_round` replays the previous round's camera every
round; `render_views --poses-from` never searches, so once the neck leaned
and the head turned, every later round was scored under a stale camera. On
the same model, replay gave 0.49 and a fresh search 0.75.

## Decision

- `measure_image.py` (and through it the gate's silhouette) gains a CIELAB
  a*b* test: a pixel whose a*b* distance from the background colour is
  above 4 is chromatic for the shadow test, and regions inside the luminance
  band that pass it are admitted as object under the existing attachment
  rule. Neutral shadows have no a*b* difference and stay out; so do
  background-coloured apertures, which is what keeps the wing and leg
  openings open. The mask notes report `pale_region_share`.
- `make_round` keeps replaying the previous camera, and when the replay
  scores under the floor it also searches a +/-30 degree window at 10 degree
  steps with two refinement rounds around that camera, keeps the better
  score, marks it `(re-searched)`, and writes that pose for the next replay.
- The reviewed-skill lock is resealed for both skills.

## Alternatives considered

- Handing the run an alpha cut-out of the same photo: the tools already
  honour alpha (ADR 0056), but Wish references are sealed by hash and the
  run cannot receive a new one, and the operator's i2i lane produces white
  grounds, not cut-outs. The tool must read the photo it was given.
- Lowering the normalised-rgb chroma tolerance: it cannot separate cream
  from a warm neutral shadow, which CIELAB a*b* does.
- A full pose search every round: about five times the cost of the window,
  for a camera that rarely moves more than the window between rounds.

## Consequences

- A reference whose subject is truly the ground's colour still has no
  silhouette; the cut-out path remains the answer there.
- A warm backdrop gradient attached to the subject could be admitted; the
  attachment rule and the opening filter bound it, and the note makes it
  visible.
- Rounds under the floor cost one bounded search more; rounds at the floor
  cost nothing extra.

## Compatibility and migration

Existing runs pick the change up through `workshop resume --refresh-tools`,
which rewrites the host-owned skills and rebinds them in the manifest. No
score floor, reference, or sealed input changes.

## Verification

`measure_image.py --self-check` gains a pale tinted region that must be
kept and a lighter neutral patch that must stay ground; `make_round
--self-check` covers the search window. On the goose reference the mask
fill rose from 0.302 to 0.359 with the openings preserved, and the run's
round-15 model scored 0.745 under a window search against 0.489 replayed.
