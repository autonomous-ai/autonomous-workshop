# Literal geometry proofs

Load this reference when the prompt gives an exact overall size, world-space
extent, straight cylindrical hole pattern, sharp rectangular through-cut, or
axis-aligned clearance/cavity. Parameter checks are not enough: a later union,
cut, fillet, offset, or placement can change the final B-rep.

## Exact final part envelope

Call `verify_bbox` after the part's last boolean operation. Use `None` for an
axis the user did not constrain.

```python
from cadlib.validation import verify_bbox

body = build_body(p)
body = add_every_feature(body, p)
body_extent_proof = verify_bbox(
    shape=body,
    expected_size=(p.length, p.width, p.height),
    expected_min=(-p.length / 2, -p.width / 2, 0),
    expected_max=(p.length / 2, p.width / 2, p.height),
    label="body",
)
```

The helper measures every solid in a `cq.Workplane`, rather than only `.val()`,
and raises immediately when a protruding feature changes the requested extent.
Its return value is a JSON-safe measurement receipt. A 0.01 mm default
tolerance covers OCCT noise without hiding a print-significant mismatch.

For a partial constraint, leave the other axes unspecified:

```python
height_proof = verify_bbox(
    shape=stand,
    expected_size=(None, None, p.exact_height),
    expected_min=(None, None, 0),
    label="stand",
)
```

## Exact cylindrical through-hole pattern

Use `verify_through_hole_pattern` after the final boolean when the request owns
the hole diameter, centers, count, and through-span:

```python
from cadlib.validation import verify_through_hole_pattern

mounting_proof = verify_through_hole_pattern(
    part=plate,
    axis="z",
    centers=p.mounting_centers,  # z axis -> (x, y) pairs
    diameter=p.mounting_hole_diameter,
    span=(0, p.thickness),
    label="mounting holes",
)
```

Coordinate pairs are in the plane normal to the hole axis: `x -> (y, z)`,
`y -> (x, z)`, `z -> (x, y)`. The helper combines exact cylindrical B-rep
faces with air/material probes. It rejects a moved, resized, blocked, blind,
open-sided, missing, or extra same-diameter through-hole.

By default, the expected centers are the complete same-axis/same-diameter
pattern on the part. If a different legitimate group uses that same diameter,
pass a world-space transverse `scope=(u_min, v_min, u_max, v_max)` around the
owned pattern. Never use scope merely to hide a stale hole that should have
been removed.

## Sharp rectangular through-cut

Use `verify_rectangular_through_cut` when the final requirement is a straight,
sharp-cornered rectangular port or slot through the complete X, Y, or Z span:

```python
from cadlib.validation import verify_rectangular_through_cut

port_proof = verify_rectangular_through_cut(
    part=panel,
    axis="x",                 # center/size are (y, z)
    center=(p.port_y, p.port_z),
    size=(p.port_width, p.port_height),
    span=(-p.panel_thickness / 2, p.panel_thickness / 2),
    label="rectangular connector port",
)
```

The complete expected prism must be air, both axial ends must meet the final
bbox, and four thin surrounding slabs must remain material. This rejects a
moved, undersized, oversized, blind, skinned-over, or refilled port. Do not use
it for rounded, tapered, keyhole, or freeform profiles.

## Empty rectangular cavity or clearance

Use `verify_clearance_box` when the request owns an axis-aligned region that
must contain no material—for example, “completely hollow, open at the top, no
posts or dividers”:

```python
from cadlib.validation import verify_clearance_box

cavity_proof = verify_clearance_box(
    part=body,
    expected_min=(p.inner_xmin, p.inner_ymin, p.floor),
    expected_max=(p.inner_xmax, p.inner_ymax, p.height),
    open_faces=("+Z",),
    label="empty main cavity",
)
```

The helper intersects the full expected volume with the final B-rep, so a
thin roof skin or divider between sparse sample points still fails. By default,
every non-open face also requires a continuous material slab. Pass an explicit
`wall_faces` subset only when a requested port intentionally interrupts one of
those walls. Use this helper only for a sharp axis-aligned box; model and prove
rounded or tapered cavities with a profile-specific contract.

## Ownership rules

- Prove each owned, separately printable part on its final post-boolean shape.
- Do **not** measure the aggregate `cq.Assembly` unless the request explicitly
  gives an overall assembled envelope. Assembly pose, lid seating, or an
  exploded preview can legitimately change the aggregate bbox.
- A requested protrusion belongs to the final envelope. Do not measure a base
  before adding it or silently reinterpret “overall” as “body without feature.”
- `verify_bbox` proves only axis-aligned size/min/max;
  `verify_through_hole_pattern` proves only straight Cartesian cylindrical
  through-holes; the rectangular helpers prove only their explicit sharp box
  volumes. Rounded/keyhole profiles, blind/counterbored/threaded holes, and
  angled dimensions still need their own final-geometry checks.
- Keep the proof in source so later EDIT/REMIX turns rerun the same contract.
  If an edit unintentionally breaks an unchanged literal dimension, the build
  fails before artifact promotion and the last green artifact remains live.
