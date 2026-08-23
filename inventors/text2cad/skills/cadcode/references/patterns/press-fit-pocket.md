# press-fit-pocket

**Trigger:** load when the user asks for a press fit, interference fit, "tight
fit", shaft hole, bearing seat, magnet pocket, or any "press the part in and
have it stay" feature.

## Why this exists (the mechanics)

An interference fit retains the insert by elastic deformation: the printed
pocket is cut smaller than the insert, and the plastic squeezes around it on
insertion. The FDM dimensional-accuracy floor is roughly 0.1 mm (varies by
printer, slicer, and shrinkage). The rule: interference DECREASES as the
press diameter grows — roughly ~0.2 mm for small steel shafts down to
~0.05 mm for large bearing ODs in PLA (springier, so a touch more, in PETG).
Insertion force scales steeply with interference: over-shoot and the pocket
splits rather than seats. For toleranced bearing seats specifically, see
`bearing-seat.md` (`cadlib/tables.py::BEARING_TABLE` owns those values).

## Use the helper

`cadlib` owns the geometry — don't re-derive it. The helper cuts the hole
undersized by the interference, adds the bottom clearance so the insert
can't bottom out, and chamfers the rim so the insert starts square:

```python
from cadlib.cutouts import add_press_fit_pocket

part = add_press_fit_pocket(
    part,
    positions=[(0, 0)],       # pocket centres in the open_face plane
    insert_diameter=22.0,     # 608 OD — nominal diameter of the insert
    insert_depth=7.0,         # how deep the insert sits (608 width)
    interference=0.05,        # undersize amount, typ 0.05–0.2 (PLA, large insert)
    lead_in_chamfer=0.4,      # rim chamfer to guide the insert (0.3–0.6)
    bottom_clearance=0.3,     # extra hole depth so it doesn't bottom out
    open_face=">Z",           # face the insert presses in from
)
```

The hole is cut at `insert_diameter - interference`, `insert_depth +
bottom_clearance` deep. Pick `interference` by the rule above (more for
small shafts, less for large ODs); for toleranced bearing seats defer to
`bearing-seat.md`. Heat-set inserts are the opposite — a LOOSE hole the
brass melts into; see `heat-set-insert-pocket.md`.

> **Calibration note:** the values assume an XY-calibrated printer
> (±0.05 mm). Stock i3-style printers often over-extrude 0.10–0.15 mm;
> print a 20 mm test cube and adjust slicer XY compensation if seats come
> out tight.

## Parameter ranges

| Param | Rule | Notes |
|---|---|---|
| interference | smaller for big ODs, larger for small shafts (see the rule above) | over-shoot splits the pocket |
| lead_in_chamfer | 0.3-0.6 mm | required - without it parts snag on the rim |
| bottom_clearance | 0.2-0.5 mm | so the part can fully seat without bottoming |
| wall thickness around pocket | >= 2 mm (>= 3 mm preferred) | thinner walls bulge and the fit loosens |
| insert_depth | >= 0.5 * insert_diameter | shorter pockets let the insert cock and pop out |

## Beyond the helper

The helper cuts a circular pocket. Hex / square / D-shaft inserts need the
matching polygon, not a circle — not in cadlib, write a
`custom_press_fit_polygon()` function (candidate to promote):

```python
import cadquery as cq

def custom_press_fit_polygon(part, *, across_flats, n_sides, depth, interference):
    # Add interference to the ACROSS-FLATS dimension, not across-corners.
    pocket_af = across_flats - interference
    return (
        part.faces(">Z").workplane()
            .polygon(n_sides, pocket_af)
            .cutBlind(-depth)
    )
```

## Pitfalls

- Forgetting the lead-in chamfer - without it the part catches the rim
  and you cannot start insertion. 0.4 mm at 45 deg is the safe default.
  (The helper always cuts it — this is the failure mode of a hand-rolled
  flat pocket.)
- No bottom clearance - the part bottoms before fully seating, leaving a
  visible gap at the rim and a wobbly fit.
- Hex / square / D-shaft inserts: pocket needs the matching polygon
  (use `.polygon(n, dia)` or a custom 2D sketch), not a circle. Add the
  interference to the across-flats dimension, not the across-corners.
- PLA cracks at high interference on small features (>0.25 mm interference
  on a <10 mm pocket usually splits). Switch to PETG when you need a
  springier press-fit, or scale interference down.
- Tolerance drifts +-0.1 mm between printers and even between filament
  spools. Print a calibration coupon (a small block with the exact pocket)
  before committing to a large part if the fit is critical.
- Lateral wall thickness around the pocket must be >= 2 mm or the walls
  bulge outward during insertion and the fit goes loose after one
  insert/remove cycle.
- Layer-line anisotropy: holes printed vertically (axis along Z) come out
  slightly smaller than holes printed horizontally because of layer
  squish. If the bearing axis lies in the print plane, drop interference
  by ~0.05 mm.
- Do not press metal bearings into bare PLA pockets that will see heat
  (motor mounts, sunlit parts) - PLA creeps above 50 C and the fit loosens
  permanently. Use PETG, ABS, or a heat-set/glued metal sleeve.
- Re-inserting the same part repeatedly wears the pocket: each cycle
  shaves ~0.02 mm off the walls. Design for one-shot assembly, or use a
  threaded retainer / heat-set insert for serviceable joints.
