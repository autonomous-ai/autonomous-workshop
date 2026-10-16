# What designing toys has taught

Rules of design judgment that earlier designs and builds paid for. Read the
section for a stage before working it. A rule never overrides `SKILL.md`, the
Inventor's Taste or the human's answer; it tells you what tends to go wrong.

## What belongs here

A rule belongs here when deleting it would leave `SKILL.md` correct but
make the same mistake likely again. Examples: how to phrase a contract row
so the run cannot read it two ways, which camera or pose misleads image
generation, which proportion the human keeps correcting.

A rule that adds a required step, a check or a field is a workflow change.
Make it in `SKILL.md`, a script or `CONTRACT-FORMAT.md`, not here. A rule
about modelling, printing or moving a part belongs in the Make wiki, upstream
(`build-a-toy` Step 8).

Each entry is one `###` heading stating the rule, then:
- **Why:** the failure class that taught it and its evidence, without naming
  the toy or the run;
- **How to apply:** what to do differently, as a number, a wording or a check
  where possible.

Extend an entry before adding a near-duplicate. Keep the file under 250
lines; when it grows past that, merge entries or move a stage into its own
file.

## Stage 1 - Spec

## Stage 2 - Contract

## Stage 3 - Reference images

### Draw a part's extra views in one turnaround image, never one view per call
- **Why:** each separate AI edit of a reference into a back or side view
  redesigned the part. In one toy, five of eleven parts drifted: a band
  wrapped onto the open back, a solid block grew a window, and a fist's back
  was drawn as its front. Views cut from one image that shows all three
  views agreed with each other.
- **How to apply:** make one generation per part: LEFT copies the reference,
  MIDDLE and RIGHT are the new cameras, at one scale on one ground line.
  Spell out the part's construction and, for a profile, its proportions in
  units. Cut the views apart by empty columns. Compose each row at the
  sheet's single scale, with the reference matched to the LEFT view's height.

### Fix a wrong detail by editing the image, on two models, and pick
- **Why:** regenerating a whole image to fix one detail redraws everything
  around it, and fresh errors appear. In one round of six fixes, three
  models each won different fixes:
  - `openai/gpt-image-2.5-sunburst` kept the source image intact best, and
    won the arm shell's inside, the elbow hole, the fist's depth and the
    hip tongue;
  - `openai/gpt-5.4-image-2` placed parts correctly where the prompt said
    where they sit, and won the neck post flush with the helmet back and a
    cutaway of the leg's slide;
  - `google/gemini-3-pro-image` won none.
- **How to apply:** for a fix, pass the current image as IMAGE 1. Name only
  the change and say "keep everything else exactly". Run it once on
  sunburst and once on gpt-5.4, then compare.
  [`scripts/gen_image.py`](scripts/gen_image.py) calls both. Sunburst is
  image-only: it goes through `/images`, and through chat it answers 404.
  For a turnaround, set `IMAGE_ASPECT=3:2`. State a spatial fact in words
  the model cannot read two ways, for example: "the post's back face is
  flush with the helmet's back face; the front half of the helmet
  overhangs it".

## Stage 3b-3d - Reconcile, print, motion

## Stage 4 - Visual review
