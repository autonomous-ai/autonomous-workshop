---
title: Organic bodies from lofts
tags: [organic, loft, station-table, spine, junction, section-family, colour-region]
aliases: [animal body, figure, hull, freeform body, curved spine, lofted segments, body count]
sources:
  - skills/cad/references/organic-lofts.md (before the move)
  - "experience: a tail resting against a body passed validate and interfere as two solids"
  - "experience: a figure designed from prose, lofted from hand-typed pairs, then from a drawn silhouette"
  - "experience: a carved carousel figure printed as midplane halves with flat-faced legs"
  - "experience: a 12-lobe pumpkin printed upright on a lamp-shade dock"
  - "experience: a sector-built lobe ring validated only with flattened poles, and its under-equator creases needed a steeper lobe flank than the lobes themselves"
related: [loft-pitfalls, frames-and-rotations, operation-families, carved-figures-on-split-prints, fuse-pitfalls]
updated: 2026-10-12
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

## No photograph: draw the silhouette, cut the stations from it

A figure designed from words has no image to read rows off, and typing
(top, bottom) pairs by hand gives a sausage: nothing holds the side view to
a line anybody drew. Draw the side outline instead — a top curve and a
bottom curve through a dozen control points each (a Catmull-Rom spline is
enough) — and derive every station from it, so the side view *is* the
drawing:

- **A barrel-like span:** each station is a point inside the silhouette and a
  chord angle; the chord ends where that ray meets each outline.
- **A sharp bend** (a neck rising off a body): perpendicular chords from a
  tightly curving spine cross inside the body and the loft folds through
  itself. Pair the two outlines by equal arc-length fraction instead — crest
  point *i* with throat point *i* — and the chords fan out without crossing.
  Where even that crosses (a throatlatch tucked tight under a jowl), set the
  few pairs through the bend by hand and keep arc length for the rest.
- **An appendage at an angle** (a head, a hand): draw it in its own frame
  with its axis level, cut its stations there, then rotate the pairs into
  place.
- **Check that a part's defining bulge lies outside its neighbour's
  silhouette.** A jowl drawn under a steeply angled head ended inside the
  neck's outline, so the loft hid it and the head read as a tube; carrying
  the head forward uncovered it. Plot both outlines together before lofting:
  a 2D plot takes a second, a loft and a render a minute.
- **Bury the joining section.** A neck whose crest ended exactly where the
  head's surface also passed fused into a valid fragment of a fraction of a
  percent ([[fuse-pitfalls#a-fuse-can-come-back-empty-assert-every-step]]).
  End it a millimetre or two inside the other loft.
- **A head is carved, not intersected.** Two outlines extruded across each
  other (side profile ∩ plan) give a box with knife edges, and filleting that
  intersection failed at every radius. Loft the head instead through sections
  whose height comes from the side profile and whose width comes from a plan
  outline (broad cheeks, a narrow nose, flared nostrils), each section a
  rounded box rather than an ellipse.

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

## A carved figure on a split print

Limbs of bones and knobs, limbs let into the flank, bevelled flat faces,
carved relief, ears across the split and split slivers are
[[carved-figures-on-split-prints]].

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

Each region constant holds a filament name, never a sampled hex: rounding a
measured colour to stock, and recording a substitution, is under **Colour** in
`skills/cad/references/build123d-modeling.md`. Merge gloss's lit and shaded
clusters of one paint first
([[measuring-reference-photos#colour-clusters-are-colour-not-parts]]), and
round every region of one part against the same stock, since a part prints in
one.

Build every tool in the frame of the body it cuts. A tool built in the world
and passed through the figure's placement a second time lands off the body,
the intersection is empty, and the region silently takes the base colour.
Assert that every colour region holds material, the same guard as every role
holding material ([[fuse-pitfalls#a-fuse-can-come-back-empty-assert-every-step]]).

Also validate every emitted colour-region solid with the topology gate. A
primitive-based physical union can be valid while a pupil or other clipped
colour leaf is self-intersecting after partition booleans. Positive region
volumes, a matching volume sum, zero missing/extra union volume and clean
interference do not prove leaf validity. Keep the physical-union checks and
the per-leaf checks on both coloured entries; repair the partition in source
and repeat the affected checks before exporting the final coloured STEP.

## A lobed body (a pumpkin): loft one lobed section

Loft a single N-arc lobed section, scaled about the axis along the profile.
Fusing N offset lobe solids instead gives a dished "donut" top, because each
lobe peaks on its own axis. A superellipse profile (p about 3.4 above the
equator) gives the flat shoulders of a pumpkin; a plain ellipse reads as an
onion. To print upright, put a ruled 45 deg flank under the bulge (a ruled
loft between two scaled sections makes exact cones, so no lobe face leans
more than the crown meridian), and start the smooth loft where the slope is
42 deg so the spline cannot pass 45. Turn the lobe pattern so a crease, not a
crown, faces the nearest obstacle on the host.

## A ring of lobes built as sectors

When each lobe must be its own surface (lobes of different heights), build one
sector piece (a core wedge plus one lobe) and pattern it round the axis so the
copies meet on planar faces. Fusing overlapping B-spline lobes instead can take
twenty times as long. A scaled revolve keeps its pole at the lobe top, and
`BRepAlgoAPI_Check` may flag some rotated copies of the same piece as
self-intersecting there. Flatten the lobe tops by about 0.6 mm: at 0.3 mm the
flats are so small that they tessellate open in `check_mesh`. Where a later
landing cut already removes the poles, do not flatten at all, or the tiny flats
come back.

Below the equator, the crease between two lobes runs flatter than either lobe.
If each lobe's underside is at the overhang limit, the crease fails the
overhang gate. Give the lobe underside about 58 deg from horizontal (32 deg off
vertical) so the crease clears 45 deg.

## A tube cannot fold tighter than its own radius

A loft along a curved spine self-folds where the spine's curvature radius is
smaller than the section radius; it builds an open hook or an invalid solid.
Keep `curvature_radius / tube_radius` above about 1.1 along the spine. For a
fabric fold (a floppy hat tip), end the first body in a rounded crown and
start a second loft inside it, so the bend is hidden in the crown.

Where a tube meets a sphere (a tip and its ball), do not cut the tube with the
sphere: the grazing intersection leaves knife edges. Part both on a plane
through the sphere at offset `d` and start the tube at `sqrt(R^2 - d^2)`, so the
joint is flush.
