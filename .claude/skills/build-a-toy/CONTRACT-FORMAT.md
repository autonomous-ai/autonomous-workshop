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

## The block

````markdown
```design-contract
{
  "schema_version": 3,
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
    {"id": "disc-peg", "kind": "static", "components": ["world-disc", "base"]},
    {"id": "disc-swing", "kind": "separable", "components": ["world-disc", "base"],
     "envelope": {"inside": "world-disc", "outside": "base", "shapes": [
       {"pose": "rest", "cylinder": {"base_mm": [0, 0, 20], "axis": [0, 0, 1],
                                     "radius_mm": 34, "height_mm": 8}}]}},
    {"id": "sun-drive", "kind": "coupled", "components": ["sun-gear", "world-disc"],
     "yielding": "world-disc",
     "poses": {"steps": 10, "movers": [
       {"component": "sun-gear", "rotation": {"axis_point": [0, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 36}},
       {"component": "world-disc", "driven": true, "rotation": {"axis_point": [40, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": -72}}]}},
    {"id": "disc-pair-mesh", "kind": "coupled", "components": ["world-disc#1", "world-disc#2"],
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
  Required in schema 3 and refused before it.
- `geometries[]`: one entry per **Unique Geometry**. `id` is lowercase kebab
  case. `count` is how many Components the toy has with this shape.
  `wall_min_mm` is the minimum wall.
- `schema_version`: `3` for every new contract: schema 2 plus a `camera` on
  every reference. Under schema 3 every Component file defines
  `assembly_pose(shape, pose)`, even one in no Interface. A schema 2 contract
  has no cameras and a schema 1 contract no `interfaces`; both stay valid only
  for runs sealed before them.
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
  `components`.
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

## Validation before any run

A contract is ready only when all of these hold. Report every failure at once.

- The block parses, and every field above is present and well formed.
- Every `id` is unique, and every `geometry:<id>` it cites exists.
- Every reference has a `camera` in range, and the person approved the
  cameras with the images.
- Every Interface has its Kind and two or more existing Components, a
  separable one its envelope and a coupled one its yielding Component and
  poses. An instance `<id>#<n>` names a geometry whose `count` is above 1,
  with `n` in 1..`count`.
- Every Unique Geometry has at least one reference whose `shows` names it.
- Every reference file exists beside `CONTRACT.md` and meets the image rules.
- **At most 16 assembly-scoped requirements, and at most 4 per Unique
  Geometry** (ADR 0072). Both limits are input guards whose provenance the ADR
  records, not judgements about the toy. A contract that exceeds either one is
  cut back by the person, not by you.
- The whole file is at most 40,000 characters.
