# wall-thickness-rules

**Trigger:** load at the START of any new design where wall thickness
is a free parameter, or when the user complains a part is too floppy /
too heavy / used too much filament.

## Why this exists (the mechanics)

FDM walls print in integer multiples of the slicer's "extrusion width"
(roughly equal to nozzle diameter for normal print settings). A 0.4 mm
nozzle gives a 0.4 mm extrusion width by default, so walls render in
steps of 0.4 mm. A wall authored at 1.0 mm prints as either 2 perimeters
+ a 0.2 mm gap-fill bead (lumpy, weak seam) or 3 perimeters compressed
together (better, but no longer 1.0 mm). Walls that are clean multiples
of the nozzle width (0.8, 1.2, 1.6, 2.0, 2.4, 3.2 mm) are the only ones
the slicer can render without compromise. Below 0.8 mm you are in
single-wall ("vase mode") territory — flimsy and porous. Above ~4 mm
thermal warping starts to dominate on big PLA prints and the extra
plastic is wasted.

## Default wall thicknesses

The rule is `wall = N × nozzle width`, where `N` is the perimeter count the
use case needs. Pick `N`, multiply by the nozzle width, and you have a wall
the slicer can render without a gap-fill bead.

Worked example at a 0.4 mm nozzle: a decorative shell wants 3 perimeters →
**1.2 mm**; a generic enclosure wants 5 → **2.0 mm**; a load-bearing part
wants 7 + ribs → **2.8 mm**. The full mapping of use case to `N` (and so to
the worked thickness at 0.4 mm):

| Use case | Perimeters (N) | At 0.4 mm | Why |
|---|---|---|---|
| Decorative shell (no load) | 3 | 1.2 mm | strong enough to handle |
| Generic enclosure | 5 | 2.0 mm | rigid, no flex, good acoustics |
| Load-bearing part | 7 + ribs | 2.8 mm | use ribs not thickness |
| Cosmetic detail / tab | 2 | 0.8 mm | thinnest robust wall |
| Living-hinge web | 1 | 0.4 mm | see living-hinge.md |
| Top wall above magnets | 1–2 | 0.4–0.8 mm | see magnet-pocket.md |
| Bottom of a tray | 3 + ribs | 1.2 mm | rigid floor |

## Nozzle-aware adjustment

The defaults above assume a 0.4 mm nozzle. For other nozzles, snap walls
to the NEAREST multiple of the nozzle width:

- 0.25 mm nozzle: 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5 mm
- 0.4 mm nozzle (standard): 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2 mm
- 0.6 mm nozzle: 1.2, 1.8, 2.4, 3.0, 3.6 mm
- 0.8 mm nozzle (large): 1.6, 2.4, 3.2, 4.0 mm

Unless the user specifies, assume 0.4 mm nozzle.

## CadQuery template

```python
import cadquery as cq

def make_thinwall_box(p):
    """Build a thin-walled box (enclosure shell) with the bottom open.

    Required params (mm):
      box_outer_x   — outer X dimension
      box_outer_y   — outer Y dimension
      box_outer_z   — outer Z dimension (height)
      wall          — wall thickness, snapped to nozzle multiples
      floor         — bottom-face thickness
    """
    return (
        cq.Workplane("XY")
        .box(p.box_outer_x, p.box_outer_y, p.box_outer_z)
        .faces(">Z")
        .shell(-p.wall)        # negative = inward shelling
    )
```

(Note CadQuery's `.shell()` may struggle on complex topologies. For a
plain box, this is robust. For complex shapes, build the outer + inner
separately and subtract.)

## Hard rules

- **Minimum printable wall** `= 1 × nozzle width` (a single perimeter; 0.4 mm
  at a 0.4 mm nozzle). Below this and the slicer skips the geometry entirely.
- **Avoid `1 < N < 2` nozzle-widths** (0.4 < t < 0.8 at a 0.4 mm nozzle) for
  non-flexure walls — that band rounds to 0 or 2 perimeters depending on
  settings, output unpredictable. Modern slicers quantize wall to
  extrusion-width multiples and use variable-width extrusion to fill gaps,
  so a non-multiple wall often prints cleanly — but snapping to nozzle
  multiples is still preferred for predictability. Check your slicer's
  perimeter / wall settings if a wall renders thinner than authored.
- **Above 4 mm**: warping risk on big PLA prints. Use solid infill walls
  or rib-stiffened thin walls instead.
- **Snap to nozzle multiples** within ±0.05 mm. A 1.0 mm wall is worse
  than a 1.2 mm wall on a 0.4 mm nozzle.
- **For STIFFNESS, doubling thickness is 8× stiffer (h³ rule)**. Adding
  one rib is usually 5–10× cheaper than doubling all walls. See
  rib-stiffener.md.

## Pitfalls

- Specifying t = 1.0 mm and expecting it to print as 1.0 mm: most slicers
  will round to 0.8 mm (2 perimeters) or 1.2 mm (3 perimeters, with gap
  fill). Either is fine but the dimension you authored isn't honored.
- Using ``.shell(-t)`` with too-thin walls on complex geometry → OCCT
  error. Snap up to the nozzle minimum (0.8 mm).
- Designing for one nozzle when the user prints with another. Make the
  wall thickness a parameter, not a constant.
- A wall thinner than the radius of any fillet it carries → fillet
  operation fails. Wall must be at least 2× max fillet on it.
- Walls thicker than 4 mm + tall print + PLA → warping at the corners.
  Better solution: hollow out + add ribs.
- Material matters: PETG is ~0.6× as stiff as PLA at the same wall
  thickness (E ≈ 2.0 GPa vs 3.5 GPa); bump up by one nozzle-multiple step.
- PETG also **creeps** under sustained load (a snap-fit lid "fine" at
  install is loose in 6 months). PLA holds dimensions; PETG slowly relaxes.
  For load-bearing fits in PETG, bump the wall by one nozzle-multiple step
  AND avoid sustained compression.
