# build123d-operations

Picking the operation, the plane, and the order — for every feature.

**Trigger:** Writing Step 6 of the spec. Load before filling the feature table.

The builder this maps onto is the `cad` skill (build123d 0.11 / cadgen 0.4.19).
Every snippet below was executed against that version before being written down.

## Why this exists

The construction family is chosen once and inherited by every later edit. A form
authored in the wrong family **cannot be rescued by parameter edits** — only by
re-authoring, which costs the user the whole follow-up conversation. This
document exists so that choice is made from the image's evidence rather than
from habit.

The second failure it prevents is subtler: a correct operation run on the wrong
plane or selector. That produces code that compiles, yields a valid solid, and
puts the hole in the wrong face. Every row of the feature table therefore names
**both** the call and the frame it runs in.

## The feature table row

```
feature | geometry + numbers | build123d call | plane / selector | order | risk
```

- **feature** — the name the generator will use for the step or helper.
- **geometry + numbers** — dimensions with confidence tags.
- **build123d call** — the actual API, with arguments.
- **plane / selector** — the frame it runs in. Never leave this blank.
- **order** — its integer position in `gen_step()`.
- **risk** — the specific way this feature is likely to fail, or `—`.

## Base solid: form class → operation family

Diagnose from the image and from `measure_image.py`'s `row_shape`/`col_shape`.

### Prismatic — constant cross-section

The section does not change along the length. Boxes, trays, brackets, plates,
extruded profiles.

```python
body = Box(p.width, p.depth, p.height)          # algebra mode, centred

with BuildPart() as bp:                          # builder mode, non-trivial outline
    with BuildSketch():
        Polygon((0, 0), (p.width, 0), (p.width, p.height), (0, p.height * 0.6))
    extrude(amount=p.depth)
body = bp.part
```

**Signal:** `row_shape: flat` and `col_shape: flat`, `fill_ratio` near 1.0.
**Risk:** none — this is the cheapest family. The risk is choosing it when the
form is *not* prismatic.

### Tapered extrude — constant section, uniform draft

One angle, section shape unchanged. Stacking bins, nesting cups, moulded housings.

```python
with BuildPart() as bp:
    with BuildSketch():
        Rectangle(p.base_w, p.base_d)
    extrude(amount=p.height, taper=p.draft_deg)
```

**Signal:** `row_shape: wide_start` or `wide_end`, straight silhouette edges.
**Risk:** `taper` applies the same angle to every side. If the image shows one
face vertical and the opposite face leaning, this is a **loft**, not a taper.

### Revolve — rotationally symmetric

Vases, knobs, bottles, domes, pulleys, anything turned on a lathe.

```python
with BuildPart() as bp:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Polyline((0, 0), (p.base_r, 0), (p.max_r, p.waist_z),
                     (p.neck_r, p.height), (0, p.height), close=True)
        make_face()
    revolve(axis=Axis.Z)
```

**Signal:** front and side silhouettes match; `symmetry.left_right` > 0.95; any
horizontal feature reads as an ellipse; `row_shape` is `waisted` or `bulged`.
**Risk:** the profile must **touch the axis** and be closed, or the revolve
produces a ring instead of a solid. A 360° revolve also leaves a **seam edge at
+X**; on a large smooth camera-facing surface that renders as a panel line, so
rotate the finished body about Z to move the seam away from the viewpoint.

### Loft — the section changes along the length

Fuselages, hulls, swooshes, sculpted grips, handles, tapering bodies whose
section shape (not just size) evolves. **This is the family most often skipped
and most often needed.**

```python
def section_at(t: float, p) -> list[tuple[float, float]]:
    """One station, sampled on fixed rails. Same point count at every t."""
    ...

wires = [
    Wire([Edge.make_spline(
        [Vector(p.length * t, y, z) for (y, z) in section_at(t, p)],
        periodic=True)])
    for t in stations
]
body = Solid.make_loft(wires, True)      # True == ruled; see the warning below
```

Two API facts that cost a build each if you get them wrong:

- **`loft()` takes Faces/Sketches; `Solid.make_loft()` takes Wires.** Passing
  wires to `loft()` fails with `More than one wire is required`, which names the
  wrong problem.
- **A smooth (`ruled=False`) loft can overshoot catastrophically.** Through
  control curves that collapse quickly at the ends — a nose or a tail — the C2
  interpolation measured **z = 314 mm on an 80 mm-tall body**, with
  `is_valid == True` and no warning. Only a render finds it. Use `ruled=True`
  with stations dense enough (~2 mm pitch) that the faceting is invisible; the
  bounding box then matches the control curves exactly.

**Signal:** `row_shape: irregular`, or `row_bands` showing three or more distinct
bands, or a visibly double-curved surface.
**Rules that keep it buildable:**
- **One `section_at(t)` helper**, parameter-driven. Never hand-place N unrelated
  wires — that is how the next edit turn becomes impossible.
- **A loft matches its sections BY INDEX.** Sampling each station at fractions of
  *that station's own* width puts a feature at a different index at every
  station, and the surface twists to reconcile them. The result is valid,
  watertight, symmetric, and looks like crumpled foil. Sample on **rails**: fix
  how many points each feature band gets, so index *i* means the same feature
  everywhere.
- **Interpolate control curves with a monotone cubic (PCHIP)**, never a
  smoothstep — smoothstep has zero derivative at both ends of every interval, so
  it is flat at each control point and steep between them, and the loft creases
  at every knot.
- **Stations at curvature events** when they are sparse: nose, widest point,
  waist, tail. `row_bands` boundaries are your station list.

**Risk:** twisted loft from index-mismatched sections; overshoot from a smooth
loft; a loft that fails to close if the first or last station is degenerate. If
a station must be a point, use a very small finite section instead.

### Sweep — constant-ish section along a curved path

Tubes, rails, straps, handles that follow a curve, cable guards, pipe runs.

```python
with BuildPart() as bp:
    with BuildLine():
        Spline((0, 0, 0), (p.mid_x, 0, p.mid_z), (p.end_x, 0, p.end_z))
    with BuildSketch(Plane.YZ):
        Circle(p.tube_r)
    sweep(is_frenet=True)
```

**Signal:** a recognisable constant profile visibly following a curve.
**Risk:** without `is_frenet=True` the section can rotate unpredictably along the
path. A path whose radius is tighter than the section is wide will
self-intersect and fail. For a **planar arch** — a roll hoop, a handle, a bail —
a band between two concentric ellipses extruded along the third axis is far more
robust than a sweep, and lands its feet exactly where you put them.

### Sketch-driven — any outline you would draw with a pencil

Reach for `BuildSketch` whenever the 2D outline is non-trivial: rounded slots,
mixed arcs and lines, outlines with internal cut-outs, profiles that need 2D
fillets before extrusion.

```python
with BuildPart() as bp:
    with BuildSketch() as sk:
        Rectangle(p.width, p.height)
        fillet(sk.vertices(), p.corner_r)      # corners FIRST
        Circle(p.hole_r, mode=Mode.SUBTRACT)   # then the hole
    extrude(amount=p.thickness)
```

**The order is the opposite of the 3D rule.** In 3D you fillet last; in a sketch
you fillet **before** the boolean. Reversed, `fillet(sk.vertices(), r)` walks
into the subtracted circle's seam vertex and raises `Vertex must connect exactly
two edges` — verified on build123d 0.11. When the corner radius is uniform,
`RectangleRounded(w, h, r)` skips the problem entirely.

**Why it matters:** a 2D fillet on the sketch always succeeds where an
equivalent 3D fillet on the extruded solid may fail. When a corner radius is
part of the *profile*, put it in the sketch — this is the escape hatch when
`fillet()` on a solid raises an OCCT error.

### Blended organic mass

Loft stack plus generous blends. Expect to spend the modelling effort in the
station function, not in fillets. Do **not** reach for a 3D fillet or chamfer on
a tangent chain or a multi-arc outline: depending only on exact dimensions it
fails silently, churns for minutes, or takes the whole process down with a
SIGSEGV. Bake the bevel into the lofted section instead.

## Additive features

| Feature in the image | Call | Frame | Risk |
|---|---|---|---|
| Boss / standoff / post | `with Locations(pts): Cylinder(r, h)` | inside floor | Must **overlap** the floor, not touch it — a tangent boss reads as a disconnected body |
| Rib / gusset | `extrude(profile, amount=t)` then `+` | plane of the rib | Root it into **both** faces it stiffens |
| Flange / foot | `extrude(Rectangle(w, d), amount=t)` | base face | — |
| Handle following a curve | `sweep(is_frenet=True)` | own path plane | Both ends must intersect the body |
| Repeated bosses | `with GridLocations(dx, dy, nx, ny): ...` | the face they sit on | One row in the table, not four |
| Repeated around an axis | `with PolarLocations(r, n): ...` | the face | Rotate the prototype, not the ring |
| Painted stripe / inlay / lens | `(inflated_body - raw_body) & tool` | — | See below |

**Conformal surface decoration.** A stripe, a badge, or a lens that follows a
sculpted skin is a *skin patch*, not a prism. Build the base form twice from the
same helper — once at nominal, once inflated by the relief height — subtract to
get a shell, then intersect that shell with a simple tool box or sphere. Do
**not** `offset()` a spline-bounded solid; the kernel returns Null for some
inward deltas. Two measured details: compute the shell **once** and intersect it
with each tool (the alternative, `(inflated & tool) - raw` per tool, was 2.2×
slower on a 200-face body), and centre a lens tool **on** the surface — anchor
it by solving the section for the surface point rather than placing it by eye,
because a tool that misses the skin intersects to `None` and the failure
surfaces far downstream as `NoneType has no attribute label`.

## Subtractive features

| Feature in the image | Call | Frame | Risk |
|---|---|---|---|
| Through hole | `Hole(radius)` | the face it enters | `Hole` goes through all — use `CounterBoreHole`/`depth=` for blind |
| Counterbored screw hole | `CounterBoreHole(r, cb_r, cb_depth)` | the face the head sits in | — |
| Countersunk hole | `CounterSinkHole(r, csk_r)` | same | — |
| Hollow interior | `offset(body, -p.wall, openings=body.faces().sort_by(Axis.Z)[-1])` | the face(s) removed | Shell **before** adding interior bosses, or it hollows them too |
| Recess / cavity with draft | `body -= loft([rim, mid, floor])` | wires on offset planes | Tool must break the rim plane by ≥1 mm |
| Wheel arch / side scallop | `body -= Cylinder(...) & half_space` | — | A full-width cylinder **severs** the body into pieces; clip the tool to the outboard side |
| Slot | `SlotOverall(w, h)` in a sketch, then cut | its own plane | — |
| Engraved text / logo | `Text(s, size)` in a sketch, `extrude(amount=-depth)` | the face | Below ~1.5 mm wide it will not print — deepen or drop |
| Decorative groove (ex-parting-line) | a revolved or extruded cutter | — | 0.4–0.8 mm deep is enough to read |

**Batch the tools.** `body - [a, b, c, ...]` in one list operation, never
`body - a - b - c`, which re-runs the whole intersection network per step and
decays O(n²). Keep the tools in a batch mutually disjoint; tools that overlap
deep below the surface are pathological, and a single multi-tool cut whose tools
cross each other can return knife-edge slivers and detached plugs.

## Finishing

```python
body = fillet(body.edges().filter_by(Axis.Z), p.corner_r)       # vertical edges
body = chamfer(body.faces().sort_by(Axis.Z)[0].edges(), 0.6)    # bed-contact edge
```

- **Fillets last**, after every boolean.
- A **unified corner radius** on the vertical edges is what makes a printed part
  read as designed rather than as a CAD default. State one radius in the spec
  and apply it everywhere eligible.
- Always chamfer the bed-contact edge (~0.6 mm) — it lifts off cleaner and hides
  elephant's foot. This is an engineering default; never ask about it.
- If `fillet()` fails on a solid, move the radius into the sketch profile as a
  2D fillet, or into the lofted section. Do **not** silently reduce a radius the
  user specified — a retry ladder converts a hard failure into an invisible
  cosmetic regression.

### Crescents, lunes, and any two-circle profile

`Circle(R) - Pos(d, 0) * Circle(r)` is the whole construction, and the trap is
in where `r` and `d` come from. **Do not read them off the pixels.** The cut
circle's edge is an *inferred* boundary — in a render it is a lit inner arc, not
a silhouette, and a few pixels of error in a radius you cannot see directly
propagates into the tip positions, which is the one thing the eye checks.

Measure the two things the image shows you honestly instead, then solve:

- **ψ** — the half-angle from the crescent's centre to its two tips. Read the
  tip coordinates; they are corner features and localise to a pixel.
- **t** — the rim thickness at its widest, opposite the gap. A clean
  edge-to-edge span.

Then, with the outer radius `R` also `[observed]`:

```
r = R + d - t                       # thickness definition
cos ψ = (R² + d² - r²) / (2 R d)    # circle-intersection condition
```

Two equations, two unknowns — substitute and solve the linear result for `d`.

Worked, from a crescent moon on a 1024 px render: R 25.56, tips subtending
88.8°, rim 9.05 mm thick → d 5.47, r 21.98. Reading `r` and `d` straight off the
pixels instead gave r 26.62, d 10.11, which **pinched the crescent to two thirds
of its width** and failed a ±10 % proportion-ledger assertion at −33.5 %. The
shape still looked like a crescent from every angle; only the ledger caught it.

The same substitution applies to any lune, C-clip, split ring, or hook profile
built from two circles: solve from the features you can localise, never from the
radius you cannot.

## Selector cookbook

The selector is where image-derived specs most often fail to build. build123d
selects with `ShapeList` methods, not with CadQuery's string mini-language.

| Selector | Selects | Use for |
|---|---|---|
| `.faces().sort_by(Axis.Z)[-1]` | Topmost face | Working on the top |
| `.faces().sort_by(Axis.Z)[0]` | Bottom face | Feet, base features |
| `.faces().group_by(Axis.Z)[-2]` | Second band from the top | The **inside floor** of a shelled box |
| `.faces().sort_by(Axis.X)[-1]` | Outermost face on an axis | Side-wall features |
| `.faces().filter_by(Plane.XY)` | All horizontal planar faces | Excluding curved faces from a fillet |
| `.edges().filter_by(Axis.Z)` | All edges parallel to Z | The corner-radius set |
| `.edges().group_by(Axis.Z)[-1]` | Highest edge band | Top rim only |
| `.faces().filter_by(GeomType.PLANE)` | Planar faces only | Keeping a fillet off a lofted skin |
| `Plane.XY.offset(h)` | A plane at a height | A feature with no face to land on |
| `Plane(origin=..., x_dir=..., z_dir=...)` | An explicit frame | Angled features, leaning faces |

Three rules from experience:

1. **Build angled frames from explicit direction vectors.** `Plane.rotated()`
   composes in **world axes, not the plane's own**. On a plane whose axes are not
   the global ones, what reads as a pitch is actually a yaw, and the result is a
   valid solid of the wrong shape that passes every deterministic check.
2. **Prefer position/axis selection to list indexes** that depend on
   construction order. Any boolean invalidates the ordering.
3. **Re-select after every boolean.** A face list captured before a cut refers to
   faces that no longer exist.

## Boolean order

```
base solid → additive (union) → shell → interior additive → subtractive (cut) → fillet
```

- **Union before cut**, unless the cut is what makes the shape possible. A hole
  cut before a union is silently refilled — no error, wrong part.
- **Shell before interior bosses**, or the shell hollows them.
- **Cut through-features after all unions**, then re-verify with
  `scripts/inspect refs --facts`: a later boolean can refill, shift, or enlarge
  an opening silently.
- **Fillet last.**
- **Gate the result, do not trust it.** `is_valid` returns True for a shell with
  a large *negative* volume — an inverted solid that exports and renders as a
  hole in the world. Check validity **and** `volume > 0`, and run
  `scripts/inspect validate`, which measures volume per solid so an inverted
  member cannot cancel against a sound one.

State the order as integers in the table. That ordering **is** the body of
`gen_step()`.

## Multi-part assemblies

When Step 5a produced more than one printed part, say explicitly that they are
labelled assembly children, not a fused solid:

```python
from cadgen.assembly import AssemblyHelper
from cadgen.color import srgb

asm = AssemblyHelper("enclosure")
asm.add(base, "base", color=srgb("#2E3742"))
asm.add(lid, "lid", color=srgb("#D9D9D6"))
return asm.compound()
```

Fusing separately printed parts loses clearances, fits, and per-part mesh export.
Name the parts in the spec in the order they should be added.

Colour is worth one line in the spec per part, because two rules about it fail
silently — raw `Color()` channels are linear RGB and come out washed out, and
colour set on a group compound never reaches the render even though it does
reach the STEP's XCAF label. So name each part's colour as a **hex** the
implementer passes to `srgb()`, and name it for every leaf, never for a group.

`cad` owns the full write-up, with the worked example and the alpha form:
**Colour** in `cad/references/build123d-modeling.md`. That skill is the one
that authors the geometry, so the rules live where they are applied.

## Assign a risk to every row

The risk column is what makes the spec worth reading twice. The common ones:

- *fillet may fail at this radius* → fall back to a 2D sketch or section fillet;
- *boss tangent to the wall* → root it in by ≥ 1 mm;
- *cut may be refilled by the later union* → move after, then verify;
- *loft sections index-mismatched* → sample on rails, same point count;
- *smooth loft may overshoot* → `ruled=True` with dense stations;
- *cutter severs the body* → clip the tool to one side;
- *decoration tool misses the skin* → anchor it on a solved surface point;
- *feature below the FDM minimum* → deepen, thicken, or drop and say so;
- *overhang > 45°* → name the print orientation or add a chamfer.

A row with a real risk named is a row the implementation will get right.
