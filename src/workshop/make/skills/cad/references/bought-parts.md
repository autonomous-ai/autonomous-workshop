# Seating a bought part — `cadmount`

A servo, gearmotor, bearing or board is the one kind of dimension a project
cannot own. It lives in a datasheet, a product page or a photograph, and once it
is typed into a generator nothing downstream can check it: `validate`,
`interfere`, `check_fit`, `check_motion` and `check_mesh` all pass a bracket
whose pocket is 2 mm too shallow for the motor it was drawn for. This is the
mate `references/parameters.md` warns about with the nominal removed from the
repository altogether.

So do not type it. Fetch the component's STEP and derive the cavity from it.

```bash
STEP_PARTS_SKILL_ROOT="$(workshop skills path)/step-parts"
python "$STEP_PARTS_SKILL_ROOT/scripts/download_step_part.py" --id sg90_micro_servo \
    --download --out-dir <project-dir>/ref
```

```python
import cadmount

servo   = cadmount.load("ref/sg90_micro_servo.step")
bracket -= cadmount.seat_for(servo, "slip", mouth=3)
bracket -= cadmount.bolt_cutter(servo, "free", depth=BRACKET_T + 2)
```

**Keep the STEP inside `<project-dir>/ref/`**, for the reason the reference
images live there: a seat derived from a file in a temp directory cannot be
re-verified once that directory is cleaned out.

## Never offset the imported solid

`offset(component, +clearance)` is the obvious way to grow a part into its
clearance envelope, and on a real catalog STEP it is a trap. Measured on
step.parts `sg90_micro_servo`:

| | bbox Z |
|---|---|
| the servo as imported | 0.00 .. **29.90** |
| `offset(servo, +0.3)` | -0.30 .. **27.00** |

OCC grew it in X and Y, dropped the output hub and all 24 spline teeth, and
returned a solid 2.9 mm *shorter* than its input with no error. A pocket cut
from that envelope is a pocket the servo's spline crashes into — and it
validates, because the bracket is a perfectly sound solid.

`cadmount` therefore never offsets the component. It sections the raw solid
along the insertion axis, unions the sections, applies clearance as a **2D**
offset of that outline where OCC is reliable, and extrudes. Then it verifies
that the seat contains the component it came from, doubles the section count
until it does, and raises rather than returning a cavity that misses material.

## `seat_for` is a prism, and that is the point

`seat_for` returns the component's silhouette along `insert`, swept straight
through. An exact offset would hug the part more closely and could not be
assembled at all: any component wider somewhere than it is at its mouth has an
undercut, and rigid parts do not bend into one.

- `insert` — the direction the component travels in. The seat is prismatic
  along it.
- `mouth` — how far to extend the cavity back past the component, to break
  through the bracket's surface. **The default of 0 is a blind pocket**, which
  is correct geometry and frequently leaves a skin the slicer prints and the
  component cannot pass.
- `fit` — a `cadfits` class. `slip` (0.20/side) is the default. An interference
  class is refused: a bought part does not compress.

`envelope_for` is the bounding box instead. It is looser and cannot miss a
feature, so it is the answer when a seat will not converge, or when a
rectangular pocket is what the bracket wanted anyway.

## Holes: read them, then pick

`bolt_holes` returns every fastener-sized bore whose axis lies along a given
direction. It is deliberately honest rather than clever — on the SG90 it
returns three, because the horn screw is a bore like any other and nothing in
the geometry says which is for mounting. `bolt_pattern` picks the largest group
of one diameter, which is the flange pattern on every servo and gearmotor in
the catalog:

    bolt_holes(servo)    -> [1.7, 2.0, 2.0]
    bolt_pattern(servo)  -> two Ø2.000 holes, 27.20 mm apart   (datasheet: 27.2)

Two things about imported bores that a naive reader gets wrong, both learned
from that file:

- **A bore is often not a full cylindrical face.** The SG90's flange holes are
  single faces sweeping 77.5 % of a turn; other importers split a bore at its
  seam into halves. `cadmount` groups faces by axis line and radius and sums
  their sweeps, requiring 60 % of a turn between them — enough to keep a
  trimmed bore and to reject a slot end, which is exactly half.
- **The centroid of a trimmed cylindrical face is not on its axis.** On those
  flange holes it sits 1.00 mm off. Reading a hole position from
  `face.center()` drills the screw hole a millimetre from where the screw is.
  Every position `cadmount` reports is derived from the axis.

`bolt_cutter` sizes the clearance holes through `cadfits.slot_for`, so a screw
clearance obeys the same table as every other mate in the project.

## The gate: `check_mount`

Deriving the seat is not proof the model has one. The generator may never have
subtracted it, may have subtracted it in the wrong place, or may have added a
feature three lines later that ate half of it — and `validate`, `interfere`,
`check_fit`, `check_motion` and `check_mesh` all pass every one of those.

```bash
python "$CAD_SKILL_ROOT/scripts/check_mount" <project-dir>                  # measure/mounts.json
python "$CAD_SKILL_ROOT/scripts/check_mount" <project-dir> --manifest <f> --json
```

It builds the **combined** entry, so parts come out in assembly pose, places
each declared component's own STEP into it, and measures what the built solids
leave each other. It recomputes none of `cadmount`: a seat typed by hand is
checked exactly as closely as a derived one.

```json
{
  "mounts": [
    {
      "id": "left-drive-servo",
      "component": "ref/sg90_micro_servo.step",
      "sha256": "7e9aeb4eebf5565e8dd049bb2697a001f2bbaf6de86ca118cef7e66e6268c19c",
      "at": {"position": [12, 0, 5], "rotation": [0, 0, 90]},
      "parts": ["chassis"],
      "min_clearance": 0.10,
      "bolt_axis": [0, 0, 1],
      "bolts": true
    }
  ]
}
```

| field | meaning |
|---|---|
| `id` | unique stable mount id used by powered-component and handoff manifests. |
| `component` | STEP path, **relative to the project**. Outside it is a failure. |
| `at` | pose in assembly coordinates: `[x,y,z]`, or `{position, rotation}` in degrees. Omitted means the origin. |
| `sha256` | the file the seat was derived from. Absent is a note; wrong is a note that names both digests. |
| `parts` | labelled parts to measure against. Omitted means the whole assembly. |
| `min_clearance` | mm, default `snug` (0.10). Below it fails: a bought part does not compress. |
| `bolt_axis` | constrain hole detection to one axis. Omitted searches any. |
| `bolts` | `false` for a strapped, glued or captive-screwed component. |
| `assembly` | top-level: name the entry when a project has several. |

Failures are `component-source`, `seat-clash`, `seat-clearance` and
`bolt-access`. Notes, which `--strict` promotes, are `component-checksum`,
`no-bolt-pattern` and `seat-clearance-loose` — a component with 3 mm of gap all
round is not located by its seat, which is a design in a foam cradle and a
defect everywhere else, and only a human reading the README can tell.

The integrated final runner is stricter about provenance than standalone
`check_mount`: every bought/foreign STEP must live under `ref/`, must be named
by at least one mount row, and every such row must carry the file's current
`sha256`. Generated STEP artifacts are distinguished by their sibling
`.step.py` entries. Putting a supplier STEP under `catalog/` and mounting a
derived or authored envelope under `ref/` is a failure, not an alternate
layout: it hides the source file from the preflight and lets a reduced envelope
stand in for the very geometry the seat is meant to prove. This keeps the
standalone gate useful while authoring a mount, but prevents a final PASS when
a catalog file changed beneath an already-derived seat.

`bolt-access` tries each hole **both ways** along its axis and passes if either
is clear, because a screw only ever needs one open side. A bracket with a back
wall would fail a stricter test for no reason.

Measured on the three fixtures this gate was built against — a bracket whose
seat and screw holes are both derived, one with the seat but no holes drilled,
and one whose pocket was typed from the datasheet's body size with the mounting
ears forgotten:

    derived        clash 0.000 mm3, clearance 0.200 mm, 2 mount holes   exit 0
    holes missing  both Ø2.00 holes walled in from both sides           exit 1
    typed by hand  clash 232.474 mm3 -- the ears                        exit 1

The last two are the ones every other gate in the toolchain passes.

## What it cannot answer

- **That the component can reach its seat.** `check_mount` measures the assembled pose only. A prismatic pocket is insertable
  in isolation; whether it is reachable through the rest of the model is
  `scripts/check_motion` with a manifest, and the seat is exactly the kind of
  joint that wants `"expect": "clear"` for the insertion and `"blocked"` for the
  direction it must not back out of.
- **That the bracket around the seat can be printed.** A seat cut close to an
  outer surface leaves a wall no gate here measures — `check_thickness`.
- **That the catalog model matches the part in your hand.** Hobby servos vary
  between vendors under one name. The STEP is a claim with a checksum, not a
  measurement.

`seat_report(bracket, component)` measures what the built solids actually
leave each other — clash volume and minimum clearance — and reads them as they
are rather than recomputing the recipe, which would reduce to `True`.

Self-check:

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/cadmount.py"
