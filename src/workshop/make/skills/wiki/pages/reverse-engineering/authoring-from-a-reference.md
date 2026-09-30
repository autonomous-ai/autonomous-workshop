---
title: Authoring parts from a supplied reference
tags: [re-authoring, reference, multi-body, carrier, mesh-conversion, frame, reverse-engineering]
aliases: [re-author from stl, rebuild supplied model, carrier entry, multi-body step, kit of parts]
sources:
  - skills/step-to-source/references/re-authoring.md
  - skills/step-to-source/references/carrying.md
  - skills/step-to-source/scripts/carrier_project
  - "experience: kits converted from meshes that could not pass validate or interfere while carried"
related: [brep-vs-source, mesh-measurement, kit-assembly-poses]
updated: 2026-09-28
---

# Authoring parts from a supplied reference

Design rules for turning a supplied part (a refused STEP, or a converted mesh)
into parametric source. The stage procedure, layout and freezing of checks
stay in `skills/step-to-source/references/re-authoring.md`.

## Build it the way it was designed

- **Model the design intent, not the facets.** Box, pocket, chamfer the floor
  edges, cut openings. Never loft between measured slices: a lofted stack
  reproduces the facets and names nothing.
- **One parameter per measured quantity**, with the reading beside it:
  `MB_SHAFT_HOLE_D = 12.0  # y-axis hole, fitted r = 5.9971, res 0.007`.
  Derive instead of repeating: a chamfer's top radius is the body radius minus
  the chamfer.
- **Plan-view 45° corner chamfers grow under offset.** Offsetting a chamfered
  rectangle outward by `d` lengthens the corner cut by `d·(2 − √2)`. A flare
  lofted between two octagons needs that correction, or its corners twist.
- **A standard element is a catalog search first.** Gears, pins and bearings
  are searched on their governing numbers (module, tooth count, bore) before
  anyone authors them ([[gears]]).
- **Mates are derived, not retyped**: the second half comes from `cadfits`
  ([[joints#two-fit-classes-per-project]]).

## When the reference is an edit of your own model

A user sometimes hands back your model edited in another CAD system. Read what
they changed by diffing it against the source, part by part, never by eye.

- **Register each part before diffing it.** For each axis, take as candidates
  the offsets that align the bounding-box minimum, maximum and centre, plus
  zero and any group offset already seen. Keep the translation with the
  smallest symmetric-difference volume. A part that was only moved then diffs
  to zero. A thin skin over the whole part means the registration is wrong
  (the part was moved *and* edited), not that a skin was added.
- **Read the features from the booleans.** `edited − source` is what was added
  and `source − edited` what was cut. Each piece's bounding box, face types and
  cylinder radii name the feature: a 4.8 box added to one part and a 5.0 box
  cut from its neighbour is a peg in a 0.1 mm-a-side socket.
- **Children sit in their group's frame**
  ([[build123d-operations-and-export#export-step-and-import-step]]).
  Something that looks like a whole group moved is usually an exploded view.
- **Separate intent from artefact.** A change is intent when every part of a
  group moves by the same offset, or when one clearance repeats on every
  socket. It is usually a modelling artefact when it is a one-off nudge under
  a millimetre, a zero-clearance fit among fits that have clearance, bodies
  merged across colours, or one side finished and the other not.
- **Interfere the edit before copying it.** A hand edit has not been through
  any gate: two plugs entering one host from different faces can meet inside
  it.
- **Carry the language, not the coordinates.** Rebuild the pattern as
  parameters: both sides, the regions the edit did not reach, and one record
  per joint for both halves. Report what was not carried over and why.

## Frames, bodies and datums

- **Give each part the frame its reference arrived in.** For a print-plate
  kit, that is the footprint's bounding box centred on the origin with the bed
  at Z = 0. Reference and source then share coordinates, so a cut at
  `z = 3.4` is the same plane in both, and datums measured on the reference
  carry straight into parameters.
- **Keep separate bodies separate and labelled** (links, pins, wing panels, a
  housing around its shaft). Return each body as its own solid with a role
  label, in its original position. An assembly identifies parts by label, so
  fusing bodies, moving one, or leaving one unlabelled breaks it
  ([[kit-assembly-poses#right-part]]).
- **Record mating datums as parameters as soon as they are measured.** A bore
  centre, a recess span or a ledge height that another part seats on belongs in
  that part's parameter block, because after the references are released that
  block is the only place it survives.

## A multi-body reference already carries structure

A reference with several solids records how many bodies there are, which ones
repeat, and where each sits. One `import_step()` throws that away. One chain
reference held 100 solids: 98 links in six repeated sizes, one body, and one
9.26e-09 mm³ degenerate sliver.

- **Group repeated bodies by volume and face count, never by bounding box.** A
  repeated body laid along a curve arrives rotated, so its box changes while
  its volume and face count do not.
- **Measure roles, don't identify them** (`body_n`, `links_n`). The
  placeholder names are replaced once the part is known. A wrong guess in a
  filename outlives every comment.
- **Degenerate solids** (slivers of ~1e-8 mm³) are reported and left out.

## What a carried mesh conversion cannot pass

A carrier (an entry that imports the reference and returns it) is a scaffold
while parts are authored, never the finish. A reference converted from a mesh
typically cannot pass:

- **`validate`**, when it holds self-intersecting solids, as mesh conversions
  often do. Fusing them in the kernel does not repair them: on one kit the
  boolean lost 3–4 % of volume or did not merge at all.
- **`interfere`**, when one file holds overlapping shells that a slicer unions
  at print time. Those clashes sit inside a part, not between parts.
- **A small file.** Every facet is a B-rep face. A 15-part kit wrote a 536 MB
  combined STEP, and about 527 MB per assembled variant.

Once parts are re-authored, the overlapping-shell class of clash disappears,
and whatever remains is a real placement problem.

## Decide by measuring the file, not by asking

For unit, recovery route and whether a set is assembled, the file's answer
beats the user's: the user is recalling what some other program did, and the
file records what it actually did. Measure, decide, declare. Ask only when
going ahead would write something unusable, not merely something assumed.
