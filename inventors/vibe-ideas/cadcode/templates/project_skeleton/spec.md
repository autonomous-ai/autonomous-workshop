# CAD Spec — `<project_name>`

Human-readable design intent. The agent reads this before touching code.

## Object

<one-sentence description of what this thing is>

## Coordinate system

- XY plane is the part footprint.
- Z is vertical (up).
- Origin is at the center of the part / assembly.
- Bottom is at Z = 0; top is at Z = `height`.

## Parts

- `<name>`: <one-line role>
- `<name>`: <one-line role>

## Literal constraints

Copy every explicit dimension, count, and forbidden feature from the request
once. The owner is the named part or feature; exact envelopes apply to final
post-boolean geometry. Defaults and fit choices may fill omissions but may not
alter these requirements.

| ID | Owner.feature | Exact final requirement | Independent final-geometry proof |
|---|---|---|---|
| C1 | `<part>.<feature>` | `<value/count/absence and scope>` | `<measurement/assertion>` |

For every side-wall through-opening, prove the **final post-boolean solid**:
the center and near-edge points are air through the full wall depth, while
points immediately outside the requested width/height remain material. A
cutter bbox or an intermediate pre-union result is not proof.

For every explicit overall size or world-space extent, call
`cadlib.validation.verify_bbox` on its owning part **after the final boolean**.
Use `None` for unconstrained axes. Do not check the aggregate assembly unless
the request explicitly owns an overall assembled envelope; see
`references/literal-geometry.md`.

For every explicit straight cylindrical through-hole pattern, call
`cadlib.validation.verify_through_hole_pattern` after the final boolean with
its owning part, axis, centers, diameter, and world-space span. The expected
centers are the exact count; do not accept a non-zero global volume delta as
proof that the requested holes are correct.

For every explicit sharp rectangular through-cut, call
`cadlib.validation.verify_rectangular_through_cut` after the final boolean with
its axis, transverse center/size, and exact world-space span. For every sharp
axis-aligned region that must stay empty—especially “hollow with no posts or
dividers”—call `verify_clearance_box` with the owned bounds and open faces. Do
not substitute sparse point samples or apply a box proof to a rounded profile.

## Assembly & setup

Ordered steps to assemble + set up the finished print, and the clearance each
needs. Model the WHOLE component (captive cables, connector collars, plugs) —
**web-search the component's dimensions and state them as assumptions** (see
`references/component-integration.md`).

1. <install component X: how it goes in, what its cable/connector needs>
2. <place the device / route the cable / fasten>

## Functional checks

What it must do, each tied to a dimension and an enforcement. Hard fits →
`validate_params` asserts; assembly feasibility → `functional_warnings`.

- <e.g. captive cable + connector collar passes the OPEN route → functional warning>
- <e.g. device rests / charges / holds → assert or warning>

## Manufacturing

- FDM 3D printing, 0.4mm nozzle, PLA/PETG.
- Minimum wall thickness: 2.0 mm.
- Clearance for press fit: 0.2 mm.
- Clearance for slip fit: 0.4 mm.
- Avoid unsupported overhangs above 45°.

## Rules

- All numeric dimensions must live in `params.py`.
- Geometry code must not hardcode numbers.
- Each physical feature is its own function.
- Each part lives in `parts/<name>.py`.
- Each assembly lives in `assemblies/<name>.py`.
- `main.py` defines `gen_step()` and returns the final shape or an envelope
  containing `shape` plus structured `warnings`.
- Keep separately printable or removable parts as stable, named
  `cq.Assembly` children; union only geometry manufactured as one part.
- Keep `cad_project.json.model.parts` aligned one-for-one with those child
  names and source files; preserve IDs/order across ordinary edits.
- `scripts/cad` writes artifacts inside the project by default; use
  `--out-dir <dir>` when they should land elsewhere.
