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
- **Envelope, wall thickness, print stance.** Name each geometry's print
  stance by the face that lies on the bed.
- **Blunt free edges.** Every point, chisel, keel and V underside ends in a
  flat land at least one print minimum across: 0.8 mm at Workshop's 0.4 mm
  nozzle. The land is sized by the printer, never by a geometry's
  `wall_min_mm`, which is a strength floor for load-bearing sections: a
  3.0 mm land would turn a 3.5 mm claw into a stub. A wing tip, a horn, a crest feather or a vault ridge is drawn and
  specified with that land, never as a knife edge. The print gate fails every
  straight knife edge as a thin wall, however its angle is tuned.
- **Every joint, pinned.** For each pair of Components that join: the joint
  type (peg and socket, collar, pin, snap, glue face), its dimensions and
  clearance in mm, and where it sits on both mating Components. Make builds
  joints exactly as written and cannot choose them: never write "hidden
  joints", "Make decides the pegs" or any other hand-off of joint geometry.
- **No two statements that cannot both hold.** A face cannot be both a
  Component's print-bed face and carry a peg, and a feature cannot sit on a
  Component the prose places it off. Make stops with a need when it finds
  such a pair.
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
thickness, a clearance, a joint range, a joint's geometry, a print stance, a
visible feature.

Every contract's prose carries the blunt-edge rule, word for word, in its
print section: "Every point, chisel, keel and V underside ends in a flat land
at least 0.8 mm across (one print minimum at a 0.4 mm nozzle)." The 0.8 mm
changes only with the nozzle: a contract for a larger nozzle states that
nozzle's print minimum instead. It never takes a geometry's `wall_min_mm`,
which sizes load-bearing sections, not lands. A requirement row that names a
sharp form says so too: "each wing ends in a chisel tip with a 0.8 mm land",
never "a sharp chisel tip".

The same section carries the detail rule, word for word: "A drawn detail
under the print minimums is enlarged to the minimum; when the enlarged detail
does not fit its spot, it is left out, and this contract names it." The print
minimums are the print-details library's, at the contract's nozzle (Stage
3c's table); a contract never states its own. Stage 3c decides, detail by
detail, which one is enlarged and which one is left out, and the contract
names every one left out where the Component Reviewer reads it: in a
requirement row of that Component, which is all of the contract the
reviewer sees besides its geometry row and Interface text ("The brow band
is a plain raised band and carries no rivets"). Fold it into the row that
already describes the host, so it costs no row of its own. Never write "never left
out": a reviewer holding that rule and an image of a detail that cannot fit
asks for exactly that detail, round after round.

Check the block against the prose line by line,
not just against itself: a block that leaves out a decided number or feature
lets the run drift, and nobody downstream reads the prose closely enough to
notice. Name each
`references[].file` as `ref-NN-<slug>.png` in the order Stage 3 will generate
them, even though the files do not exist yet. A toy with more than one
component also gets one `"shows": "assembly"` reference, listed first.

Write the block as `"schema_version": 4`. Every reference gets a `camera`
(ADR 0083), which Stage 3b fills in once the image exists, and every place
two or more Components meet gets an `interfaces[]` entry (ADR 0082): a peg in a socket, a
pinion on a sector, a wing swinging past a housing. Give each its Interface
Kind:

- **static** for parts that sit together and never move against each other.
- **separable** when one Component only has to keep clear of another. Give
  it a Keep-out Envelope: which Component stays `inside` and which stays
  `outside`, and one simple box or cylinder in assembly coordinates per
  declared pose (or one for a part that does not move). Size it from the
  prose's clearances, so each side can be built without the other's outline.
- **coupled** for anything that needs contact or shares space over time:
  gears, cams, linkages, parts that pass through one space at different
  times. Name its `yielding` Component, the one that changes when the
  check fails, and give its pose table (`poses`: steps and movers, each with
  its rotation or translation in assembly coordinates) from the same numbers
  Stage 3d checks.

Give every Interface its `text` (ADR 0084): in words, what it imposes on
each Component it joins, with sizes and places, for example "The staff's
bottom 10 mm, a bare Ø3.7 shaft below the ferrule, sits in a Ø3.9 × 10
socket in the base at X −40, Y −32." Name every joint feature it puts on
each side: pegs, sockets, plugs, seat faces. Make hands this text to each
joined Component's reviewer and worker, and where an image shows something
the text forbids, the contract wins and the run reports the image.

When copies of one Unique Geometry meet each other, or only one copy meets
another part, name the copy: `<id>#<n>`, with `n` from 1 to the geometry's
`count`. A mirror pair that meshes, such as two wing roots geared to each
other, is a coupled Interface between `wing#1` and `wing#2`; a pinion that
drives only the left wing joins `wing#1` and the pinion's geometry. Use the
same names in `inside`, `outside`, `yielding` and the movers, and never put
`wing` and `wing#1` in one Interface.

A toy whose Components never meet has `"interfaces": []`. Never leave a
meeting out: one the block does not name is one nobody checks before
assembly.

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

6. **Reference Camera.** Estimate, by eye, the camera each image shows its
   subject from: `[AZ, EL]` in degrees, in the Display Pose (assembly)
   frame, rounded to 15 degrees, in the convention
   [CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md) gives (AZ -90 is
   the front, 0 the right side; EL 90 looks straight down). For a component
   image this is where the camera stands relative to the Component as it sits
   in the assembled toy, not as it prints. Write the cue you read it from in
   the working notes ("front and left faces visible, seen slightly from
   above"), and the camera into the image's `references[]` entry. Make
   renders the Component from exactly this camera beside its image, so a
   camera that shows the wrong side wastes a run. There is no silhouette
   pose search; the estimate is yours.

7. **Joint features.** For every joint feature an Interface puts on a
   Component (a peg, a socket, a plug, a seat face), look at that
   Component's image from its Reference Camera. If the camera can see the
   feature, the image must show it as the Interface `text` contracts it:
   a ferrule drawn as the foot where the shaft continues into a socket, or
   a flat flange where the Interface makes a seat cone, is a disagreement.
   If the camera cannot see it, the image need not show it. An image left
   showing what the contract forbids becomes a Reference Conflict in every
   review of that Component.

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
limits.

The minimums are the print-details library's `limits()`, the ones Make
builds detail with and the Component Reviewer judges by; where this table
and the library ever disagree, the library wins. Print them for
the contract's nozzle with
`python src/workshop/make/skills/print-details/scripts/print_details.py --limits --nozzle N`;
at Workshop's 0.4 mm nozzle they are:

| Feature | Minimum at 0.4 mm | `limits()` name |
|---|---|---|
| A solid thin member: a bar, rib, claw, shaft, blade edge or wall | 0.8 mm across | `min_wall` |
| The end of a point, chisel, keel, crest, ridge or V underside | a flat land 0.8 mm across | `min_wall` |
| A rivet, boss or dome | 2.0 mm across | `min_feature` |
| A raised band, rim or rib | 0.9 mm across | `min_relief_width` |
| Any raised detail | 0.5 mm high | `min_relief_height` |
| A groove, slit, slot, gap or opening meant to stay open | 0.5 mm across | `min_cut_width` |
| An engraved or inset cut | 0.5 mm deep | `min_cut_depth` |
| Material between two cut copies: slits or windows side by side | 1.6 mm | `min_web` |

Then check every **stacked or curved placement**: each detail the images draw
on another detail (rivets on a band, a boss on a rim) or on a curved host (a
band round a helm, rivets round a chin). Size each detail at its minimum, or
at its contract size when that is larger, and check:

- **The host holds it.** The host is at least the detail's size plus 0.5 mm
  on each side: a 2.0 mm rivet needs a band or ridge at least 3.0 mm wide.
- **It stands clear of a concave host.** A raised detail on a concave surface
  keeps at least 0.5 mm above it everywhere, across the curve, not only at
  its centre.
- **Copies keep apart.** Copies in a row keep a 0.5 mm gap between them, so a
  row of 2.0 mm rivets has a pitch of at least 2.5 mm; count how many fit
  the host's length at that pitch.

A detail that fails is resolved with the list below, in its order: a bigger
toy, then a bigger host, then the detail left out. A detail left out is
named in the Component's requirement row (Stage 2), never silently dropped,
and the images are edited to match whichever way it went.

Worked example: Broken God's crest helm (`ref-07`, attempt 14). Its face is
about 20 mm wide at contract scale, and the image draws a riveted brow band, a
riveted nose bar and rivets round the chin. The band measures about 1 mm
wide, and its rivets are smaller than the band.

| Detail | At contract scale | Minimum | Stacked check | Verdict |
|---|---|---|---|---|
| Brow band | 1.0 mm wide | 0.9 mm across (`min_relief_width`) | none | passes |
| Rivets on the band | under 1.0 mm across | 2.0 mm across (`min_feature`) | band at least 2.0 + 2 x 0.5 = 3.0 mm wide; it is 1.0 mm | fails |

The contract said "every rivet at least 1.0 mm across" and "never left out",
so nothing caught this before the run. Enlarged to 2.0 mm, a rivet covers
twice the band's width and hangs over both its edges, and the Component
Reviewer, holding the image and that rule, asked for a band and rivets that
could not print together; the worker spent 18 rounds on the refusals. In
Stage 3c's order:

1. **Bigger toy.** A 3.0 mm band needs the helm three times larger; the rest
   of the toy cannot grow with it. Rejected.
2. **Bigger host.** A 3.0 mm brow band is 15% of a 20 mm face: a visor, not a
   band. Rejected, because it changes the read.
3. **Leave the rivets out.** The band stays, as a plain raised band at its
   own size; the rivets go. The helm's requirement row names it: "The brow
   band is a plain raised band and carries no rivets." The image is edited to
   a plain band, and Stage 3b runs again on it.

The nose bar and the chin rivets get the same check, each against its own
host: rivets on the nose bar need a bar at least 3.0 mm wide, and the chin
holds only as many 2.0 mm rivets as its length allows at a 2.5 mm pitch.

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
5. **Leave the detail out**, only when nothing above works, and name it in
   the Component's requirement row.

Any change to size, shape or stance amends the contract. When an image no
longer shows what the contract says, fix the image by AI editing. Then redo
Stage 3b for every image you touched, and the assembly image.

Then check every hidden joint the contract pins, which no image shows. For
each Component, take its print stance and its bed face, and for each peg,
socket, collar, pin or boss it carries:

- **Nothing stands on the bed face.** A peg or collar on the bed face lifts
  the part off the bed. Mating faces that print face down cannot also carry
  pegs; move the pegs to the other side of the joint or change the stance.
- **Nothing prints over air.** A collar, lip or boss that sticks out sideways
  in the print stance hangs unsupported. A socket or pin hole that runs
  parallel to the bed needs a teardrop or pointed top.
- **Both sides agree.** The peg and its socket have the same axis and
  position on the two mating Components, and the clearance is at least
  0.2 mm a side.

Resolve each problem with the list above. A resolution that moves a visible
feature from one Component to another is a visible change: redo the images it
touches. Compute the checks with a script only when the joints are too many to
check reliably by hand.

Then check every **ceiling over a moving part**, when the toy has one. A part
that turns or slides through the inside of another part empties the space it
sweeps: the other part may not stand anything there, from its bed up to the
moving part's far face plus the clearance. In that other part's print stance,
every ceiling, overhang or bridge over the swept space prints over air. For
every moving part, take its full travel plus the clearance, and for every
other part it passes through:

- **Clearance first.** The ceiling sits at least the clearance beyond the
  moving part's far face.
- **Each ceiling point is bridged or vaulted.** It has support on both sides
  along one line within 12 mm, or the ceiling rises from the nearest support
  at 50 degrees (1.19 mm per mm) and still fits inside the part, with its
  minimum wall behind it.
- **Each seat holds.** A hinge, axle or bore seat in such a ceiling sits at
  the height its pin needs: a vault that lifts the seat shortens the pin's
  press depth.

The swept space includes everything the contract fixes on the moving part:
every gear at its tip radius (a 24-tooth gear at pitch radius 16 is a full
disc unless the contract trims it), every boss, the teeth the travel needs
plus one spare at each end, and the plate and blades. Leaving a piece out can
only hide a failure. When the moving parts turn about axes normal to the
other part's bed, compute the check with
`python .claude/skills/design-a-toy/scripts/swept_ceiling.py CHECK.json --map`;
its docstring gives the input. Otherwise sample the sweep by hand in each bed
layer.

Resolve a failure with the list above: a different stance or a split, so the
ceiling becomes a wall or a bed face, comes before reshaping. A vault that
lifts a seat changes its pin, and an opening that lets the travel through
changes what the images show.

Worked example: Broken God's spine housing (attempt 15, amend-i). The housing
prints on its front face, the mating plane at Y 7.3, and builds toward its
back wall, whose front face at Y 17.5 carries both wing hinge seats (X ±16,
Z 198.8). Each wing's 24-tooth sector gear (pitch radius 16, tip radius 17.1)
turns 35 degrees in the layer Y 11.8 to 17.1, and the heart pinion (tip
radius 9.25 on X 0, Z 180.9) turns in front of the housing's pillar.

| Check | Value | Limit | Verdict |
|---|---|---|---|
| Back wall behind the sector layer | Y 17.5 | 17.1 + 0.5 = 17.6 | fails |
| Hinge seat, nearest support | 18.0 mm (the gear is a full disc round the seat) | bridge within 12 | fails |
| Hinge seat, vault height | Y 39.1 | 17.5, where the Ø3 × 16 dowel is pressed 6.3 | fails |
| Pillar face over the pinion, bridge | 19.5 mm | 12 | fails |

Nothing caught this before the run. Amend-e had checked the hinge seats
against the root bosses only, not the sector layer behind them, so the worker
spent its rounds on the back wall's overhangs and then reported itself
blocked. Keeping the wings below Z 206.2 inside the housing, the first fix
proposed, still fails the check (the seat's vault reaches Y 27.1, nearest
support 8.0), and Stage 3d refutes it anyway: the teeth that mesh through the
35 degree travel reach Z 208.6 even without a spare tooth. The fix has to
change the stance or split the housing, so that the back wall prints as a
wall or on its own face.

Record every check in the working notes as a table: image or joint, feature,
size at contract scale, minimum, verdict, resolution.

Done when: every feature the images show meets its minimum, every stacked or
curved detail fits its host or is left out and named, every form and
every hidden joint has a support-free stance, every ceiling over a moving
part's sweep is bridged or vaulted with its seats held, and every change is in
both the contract and the images.

## Stage 3d - Check that the mechanism can move

When the toy has no moving part, skip to the camera-composition check at the
end of this stage, which every toy runs. Otherwise, the images and
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

Bring the Interfaces up to date with what you fixed: every mesh and every
swept clearance is a coupled Interface whose pose table matches the sweep
you just ran, and every envelope still holds its side through the travel.

Then check every **travel stop** the contract names: each hard stop that a
host Component's material puts at an extreme of a motion ("hard stops on
vertical housing faces end both extremes"). The swept space, the openings
that let the travel through and the print stance were each fixed for their
own reasons, and together they can leave the host no material to stop with.
For each stop, at each extreme it names, the host needs material that

- lies outside every moving part's swept space over its travel, plus the
  clearance;
- lies in a stopping part's way within 4 degrees past the extreme (its lead;
  a part geared to it counts too);
- prints in the host's stance: it grows from the bed, or from material the
  contract already prints, never steeper than the overhang limit, at least
  0.8 thick.

When the parts turn about one axis, compute it with
`python .claude/skills/design-a-toy/scripts/travel_stop.py CHECK.json --map`;
its docstring gives the input. The script cannot read the contract, so
supply it: one slice per layer the moving parts occupy along their axis
(each with the host's section there as an outline, its contract openings and
other parts' envelopes as `keep_out`, and as `anchors` only material the
contract prints by other means, such as a pillar whose roof leans on a wall
behind the slice), each moving part's section in that layer at its contract
numbers with its travel toward the extreme, and the build direction from the
host's stance. Leave out nothing the contract fixes on a moving part, as in
Stage 3c. For any other motion, sample the leads by hand.

When no slice holds a site, the stop cannot be built where the contract puts
it. Before sealing, name another stop: another Component, a shoulder in the
gear train or the detent, keeping the words to what is buildable. A new
stop that shows changes the images too.

Worked example: Broken God's open extreme (attempt 17, amend-k). R03, the
`wing-housing` Interface and the mechanism prose put hard stops on vertical
spine-housing faces at both ends of the 35 degree wing travel. The housing
prints upside down on its top (Z 208.7), and its shoulder slots open through
the top in front of the back wall (Y 7.3 to 17.6).

| Slice | Extreme | Wing lead (wing#1 / wing#2) | Verdict |
|---|---|---|---|
| Sector layer, Y 11.8 to 17.6 | open | wholly outside the 40.7 outline | no site |
| Boss layer, Y 7.3 to 11.8 | open | 3.3 / 2.0 mm² free, nearest printable 14.2 / 12.0 away: each hub sweeps the column to the bed | no site |
| Boss layer, Y 7.3 to 11.8 | closed | a central rib above the sector mesh, Z 199.5 | site |

No housing stop can end the open extreme. Nothing caught this before the
run, which measured 0.000 mm³ of top-down-printable housing in both wings'
leads and stopped on a Contract Contradiction. The fix (amend-l) kept the
closed hard stop and named R06's detent for the open extreme, a change to the
words alone.

Record every stop in the working notes as a table: stop, host, extreme,
slice, lead, site, verdict, resolution.

Last, check every **camera-named composition claim**, moving parts or not.
The pose, the cameras and the words were fixed separately, and a claim true
from one camera can be false from another. For every requirement that names
a camera and claims a composition or silhouette in the Display Pose (framing,
a V, a line, an arc, symmetry, what is in front of what), project the
landmarks the contract pins through that camera and confirm the claim. The
landmarks are the ones the claim is about, at their contract numbers: blade
and limb centrelines, hinge and pivot points, extents, the focal part's
centre. Compute it with
`python .claude/skills/design-a-toy/scripts/camera_composition.py CHECK.json`;
its docstring gives the input, the camera convention (`render_review`'s, the
one `references[].camera` uses) and the claims it judges. Read framing, arcs
and silhouettes from the screen positions it prints. When the prose gives a
camera in another convention ("35 degrees azimuth" with no frame), convert it
and record the conversion; if the claim's truth depends on the reading, the
words are ambiguous and must change too.

A claim that fails changes before the images are approved: the camera, the
pose or the words, whichever the Inventor's Taste can best spare. Prefer
deleting or narrowing the words when the images already show the pose; a new
camera or pose changes what the images show, so redo Stage 3b for them.

Worked example: Broken God's R01 (attempt 16): "At 35 degrees azimuth and 22
degrees elevation ... the chest cage ... is the focal point, framed by the
open wings as a V." R02 fixes the pose: both wings open and mirrored, each top
blade's centreline 4.3 degrees above horizontal. The blades hinge at X ±16,
Z 198.8 and reach about 175 mm outward along ±X.

| Camera | Blade at +X | Blade at -X | Claim "as a V" |
|---|---|---|---|
| [35, 22] in `render_review`'s convention | falls 22.5 | rises 33.3 | fails |
| [-55, 22], 35 degrees round from the front | falls 10.1 | rises 19.2 | fails |
| [-90, 15], ref-01's camera | rises 4.2 | rises 4.2 | holds, a shallow V |

From either reading of R01's camera the blades make a tilted, near-straight
line, not a V; only near the front do they rise in mirror. Nothing caught this
before the run, which stopped on a Contract Contradiction that both its
Contract Reviewer and a blind critic confirmed. The fix (amend-k) deleted
"as a V" from R01, a change to the words alone, so no image changed.

Record every claim in the working notes as a table: requirement, camera,
landmarks, projected numbers, verdict, resolution.

Done when: every check passes on the contract as amended, the motion plan is
in the contract, the Interfaces match it, every named travel stop has a
printable site at each extreme it ends, and every camera-named composition
claim holds from its camera.

## Stage 4 - Visual review

**Stop. This is the only approval gate.** Show the human every reference image
at once, assembly first. Give each one a single line in plain words: what it is,
how many parts use it, and the camera it is seen from with its cue
("ref-02 wheel - four of these; seen from the front-left, slightly above
(-60, 15)"). Approving the images approves these cameras. Publish them as one
private Artifact page (load the `artifact-design` skill first) that works at
phone width and shows the whole set in one look, and give the human its link
plus each file path. Do not show the contract, the requirement rows, the
measurement table or millimetre lists unless the human asks.

Also say, in plain words, anything the build will not match exactly, from
Stage 3b or from the generation notes. List each Stage 3c change the same way:
what grew, what was reshaped for printing, and what was left out ("the chin
rivets print as six 2 mm bumps, not ten small ones"; "the brow band prints
plain, without rivets"). A Stage 3d change hidden
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
