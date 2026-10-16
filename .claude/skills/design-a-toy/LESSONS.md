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

### Specify a bent or folded form as a 3D centre curve, never a fitted silhouette

- **Why:** a folded part placed and bent by fitting front silhouettes
  settled on a thin plate bent round a straight hinge. It matched the front
  view and read as a lid from every other camera. The fit also pinched the
  width at the bend, and a colour pocket stopped short of the bend, so the
  colour showed as one patch. The owner rejected it twice.
- **How to apply:** before deciding a fold's shape, read the concept panel
  that shows it at full resolution (crop it). Write the fold as a spine in the
  host frame: a foot point, rise and fold directions, and a curvature table
  with ramps at each end so the bend has no visible start or end. Give the
  width table with no waist. State that a colour layer runs unbroken through
  the whole bend, with its start and end stations. Report likeness instead of
  gating on it.

## Stage 3 - Reference images

### Show a colour layer hidden inside a fold with a cutaway; fix one defect by editing

- **Why:** views looking into a narrow fold came out as a cup on every model,
  and edge-on profiles of a thick bent part came out as a bent pipe. A cutaway
  showed the hidden layer as one unbroken line round the fold. When one small
  defect was left (a flared foot), regenerating would have lost the rest, but
  an edit of the chosen image fixed only that spot.
- **How to apply:** prompt "sliced in half down its middle, look square at the
  cut face" and name the layer's start, path and end. To fix one detail, send
  the chosen image as the input and say "keep everything exactly the same,
  change only X". Run the same prompt on two or three models and pick the
  best. A model can draw a thick part thinner (a blade) or round (a pipe), so
  check the thickness against the contract before choosing.

## Stage 3b-3d - Reconcile, print, motion

## Stage 4 - Visual review
