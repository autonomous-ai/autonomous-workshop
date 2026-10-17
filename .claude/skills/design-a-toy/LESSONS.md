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

### Settle the room plan before any component image
- **Why:** a diorama's owner reworked which wall holds what (books on the
  side walls, desk under the window, pictures on the right) after a full,
  measured reference set existed; every component image and the contract
  had to be redone.
- **How to apply:** for a scene inside a box, put one plan question in
  Stage 1: what stands against each wall (left, back left/centre/right,
  right) and on the floor (front left/centre/right). Then iterate a single
  direction image with the owner, one change per round, and start
  component images and measurement only after an explicit OK on it.

### Check every prop against the scene's period before the owner does
- **Why:** a modern mug and an electric bell-shaded lamp in a 19th-century
  study were each caught by the owner as clashing, costing a round each.
- **How to apply:** name the scene's style and era in the spec (for a book
  room: Dark Academia, Victorian study) and list each prop with an
  era-consistent form: oil lamp, quill and inkwell, hourglass, porcelain
  cup, fern or plain leafy plant in a stoneware pot.

## Stage 2 - Contract

## Stage 3 - Reference images

### Edits drop objects nobody asked to remove
- **Why:** each "change only X" edit silently lost one or two unrelated
  objects (an inkwell, a framed picture, a sill plant) in four of seven
  rounds.
- **How to apply:** list every object to keep by name in each edit prompt,
  compare the result's object list with the previous image's, and restore
  a lost object in one follow-up edit, passing the earlier image as a
  reference and describing the object as it looked there. A generic noun
  ("terracotta pot, green plant") brings back a different object.

### Redraw fresh after about four chained edits
- **Why:** editing an edit accumulates blur and artifacts; after five
  rounds the owner saw them. A text-only redraw lost the box proportions;
  a redraw with the last image attached as a layout guide kept them.
- **How to apply:** after four edits, regenerate with the last image as the
  only reference, labelled "a LAYOUT GUIDE: do not copy its pixels", plus a
  full scene description wall by wall.

### Extract a component by removing, not by redrawing
- **Why:** "redraw this as the empty case" let the model reflow the
  layout (shorter bookcase, smaller window, an angled wall); "edit: remove
  the chair, the desk ... keep everything else" kept every position.
- **How to apply:** for a component that is the assembly minus parts,
  edit the assembly image and name every part to remove and what shows
  behind it. For a top view, pass an earlier clean top view as the first
  reference (camera and style) and the assembly second (objects); a text
  request for a top view returns a three-quarter view.

### Ask for proportion changes as relative edits
- **Why:** "N times taller than wide" was ignored for thin parts (a ladder
  asked at 9:1 came back 4:1; a window asked at 2.6:1 came back far
  slimmer than asked); "make it half as wide" landed within the 20% resize
  allowance.
- **How to apply:** generate, measure the aspect, then edit with a
  relative instruction ("half as wide", "move the left end to 52% of the
  width") and close the rest with the allowed resize. Side profiles: pass
  an existing side-profile image as a second reference.

## Stage 3b-3d - Reconcile, print, motion

### Read heights from a level view, not from the assembly
- **Why:** an AI front view at EL 15 is neither true perspective nor
  orthographic; back-wall heights read from it were off by tens of mm.
- **How to apply:** take Z from an EL 0 component image and X/Y from a top
  view; use the assembly only for X positions and counts. When three
  images place one datum differently, put the datum where every image is
  within 5% rather than editing all three.

### In a back-face stance, nothing may stand in front of an opening
- **Why:** a plant on a window sill, curtains overlapping an inserted
  window frame and a free-standing globe all printed over air once the
  case lay on its back face.
- **How to apply:** move what stands in front of a through-opening onto
  the insert that fills it (printed as relief on its face); give anything
  overlapping a separately inserted part a 52 degree chamfered back and
  0.2 clearance; give round objects against the wall a 52 degree cone back.
  Remove the moved feature from the host's image so it does not become a
  Reference Conflict.

### Check purchased parts against every ceiling
- **Why:** a battery box at its stated maximum height rose 1 mm into the
  floor slab above the tray, unnoticed through one full contract.
- **How to apply:** for each purchased part, add its height to its seat
  and compare with the nearest ceiling in the assembly; cap the part's
  stated maximum so it clears by 0.5.

## Stage 4 - Visual review

### Offer two variants for a taste question
- **Why:** the owner decides by picture; questions like "fern or the
  earlier plant?" or "is this a style clash?" settled in one round when
  both options were drawn side by side, and dragged when asked in words.
- **How to apply:** for any choice of style, species, prop or layout, draw
  both options from the same base image (one change each) and publish them
  side by side with one line each.
