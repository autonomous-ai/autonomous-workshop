# build123d modeling patterns

Read this file when writing or repairing build123d Python source.

## Modeling objective

Create a valid STEP-ready BREP model, not a visual mesh. Prefer closed solids, explicit labels, and stable parametric dimensions. Define `gen_step()` returning the STEP-ready shape or labeled compound; the CLI owns output paths (see `step-generation.md`). Name a buildable entry generator `<name>.step.py` (the marker the build tools scan for); keep `<name>.py` for helper/library modules that are only imported, not built on their own (see "Entry generators are named `<name>.step.py`" in `step-generation.md`).

## Design strategy

Decide how the part is constructed before writing geometry code: construction
family, part vs assembly, origin from the functional datum, fragile operations
last, overshooting boolean tools, and one revolved profile for axisymmetric soft
forms. The rules and their reasons: `skills/wiki/pages/modeling/construction-strategy.md`
(`wiki show construction-strategy`); the operation family for each form:
`wiki show operation-families`.

## Topology stack

Think in this order:

```text
Vertex → Edge → Wire → Face → Shell → Solid → Compound
```

For assemblies, use these repo topology terms consistently:

- **Occurrence**: a placed node in the assembly tree. An occurrence has a parent, transform, path, and user-facing role such as `lid` or `m3_screw:front_left`.
- **Shape**: an exported geometry/body inside an occurrence. Shape rows own topology; faces and edges belong to a shape, and the shape belongs to an occurrence.
- **Face/edge**: selectable topology owned by a shape. Do not assume arbitrary faces or edges have persistent intent labels; inspect them by occurrence, shape, ordinal, surface/curve type, and measured geometry.

When inspecting topology, follow `assembly occurrence -> shape/body -> faces -> edges`. Every face/edge row should be traceable through both `occurrenceId` and `shapeId`.

For normal STEP output, return one of:

- a valid `Solid`
- a compound of valid solids
- a labeled assembly compound

Avoid returning loose wires, open faces, or construction surfaces unless the user explicitly requested them.

## Parameters first

Put meaningful dimensions in named variables:

```python
width = 80.0
depth = 50.0
thickness = 6.0
hole_diameter = 4.5
hole_offset_x = 30.0
hole_offset_y = 17.5
```

Avoid burying important numbers inside geometry calls.

## Coordinate system

Declare or comment the convention:

```text
Origin: center of primary part or chosen mating datum
XY: main base/sketch plane
+Z: up/extrusion direction
```

Use `Location`, `Plane`, and `Axis` intentionally. For positioning-sensitive tasks and source-level assembly relationships, read `positioning.md`.

## Builder contexts

Use the context that matches the geometry:

```python
with BuildLine() as path:
    ...

with BuildSketch() as profile:
    ...

with BuildPart() as part:
    ...
```

Typical flow:

```text
curves/paths → sketches/profiles → solids/features → labels → STEP
```

## Selection practices

Select by axis, normal, position or plane grouping, never by an index that a
boolean can reorder, and re-select after every boolean. Cookbook and rules:
`skills/wiki/pages/modeling/build123d-selectors.md` (`wiki show build123d-selectors`).

## Assemblies and positioning

For assemblies, keep this file focused on BREP modeling patterns and labels. Use `positioning.md` as the single source of truth for:

- part-local coordinate conventions
- when to use `cadgen.assembly.AssemblyHelper`, build123d joints, or explicit `Location` transforms
- `connect_to()` behavior
- CLI `inspect align` as read-only selector-pair alignment validation
- frame, measure, and positioning report expectations

## Labels and assemblies

Label every exported part and assembly child with native build123d labels. Prefer concise intent labels through `cadgen.assembly` helpers:

```python
from cadgen.assembly import AssemblyHelper, label_shape

asm = AssemblyHelper("electronics_enclosure")
base = asm.add(make_base(), "base")
lid = asm.add(make_lid(), "lid")

boss = label_shape(Cylinder(radius=3.0, height=12.0), "m3_boss", "front_left")
```

Do not prefix labels with topology categories like assembly, component, feature, datum, mate, or hardware. The assembly tree and topology inspection already expose those structural categories. Use labels for the intent topology cannot reliably infer: role, placement, interface, repetition, or mating purpose. Feature labels survive STEP export best when the feature remains a labeled child shape in a `Compound`; boolean-subtracted or fused feature history should be represented by source parameters, named datums, and validation refs instead of assumed persistent feature labels.

Label for inspection:

- Label the root assembly.
- Label every exported part, subassembly/module, and repeated component occurrence.
- Use occurrence labels for assembly role and placement, especially repeated parts: `m3_screw:front_left`, `m3_screw:rear_right`.
- Use shape labels for retained exported geometry/body roles where useful.
- Use feature/datum labels only when that geometry remains exported as a child shape.
- Use named mate datums for source-level positioning intent, then validate the exported STEP topology and occurrence frames.

Occurrence and shape labels are exported through STEP names and surfaced in `STEP_topology` when available. Downstream tools use occurrence labels for assembly/tree references and shape labels for shape references. Faces and edges inherit their context from `occurrenceId` and `shapeId`; do not promise persistent face/edge intent labels unless explicit tested support exists.

For repeated parts, keep occurrence labels, transforms, or joint connections explicit and inspect frames/positioning after generation.

## Colour

Three rules. The first and the last fail silently — no error, just a model that
looks wrong.

**Channels are LINEAR RGB, not sRGB.** The renderer converts them to sRGB on the
way to the screen, so `Color(0.5, 0.5, 0.5)` displays as roughly `#BCBCBC`, not
`#808080`. Picking channel values off a hex palette by eye gives a washed-out,
desaturated model. Never author a channel triple by hand.

**Every printable part takes its colour by name from the filament palette.** Three
stocks are loaded — Bambu Lab PLA Lite, PLA Matte and PETG Basic — so a model
coloured from them shows spools that can actually be loaded; a free hex invents
a filament nobody can buy. `scripts/cadfilament.py` owns the tables and does
the sRGB conversion, and imports with no path setup wherever `cadfits` does:

```python
from cadfilament import filament

body.color = filament("sunflower yellow")                    # PLA Lite
fin.color = filament("mandarin orange", material="PLA Matte") # PLA Matte
shell.color = filament("misty blue", material="PETG Basic")  # PETG Basic
lens.color = filament("cyan", 0.42)                          # with alpha
```

`material` defaults to PLA Lite. PLA Matte carries the pastels and muted tones
PLA Lite lacks (a mint, a coral-peach, a pale pink, warm off-whites): reach for
it before substituting a saturated Lite spool for a soft reference colour. Reach for PETG when a part flexes, takes an
impact, or sits somewhere warm; it is tougher and less brittle than PLA. A
print-in-place joint in it also needs `cadfits.print_in_place_gap(...,
material="PETG")`, because PETG strings and oozes more than PLA does.

**PLA Lite** — `material` default, no keyword needed:

| name | hex | name | hex |
| --- | --- | --- | --- |
| `beige` | `#F7E6DE` | `gray` | `#9FA19F` |
| `black` | `#000000` | `green` | `#00BB31` |
| `blue` | `#004EA8` | `orange` | `#FF671F` |
| `cocoa brown` | `#8E3C06` | `red` | `#FF0000` |
| `cyan` | `#00FFFF` | `sunflower yellow` | `#FFB549` |
| `dark gray` | `#6F6E6D` | `white` | `#FFFEF7` |
| | | `yellow` | `#FFD834` |

**PLA Matte** — `filament("<name>", material="PLA Matte")`, from Bambu's own
hex table:

| name | hex | name | hex |
| --- | --- | --- | --- |
| `apple green` | `#C2E189` | `ice blue` | `#A3D8E1` |
| `ash gray` | `#9B9EA0` | `ivory white` | `#FFFFFF` |
| `bone white` | `#CBC6B8` | `latte brown` | `#D3B7A7` |
| `caramel` | `#AE835B` | `lemon yellow` | `#F7D959` |
| `charcoal` | `#000000` | `lilac purple` | `#AE96D4` |
| `dark blue` | `#042F56` | `mandarin orange` | `#F99963` |
| `dark brown` | `#7D6556` | `marine blue` | `#0078BF` |
| `dark chocolate` | `#4D3324` | `nardo gray` | `#757575` |
| `dark green` | `#68724D` | `plum` | `#950051` |
| `dark red` | `#BB3D43` | `sakura pink` | `#E8AFCF` |
| `desert tan` | `#E8DBB7` | `scarlet red` | `#DE4343` |
| `grass green` | `#61C680` | `sky blue` | `#56B7E6` |
| | | `terracotta` | `#B15533` |

**PETG Basic** — `filament("<name>", material="PETG")`:

| name | hex | name | hex |
| --- | --- | --- | --- |
| `black` | `#000000` | `orange` | `#FF671F` |
| `dark beige` | `#DBC8B6` | `pine green` | `#034638` |
| `dark brown` | `#4F2C1D` | `red` | `#D6001C` |
| `gray` | `#7F7E83` | `reflex blue` | `#001489` |
| `green` | `#009639` | `white` | `#FFFFFF` |
| `misty blue` | `#688197` | `yellow` | `#FCE300` |
| `navy blue` | `#0086D6` | | |

Names match case- and separator-insensitively (`"Dark Gray"` = `"dark_gray"`),
and so do stock names (`"PETG Basic"` = `"petg_basic"` = `"PETG"`). A bare
`"PLA"` raises: two PLA stocks are loaded, so name one. Seven names are in both
PLA Lite and PETG Basic and five of them are a **different** hex in each, so the
stock is what decides which spool `filament("red")` means, and it is PLA Lite
unless you say otherwise. An unknown name raises with the list for the stock
asked for rather than guessing a near colour; a PETG-only name asked for as PLA
names the stock that carries it.
Run `python "$CAD_SKILL_ROOT/scripts/cadfilament.py"` for its self-check, which
round-trips every colour back to the published hex.
Two parts that must be visually distinct need two names from these tables — if
the reference colour is not in them, pick the nearest filament and record the
substitution in the spec, do not reach for the exact hex.

`cadgen.srgb("#rrggbb")` stays available for geometry that is deliberately not
printed filament — a purchased component, a reference surface, a see-through
datum:

```python
from cadgen import srgb

bearing.color = srgb("#8A8F98")       # purchased part, not a spool
```

**Colour on a group compound is ignored.** Only *leaf* occurrences carry colour
into the render package, so a colour set on a `Compound` that has children never
reaches the screen. It does reach the STEP file's XCAF label, which is why this
looks like it worked if you only check the STEP. Colour every leaf.

## Kernel gotchas

Every trap below builds a valid-looking solid or fails far from its cause, and
most pass `validate`. The measurements and fixes live in the wiki
(`skills/wiki/pages/modeling/`, `wiki search <words>`):

| trap | page |
|---|---|
| `Plane.rotated()` composes in world axes; write the inverse of a hand frame and assert the round trip | `frames-and-rotations` |
| lofts match sections by index; smoothstep creases; smooth lofts overshoot; diagnosing a failed loft; blend lobes that close inside the body | `loft-pitfalls` |
| `is_valid` passes inverted solids; BOP check after tangency-prone cuts; `Part(solid.wrapped)` has zero volume; control-hull bounding boxes | `kernel-validity` |
| a revolve or `Cylinder` seams at +X; a seam inside the material makes an invalid solid | `revolve-seam` |
| fillet retry ladders degrade silently; chamfers on tangent chains can SIGSEGV; dense periodic splines break taper, offset and fuse | `fillet-chamfer-pitfalls` |
| pairwise tool accumulation decays O(n²); overlapping tools misbehave; near-tangent and near-coincident booleans | `boolean-pitfalls` |
| 2D union decay, polygon winding, `Plane.XZ` extrude direction, `align=None` is the raw datum | `sketch-and-extrude-direction` |
| fitting a B-spline through a height grid rings; use the grid as control net | `bspline-height-fields` |
| one untriangulable face kills a whole-shape tessellation | `unmeshable-faces` |

## Common failure modes

The failure classes and what each usually means — open profiles, selector
drift, `ShapeList` accumulators, joints treated as persistent constraints,
`.connect_to()` fixing the wrong side — are `wiki show modeling-failure-modes`.

When generation or validation fails, read the failing gate's own output and
repair the source; `inspection-and-validation.md` covers how to read a
`validate` or `interfere` finding.
