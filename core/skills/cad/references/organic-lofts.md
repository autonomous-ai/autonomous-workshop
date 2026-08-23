# Organic bodies: lofts, junctions, and the checks that catch what renders hide

Read this before modelling any animal, figure, vehicle body, hull, or other
freeform mass — anything whose cross-section changes continuously along a
curved spine. Extrudes, revolves and sketches are covered in
`build123d-modeling.md`; this file is only about the loft family and the
failures specific to it.

## The station table is the model

A freeform body is a table before it is code. One row per station along the
spine:

    (x, z, half-height, half-width)      body, spine in the XZ plane
    (x, z, y, radius)                    tail/limb, spine leaving that plane

Read the rows off the reference views — `$image-to-cad`'s `grid_overlay.py`
puts labelled pixel coordinates on the photograph so a curve can be read as
numbers rather than adjectives. Put the table in the spec **and** in the
library as a named constant. Two things follow from that and both matter:
the shape becomes reviewable without running anything, and a likeness failure
localised to one height band by `check_likeness.py` points at specific rows.

Twelve to sixteen stations carry a body. A tight spiral needs a station every
~25° of turn or it reads as a polygon.

## Build the station frame from a lateral reference, never from Z

```python
def _station_wire(centre, tangent, half_h, half_w):
    t = Vector(*tangent).normalized()
    x = Vector(0, 1, 0).cross(t)          # lateral reference
    if x.length < 1e-6:                   # only if the spine runs along Y
        x = Vector(0, 0, 1).cross(t)
    plane = Plane(origin=Vector(*centre), x_dir=x.normalized(), z_dir=t)
    return (plane * Ellipse(half_h, half_w)).wire()
```

The obvious frame — `x_dir = Z × tangent` — degenerates the moment the spine
turns vertical, and a curled tail, a hook, a handle or an S-bend all do that.
`Z × t` goes to zero there and the loft fails or twists. A lateral reference
(`Y × t`) stays well conditioned for any spine that stays roughly in the XZ
plane, which is what a side-view-driven station table always produces.

Note what the frame does to the ellipse's arguments: with `x_dir` in the XZ
plane, `Ellipse(a, b)` takes **a = half-height, b = half-width**. Getting this
backwards produces a body that is correct in silhouette from the side and
wrong from the front, which one view will not show you.

## Consecutive lofted segments must OVERLAP, not meet

This is the expensive one.

A loft's end cap is a plane **normal to the spine tangent at the last
station** — not a vertical wall, and not where you think it is. Its extent is
the last station's ellipse, tilted. So a segment whose last station sits at
`(x=-62, z=103)` with a half-height of 19 does not end at x = -62: its cap
sweeps from `(-77.6, 113.9)` to `(-46.4, 92.1)`, and every point beyond that
plane is outside the solid.

Start the next segment's first station **inside** the previous segment — a
station or two back along the spine, sized to fit within that section — not at
the seam. Overlapping costs nothing; a boolean union of overlapping solids is
one solid, and of touching solids is often two.

```python
BODY_STATIONS = [ ..., (-55, 113, 28, 16), (-62, 103, 19, 13) ]
TAIL_STATIONS = [ (-52, 116, 0.0, 13.0),      # INSIDE the haunch, not at the tip
                  (-59, 106, -0.5, 12.0), ... ]
```

## Assert the body count in the source

Nothing else catches this. A tail resting against a body and a tail attached to
one are the same picture:

- `inspect validate` returns `ok` — both solids are closed and positive.
- `inspect interfere` returns `ok` — it compares *parts*, not the bodies inside
  one part.
- `scripts/check_fit` reports `multi-body-part`, but only for `part_*.step.py`
  entries and only as an advisory note.

So put the assertion where the geometry is built:

```python
def build_subject():
    subject = build_primary_mass() + build_appendage() + build_secondary_mass()
    assert len(subject.solids()) == 1, (
        f"{len(subject.solids())} disconnected bodies — a segment junction "
        "does not overlap")
    return subject
```

## The cap that shows

Even when two segments do overlap, the earlier segment's cap can protrude
through the later one's surface and render as a flat facet on an otherwise
smooth flank. Two fixes, in order of preference:

1. **One loft, not two.** If the spine is continuous, put every station in one
   list and loft once. The cross-section can go from a tall ellipse to a circle
   inside a single loft; there is no reason to split at the anatomical
   boundary.
2. If the segments must stay separate (different construction families, or a
   branch), make the earlier segment's final station **smaller than** the
   later segment's tube at that point, so the cap is buried.

## A section is not always an ellipse

An ellipse loft gives a plump, round body. Real bodies may instead be laterally
compressed, keeled, chined, or flat-bottomed. If the reference's half-height ÷
half-width ratio is far from 1, an ellipse will read as a balloon however
carefully the stations are measured.

When the section has character, build it from a parametrised sketch and loft
the sketches:

```python
def _section(half_h, half_w, keel=0.0, belly=1.0):
    """Rounded belly, optional keeled back, in the station's own plane."""
    pts = [(-half_h * belly, 0.0), (0.0, half_w), (half_h, keel * half_w),
           (0.0, -half_w)]
    return make_face(Spline(*pts, tangents=..., periodic=True))
```

State the section family in the spec next to the station table; it is a
construction-family decision, and the same rule applies as for the base solid —
a body authored in the wrong section family cannot be rescued by editing
numbers.

## Colour is part of the likeness

For a model reconstructed from a photograph of a multi-material print, the
silhouette is only half of what a reader compares. STEP carries colour, so the
per-region colour below survives into the artifact even though this toolchain
renders nothing to check it against the photograph.

Keep the two representations separate, because they answer different questions:

- **`part_<role>.step.py` returns one fused solid.** That is what gets sliced,
  and what `check_fit` counts bodies on.
- **The combined entry may return coloured pieces.** Cut the fused body into
  disjoint colour regions with simple tools (half-spaces, boxes, cylinders),
  label each, and give each a `Color`. Disjoint means `inspect interfere` still
  reports nothing, because the pieces do not overlap.

```python
regions = [("head", head_tool, COL_HEAD), ("legs", leg_tool, COL_LIMB), ...]
taken = None
for name, tool, colour in regions:
    piece = fused & tool
    taken = tool if taken is None else taken + tool
    asm.add(piece, name, color=Color(*colour))
asm.add(fused - taken, "body", color=Color(*COL_BODY))
```

Sample the colours off the reference rather than naming them: a
`--palette`/`--isolate` run in `$image-to-cad` reports hex values, and a
glossy surface splits into a lit and a shaded cluster of the same paint, so
merge those by eye before writing the constant.

## Cost of the loop

A dense loft is the slow part of an organic model, and every `gen` rebuild pays
it. Two habits keep the edit loop short:

- Build and check the pieces in a plain Python session (`build_body()`,
  `build_tail()`) before running `scripts/gen`, which additionally writes the
  GLB package.
- Remember `rm -rf __cadgen__` after editing the `_lib.py` — see the repo's
  CLAUDE.md.
