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

`offset(component, +clearance)` on a real catalog STEP silently drops features
and can return a *shorter* solid (the step.parts SG90 loses its hub and spline
and 2.9 mm of height, with no error), and the pocket cut from it validates.
`cadmount` therefore never offsets the component: it sections the raw solid
along the insertion axis, unions the sections, applies clearance as a **2D**
offset of that outline, and extrudes. Then it verifies that the seat contains
the component it came from, doubles the section count until it does, and raises
rather than returning a cavity that misses material. The measurement and the
design reasoning behind seats: `skills/wiki/pages/printing/seating-bought-parts.md`
(`wiki show seating-bought-parts`).

## `seat_for` is a prism, and that is the point

`seat_for` returns the component's silhouette along `insert`, swept straight
through, because an exact offset would leave an undercut the rigid part cannot
pass (`wiki show seating-bought-parts#a-seat-is-a-prism-along-the-insertion-direction`).

- `insert` — the axis the component travels along. The seat is prismatic
  along it, and the sign matters only for the mouth: **the mouth is on the
  +insert side**, so point `insert` out of the opening, toward where the part
  comes from — (0, 0, 1) for a part dropped in from above. Pointed the way the
  part travels, the mouth lands on the floor, the opening keeps a skin as thin
  as the clearance, and only `check_motion` sees the part cannot go in.
- `mouth` — how far to extend the cavity past the component on that side, to
  break through the bracket's surface. **The default of 0 is a blind pocket**,
  which is correct geometry and frequently leaves a skin the slicer prints and
  the component cannot pass.
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

`cadmount` groups bore faces by axis line and radius and sums their sweeps
(requiring 60 % of a turn), and derives every position from the axis, never
from `face.center()` — imported bores are often trimmed or split faces whose
centroid sits off the axis
(`wiki show seating-bought-parts#reading-holes-off-an-imported-step`).

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
| `solid` | which solid of a multi-solid STEP is the part: `"largest"`, `"all"`, or an index. Omitted refuses a multi-solid file. |
| `assembly` | top-level: name the entry when a project has several. |

A catalog STEP that imports as several solids is refused by default, because a
seat derived from all of them at once is a seat for a **pose** rather than for a
part: the servo's horn and the motor's output shaft turn, and a socket cut
around them where they happen to sit fits nothing after the first revolution.
`solid` is how the manifest overrides that, and each value is a different claim
the gate then records:

- `"largest"` — the rest of the solids are the parts that move. A DC gearmotor
  whose file carries body, hub and lead stub seats on its body.
- an integer — that index of `solids()`. Read the index from the file in the
  same session; import order is not a contract, so a number carried over from
  another machine or another vendor revision is a guess.
- `"all"` — nothing in this component moves relative to anything else in it at
  the pose being checked. True of a cell holder's shell and contacts, false of
  anything with an output shaft.

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

One STEP under `ref/` is not a component: the one an entry declares it
`CARRIES = "ref/<name>.step"`. That is the mesh route's carrier entry, whose
body *is* the converted file it imports and returns, so a mount row would have
to say where the part sits inside itself, and every geometry gate already
measures it through the entry. The declaration is literal and read statically,
like `PRINTABLE`; it must name a file that exists and is under `ref/`, and it
exempts nothing else. Seating a purchased part stays exactly as strict.

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

## One row per state the part is checked in

A row measures its component against its own `parts`, so a component that meets
different neighbours at different assembly steps, or rests on one by design,
gets a row for each state rather than one row that is wrong for all of them:

- **Screwed on the bench, then installed.** A gearmotor bolted to its bracket
  before the bracket goes into the body is checked for `bolt-access` against
  the bracket alone; in the finished assembly the screw line runs into the
  worm, the walls and the lid on both sides, and the gate reads the bench
  screws as walled in. A second row with `"bolts": false` measures the
  installed clearance.
- **A pressed fit on a bought shaft.** A printed hub pressed onto the motor's
  shaft at the `snug` fit reads back exactly the floor. Give it its own row
  with half the pressed clearance as the floor: zero is still a clash.
- **Resting on a face by design.** A cell holder that stands on its door has
  zero clearance to the door, and that contact is the seat. One row with
  `"min_clearance": 0.0` against the door alone proves the door does not
  intrude; the holder's walls keep their clearance in another row.

Every row names the same `component` and checksum; a power manifest's
`mount_id` points at the row for the installed state.

A swept clearance envelope (a wire loom) that the model is cut from needs the
cutter grown at the envelope's ends as well as its radius: a leg that stops at
a wall otherwise meets it flush, and reads zero clearance.

## What it cannot answer

- **That the component can reach its seat.** `check_mount` measures the assembled pose only. A prismatic pocket is insertable
  in isolation; whether it is reachable through the rest of the model is
  `scripts/check_motion` with a manifest, and the seat is exactly the kind of
  joint that wants `"expect": "clear"` for the insertion and `"blocked"` for the
  direction it must not back out of.
- **That the bracket around the seat can be printed.** A seat cut close to an
  outer surface leaves a wall only one gate here measures — `check_thickness`,
  and only when `--print-gates` is on. Keep the wall in the parameter block with
  its own provenance comment either way.
- **That the catalog model matches the part in your hand.** Hobby servos vary
  between vendors under one name. The STEP is a claim with a checksum, not a
  measurement.

`seat_report(bracket, component)` measures what the built solids actually
leave each other — clash volume and minimum clearance — and reads them as they
are rather than recomputing the recipe, which would reduce to `True`.

Self-check:

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/cadmount.py"
