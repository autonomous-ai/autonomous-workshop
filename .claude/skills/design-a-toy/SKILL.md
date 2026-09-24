---
name: design-a-toy
description: Design a complete Workshop toy with an Inventor before any run starts - grill the idea into a frozen spec, gate it, then generate one reference image per unique geometry and write the Design Contract for `build-a-toy`. Use when starting a new toy, or when a previous run drifted from what you wanted.
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

## Who designs

Read the Inventor's `TASTE.md` from `inventors/<id>/TASTE.md` and work as that
Inventor throughout. The Taste is the constitution: it decides what is in scope,
what wins a trade-off, and what gets rejected. Do not paraphrase it into
something more agreeable. If the idea the human wants is outside the Taste, say
so plainly and name which clause it fails — do not quietly widen the Taste to
fit.

Default Inventor: `ad-astra`.

## Stage 1 - Grill the idea into a spec

Invoke the `grilling` skill and work the design as a decision tree. Do not skip
this because the human arrives with a clear idea; a clear idea is usually a
clear *image* with the decisions still unmade underneath it.

Drive to a written spec containing:

- **Source game and rights.** The exact ruleset, its public-domain evidence, and
  the frozen rule-equivalence ledger: player counts, component functions and
  quantities, setup, turn order, legal actions, information, randomness,
  state transitions, interaction, ending, tie-breakers, scoring.
- **Theme mapping.** Every mechanical role to a thematic meaning and a physical
  cue, one to one. Flag any mapping that is only a renamed noun.
- **The unique-geometry list.** Group the component inventory by *shape*, not by
  part. Name each unique geometry and how many parts use it. This list drives
  everything downstream, and its length is the image budget.
- **The hero.** Exactly one component is the `signature`. Name it, say what it
  costs in sightlines and from which seats, and accept that cost in writing.
- **Per-geometry physical spec.** Form, duty, dimensions in mm, placement,
  interfaces, what it mates with. No hedged quantities — the Workshop concept
  contract rejects "roughly", "about", "several", "as needed". If a number is
  not decided, decide it.
- **Envelope, wall thickness, print stance.**
- **The fixed-frame plan.** How the set composes at 35 degrees azimuth, 22
  degrees elevation, against `#f5f0e6`, and which component is the focal point.
- **Mid-game check.** How the set reads in a crowded mid-game and a late-game
  position, with captured pieces off the board.

## Stage 2 - The gate

**Stop. Show the human the spec and the Design Contract block together, and
wait for explicit approval of both.**

Draft the block per
[CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md): one `geometries[]`
entry per item on the unique-geometry list, and one `requirements[]` row for
every checkable claim the prose decided — a dimension, a count, a wall
thickness, a visible feature. Check the block against the prose line by line,
not just against itself: a block that leaves out a decided number or feature
recreates the defect this gate exists to close. Name each
`references[].file` as `ref-NN-<slug>.png` in the order Stage 3 will generate
them, even though the files do not exist yet.

Check the drafted block against CONTRACT-FORMAT.md's row limits before
showing it: at most 16 assembly-scoped requirements, at most 4 per Unique
Geometry, and the whole file (prose plus block) under 40,000 characters. A
contract over either limit is cut back by the human, not by you.

This gate exists because image generation is the expensive stage: one image per
unique geometry, each iterated against pass criteria. Approving the spec and
its contract before spending that is the whole point. Do not generate a
single image before the human has approved both in this conversation.

If the human changes anything, update the spec and the block and show both
again.

## Stage 3 - Reference images

Generate **one image per unique geometry** from the approved list. A chess set
has six piece shapes, not thirty-four.

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

A generated image is allowed to be looser than the spec. That is a feature. The
spec carries the millimetres, the image carries the silhouette and the read.

Each image must be:

- **800x800 or smaller.** The likeness gate extracts a silhouette, normalizes
  height, and does not read color. Resolution beyond this buys no accuracy and
  spends the Wish's 48 MiB reference budget.
- **One subject, fully inside the frame.** The gate rejects a reference whose
  subject touches the image boundary. A populated board position cannot be a
  reference.
- **Named `ref-NN-<slug>.png`**, numbered from `01` in order with no gaps.
  Lowercase kebab slug. `png`, `jpg`, or `webp`. At most 99 images, at most
  12 MiB each.

Iterate each image against criteria stated up front — silhouette reads the
piece's role at thumbnail size, one focal point, contrast holds against
`#f5f0e6` — with a hard round cap. "Until it looks good" is not a stopping
condition. Take the best image at the cap and note what fell short.

Web imagery may be used as material to edit while composing an image. Judge
whether a source is safe to build from, and **record the source URL of every web
image you edit from** in the working notes beside the images. Never pass a found
image through as the reference itself: the likeness gate writes a measured
similarity score into the toy's public archive, and what that score describes
must be the Inventor's own expression.

## Stage 4 - Write the contract and hand off

Write `CONTRACT.md` beside the reference images: the approved prose, then the
approved `design-contract` block, exactly as
[CONTRACT-FORMAT.md](../build-a-toy/CONTRACT-FORMAT.md) requires. Confirm the
block's `references[].file` entries now match Stage 3's images one for one —
that is what lets `workshop wish --contract` seal this exact file, byte for
byte, as the run's hash-checked objective.

Hand off to the `build-a-toy` skill with the path to this `CONTRACT.md`. That
skill owns every run this design starts, round 0 through every correction,
always under `--contract`. Do not print a bare `workshop wish` command here.

Then state plainly what happens next: Make builds against these images, the
silhouette-likeness gate re-checks every round at IoU >= 0.90, and every
correction runs through `build-a-toy`, not back through this skill.

## What this skill does not do

- It does not run Workshop, publish, or touch a live run.
- It does not add a checkpoint inside Make. Once the Wish is sealed, the
  likeness gate is the enforcement.
- It does not widen the Inventor's Taste to accommodate an idea. That is a
  human edit to `inventors/<id>/TASTE.md`, made deliberately and separately.
