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

## Stage 3b-3d - Reconcile, print, motion

## Stage 4 - Visual review
