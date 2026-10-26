---
name: design-a-toy
description: Design any physical Workshop toy - a vehicle, a jointed robot, a bone dragon, a puzzle, a game - with an Inventor before any run starts - grill the idea into a frozen spec, draft the Design Contract, generate one reference image per unique geometry plus the assembly, reconcile them with the contract feature by feature and with a Contract Proof modelled from the contract alone, check that everything they show can be printed and that any mechanism can move, then get the human's one visual review before handing off to `build-a-toy`. Use when starting a new toy, or when a previous run drifted from what you wanted.
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
contract and the images in agreement is this skill's job, done by the
Contract Proof and measurement in Stages 3a and 3b, so that approving the images is the same as approving the
contract.

## Lessons

[LESSONS.md](LESSONS.md) holds what earlier designs and builds taught. Read
its section for each stage before working that stage. It never overrides this
file, the Taste or the human's answer.

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
wall thicknesses, clearances, pin diameters or print stance. Decide
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
- **Kit or one print.** Whether the buyer assembles the toy from loose Parts,
  Rolife-style (a book nook does), or receives each Component as one
  printed object. A kit gets an Assembly Tree (Stage 2b). A kit is flat-pack: its furniture, boxes, shell and frames are
  flat Panels joined by tab and slot, and only small round or 3D props
  print whole (Stage 2b).
- **Colour and paper.** The filament colour of each printed Part, from the
  owner's filament catalogue (`src/workshop/wish/catalogues/filaments.json`).
  In a kit, each printed Part is one colour and a Component may hold Parts
  in several colours, with no cap on how many: a black hat and a brass
  stand on an oak desk are three Parts, never merged into the desk. A
  colour outside the catalogue needs the owner's approval, which is the
  owner adding it to the catalogue. Everything the images show that a
  filament cannot carry - pictures, covers, spines, page text, textures,
  skies, glazing - is printed paper the buyer applies (see Print Sheets,
  after Stage 3b): which pieces, on which part, and how each is applied.
- **Bought Parts.** Every purchased part (battery box, LED, pin, screw,
  clear jar, bead, wire) from the owner's Bought Part catalogue
  (`bought-parts.json`), within its size limits. One outside it needs the
  owner's approval, the same way.

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

### The chosen Concept Image, from three sides

The human agrees the chosen Concept Image before any component image or
contract exists. It usually comes from `brainstorm-concepts`; otherwise make
one with AI generation now. Work on it with the human, one change per round,
until they say it is right.

1. **Three sides.** Redraw the chosen Concept Image from three cameras in one
   generation, one row on one ground line (LESSONS.md, "Draw a part's extra
   views in one turnaround image"). Choose the cameras that show the most:
   the camera it was drawn from, then the sides it hides, such as the back,
   the side that shows a profile, or a top view of a scene in a box. Split
   the sheet into its views with
   [`scripts/proof_views.py`](scripts/proof_views.py) `split`. Where two
   views disagree (a window on one side only, a count that changes), it is a
   disagreement: fix it by editing, as Stage 3b resolves one, before the
   human sees the sheet. Every later edit of the concept keeps all three
   views.
2. **Fine details.** List every detail the concept shows that comes near the
   print minimums (Stage 3c's table) at the toy's size: feathers, quills,
   rivets, spokes, lettering, lace, thin legs and rails, a texture. For each,
   ask two questions: does it print, and does it still read as itself at the
   minimums? A 1.2 mm feather prints, as a flat stick.
3. **Show the ways.** For each detail at risk, show the human true-size
   renders of two or three ways to make it, chosen from: solid at the
   minimum, on a Print Sheet (ADR 0091), enlarged, left out. Model each way
   as a small CAD sketch of the detail with the CAD skill and render it with
   `proof_views.py render --px-per-mm N` at one scale for every way, beside a
   crop of the concept at the same scale. Mark the way you recommend and say
   why in one line ("the fan on paper keeps five feathers; solid it is a
   notched blade").
4. **The human picks** by eye. Write each answer into the spec, and edit the
   chosen Concept Image to show it. Stage 3c later checks every detail
   against what the human picked; it decides no fine detail on its own.

Done when: the human has said the chosen Concept Image is right, its three
views agree, and every detail at risk has the human's answer in the spec.

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
3c's table); a contract never states its own. The human chose in Stage 1
how each fine detail at risk is made, and Stage 3c checks the rest. The
contract names every detail that goes on paper or is left out where the
Component Reviewer reads it: in a requirement row of that Component, which is all of the contract the
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

Write the block as `"schema_version": 8` (ADR 0093), for every toy, kit or
not: [CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md) gives what
schema 8 adds to the earlier schemas, and Stage 2b adds a kit's Assembly
Tree to the same block. Every reference gets a `camera`
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

Then check every **shared face**. For every requirement or Interface
sentence that puts several Components on one face, plane or level ("share one
flat back face at Z 0"), check that each named Component's `extents_mm` and
every Interface range that places it allow it. Where a Component only reaches
the face, such as an inlay whose top is level with it, name it only in the
clause it meets. A Component thinner or thicker than its neighbours states its
thickness in its own row. Pixel Tree Key's R08 put the baubles on the body's
back face at Z 0, but each bauble is 0.8 thick and its Interface sets it at
Z 2.7 to 3.5, and the run stopped on the contradiction.

Then check every **assembly row**. An assembly-scoped requirement states only
what renders of the assembled toy in its Display Pose show: silhouette,
colours, counts, placement, visible features. The blind signature review
needs visible evidence for every assembly row, so a claim no render can show
fails it after everything else has passed. Move materials, filament types,
print order, pauses, inserted parts and physical behaviour to the prose, or
to a geometry row a gate measures. Pixel Tree Key's R09 named PLA types, the
print order and an inlay pause, and its run stopped after every round passed.

For a kit, write **one requirement row per Part** for what can be seen of it:
its outline, its relief, its colour and where it sits on its Component
("D01, each inkwell: a dark-blue bulb 3.6 across and 4.2 tall on a 2.4 neck,
standing on the shelf's left half"). A Component of thirteen Parts that packs
its inkwells, jar, feather fan and books into one row leaves the worker to
invent the rest.

Then split the prose into **one `###` section per Component**, or per Part
of a kit, and give every `geometries[]` entry its `prose_sections`: the
exact `###` heading text of each section that describes it
(`"prose_sections": ["Door (B06)", "Strap hinges (C01, two) and ring pull
(C02)"]`). A section that describes several Components, such as a joint
between two of them, may be named by each. The host hands a Component's
sections to its Component Worker with its rows. Rows still win: where a
section and a row disagree, the worker follows the row, and the Component
Reviewer judges by the rows and the reference alone.

Keep the whole file (prose plus block) under 40,000 characters.

Do not show the block to the human and do not wait for approval. For a kit,
go to Stage 2b; otherwise go straight to Stage 3.

## Stage 2b - Draft the Assembly Tree and the Component cut

A kit's contract adds the `assembly_tree` section of
[CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md) (ADR 0092). Draft it
now, after the concept is chosen and before any Reference Image, because the
Component cut decides which reference images there are. Read
`docs/research/book-nook-kits/rolife-assembly-trees.md` first. A split that
cannot be explained in one clear Manual step is a bad split.

1. **List the Parts.** Every thing the buyer handles: one printed Part per
   body of one filament colour (`A01-<mnemonic>`, any letter but M, N, P
   and S, one letter per filament), each Print Piece (`M01-...`) and each Bought Part
   (`P01-...`) from the catalogue. Tools, foam tape and dots, glue and jigs
   are not Parts: list them in `materials`.

   Draft the printed Parts **flat-pack** (owner decisions Q33-Q37,
   2026-10-26), as Rolife does (TGB19 page 14: a shelf is two slotted side
   panels with its shelves and bars slotted between them):
   - Furniture, boxes, the shell and frames are separate flat **Panels**,
     `"form": "panel"`, joined by tab and slot. Each prints flat without
     support, and its relief prints face-up and crisp.
   - Small round or 3D props (an inkwell, a ring pull, a feather fan, a
     crystal ball, a hat) are `"form": "solid"`, printed whole.
   - Every Panel of the toy is one thickness, `panel_mm` (default 2.0 mm,
     five 0.4 mm lines). A Panel that must be thicker states its
     `thickness_mm` and `thickness_reason`; do not reach for one without a
     reason a buyer would see (a moulding that cannot be relief on 2 mm).
   - A Panel is one filament colour. Its relief detail (a door's arch
     moulding, a frame) prints on its face; texture and colour go on Print
     Pieces.
   - Tabs press into slots without glue. Never write a clearance into the
     contract: it is one printer setting, `TAB_SLOT_CLEARANCE` in
     `print-details` (an estimate until the pilot's fit coupon).
   - A box closes with each Panel entering alone: the last Panel slides in
     along grooves, so no step moves two Panels at once.
2. **Order the steps** as Rolife does:
   - furniture and props are finished and dressed outside the room, then
     placed whole;
   - walls and ceilings are dressed while open or loose, then joined;
   - the interior goes in floor first, and the front and roof come last;
   - wiring is laid before anything closes over it: a step that encloses
     a lead declares its route and where it comes out, and the step that
     joins the leads sits at or above the smallest Sub-assembly holding
     every lamp it joins;
   - the light test comes first. It is a Check Step, outside the tree:
     list it in `checks` with every lamp and its power source.

   Each step joins its inputs with one joint kind (peg and socket, tab and
   slot, steel-pin hinge or foam tape; glue only with a stated reason), and
   every input that moves goes in alone along one straight direction.
   Applying a Print Piece is its own `paper` step, anywhere after its host
   exists. Write each step's instruction as one short English sentence, and
   mark a step a buyer could easily get wrong `error_prone`.
3. **Cut the Components.** Choose the subtrees that get their own reference
   image, worker and review: each Component is one contiguous subtree, and
   every printed and Bought Part belongs to exactly one. Each Component is
   one Unique Geometry, and its subtree is made as many times as that
   geometry's `count`. Prefer few Components of several Parts to many
   single-Part ones: a teacher's desk with its hat, ball and books is one
   Component of seven Parts in four colours, not seven Components, and a
   flat-pack cabinet is one Component of about six Panels plus its props,
   not one Component per Panel. The
   steps above the Components join them, and each join is an Interface.
4. **Lint.** Run
   `python3 .claude/skills/design-a-toy/scripts/contract_lint.py CONTRACT.md`
   on the draft. It runs the host's own parser and refuses a Part in two
   Components, a non-contiguous Component, a duplicate id or mnemonic, a
   colour or Bought Part outside the catalogues and a Print Piece whose `on`
   names nothing, and a printed Part without its `form` or a Panel off
   `panel_mm` without a reason. Fix every error. Its warnings name each
   catalogue entry the owner has not confirmed yet, which you list for
   Stage 4, and each Panel of another thickness with its reason, which you
   give a verdict in the working notes.

Make may not change the tree: its tree gates (ADR 0092 decision 8) check
every body, Print Piece and Bought Part against it. In the pilot a contract
tree defect (the tree itself missing, adding or duplicating a Part against
the Print Sheet or catalogue side, or otherwise inconsistent) stops the run
for the owner (decision 10). A labelling slip, a built body that does not
match a sound tree, is repaired in the run like any gate (owner decision
Q28, 2026-10-23). Once the owner has approved the tree in Stage 4, treat any
contract defect found later the same way, whoever finds it (a gate, a
review, an image check): log it as a row of the toy's `TREE-ISSUES.md`
(format in `build-a-toy`'s Step 3) and report it to the owner; never change
the tree yourself to make it go away. Bought Parts render in the reserved
magenta `#ff00ff` (bought, not printed): never name a filament of that
colour, nor draw a Bought Part in it on a reference image. Make writes the
kit's Manual from the tree with the step texts as written (decision 9), so
write each `text` as the buyer should read it.

## Stage 3 - Reference images

Generate **one image per unique geometry** from the Stage 1 list. Four
identical wheels are one image, not four. When the toy has more than one
component, also generate **one assembly image** of the whole toy, in its
Display Pose when it has moving parts: the overall silhouette is what a vehicle,
robot or creature is judged by first.

Draw each Component as a **three-view sheet**, in one generation (LESSONS.md,
"Draw a part's extra views in one turnaround image"): its reference camera
and two more that show what that camera hides. Split it with
`proof_views.py split` (Stage 3a). The view at the reference camera becomes
its Reference Image, `ref-NN-<slug>.png`, sealed and compared by the
Component Reviewer exactly as before. The other two become that Component's
Guide Image (Guide Images, below). Where the three views disagree with each
other, it is a disagreement, resolved as Stage 3b resolves one. The assembly
image stays one view.

**Always use AI image generation or AI image editing to make Reference
Images and the AI views of Guide Images.** No hand-written ray caster, no
procedural renderer, no parametric CAD script, no matplotlib, no SVG
assembled from coordinates draws one of them. CAD in this skill only checks:
the Contract Proof (Stage 3a) and Stage 1's true-size renders of a detail's
ways. The one exception is a trial: a Component reference AI-edited from
the Proof render (Stage 3a, last subsection), which the owner chooses. A Proof is never a Reference Image, and nothing compares it with the
model Make builds.

The reason is division of labour. A reference image is **concept art that
Make builds from**: it carries the read, the style and the design the words
have not caught yet. Hand-built exact geometry would do Make's work outside
every gate the run applies to it. The Proof does a different job. It is a
back-translation of the contract's words by someone who never saw the
images, so wherever it differs from an image, the words are wrong or
incomplete.

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
  spends the Wish's 480 MiB image budget.
- **One subject, fully inside the frame.** The gate rejects a reference whose
  subject touches the image boundary. The assembled toy counts as one subject; a
  scene, a diorama or a populated board position does not.
- **Named `ref-NN-<slug>.png`**, numbered from `01` in order with no gaps
  (`ref-100-<slug>` after `ref-99`). Lowercase kebab slug. `png`, `jpg`, or
  `webp`. At most 999 images, at most 12 MiB each.

Every image prompt limits plastic to the filament catalogue's colours: name
the colour of each printed Part from `filaments.json` ("the desk dark oak,
the hat black, the stand brass") and say that every plastic surface is one of
those flat colours. Paper areas are free: printed art may use any colour.

For a kit, also generate the one **kit image** the human approves the tree
from, with AI generation like the references: an **"in the box" flat lay**
of every Part laid out loose, each as many times as the toy holds it, in its
own filament colour, printed Parts grouped by colour, the Print Sheets and
Bought Parts beside them, with no arrows. Name it `kit-01-<slug>.png`. It is
never sealed or passed to a run; the contract and its tree win wherever they
disagree. Check it against the tree by count (every Part appears as often
as the toy holds it, and nothing else does) and by handedness: each Panel's
slots, knuckles and relief on the side and edge the contract puts them,
not mirrored.

Do not generate exploded views (owner decision Q31, 2026-10-26). Image
models cannot draw them correctly: in eight regenerate-and-review rounds
they mirrored Parts, pointed arrows backwards or at the wrong seat, left
inputs sitting in place and dropped one arrow while fixing another. The
exploded views with arrows come only from Make's deterministic Manual,
rendered from the built STEP, and the owner reviews them in the Manual
after the build.

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

## Stage 3a - Contract Proof

The human approves images and never reads the contract, so its words are
never reviewed against what they describe. The **Contract Proof** (ADR 0093)
reviews them: a fresh subagent that has seen no image and no note models
every Component, and every Part of a kit, in CAD at its true size from
`CONTRACT.md` alone. Every number it had to choose is a gap in the contract,
and laid over an image it shows where the image and the numbers disagree.

1. **Build.** Start the Proof as soon as Stage 2 (and 2b) has a draft; it
   needs no image and runs while Stage 3 draws. Spawn a fresh subagent with
   [proof-prompt.md](proof-prompt.md), its paths filled in: the contract,
   `<contract-dir>/proof/` and the contract's nozzle. Give it nothing else.
   It writes the CAD project, `GUESSES.md` and `FINDINGS.md`.
2. **Guesses to zero.** Close every row of `GUESSES.md` in the contract,
   prose and row together: a number, an outline or a position, decided as
   the Inventor from the chosen Concept Image and the images. Where the
   choice truly does not matter, write "free" in the contract at that spot
   (a hidden face's preview colour). Send the amended contract to the same
   Proof subagent, which still has seen no image, and repeat until its list
   is empty. The cabinet pilot listed 17 guesses, among them the door's arch
   curve, the inkwells' bulb and almost the whole feather fan.
3. **Contradictions.** Fix each one in `FINDINGS.md` as Stage 3b resolves a
   disagreement. Some live in the numbers alone: Night Charms Hall's cabinet
   door plate (19.5 x 25.3) could not cover its face (21.6 x 30.8), and no
   image showed it, because the stair hid the door.
4. **Compare.** Estimate each reference's camera (Stage 3b check 6) and the
   cameras of each Component's two other views, then lay the Proof over
   every image:

   ```sh
   uv run python .claude/skills/design-a-toy/scripts/proof_views.py refs CONTRACT.md \
     --proof <contract-dir>/proof --images <contract-dir> -o <contract-dir>/proof/compare
   uv run python .claude/skills/design-a-toy/scripts/proof_views.py compare <view.png> \
     <contract-dir>/proof/part_<id>.step.py --camera=AZ,EL -o <out.png>
   ```

   [`scripts/proof_views.py`](scripts/proof_views.py)'s docstring gives
   every command. Each compare is three panels: the AI image, the Proof at
   that camera and a 50% overlay, both at contract scale with a 10 mm bar. Every difference
   over Stage 3b's tolerance is a disagreement. Resolve it as Stage 3b does:
   an image that looks better amends the contract (and the Proof is
   rebuilt); otherwise edit the image by AI. When the image still disagrees
   after Stage 3's round cap and the contract is right, keep the image and
   name the difference in that Component's requirement row ("the reference
   draws the door taller; 24.5 holds"). The Component Reviewer then lists it
   as a Reference Conflict from the first round, not as a difference.
5. **Print gates.** `FINDINGS.md` lists every failure of Make's own print
   gates (`check_mesh`, `check_overhang`, `check_thickness` at the
   contract's nozzle) on the Proof's printable entries. Stage 3c resolves
   them.

The Proof runs again after **every** amendment, from here to Stage 5:
send the amended contract to the Proof subagent (a fresh one once its
context is gone, never one that has seen an image), then redo the compares
and print gates the change touches.

Record the guesses, findings and compares in the working notes.

Done when: `GUESSES.md` is empty, `FINDINGS.md` has no contradiction, every
compare shows no difference over the tolerance that its Component's rows do
not name, and all of it ran on the contract as it now stands.

### Trial: a Component reference edited from the Proof

An option being trialled (ADR 0093, owner decision 2026-10-26), not the
default. In the cabinet pilot, AI-editing the exact Proof render gave
references within about 0.2 mm on the first try, where six rounds of free
generation never came closer than 1-2 mm. The risk is the other way: the
edit draws only what the contract says and can drop what the concept drew.
Use it for **Component references only**, once the Proof's guesses are zero;
the assembly reference stays AI-drawn from the chosen Concept Image.

1. **Checklist.** Before editing, list every detail of the original: the
   Component's AI reference, or its view of the chosen Concept Image. One
   line per feature, count, colour, surface detail and ornament ("four
   round rivets on each strap", "wood grain running vertically", "a black
   ring pull with a hole").
2. **Edit.** Render the Proof at the reference camera
   (`proof_views.py render`) and AI-edit that render (`gen_image.py`, the
   render as IMAGE 1, the original as IMAGE 2): keep every outline and
   position of IMAGE 1, and give it the materials, colours and details of
   IMAGE 2.
3. **Check.** A fresh subagent checks the edit against the checklist from
   [carry-check-prompt.md](carry-check-prompt.md), with the details the
   contract leaves out or puts on paper quoted as `<NAMED>`; those are not
   losses. Its reply is one plain line.
4. **Lost details.** Re-edit naming each lost detail, up to Stage 3's round
   cap. When details are still lost, fall back to the AI-drawn reference.
5. **Sheet.** Compose the owner's comparison with the check's line:
   ```sh
   uv run python .claude/skills/design-a-toy/scripts/proof_views.py carry <original.png> \
     <edited.png> <proof>/part_<id>.step.py --camera=AZ,EL --line "<the check's line>" -o <out.png>
   ```

The owner chooses at Stage 4 which image becomes the Reference Image. The
one chosen goes through Stages 3b to 3e like any reference.

## Stage 3b - Reconcile every image with the contract

An image that passes its own criteria can still describe a different toy.
Before Stage 4, **measure** every image against the drafted contract. Do not
judge by eye. Measuring scripts are allowed here. They read an image; they do
not draw one. Stage 3a's overlays are the first instrument: the Proof sits at
contract scale beside each image, so read aspect, landmarks, masses and every
dimensioned feature off them, and measure the image alone only for what the
Proof does not draw.

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
   overall aspect matches. In the assembly image, measure each body's left
   and right edge too, not only its width, against the bodies above and
   below it: a shin block drawn flush under its thigh but contracted 4 mm
   wider on the outer side only reads as a leg shifted sideways, though each
   width alone passes.
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

   Then the **outline**. In each component image, measure the silhouette's width at
   every tenth of its height and every place it steps in or out, stands
   proud, curls or is cut away. Each one is a contract statement of outline:
   how far it stands proud, where it steps and where it is cut away. A
   detail the contract writes as an engraved line or a groove on a plain face
   while the image draws it changing the silhouette is a disagreement,
   however the feature list reads ("four fingers, a thumb: drawn, ok" passed
   a fist the contract kept as a box).

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

8. **Part colours** (kit). For each printed Part an image shows, sample its
   colour where the Part is lit flat and compare it with its filament's
   `hex` in `filaments.json`. A large miss (another colour family, or a
   light colour drawn dark) is a disagreement: regenerate or edit the image
   with the Part's colour named in the prompt. Shading is not a miss.

9. **Visible faces.** Every face an image shows must be visible from its
   Reference Camera in the Display Pose. For each moving or opening part (a
   door, a lid, a flap), name the faces the camera sees with the part in
   its Display Pose, and compare them with what the image draws. A door's
   outer face drawn together with the interior behind it, from a camera
   that would see the door's plain back, is a disagreement: no build can
   show it. Fix it by changing the composition (the open door continues the
   side panel forward) or the camera, never by accepting it.

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
  bed size. Then re-measure **every** image against the
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

### Guide Images

**Guide Images** (ADR 0089) explain the design rather than show one subject
to build toward. The run never compares them with the model, and the
Component Reviewer never sees them; the Workshop Manager and the Component
Workers read them. The contract wins over a Guide Image, never the other way.

**Every Component has one** (ADR 0093): a sheet with the two other views of
its three-view sheet on top and the Contract Proof at the same two cameras
below, at one scale with a 10 mm bar. Build it once Stage 3a's compares
agree:

```sh
uv run python .claude/skills/design-a-toy/scripts/proof_views.py guide \
  <proof>/part_<id>.step.py --view=AZ1,EL1=<view-2.png> --view=AZ2,EL2=<view-3.png> \
  --title "<Component>: two more sides" -o <contract-dir>/guide-NN-<id>.png
```

Its `guides[]` entry names the file, what it `shows` ("the door from the
hinge side and the back") and `"geometries": ["<id>"]`, so only that
Component's worker reads it.

A toy whose parts move between poses (a transformer, a folding vehicle) also
gets a colour-coded **transformation sheet** that draws every move, made with
AI editing from the approved references (LESSONS.md, "Draw transformation
steps as one chain of edits"), one colour per Unique Geometry. Its entry
lists the `steps` it draws, in order, worded as the Transformation section's
moves, and has no `geometries`, so it reaches every worker. Check it by eye
and by count: the number of steps and their order match the Transformation
section, each part keeps one colour in every panel, no panel shows a part,
joint or move the contract does not have, and the robot and car panels keep
the reference images' proportions. Fix a disagreement by editing the panel.

### Print Sheets

Each printed Part prints in one filament colour: a Component prints in one
colour unless it is a kit Component of several Parts (Stage 2b). Anything
the images show in more colours or finer detail than its Part's colour can
carry goes on paper instead (ADR 0091): pictures, notices, labels, book covers and spines, page text,
stone, wood and floor textures, wallpaper, skies, maps, glazing. The maker
prints these on A4 **Print Sheets** and ships them; the buyer cuts them out
with scissors, folds them and applies them. Decide this in Stage 1 with the
human, as a question about the toy ("the portrait and the notices are printed
paper in a shallow recess; the books are printed covers wrapped round plain
blocks"), never as a question about stocks or millimetres.

Give the contract a `print` section
([CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md)): the stocks, one
`art[]` entry per image and one `pieces[]` entry per thing the buyer cuts out.
Choose each piece's way from what it lands on:

| What it is | `way` | Stock |
|---|---|---|
| A picture, notice, texture or sky on a face | `flat`, into a recess about 0.4 mm deep | `paper` |
| Glazing in a frame | `flat` | `film` |
| A label or small sign that must stay put | `sticker` | `sticker` |
| A closed book, a box | `wrap` (`cover` or `band`) round a printed block | `paper` |
| A globe | `sphere` | `paper` |
| An open book, a scroll's pages | `fold` | `paper` |
| A cloud, tree or far roof layer that stands up | `stand`, in a slot | `card` |

Keep Kit-style economy: a shelf row of books is one `flat` spine strip, not a
piece per book; one art file may serve several pieces (`count`, or several
pieces naming it). The block, recess, sphere, fold face or slot each piece
lands on is part of its Unique Geometry: say so in that geometry's rows. In
a kit, a piece is a Part (`M01-<mnemonic>`), and its `on` names the printed
Part, Bought Part or Sub-assembly it lands on.

**Art.** Find patterns first: wallpaper, wood grain, stone, brick, fabric,
paper and sky come from CC0 stock (ambientCG, Poly Haven, public-domain
pattern scans), recorded with `source` and `"licence": "CC0-1.0"`; never use
anything that is not CC0. Draw only what stock cannot give (a portrait, a
notice's words, a book's cover) with AI generation, matching the reference
images' palette and style. Make every art file the shape of its piece laid
flat and at least 300 dpi at its printed size: a `wrap` cover is back, spine
and front, left to right; a `sphere` strip is the whole joined gore strip;
a `fold` strip is every page, left to right.

**Sheet proof.** Lay the sheets out with the same tool the run's gate uses:

```sh
uv run python src/workshop/make/skills/print-details/scripts/print_sheets.py \
  --contract CONTRACT.md --art <contract-dir> -o <contract-dir>/print-proof
```

It exits 1 and names every failure: a piece that fits no A4 sheet, a cut
edge under 5 mm, art missing, the wrong shape or under 300 dpi. Fix the
contract or the art until it passes. Its `sheet-<stock>-<n>.png` previews
are the sheet proof Stage 4 shows.

The Reference Images and the art must agree: where a reference shows a
printed area, its placement, size and overall colour are the reference's,
and its content is the art's. The run judges it that way, so redraw a
reference whose printed area shows something the art does not, or the art.

## Stage 3c - Check that what the images show can be printed

The build is scored against these images, so everything they show must be
printable at the size the contract gives it. Otherwise Make has to simplify it,
and a simplified part looks crude next to its picture. Workshop prints with a
0.4 mm nozzle, and its print gate refuses any part that needs support.

Start from the Contract Proof's print gates (Stage 3a step 5): Make's own
`check_thickness`, `check_overhang` and `check_mesh`, run on the contract's
numbers at its nozzle. They replace measuring scaled AI images for every
feature the Proof models: resolve each failure they name with the lists
below. The checks below the table still run, because no gate sees them: a
detail the Proof does not model, stacked and curved placements, hidden
joints and ceilings over moving parts.

Every fine detail at risk was answered by the human in Stage 1. One you find
now that has no answer goes back to the human the same way, with true-size
renders of its ways and your recommendation, before Stage 4; do not choose
for them.

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

Then check every feature **against its print stance and its floor**. For each
groove, slot, notch, curl, proud detail and cut-away the contract gives, turn
it into the stance the contract names and check that it prints without
support: an open-top groove or slot is free; one whose opening faces sideways
across the build direction has a roof, which fails unless it is a ledge under
1 deep or rises at 52 degrees. A finger groove 3 deep printed on the part's
side is a 3 mm cantilevered roof. When a detail fails, change the stance
before the detail. Then check each feature's width or thickness against its
geometry's `wall_min_mm`: a feature under the floor either grows, or the
contract lowers that geometry's floor and names why.

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

A detail that fails is resolved with the list below, in its order: on paper
when a Print Sheet can carry it (ADR 0091), otherwise a bigger toy, then a
bigger host, then the detail left out. A detail on paper or left out is
named in the Component's requirement row (Stage 2), never silently dropped,
and the images are edited to match whichever way it went. A fine detail at
risk takes the way the human picked in Stage 1.

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

Resolve each problem in this order of preference, and keep the look. A fine
detail at risk takes the way the human picked in Stage 1; you resolve the
rest:

1. **Make the whole toy bigger**, when many details are too small together and
   the bed still fits.
2. **Put the detail on paper** (a Print Sheet, ADR 0091), when it is a
   picture, texture, lettering or a flat detail paper can carry, and name
   the piece in the Component's requirement row.
3. **Enlarge the one detail**, when it can grow without changing the read.
4. **Change the print stance or split the part**, for a support problem.
5. **Reshape the underside**: a 45 degree chamfer, a teardrop hole or a
   pointed arch. Keep the silhouette the image shows. Never flatten an organic
   form into a box to pass the gate.
6. **Leave the detail out**, only when nothing above works, and name it in
   the Component's requirement row.

Any change to size, shape or stance amends the contract. Run Stage 2's
shared-face check again on every row and Interface the change touches. When
an image no longer shows what the contract says, fix the image by AI editing.
Then redo Stage 3b for every image you touched, and the assembly image.

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

Done when: the Proof's print gates pass on the contract as it now stands,
every feature the images show meets its minimum, every stacked or
curved detail fits its host or is on paper or left out and named, every form and
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
geometry. The script calculates; it never draws an image. Where the
Contract Proof models the moving parts, its sweep answers a check as well.

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

## Stage 3e - Lint the contract and have it audited

Stages 3b to 3d check the contract against the images and the model one fact
at a time, and one author does them. Two failures get past that: the same
fact stated twice that an amendment changed in one place only (an envelope
left at the old depth, a move still at its old angle), and the author
reading the contract as they meant it. This stage checks both, and runs again
after **every** amendment: Stage 4's changes, `build-a-toy`'s root
amendments and folded in-run amendments.

1. **Facts.** The Stage 3d model script writes the facts the contract states
   more than once: the Display Pose box, each Component's box and X span at
   each 1 mm of Z, a geometry's extents in its own frame when they are not
   its box, and each Component's moves and posing ranges.
   [`scripts/contract_lint.py`](scripts/contract_lint.py)'s docstring gives
   the format.
2. **Claims.** A fresh subagent that has not seen this design transcribes
   every move angle, placed range, feature size and envelope size the prose,
   the rows and the Interface texts state into `claims.json`, from
   [claims-prompt.md](claims-prompt.md) with its paths filled in. It copies
   numbers; it never computes or judges.
3. **Lint.** Run
   `python3 .claude/skills/design-a-toy/scripts/contract_lint.py CONTRACT.md facts.json --claims claims.json`.
   It compares the block (`envelope_mm`, `extents_mm`, Interface poses) and
   every claim with the facts, every feature size with its geometry's floor,
   and warns where a Component, or two it joins, keeps one X edge while the
   other steps. Fix every error in the contract or the model, whichever is
   wrong. Check every warning against the assembly image's edges there, and
   record the verdict.
4. **Audit.** Another fresh subagent audits the contract against the images
   from [audit-prompt.md](audit-prompt.md): outlines, neighbouring edges,
   printing in each stance, and contradictions. Resolve every finding as
   Stage 3b resolves a disagreement, and redo the checks it touches.

Record the lint output, the claims file and the audit in the working notes.

Done when: the lint reports no error, every warning and audit finding has a
recorded verdict, and both ran on the contract as it now stands.

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

Show a Component reference made by the Stage 3a trial as its `carry`
sheet: the original AI image, the image edited from the Proof and the Proof,
with the checklist's line under them ("14 of 14 details kept; the arch's
rim is named as left out"). The owner chooses which of the two becomes the
Reference Image; until they do, neither is sealed.

Show each reference as its Stage 3a compare: the AI image, the Contract
Proof at the same camera and their 50% overlay, side by side. The human
approves what will print, not only the concept. Name every difference a
requirement row keeps in one line under its compare ("the picture draws the
door a little taller; the door prints 24.5 mm").

Also say, in plain words, anything the build will not match exactly, from
Stage 3b or from the generation notes. List each Stage 3c change the same way:
what grew, what went on paper, what was reshaped for printing, and what was
left out ("the chin
rivets print as six 2 mm bumps, not ten small ones"; "the brow band prints
plain, without rivets"). A Stage 3d change hidden
inside the body gets one line ("the heart gear sits in front of the wing
gears so the train cannot jam; hidden in the back").

Show each Guide Image too, after the references, with one line on what it
explains ("guide-03 - the door from the hinge side and the back, drawn and
as it will print"; "guide-01 - the colour-coded transformation, car to robot,
seven steps"). Approving the images approves the Guide Images.

For a contract with a `print` section, show the print art and the sheet proof last: each
art image with one line on the piece it becomes and how the buyer applies it
("print-03 - the spell book's cover, wrapped round each of the six desk
books"), then every `sheet-<stock>-<n>.png` from the passing proof, with the
stock in plain words ("two sheets of thin paper, one of stickers, one of
card"). Approving the images approves the art and the sheets. A change to a
piece's art, size or count reruns the proof and shows the sheets again.

For a kit, show the "in the box" flat lay after the references, with one
line per Component naming its Parts and their colours ("the teacher's desk
- seven Parts: dark-oak desk, black hat, brass stand, clear ball, three
green books"). Approving the references and the flat lay approves the tree
and the Component cut; say that the exploded views come in the Manual after
the build, where the owner reviews them. Before showing it, reconcile the
tree's Print Sheet and Bought Part sides: `contract_lint.py` passes, every
Print Piece is one leaf applied as many times as it is printed, and every
Bought Part is one catalogued leaf. List each unconfirmed catalogue entry
the tree uses, in plain words, as a question for the owner ("is the 2.2 mm
cool-white LED the one in stock?"). A change to a Part, its colour or the
cut redraws the flat lay.

Wait for explicit approval of the images. If the human wants a change - a
different shape, proportion, count, pose or feature - fix the images by AI
editing or regeneration, amend the contract so it says what the new images
show, and redo Stages 3a to 3e for **every** image. Then update the same
Artifact page and show only the images that changed, each with its compare,
always with the assembly image, which is the one the likeness gate scores. Repeat until the human approves.

## Stage 5 - Write the contract and hand off

Write `CONTRACT.md` beside the reference images, the guide images and any
print art: the prose, then the
`design-contract` block, both reconciled with the approved images, exactly as
[CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md) requires. Confirm the
block's `references[].file` entries now match Stage 3's images one for one —
that is what lets `workshop wish --contract` seal this exact file, byte for
byte, as the run's hash-checked objective.

Approving the images is the go-ahead. Do not ask again: write the contract
and hand off to the `build-a-toy` skill straight away (for a kit,
only once its Make gates exist; until then report the contract as designed
and unbuilt) with the path to this
`CONTRACT.md`. That skill owns every run this design
starts, round 0 through every correction, always under `--contract`. Do not print a bare `workshop wish` command here.

Then state plainly what happens next: Make builds against these images, the
silhouette-likeness gate re-checks every round at IoU >= 0.90, and every
correction runs through `build-a-toy`, not back through this skill.

## Write back what the design taught

After the hand-off, add to [LESSONS.md](LESSONS.md) whatever this design
taught that the file did not already say. Sources: each change the human
asked for in Stage 4, a Stage 3b/3c/3d finding that took more than one pass,
and an image prompt that failed before one worked.

Apply its own test: a rule that adds a required step or check is a workflow
change to this file instead. Extend an entry before adding one, and name no
toy. Commit `LESSONS.md` and push it to the working branch, as any workflow
change; it reaches `main` with that branch. When nothing new was learned,
say so and change nothing.

## What this skill does not do

- It does not run Workshop, publish, or touch a live run.
- It does not add a checkpoint inside Make. Once the Wish is sealed, the
  likeness gate is the enforcement.
- It does not widen the Inventor's Taste to accommodate an idea. That is a
  human edit to `inventors/<id>/TASTE.md`, made deliberately and separately.
