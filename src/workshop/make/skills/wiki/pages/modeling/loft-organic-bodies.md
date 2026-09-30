---
title: Organic bodies from lofts
tags: [organic, loft, station-table, spine, junction, section-family, colour-region]
aliases: [animal body, figure, hull, freeform body, curved spine, lofted segments, body count]
sources:
  - skills/cad/references/organic-lofts.md (before the move)
  - "experience: a tail resting against a body passed validate and interfere as two solids"
related: [loft-pitfalls, frames-and-rotations, operation-families]
updated: 2026-09-23
---

# Organic bodies from lofts

Any animal, figure, vehicle body, hull, or other freeform mass — anything
whose cross-section changes continuously along a curved spine. General loft
failures are in [[loft-pitfalls]]; this page is the body-specific part.

## The station table is the model

A freeform body is a table before it is code. One row per station along the
spine:

    (x, z, half-height, half-width)      body, spine in the XZ plane
    (x, z, y, radius)                    tail/limb, spine leaving that plane

Read the rows off the reference views — `$image-to-cad`'s `grid_overlay.py`
puts labelled pixel coordinates on the photograph so a curve can be read as
numbers rather than adjectives. Put the table in the spec **and** in the
library as a named constant. The shape becomes reviewable without running
anything, and a likeness failure localised to one height band by
`check_likeness.py` points at specific rows.

Twelve to sixteen stations carry a body. A tight spiral needs a station every
~25° of turn or it reads as a polygon.

Build each station's frame from a lateral reference, never from Z
([[frames-and-rotations#a-loft-station-frame-from-a-lateral-reference-never-from-z]]).

## Consecutive segments must overlap, not meet

This is the expensive one. A loft's end cap is a plane **normal to the spine
tangent at the last station** — not a vertical wall, and not where you think
it is. Its extent is the last station's ellipse, tilted. So a segment whose
last station sits at `(x=-62, z=103)` with a half-height of 19 does not end at
x = -62: its cap sweeps from `(-77.6, 113.9)` to `(-46.4, 92.1)`, and every
point beyond that plane is outside the solid.

Start the next segment's first station **inside** the previous segment — a
station or two back along the spine, sized to fit within that section — not
at the seam. Overlapping costs nothing; a boolean union of overlapping solids
is one solid, and of touching solids is often two.

```python
BODY_STATIONS = [ ..., (-55, 113, 28, 16), (-62, 103, 19, 13) ]
TAIL_STATIONS = [ (-52, 116, 0.0, 13.0),      # INSIDE the haunch, not at the tip
                  (-59, 106, -0.5, 12.0), ... ]
```

## Assert the body count in the source

Nothing else catches it. A tail resting against a body and a tail attached to
one are the same picture:

- `inspect validate` returns `ok` — both solids are closed and positive.
- `inspect interfere` returns `ok` — it compares *parts*, not the bodies
  inside one part.
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
   list and loft once. The cross-section can go from a tall ellipse to a
   circle inside a single loft; there is no reason to split at the anatomical
   boundary.
2. If the segments must stay separate (different construction families, or a
   branch), make the earlier segment's final station **smaller than** the
   later segment's tube at that point, so the cap is buried.

## A section is not always an ellipse

An ellipse loft gives a plump, round body. Real bodies may instead be
laterally compressed, keeled, chined, or flat-bottomed. If the reference's
half-height ÷ half-width ratio is far from 1, an ellipse will read as a
balloon however carefully the stations are measured.

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
construction-family decision, and a body authored in the wrong section family
cannot be rescued by editing numbers.

## Colour regions on one fused body

For a model reconstructed from a photograph of a multi-material print, the
silhouette is only half of what a reader compares. STEP carries colour, so
per-region colour survives into the artifact.

Keep the two representations separate, because they answer different
questions:

- **`part_<role>.step.py` returns one fused solid.** That is what gets sliced,
  and what `check_fit` counts bodies on.
- **The combined entry may return coloured pieces.** Cut the fused body into
  disjoint colour regions with simple tools (half-spaces, boxes, cylinders),
  label each, and give each a colour. Disjoint means `inspect interfere` still
  reports nothing, because the pieces do not overlap.

```python
from cadfilament import filament

regions = [("head", head_tool, COL_HEAD), ("legs", leg_tool, COL_LIMB), ...]
taken = None
for name, tool, colour in regions:
    piece = fused & tool
    taken = tool if taken is None else taken + tool
    asm.add(piece, name, color=filament(colour))
asm.add(fused - taken, "body", color=filament(COL_BODY))
```

Measure the reference, then round to stock. A `--palette`/`--isolate` run in
`$image-to-cad` reports hex values — and a glossy surface splits into a lit
and a shaded cluster of the same paint, so merge those by eye first. Each
merged hex then picks the nearest filament name from the part's own stock (the
tables under **Colour** in `skills/cad/references/build123d-modeling.md`), and
that name is what the region constant holds. One part prints in one stock, so
round every region of it against the same table and pass that stock to
`filament(..., material=...)`. A region in a colour outside its palette cannot
be printed as drawn, so record the substitution in the spec instead of passing
the sampled hex through `Color()` or `srgb()`.
