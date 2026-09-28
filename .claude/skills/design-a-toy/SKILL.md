---
name: design-a-toy
description: Design any physical Workshop toy - a vehicle, a jointed robot, a bone dragon, a puzzle, a game - with an Inventor before any run starts - grill the idea into a frozen spec, draft the Design Contract, generate one reference image per unique geometry plus the assembly, reconcile them with the contract feature by feature, check that everything they show can be printed and that any mechanism can move, then get the human's one visual review before handing off to `build-a-toy`. Use when starting a new toy, or when a previous run drifted from what you wanted.
---

# Design a toy before the run

This skill does the creative work **outside** Workshop, where the human watches
every step, and hands Workshop a finished design.

Workshop's Spark route is `("make", "release")`: the Wish goes in, Make builds,
Release publishes. Nothing in the run verifies that the Manager consulted the
Inventor or passed it the Wish verbatim — the Inventor subagent's instructions
carry only its Taste. The answer is not to police the run. It is to leave
nothing for the run to invent.

The output of this skill is one `CONTRACT.md`, handed to `build-a-toy`.

The human reviews **pictures, not the contract**. They answer the design
questions in Stage 1 and approve the finished set of images in Stage 4. They
never read or approve the `design-contract` block or a contract diff. Keeping the
contract and the images in agreement is this skill's job, done by measurement
in Stage 3b, so that approving the images is the same as approving the
contract.

## Who designs

Read the Inventor's `TASTE.md` from `inventors/<id>/TASTE.md` and work as that
Inventor throughout. The Taste is the constitution: it decides what is in scope,
what wins a trade-off, and what gets rejected. Do not paraphrase it into
something more agreeable. If the idea the human wants is outside the Taste, say
so plainly and name which clause it fails — do not quietly widen the Taste to
fit.

There is no default Inventor. Read the `description` line of every
`inventors/*/TASTE.md`, propose the one or two whose scope fits the idea, name
the clause that makes each fit, and let the human choose. A board-game
Inventor is not a safe fallback for a vehicle, a creature or a mechanism.

## Stage 1 - Grill the idea into a spec

Invoke the `grilling` skill and work the design as a decision tree. Do not skip
this because the human arrives with a clear idea; a clear idea is usually a
clear *image* with the decisions still unmade underneath it.

Ask the human only about what the toy looks like and does: which parts it
has, which one dominates, what moves, how many of each, the pose. Keep each
question short and in plain words about the toy. Do not ask for millimetres,
wall thicknesses, clearances, pin diameters, print stance or row limits. Decide
those yourself as the Inventor, from the Taste and the feasibility checks, and
write them into the spec without asking.

Drive to a written spec containing:

- **The unique-geometry list.** Group the component inventory by *shape*, not by
  part. Name each unique geometry and how many parts use it. This list drives
  everything downstream, and its length is the image budget. A bone dragon's
  thirty vertebrae may be three shapes; four identical wheels are one.
- **The Focal Component.** Exactly one component is allowed to dominate: a car's
  body, a robot's chest, a dragon's skull. Name it, say what it costs the rest
  of the object, and accept that cost in writing.
- **Per-geometry physical spec.** Form, duty, dimensions in mm, placement,
  interfaces, what it mates with. No hedged quantities — the Workshop concept
  contract rejects "roughly", "about", "several", "as needed". If a number is
  not decided, decide it.
- **Envelope, wall thickness, print stance.**
- **The fixed-frame plan.** How the toy composes in Release's product frame at
  35 degrees azimuth, 22 degrees elevation, against `#f5f0e6`, with the Focal
  Component as the focal point.
- **Handling check.** How the toy survives being held, rolled, posed or
  dropped: which parts break or come loose first, and that nothing load-bearing
  is under 3 mm.

When the toy has any moving part — a wheel, an axle, a joint, a hinge, a
sliding or spinning part — also drive to:

- **Motion and fit.** Every moving part, what it moves against, and how it is
  retained. Whether it prints in place or is assembled. Each motion stated as
  geometry the build can be checked against: clearance in mm, pin or axle
  diameter, joint range in degrees. "Rolls freely" or "poses well" is prose for
  the spec, never a requirement.
- **The Display Pose.** One fixed arrangement of every moving part. The assembly
  reference image and the built toy both use it, so the likeness gate compares
  one silhouette against one silhouette.

Only when the human explicitly asks for a playable game, also drive to:

- **Source game and rights.** For a reskin: the exact ruleset, its public-domain
  evidence, and the frozen rule-equivalence ledger — player counts, component
  functions and quantities, setup, turn order, legal actions, information,
  randomness, state transitions, interaction, ending, tie-breakers, scoring.
  For an original game: the full ruleset to the same depth.
- **Theme mapping.** Every mechanical role to a thematic meaning and a physical
  cue, one to one. Flag any mapping that is only a renamed noun.
- **Play-state check.** How the set reads in a crowded mid-game and a late-game
  position, with captured pieces off the board, and what the Focal Component
  costs in sightlines from each seat.

## Stage 2 - Draft the contract

Draft the block per
[CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md): one `geometries[]`
entry per item on the unique-geometry list, and one `requirements[]` row for
every checkable claim the prose decided — a dimension, a count, a wall
thickness, a clearance, a joint range, a visible feature. Check the block against the prose line by line,
not just against itself: a block that leaves out a decided number or feature
lets the run drift, and nobody downstream reads the prose closely enough to
notice. Name each
`references[].file` as `ref-NN-<slug>.png` in the order Stage 3 will generate
them, even though the files do not exist yet. A toy with more than one
component also gets one `"shows": "assembly"` reference, listed first.

Check the drafted block against CONTRACT-FORMAT.md's row limits: at most 16
assembly-scoped requirements, at most 4 per Unique Geometry, and the whole
file (prose plus block) under 40,000 characters. If the design does not fit,
do not silently drop decisions. Ask the human which *features* to give up, in
plain words about the toy ("keep the moving jaw or the separate claws?"), never
as contract rows.

Do not show the block to the human and do not wait for approval. Go straight to
Stage 3.

## Stage 3 - Reference images

Generate **one image per unique geometry** from the Stage 1 list. Four
identical wheels are one image, not four. When the toy has more than one
component, also generate **one assembly image** of the whole toy, in its
Display Pose when it has moving parts: the overall silhouette is what a vehicle,
robot or creature is judged by first.

**Always use AI image generation or AI image editing to make these images.
Never build them by hand.** No hand-written ray caster, no procedural renderer,
no parametric CAD script, no matplotlib, no SVG assembled from coordinates. If
you catch yourself writing intersection maths or typing polygon vertices, stop:
you are doing the wrong job.

The reason is not convenience, it is division of labour. A reference image is
**concept art that Make builds from**. The moment you hand-build exact geometry,
you have already done Make's work, badly and outside every gate the run applies
to it - and then the run is reduced to copying your render instead of
engineering the object. The hand-built version also lies in a specific
direction: it draws whatever the spec's numbers say and nothing the spec forgot,
so it can never show you that the spec is wrong, which is the one thing a
reference image is for at this stage.

A generated image is allowed to be looser than the spec in surface detail. That
is a feature. The spec carries the millimetres, the image carries the silhouette
and the read. It is **not** allowed to disagree with the spec in proportion,
landmark position, count or side. Make is scored on the silhouette, so an image
that draws a different body from the one the contract dimensions will fail the
likeness gate however well Make builds. Stage 3b closes that gap before
anything is sealed.

Each image must be:

- **800x800 or smaller.** The likeness gate extracts a silhouette, normalizes
  height, and does not read color. Resolution beyond this buys no accuracy and
  spends the Wish's 48 MiB reference budget.
- **One subject, fully inside the frame.** The gate rejects a reference whose
  subject touches the image boundary. The assembled toy counts as one subject; a
  scene, a diorama or a populated board position does not.
- **Named `ref-NN-<slug>.png`**, numbered from `01` in order with no gaps.
  Lowercase kebab slug. `png`, `jpg`, or `webp`. At most 99 images, at most
  12 MiB each.

Iterate each image against criteria stated up front — silhouette reads the
component's role at thumbnail size, one focal point, contrast holds against
`#f5f0e6` — with a hard round cap. "Until it looks good" is not a stopping
condition. Take the best image at the cap and note what fell short.

Web imagery may be used as material to edit while composing an image. Judge
whether a source is safe to build from, and **record the source URL of every web
image you edit from** in the working notes beside the images. Never pass a found
image through as the reference itself: the likeness gate writes a measured
similarity score into the toy's public archive, and what that score describes
must be the Inventor's own expression.

## Stage 3b - Reconcile every image with the contract

An image that passes its own criteria can still describe a different toy.
Before Stage 4, **measure** every image against the drafted contract. Do not
judge by eye. Measuring scripts are allowed here. They read an image; they do
not draw one.

For each image, take its alpha silhouette and check:

1. **Aspect.** Compare the silhouette's width to height with the contract's
   ratio in the view the image shows. For a component, that is its extents; for
   the assembly, the envelope in the Display Pose. A component image must show
   the view its extents describe, orthographic front or side, so the two
   ratios compare.
2. **Landmarks.** Scale the image to the contract's height and draw the
   contract's datums over it. For the assembly, these are every stated Z height
   and X position: base top, pelvis, heart, hinge axes, shoulders, crest top.
   For a component, they are its named features: window centre, hole
   positions, bend angle. Read off where the image puts each one.
3. **Masses.** Compare the width of each major body at its own height with the
   contract dimension. A torso, a head, a base or a wing root are examples. A
   56 mm torso drawn as a 33 mm skeleton is a disagreement even when the
   overall aspect matches.
4. **Counts, sides and orientation.** Tooth, blade, spoke and finger counts;
   which side the eye or the claw is on; which way a hole faces. Count blades
   and teeth by machine (edge crossings along a scan line), not by eye.
5. **Every dimensioned feature.** Go through the contract, prose and block,
   and list every millimetre number that describes something an image shows:
   a hole or window diameter, a blade or rib width, a shaft diameter, a claw
   or segment length, a gap, a depth seen from the side. Measure each one in
   the image at contract scale, one row per number. A number with no row
   means Stage 3b is not done. Broken God round 0 passed checks 1 to 4 and
   still shipped crude parts: the contract said a 20 mm heart window, 5-8 mm
   wing blades and 18 mm claws, and the images drew 9 mm, 11-13 mm and
   37 mm. Make followed the numbers, and every part came out a different
   shape from its picture.

A measurement is a **disagreement** when it is off by more than 5% of the
dimension it measures and by more than 0.5 mm. The 0.5 mm floor is for small
features, where 5% is less than the measuring error. Any count, side or
orientation that differs is also a disagreement. Record every check in the
working notes as a table: image, check, contract value, image value, verdict.

**Resolve each disagreement by judging which one is right.** Do not assume the
contract wins. Look at the image as the Inventor would, against the Taste:

- **The image is better,** meaning it reads more clearly, has better
  proportions or is more sensible as an object. Then amend the contract to
  match the image. Change the prose and the block together, and derive the new
  numbers from the image's measured proportions. Redo every feasibility check
  the changed numbers touch: gear centres, joint ranges, clearances, walls,
  bed size, the row limits. Then re-measure **every** image against the
  amended contract, because one changed height can move five landmarks.
- **The contract is better, or the image is not buildable as drawn.** Then fix
  the image by AI editing or regeneration, never by hand. An anisotropic resize
  of the keyed silhouette may close a residual aspect gap of up to 20%. It
  cannot fix a landmark or a mass that sits in the wrong place.

The assembly image matters most. The final likeness gate scores it against the
whole built toy, so its landmarks and masses must match the contract before
anything else is accepted.

Make these decisions yourself and keep going. Do not show the human the
disagreement table or a contract diff: they review the images in Stage 4, and
the contract follows whatever images they approve.

Done when: no disagreement remains, and every dimensioned feature has its
row. A disagreement you cannot close after the round cap is not waved through:
raise it at Stage 4 as a visible difference in the picture ("the image shows
three horns, the build will have two").

## Stage 3c - Check that what the images show can be printed

The build is scored against these images, so everything they show must be
printable at the size the contract gives it. Otherwise Make has to simplify it,
and a simplified part looks crude next to its picture. Workshop prints with a
0.4 mm nozzle, and its print gate refuses any part that needs support.

Scale each image to its contract size after Stage 3b. Measure the smallest
features it shows, and check the contract's own numbers against the same
limits:

| Feature | Minimum |
|---|---|
| A solid thin member: a bar, rib, claw, shaft, blade edge or wall | 0.8 mm across |
| A gap, slot, slit or opening meant to stay open | 0.5 mm |
| Raised or sunk decoration: a rivet, boss, ridge or groove | 1.0 mm across |

Then check support. Name each geometry's print stance. In that stance, find
every form the image shows that would print over air: an underside flatter
than 45 degrees from vertical, a hanging claw or hook, a dome or lip that
overhangs, a bridge longer than 12 mm. Workshop's print gate fails a part
that needs support, and it cannot be told that a part is allowed support.

Resolve each problem yourself, in this order of preference, and keep the look:

1. **Make the whole toy bigger**, when many details are too small together and
   the bed still fits.
2. **Enlarge the one detail**, when it can grow without changing the read.
3. **Change the print stance or split the part**, for a support problem.
4. **Reshape the underside**: a 45 degree chamfer, a teardrop hole or a
   pointed arch. Keep the silhouette the image shows. Never flatten an organic
   form into a box to pass the gate.
5. **Drop the detail**, only when nothing above works.

Any change to size, shape or stance amends the contract. When an image no
longer shows what the contract says, fix the image by AI editing. Then redo
Stage 3b for every image you touched, and the assembly image.

Record every check in the working notes as a table: image, feature, size at
contract scale, minimum, verdict, resolution.

Done when: every feature the images show meets its minimum, every form has a
support-free stance, and every change is in both the contract and the images.

## Stage 3d - Check that the mechanism can move

Skip this stage when the toy has no moving part. Otherwise, the images and
the print fixes of Stages 3b and 3c may have moved a gear, a hinge or a
blade, so check the mechanism against the contract as it now stands.

Compute the checks with a script from the contract's own numbers: axis
positions, pitch and tip radii, face widths, part thicknesses, angles and
travel. A 2D layout seen along each axis is enough, with shapely or plain
geometry. The script calculates; it never draws an image or builds CAD, for
the same reason as Stage 3.

Check every item:

1. **No gear ring.** List every pair of gears whose centre distance equals the
   sum of their pitch radii and whose layers overlap: those mesh, whether the
   contract meant them to or not. Gears that mesh in a closed ring cannot
   turn. Broken God's pinion sat 24 from both wing sectors (16 + 8) in one
   layer, and the two sectors mesh each other, so the train was locked.
2. **Teeth fit the part.** Each gear's face width fits inside the thickness of
   the part that carries it, and the part's extents include any boss that
   carries teeth. Broken God declared 8 wide gears on a 5.3 thick wing.
3. **Nothing collides through the travel.** Sweep every moving part through
   its full travel, every 5 degrees or finer, against every other part in its
   layer. It must keep the contract's clearance, and at least 0.5. Check the
   teeth that turn away from their mesh too: a tooth at the mesh when closed
   is 35 degrees round the gear when open, and may reach a third gear.
4. **Teeth cover the travel.** Each toothed arc still engages at both ends of
   the travel, with at least one tooth to spare.
5. **The ratio agrees.** The tooth ratio times the input angle equals each
   output angle the contract states, in the right direction, and mirrored
   parts turn in mirror.
6. **Axles are long enough.** Each purchased axle or pin covers the press depth
   plus every layer it passes through, in a length the contract's supplier
   actually stocks.

A failed check is resolved in this order, keeping the look:

1. **Separate the layers.** Put the gears that must not meet in different
   layers, with 0.5 between them, and carry the one mesh that must cross
   layers on a boss hidden inside the body.
2. **Move an axis or change a tooth count**, then redo Stage 3b for the
   landmarks it moves.
3. **Shorten the travel**, only when nothing above works.

A resolution that changes something the images show also changes the images,
by AI editing, and redoes Stages 3b and 3c for them and the assembly image. A
resolution hidden inside the body changes only the contract.

Then write the motion plan into the contract's prose, because Make's motion
check stops at its time limit and an unfinished sweep proves nothing:

- `--check-motion true` on the wish and on every resume and correction;
- one sweep of the full travel, at most 10 steps, against only the parts a
  moving part can reach;
- one one-tooth sweep per mesh, at most 10 steps, with no obstacles;
- a skipped, killed or timed-out sweep fails the motion requirement, never
  passes it. Add this to that requirement's own row.

Record every check in the working notes as a table: check, parts, value,
limit, verdict, resolution.

Done when: every check passes on the contract as amended, and the motion plan
is in the contract.

## Stage 4 - Visual review

**Stop. This is the only approval gate.** Show the human every reference image
at once, assembly first. Give each one a single line in plain words: what it is
and how many parts use it ("ref-02 wheel - four of these"). Publish them as one
private Artifact page (load the `artifact-design` skill first) that works at
phone width and shows the whole set in one look, and give the human its link
plus each file path. Do not show the contract, the requirement rows, the
measurement table or millimetre lists unless the human asks.

Also say, in plain words, anything the build will not match exactly, from
Stage 3b or from the generation notes. List each Stage 3c change the same way:
what grew, what was reshaped for printing, and what was dropped ("the rivets
are drawn at 0.7 mm and will print as 1 mm bumps"). A Stage 3d change hidden
inside the body gets one line ("the heart gear sits in front of the wing
gears so the train cannot jam; hidden in the back").

Wait for explicit approval of the images. If the human wants a change - a
different shape, proportion, count, pose or feature - fix the images by AI
editing or regeneration, amend the contract so it says what the new images
show, and redo Stages 3b, 3c and 3d for **every** image. Then update the same Artifact
page and show only the images that changed, always with the assembly image,
which is the one the likeness gate scores. Repeat until the human approves.

## Stage 5 - Write the contract and hand off

Write `CONTRACT.md` beside the reference images: the prose, then the
`design-contract` block, both reconciled with the approved images, exactly as
[CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md) requires. Confirm the
block's `references[].file` entries now match Stage 3's images one for one —
that is what lets `workshop wish --contract` seal this exact file, byte for
byte, as the run's hash-checked objective.

Approving the images is the go-ahead. Do not ask again: write the contract
and hand off to the `build-a-toy` skill straight away with the path to this
`CONTRACT.md`. That skill owns every run this design
starts, round 0 through every correction, always under `--contract`. Do not print a bare `workshop wish` command here.

Then state plainly what happens next: Make builds against these images, the
silhouette-likeness gate re-checks every round at IoU >= 0.90, and every
correction runs through `build-a-toy`, not back through this skill.

## What this skill does not do

- It does not run Workshop, publish, or touch a live run.
- It does not add a checkpoint inside Make. Once the Wish is sealed, the
  likeness gate is the enforcement.
- It does not widen the Inventor's Taste to accommodate an idea. That is a
  human edit to `inventors/<id>/TASTE.md`, made deliberately and separately.
