# The Design Contract file

A Design Contract is one Markdown file, `CONTRACT.md`, kept in the same
directory as its reference images. It has two parts:

1. **Prose.** The full spec that `design-a-toy` Stage 1 wrote and the person
   approved at Stage 2. The Make agent reads it for intent.
2. **One fenced `design-contract` block.** The checkable enumeration of that
   same spec. This skill checks conformance against the block.

The whole file becomes the Wish objective, byte for byte. That is what lets
batch 2 seal this exact format with `workshop wish --contract` instead of
inventing a second one (ADR 0072). Keep the whole file under **40,000
characters**. A correction brief is itself a Wish objective, which is limited
to 50,000 characters, and every brief carries the full contract plus that
round's findings.

The block must cover the prose. If the prose decides something checkable, such
as a dimension, a count, a wall thickness or a visible feature, and the block
does not carry it, the contract is incomplete. Complete it and get it
re-approved before any run starts. A block that leaves something out
recreates the defect this skill exists to remove.

## The block

````markdown
```design-contract
{
  "schema_version": 1,
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
  ]
}
```
````

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
  `shows` is `assembly` or `geometry:<id>`.
- `geometries[]`: one entry per **Unique Geometry**. `id` is lowercase kebab
  case. `count` is how many Components the toy has with this shape.
  `wall_min_mm` is the minimum wall.
- `requirements[]`: the visual requirements, meaning what a person would
  judge by looking. `id` is `R` followed by two digits, unique. `scope` is
  `assembly` or `geometry:<id>`. That is the requirement's Requirement Scope.
  Write the text as one observable claim. A number already carried by a
  geometry field is not repeated here.

## Validation before any run

A contract is ready only when all of these hold. Report every failure at once.

- The block parses, and every field above is present and well formed.
- Every `id` is unique, and every `geometry:<id>` it cites exists.
- Every Unique Geometry has at least one reference whose `shows` names it.
- Every reference file exists beside `CONTRACT.md` and meets the image rules.
- **At most 16 assembly-scoped requirements, and at most 4 per Unique
  Geometry** (ADR 0072). Both limits are input guards whose provenance the ADR
  records, not judgements about the toy. A contract that exceeds either one is
  cut back by the person, not by you.
- The whole file is at most 40,000 characters.
