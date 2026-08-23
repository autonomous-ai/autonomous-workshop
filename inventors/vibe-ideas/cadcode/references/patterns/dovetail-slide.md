# dovetail-slide

**Trigger:** load when the user asks for a slide-on lid, dovetail joint,
sliding rail, T-slot mount, dovetail-mount drawer, modular mounting tab.

## Why this exists (the mechanics)

A dovetail is a trapezoidal cross-section: wider on the "inside" face,
narrower at the slot opening. The wedge angle (typically 7-15°) gives
lateral capture — the tab can only exit by sliding along the slot axis,
never by lifting perpendicular to it. Larger angle = stronger capture but
harder insertion and more stress on the slot walls; smaller angle = easier
to slide but the joint can lift under load. FDM printing requires generous
clearances (0.3-0.5 mm) because the trapezoidal walls are slanted and
slicer rounding plus elephant's-foot effects push the actual print fatter
than the model.

## Use the helper

`cadlib` cuts the **female (slot) half only**. It builds the trapezoidal
cross-section, applies `clearance` to each face, and cuts it along the axis:

```python
from cadlib.mechanical import add_dovetail_slot

part = add_dovetail_slot(
    part,
    position=(0, 0, 0),  # local anchor of the slot mouth
    length=40.0,         # length along the slide axis
    base_width=10.0,     # narrow side (the slot opening)
    angle_deg=10.0,      # wedge angle, must be in (0, 30)
    depth=4.0,           # depth into the surface
    clearance=0.4,       # added to the slot on each face for a free slide
    axis="+X",           # slide direction: +X/-X/+Y/-Y
)
```

Trust the helper for the slot geometry. (The old female template here cut an
extra `depth + clearance` of depth on top of the per-face clearance — the
helper does NOT do that, and you don't want it: the matching male tab is
sized to `depth`, so the slot only needs per-face clearance to slide.)

## Param map

The old doc named everything `dovetail_*`; map to the helper kwargs:

| Old doc term | Helper kwarg | Notes |
|---|---|---|
| `dovetail_width_base` | `base_width` | narrow side / slot opening |
| `dovetail_height` | `depth` | depth into the surface |
| `dovetail_length` | `length` | length along the slide axis |
| `dovetail_angle` | `angle_deg` | wedge angle, helper guards (0, 30) |
| `dovetail_clearance` | `clearance` | per-face, slot only |
| `face=">Z"` selector | `axis` | slide direction string |

Reasonable ranges (unchanged): `angle_deg` 7–15° (10° is the universal sweet
spot), `depth` 3–6 mm, `base_width` 8–20 mm, `clearance` 0.3–0.5 mm,
`length` 10–100 mm.

## Geometry rules

For a 10° dovetail with a 10 mm base (narrow / opening side):

- base (narrow, at the slot opening) = 10.0 mm
- top (wide, captured inside) = base + 2 × depth × tan(angle)
- with depth = 4 mm: top = 10.0 + 2 × 4 × tan(10°) = 10.0 + 2 × 4 × 0.1763 = **11.41 mm**
- the overhang on each side = depth × tan(angle) = 4 × 0.1763 = **0.71 mm**

That 0.71 mm overhang per side is what mechanically captures the joint.
If clearance eats more than ~60% of it, the joint loses its lateral
capture — keep `clearance < 0.4 × depth × tan(angle)`.

## Beyond the helper

The **male tab is not in cadlib — write it inline (candidate to promote)**.
Build a trapezoid of the same nominal base, depth, and angle (no clearance on
the male — the slot carries it) and extrude it along the slide axis:

```python
# male tab not in cadlib — candidate to promote
import cadquery as cq
import math

def _trapezoid_points(width_base, height, angle_deg):
    """4 points for a trapezoid centered on X, base on Y=0.
    width_base is the narrow side (slot opening / top of tab);
    the wide side at Y=height is wider by 2*height*tan(angle)."""
    half_base = width_base / 2.0
    half_top = half_base + height * math.tan(math.radians(angle_deg))
    return [(-half_base, 0), (half_base, 0),
            (half_top, height), (-half_top, height)]

def custom_dovetail_male(width_base, height, length, angle_deg):
    pts = _trapezoid_points(width_base, height, angle_deg)
    return cq.Workplane("XY").polyline(pts).close().extrude(length)
```

`polyline` + `close` + `extrude` is the canonical way to turn an arbitrary 2D
profile into a solid. Add a 1 mm × 45° lead-in chamfer on the leading edge
(`.edges(">Y and >Z").chamfer(1.0)`) so the tab self-aligns on insertion.

## Pitfalls

- Clearance too tight: tab won't slide in at all — slanted walls overshoot
  on FDM and the slot opening prints narrower than modeled. Start with
  0.4 mm clearance, sand or file only if needed; reprinting tighter is easy.
- Clearance too loose: tab rattles and the capture is weak. Better to aim
  for a tight fit plus a lead-in chamfer than to oversize the slot.
- Wedge angle below 5°: tab can pop out of the slot under load — the
  trapezoid is barely distinguishable from a rectangle and defeats the
  whole point of the dovetail. (The helper rejects `angle_deg <= 0`.)
- Wedge angle above 20°: tab requires excessive insertion force, concentrates
  stress at the sharp corners of the female slot, and can crack the slot
  walls — especially with low-infill or thin-wall prints. (The helper rejects
  `angle_deg >= 30`.)
- Print orientation matters: lay both parts so the slide axis is horizontal
  on the build plate and the trapezoidal cross-section faces up. Slanted
  walls steeper than 45° from vertical need supports — orient to avoid
  them on the visible faces.
- No end stop: without a stop feature, the tab slides straight through and
  out the other side. Add a pin, bump, or closed end to the female slot,
  or a shoulder on the male tab.
- No lead-in: square leading edges catch on the slot opening. Add a 1 mm ×
  45° chamfer to the leading edge of the tab so it self-aligns on insertion.
- Forgetting first-layer squish: the bottom 0.2 mm of both parts prints
  slightly wider (elephant's foot). If the slot opening is on the bottom
  face, add an extra 0.1-0.2 mm clearance or chamfer the bottom edge.
