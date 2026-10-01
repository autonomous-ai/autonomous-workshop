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
  "schema_version": 2,
  "title": "Antisol",
  "inventor": "ad-astra",
  "envelope_mm": [200, 200, 60],
  "references": [
    {"file": "ref-01-antisol.png", "shows": "assembly"},
    {"file": "ref-02-world-disc.png", "shows": "geometry:world-disc"}
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
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": -72}}]}}
  ]
}
```
````

(The example abridges `geometries[]`; every id an Interface names must be a
Unique Geometry.)

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
- `geometries[]`: one entry per **Unique Geometry**. `id` is lowercase kebab
  case. `count` is how many Components the toy has with this shape.
  `wall_min_mm` is the minimum wall.
- `schema_version`: `2` for every new contract. A schema 1 contract has no
  `interfaces` and stays valid only for runs sealed before them.
- `interfaces[]` (ADR 0082): one entry per place two or more Components meet;
  `[]` when none do. `id` is lowercase kebab case and unique. `kind` is
  `static`, `separable` or `coupled`. `components` lists two or more
  different Unique Geometry ids.
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
- Every Interface has its Kind and two or more existing Components, a
  separable one its envelope and a coupled one its yielding Component and
  poses.
- Every Unique Geometry has at least one reference whose `shows` names it.
- Every reference file exists beside `CONTRACT.md` and meets the image rules.
- **At most 16 assembly-scoped requirements, and at most 4 per Unique
  Geometry** (ADR 0072). Both limits are input guards whose provenance the ADR
  records, not judgements about the toy. A contract that exceeds either one is
  cut back by the person, not by you.
- The whole file is at most 40,000 characters.
