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
file (Stage 3 lives in `LESSONS-REFERENCE-IMAGES.md`).

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
  unchanged may be written as an engraved line or a groove. The same holds
  for a small cut that means a direction: an eye pit written as a 1.6 circle
  under a sloping lid was built to its numbers and read backwards by two
  reviews, and only a wedge outline (5 degree sill, 40 degree lid) read. Write
  such a cut as an outline that points.

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

### Say beside every engraved cut that its size is not a print minimum
- **Why:** a run read the blunt-edge rule's "a flat land at least 0.8 mm
  across" as a minimum width for every groove. It briefed five workers to
  widen sealed 0.6 grooves to 0.8 and deepen 0.6 cuts to 1.0. Every gate
  passed the result, which broke four sealed numbers per face, until two
  workers filed Blocked Reports and the Manager withdrew the brief.
- **How to apply:** in the section that seals an engraving's width and depth,
  add that these sizes are not bound by the blunt-edge land rule, which sizes
  only the flat end of a point, chisel, keel or V underside.

### Write each Component's colour in its own row, never in a shared section
- **Why:** a set's member-to-colour list sat in the print-stance and
  assembly sections every Component names. Recolouring one shell changed
  all nine Components' contract text, so every carried review stopped
  binding and one colour fix cost fresh reviews of parts it never touched.
- **How to apply:** give each colour in a requirement row of the geometry
  it colours ("shell 4 is opaque brass"), and keep shared sections free of
  colour words; a recolour then reaches only that Component's review.

## Stage 3 - Reference images

The Stage 3 entries are in
[LESSONS-REFERENCE-IMAGES.md](LESSONS-REFERENCE-IMAGES.md), under the same
rules as this file.

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

### Overlay every sealed small cut on its reference before the review
- **Why:** two face references drew their eyes and mouths larger than the
  sealed cut sizes. The run built the sealed sizes, and every fresh
  Component Reviewer asked for the drawn faces, which the contract forbids;
  a colour fix stalled on two faces nobody had changed.
- **How to apply:** for each engraved or cut feature under about 3 mm,
  project its contract outline through the reference camera onto the image
  and compare. Where they differ, redraw that area to the outline (blank the
  face with one edit, then place each cut at its contract size) before
  Stage 4, never after a run has sealed the images.

### Check purchased parts against every ceiling
- **Why:** a battery box at its stated maximum height rose 1 mm into the
  floor slab above the tray, unnoticed through one full contract.
- **How to apply:** for each purchased part, add its height to its seat
  and compare with the nearest ceiling in the assembly; cap the part's
  stated maximum so it clears by 0.5.

## Stage 4 - Visual review

### Offer two variants for a taste question
- **Why:** the owner decides by picture; "fern or the earlier plant?"
  settled in one round drawn side by side, and dragged when asked in words.
- **How to apply:** for any choice of style, species, prop or layout, draw
  both options from the same base image (one change each) and publish them
  side by side with one line each. For a lit or translucent detail, show
  the variants as one backlit sheet at true scale and gate each: lines
  under 2 mm pitch blur in a 2 mm plate, and the library's 1.6 web is a
  margin, not the gate's 0.8; write a chosen exception into the contract.

### Name the two objects that touch before fixing a region the owner flags
- **Why:** "the lower part of this image is wrong" was fixed three times as
  the wrong thing (a pilaster, a width, an open underside) before it turned
  out to mean the stair's foot touching the right wall.
- **How to apply:** when a complaint names a region, not an object, crop
  that region, list what touches what there, and fix the contact that
  breaks the contract or the room plan. If two readings remain, show a crop
  of each in one question.

