# The Design Contract file

A Design Contract is one Markdown file, `CONTRACT.md`, kept in the same
directory as its reference images. It has two parts:

1. **Prose.** The full spec that `design-a-toy` Stage 1 wrote, reconciled with
   the reference images the person approved. The Make agent reads it for
   intent.
2. **One fenced `design-contract` block.** The checkable enumeration of that
   same spec. This skill checks conformance against the block.

This is the exact format `workshop wish --contract` and `workshop fix
--contract` seal: the whole file becomes the Wish objective, byte for byte
(ADR 0072). Keep the whole file under **40,000 characters**. A correction
brief is itself a Wish objective, which is limited to 50,000 characters, and
does not need to repeat the contract, since `fix --contract` seals it
separately from the brief.

The block must cover the prose. If the prose decides something checkable, such
as a dimension, a count, a wall thickness or a visible feature, and the block
does not carry it, the contract is incomplete. Complete it and get it
re-approved before any run starts. A block that leaves something out
recreates the defect this skill exists to remove.

## Print minimums in the prose

The prose states no print minimum of its own. Every minimum is the
print-details library's `limits()` at the contract's nozzle, the numbers Make
builds detail with and the Component Reviewer judges by: at a 0.4 mm nozzle a
rivet, boss or dome is at least 2.0 mm across, a raised band, rim or rib
0.9 mm, a wall or land 0.8 mm, a groove or gap 0.5 mm. `design-a-toy` Stage
3c lists them all. The print section carries two rules, word for word:

- "Every point, chisel, keel and V underside ends in a flat land at least
  0.8 mm across (one print minimum at a 0.4 mm nozzle)." The 0.8 mm is the
  nozzle's print minimum, never a geometry's `wall_min_mm`.
- "A drawn detail under the print minimums is enlarged to the minimum; when
  the enlarged detail does not fit its spot, it is left out, and this
  contract names it."

Every detail left out is named in a `requirements[]` row of its Component
("The brow band is a plain raised band and carries no rivets"): the
Component Reviewer reads that Component's rows and Interface text, not the
prose. Never write that a detail is "never left out", and never state a
smaller minimum, such as "every rivet at least 1.0 mm across".

## The block

````markdown
```design-contract
{
  "schema_version": 4,
  "title": "Antisol",
  "inventor": "ad-astra",
  "envelope_mm": [200, 200, 60],
  "references": [
    {"file": "ref-01-antisol.png", "shows": "assembly", "camera": [-60, 30]},
    {"file": "ref-02-world-disc.png", "shows": "geometry:world-disc", "camera": [-90, 75]}
  ],
  "geometries": [
    {"id": "world-disc", "name": "Planet disc", "count": 16,
     "extents_mm": [30, 30, 6], "wall_min_mm": 1.2}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly",
     "text": "The sun den is the focal point at 35 degrees azimuth, 22 elevation."},
    {"id": "R02", "scope": "geometry:world-disc",
     "text": "Each disc carries one raised equatorial band."}
  ],
  "interfaces": [
    {"id": "disc-peg", "kind": "static", "components": ["world-disc", "base"],
     "text": "Each disc's flat underside carries a 4 mm peg, 6 mm long, at its centre; the base has a 4.2 x 6 socket under each disc."},
    {"id": "disc-swing", "kind": "separable", "components": ["world-disc", "base"],
     "text": "Each disc swings inside a 34 mm radius drum above the base; the base keeps that drum clear.",
     "envelope": {"inside": "world-disc", "outside": "base", "shapes": [
       {"pose": "rest", "cylinder": {"base_mm": [0, 0, 20], "axis": [0, 0, 1],
                                     "radius_mm": 34, "height_mm": 8}}]}},
    {"id": "sun-drive", "kind": "coupled", "components": ["sun-gear", "world-disc"],
     "text": "The sun gear's rim teeth mesh with a toothed rim on each disc's edge.",
     "yielding": "world-disc",
     "poses": {"steps": 10, "movers": [
       {"component": "sun-gear", "rotation": {"axis_point": [0, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 36}},
       {"component": "world-disc", "driven": true, "rotation": {"axis_point": [40, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": -72}}]}},
    {"id": "disc-pair-mesh", "kind": "coupled", "components": ["world-disc#1", "world-disc#2"],
     "text": "The first two discs' rim teeth mesh with each other.",
     "yielding": "world-disc#2",
     "poses": {"steps": 8, "movers": [
       {"component": "world-disc#1", "rotation": {"axis_point": [40, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 30}},
       {"component": "world-disc#2", "driven": true, "rotation": {"axis_point": [72, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": -30}}]}}
  ]
}
```
````

(The example abridges `geometries[]`; every id an Interface names must be a
Unique Geometry. `world-disc#1` and `world-disc#2` are two of its 16
instances.)

## Field rules

- **JSON, not YAML.** The host must parse it deterministically with the
  standard library.
- `title`: the toy's name, without a revision suffix. The loop adds
  suffixes such as `v01`.
- `inventor`: an id from `inventors/`, passed to `--inventor`.
- `envelope_mm` and `extents_mm`: three positive numbers in millimetres, in any
  order. They are compared sorted, because Make chooses the axes. The
  tolerance is fixed at ±0.05 mm and is not a field: it describes the
  measuring instrument, not the design.
- `references[].file`: named `ref-NN-<slug>.png`, `.jpg` or `.webp`,
  numbered from `01` without gaps, each at most 800x800 pixels and 12 MiB,
  with one subject fully inside the frame. These are `design-a-toy`'s rules.
  `shows` is `assembly` or `geometry:<id>`. Pass every one of these files to
  `--ref` under these names and in this order: `wish --contract` and
  `fix --contract` refuse missing images and images that would seal under any
  other name, because Make finds an image's label by its name.
- `references[].camera` (ADR 0083): the reference's **Reference Camera**,
  `[AZ, EL]` in degrees, in the Display Pose (assembly) frame, assembly
  reference included. AZ is in -180..180 and EL in -90..90, in
  `render_review`'s convention: AZ 0 looks from +X, -90 from the front (-Y),
  90 from the back, 180 from the left; EL 0 is level and 90 looks straight
  down. design-a-toy estimates it by eye, rounded to 15 degrees. Make renders
  each Component placed by its `assembly_pose(shape, None)` from this camera
  beside its reference, so a wrong camera shows the wrong side of the model.
  Required from schema 3 and refused before it.
- `geometries[]`: one entry per **Unique Geometry**. `id` is lowercase kebab
  case. `count` is how many Components the toy has with this shape.
  `wall_min_mm` is the minimum wall.
- `schema_version`: `4` for every new contract: schema 3 plus a `text` on
  every Interface (ADR 0084). Schema 3 is schema 2 plus a `camera` on every
  reference; from schema 3 every Component file defines
  `assembly_pose(shape, pose)`, even one in no Interface. A schema 3
  contract has no Interface text, a schema 2 contract no cameras and a
  schema 1 contract no `interfaces`; they stay valid only for runs sealed
  before them.
- `interfaces[]` (ADR 0082): one entry per place two or more Components meet;
  `[]` when none do. `id` is lowercase kebab case and unique. `kind` is
  `static`, `separable` or `coupled`. `components` lists two or more
  different Components. Each is a Unique Geometry id or, when that
  geometry's `count` is above 1, one instance of it written `<id>#<n>` with
  `n` from 1 to `count` (issue #80): `wing#1` and `wing#2` for two wings that
  meet each other, or `wing#1` alone where only the left wing meets
  `heart-core`. One Interface never names a geometry and an instance of it
  together. Every other field that names a Component (`inside`, `outside`,
  `yielding`, a mover's `component`) uses the same references as
  `components`. `text` (schema 4, required and non-empty, no length limit)
  states in words what the Interface imposes on each Component it joins:
  every joint feature it puts on each side (a peg, a socket, a plug, a seat
  face), with its size and place. Make writes it into each joined
  Component's review packet and round summary, so the Component Reviewer
  and the Component Worker read it from the sealed contract. No gate
  measures or scores it; Interface checks stay numeric.
  - A `separable` Interface has an `envelope`: `inside` and `outside`, two of
    its Components, and `shapes`, each a lowercase `pose` name with exactly
    one `box` (`min_mm`, `max_mm`, min below max) or `cylinder` (`base_mm`, a
    non-zero `axis`, positive `radius_mm` and `height_mm`), in assembly
    coordinates. One shape is a static envelope; several are one per pose,
    each pose named once.
  - A `coupled` Interface has `yielding`, one of its Components, and exactly
    one of `poses` (`steps`, a positive integer, and `movers`, each naming
    one of its `component`s once with a `rotation` and/or `translation` in
    `check_motion`'s form and an optional `driven`) or `poses_from`, the id
    of a `coupled_motion_collision` condition in the CAD project's
    `measure/motion.json` whose movers name Components by id.
  - A `static` Interface has nothing more. No Kind takes another Kind's
    fields.
- `requirements[]`: the visual requirements, meaning what a person would
  judge by looking. `id` is `R` followed by two digits, unique. `scope` is
  `assembly` or `geometry:<id>`. That is the requirement's Requirement Scope.
  Write the text as one observable claim. A number already carried by a
  geometry field is not repeated here.
  An `assembly` row states only what renders of the assembled toy in its
  Display Pose show, because the blind signature review needs visible
  evidence for it. Materials, print order, pauses, inserted parts and
  physical behaviour go in the prose, or in a geometry row a gate measures.
  A row or Interface `text` that puts several Components on one face, plane
  or level agrees with each one's `extents_mm` and every Interface range
  that places it, and a Component thinner or thicker than its neighbours
  states its thickness in its own row.

## Validation before any run

A contract is ready only when all of these hold. Report every failure at once.

- The block parses, and every field above is present and well formed.
- Every `id` is unique, and every `geometry:<id>` it cites exists.
- Every reference has a `camera` in range, and the person approved the
  cameras with the images.
- Every Interface has its Kind, two or more existing Components and its
  `text`, a separable one its envelope and a coupled one its yielding
  Component and poses. An instance `<id>#<n>` names a geometry whose `count` is above 1,
  with `n` in 1..`count`.
- Every Unique Geometry has at least one reference whose `shows` names it.
- Every reference file exists beside `CONTRACT.md` and meets the image rules.
- Every assembly row states only what the assembled renders show, and
  every shared face agrees with the extents and Interface ranges of the
  Components it names.
- The prose carries the blunt-edge and detail rules above, states no
  minimum below the library's, and every detail left out has its row.
- **At most 16 assembly-scoped requirements, and at most 4 per Unique
  Geometry** (ADR 0072). Both limits are input guards whose provenance the ADR
  records, not judgements about the toy. A contract that exceeds either one is
  cut back by the person, not by you.
- The whole file is at most 40,000 characters.
