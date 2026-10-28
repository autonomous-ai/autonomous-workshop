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
  right) and on the floor (front left/centre/right). Settle the answer on
  the chosen Concept Image's three views (SKILL.md Stage 1).

### Check every prop against the scene's period before the owner does
- **Why:** a modern mug and an electric bell-shaded lamp in a 19th-century
  study were each caught by the owner as clashing, costing a round each.
- **How to apply:** name the scene's style and era in the spec (for a book
  room: Dark Academia, Victorian study) and list each prop with an
  era-consistent form: oil lamp, quill and inkwell, hourglass, porcelain
  cup, fern or plain leafy plant in a stoneware pot.

## Stage 2 - Contract

### Write a detail that changes the outline as outline, never as grooves on a box
- **Why:** a contract gave a fist as a 20 x 15 box with fingers "split by
  grooves 0.8 wide and 2 deep" and a thumb inside that face. The run built
  exactly that, the reviewer agreed, and the owner saw a square block twice:
  the image's fingers stand proud, curl under, and its thumb sticks out over
  a cut-away corner.
- **How to apply:** for each detail the image shows, ask whether it changes
  the silhouette in the front or side view. If it does, give its outline in
  numbers: how far it stands proud, where the outline steps in or is cut
  away, how the end rounds or curls. Only a detail that leaves the silhouette
  unchanged may be written as an engraved line or a groove.

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

### Start a colour layer from the cut that seats the part, not from a fixed station

- **Why:** a part was seated on a flared shade at a slant, and its colour
  layer started at one fixed station along the part. On one side the seating
  cut ran through the layer, so the colour showed on the mounting face, and
  the build stopped on the contradiction.
- **How to apply:** when a part's foot is cut to follow a curved or slanted
  surface, compute where that cut meets the colour interface across the
  width. Start the layer a fixed distance above that line (for example
  s = max(s0, s_cut(t) + 4 mm)) and tabulate it. Add a check that the layer
  keeps a set BRep distance from the mounting face.

### Check every relational word against the coordinates
- **Why:** with every number linted, a fresh read still found nine words the
  coordinates denied: rails that "meet" 3.4 apart, a "square" 4 x 2 newel,
  bosses "clear of" rings they bear on, a stand narrower than its ring, a
  door plate running through the hinge pin where only knuckles were bored.
- **How to apply:** before the fresh Proof read recompute each meet, touch, clear of,
  beside, square and parallel from the stated ranges. For a pin hinge, say
  where the leaf's edge stops beside the knuckles.

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
- **Why:** regenerating to fix one detail redraws everything around it. In
  one round of six fixes `openai/gpt-image-2.5-sunburst` kept the source
  intact best (won four), `openai/gpt-5.4-image-2` placed parts where the
  prompt said they sit (won two), `google/gemini-3-pro-image` won none.
- **How to apply:** pass the current image as IMAGE 1, name only the change
  and say "keep everything else exactly"; run sunburst and gpt-5.4
  ([`scripts/gen_image.py`](scripts/gen_image.py); sunburst is image-only,
  via `/images`) and compare. For a turnaround set `IMAGE_ASPECT=3:2`. State
  a spatial fact one way only: "the post's back face is flush with the
  helmet's back face; the front half of the helmet overhangs it".

### Draw what the camera can see, and pick a camera that shows the defining profile
- **Why:** the owner caught a slot open on top invisible from 15 degrees
  above, an L-shaped wing read as a flat bar head-on, and a post and guard
  contracted level drawn at different heights.
- **How to apply:** for each feature the contract places, edit it in if the
  camera can see it. Give a profile part (L, T, U) a three-quarter camera
  showing the profile at one end. Say "ends at exactly the same height as"
  for level things, and give widths as a percentage of the height, because
  the models draw parts too slim.

### Draw transformation steps as one chain of edits, one move per edit
- **Why:** step panels made as separate edits each redrew the toy, so parts
  changed between steps and the owner rejected the whole sheet.
- **How to apply:** start from the approved robot (or end) image. Make
  each step one edit of the previous step's image that names only that
  move, and keep the camera. Give the moved part's new size relative to a
  part in the image, such as "the nose above the chest is 1.2 times the
  chest's height", because the models shorten long parts. Lay the vehicle
  down from the last stood-up step, and pass the old vehicle view only as
  a camera example.

### Show a colour layer hidden inside a fold with a cutaway; fix one defect by editing

- **Why:** views looking into a narrow fold came out as a cup on every model,
  and edge-on profiles of a thick bent part came out as a bent pipe. A cutaway
  showed the hidden layer as one unbroken line round the fold. When one small
  defect was left (a flared foot), regenerating would have lost the rest, but
  an edit of the chosen image fixed only that spot.
- **How to apply:** prompt "sliced in half down its middle, look square at the
  cut face" and name the layer's start, path and end. Fix a leftover defect by
  editing (see above). Check the drawn thickness against the contract, since a
  model can draw a thick part as a blade or a pipe.

### Edits drop objects nobody asked to remove
- **Why:** each "change only X" edit lost one or two unrelated objects (an
  inkwell, a framed picture, a sill plant) in four of seven rounds.
- **How to apply:** name every object to keep in each edit prompt, compare
  object lists after, and restore a lost one in one edit with the earlier
  image passed and the object described as it looked there; a generic noun
  brings back a different object.

### When the models keep moving a part, change the composition, not the prompt
- **Why:** a cabinet "under the stair" landed on the dais in seven tries,
  and an open door lay flat beside its cabinet or hung on its far edge in
  four of six; a niche in the stair's side and "the open door continues the
  side panel forward" were drawn right at once.
- **How to apply:** after three generations put a part in the same wrong
  spot, build it into a neighbour the model already draws; amend the contract.

### Redraw fresh after about four chained edits, counting the whole lineage
- **Why:** editing an edit accumulates blur; the owner saw it after five,
  including an assembly fixed back and forth across rounds with no single
  round making four edits. A text-only redraw lost the box proportions; one
  with the last image as a layout guide kept them.
- **How to apply:** count every edit since the last fresh generation. At
  four, regenerate with the last image as the only reference, labelled "a
  LAYOUT GUIDE: do not copy its pixels", describing every object as it is
  drawn there (shape, colour, count, position) at the same camera; then
  compare object by object and fix any difference with one edit.

### Extract a component by removing, not by redrawing
- **Why:** "redraw this as the empty case" reflowed the layout; "remove the
  chair, the desk ... keep everything else" kept every position.
- **How to apply:** edit the assembly and name every part to remove and
  what shows behind it. For a top view pass a clean earlier top view first
  (camera) and the assembly second; text alone returns a three-quarter view.

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

### Name the two objects that touch before fixing a region the owner flags
- **Why:** "the lower part of this image is wrong" was fixed three times as
  the wrong thing (a pilaster, a width, an open underside) before it turned
  out to mean the stair's foot touching the right wall.
- **How to apply:** when a complaint names a region, not an object, crop
  that region, list what touches what there, and fix the contact that
  breaks the contract or the room plan. If two readings remain, show a crop
  of each in one question.

