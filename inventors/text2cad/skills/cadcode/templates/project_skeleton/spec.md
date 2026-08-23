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
- The final shape is assigned to `result` at the end of `main.py`.
- Exports land in `exports/` (see `main.py`).
