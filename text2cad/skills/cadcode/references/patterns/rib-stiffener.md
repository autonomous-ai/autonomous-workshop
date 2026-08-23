# rib-stiffener

**Trigger:** load when the user asks for ribs, stiffeners, gussets, "make
this stronger without making it thicker", reinforced wall, braced boss,
or any "panel is too flexible / too weak" complaint.

## Why this exists (the mechanics)

Bending stiffness scales with the SECOND MOMENT OF AREA: for a thin plate
of thickness h, `I ∝ h³`. Doubling the wall thickness gives 8x the
stiffness but 2x the weight (and 2x the print time). A rib added
perpendicular to the bending axis raises the effective I by moving
material away from the neutral axis — same stiffness as a much thicker
wall for a fraction of the plastic. Rule of thumb: a rib of height
`= 4 x wall_thickness` gives roughly 10x the panel's bending stiffness.

## Use the helper

`cadlib` adds ONE rib between two anchor points on a single Z plane. It
sizes the box, rotates it to run start→end, unions it, and applies the root
fillet:

```python
from cadlib.mechanical import add_rib_stiffener

part = add_rib_stiffener(
    part,
    start=(-20, 0, 5),   # rib base anchor (both ends share one Z)
    end=(20, 0, 5),      # rib runs start -> end in XY
    height=8.0,          # how far the rib stands proud of its base
    thickness=1.2,       # rib width (~0.6x wall is the sweet spot)
    root_fillet=0.5,     # fillet at the rib-to-parent junction
)
```

`start` and `end` must share the same Z (the helper raises `ValueError`
otherwise, and if the two points coincide in XY). Call it once per rib.

## Param map

The old doc drove a whole array off one params dict; the helper is a single
rib by endpoints. Map the per-rib terms:

| Old doc term | Helper kwarg | Notes |
|---|---|---|
| `rib_height` | `height` | proud height above the base |
| `rib_thickness` | `thickness` | rib width |
| `rib_fillet` | `root_fillet` | junction fillet |
| `rib_length` + `origin` | `start` / `end` | give the two endpoints directly |
| `rib_count` / `rib_pitch` | — | loop the call yourself (see below) |
| `rib_taper` | — | not exposed (see below) |

## Sizing rules of thumb

All ratios, not hard law — they scale off the wall they brace:

- **Rib thickness**: `~0.5-0.6 x wall_thickness`. Thicker ribs sink-mark
  the opposite face during injection moulding; for FDM, thicker is fine
  but wasteful and prints slower.
- **Rib height**: `<= 3x rib_thickness` for moulded parts (sink marks);
  FDM can go to `4-6x` without issue. So for a 2 mm wall: ribs
  ~1.0-1.2 mm thick x 4-8 mm tall.
- **Rib pitch (spacing)**: roughly `5-10x rib_thickness`. Less = closer
  to a solid plate (wastes plastic); more = panel buckles between ribs.
- **Rib fillet at root**: `>= 0.5 mm`. Without it, the panel cracks at
  the rib-to-panel junction under repeated load (stress concentration).
- **Taper**: 1-2 degrees makes injection moulding release easier and
  prints with marginally less material; not required for FDM.

## Two common configurations

1. **Parallel ribs**: ribs all aligned with one direction. Stiffens
   against bending around the perpendicular axis. Use when you know
   which way the panel will be loaded (e.g. a shelf bending down under
   weight — run ribs front-to-back).
2. **Cross-rib grid**: ribs in both X and Y. Stiffens against bending in
   any direction. Use when load direction is unknown. Roughly 1.6x the
   stiffness of parallel ribs for ~2x the material.

For a boss reinforcement: ribs should radiate FROM the boss outward at
3-4 equal angles (cross pattern). One rib only stiffens against one
load direction.

## Beyond the helper

The **rib array and tapered rib are not in cadlib — write a `custom_ribs()`,
candidate to promote**. Loop the helper for a parallel array, and use a loft
when you need a draft-tapered (narrower-top) rib:

```python
# rib array / taper not in cadlib — candidate to promote
import cadquery as cq
import math

def custom_ribs(part, *, count, pitch, length, height, thickness,
                base_z, origin=(0.0, 0.0), root_fillet=0.5):
    """Centred parallel array along Y; each rib runs length along X."""
    x0, y0 = origin
    y_start = y0 - (count - 1) * pitch / 2.0
    for i in range(count):
        yc = y_start + i * pitch
        part = add_rib_stiffener(
            part,
            start=(x0 - length / 2, yc, base_z),
            end=(x0 + length / 2, yc, base_z),
            height=height, thickness=thickness, root_fillet=root_fillet,
        )
    return part

def custom_tapered_rib(length, height, thickness, taper_deg):
    """Loft two stacked rects so the rib is narrower at the top."""
    shrink = height * math.tan(math.radians(taper_deg))
    top_t = max(thickness - 2.0 * shrink, 0.4)
    return (
        cq.Workplane("XY")
        .rect(length, thickness)
        .workplane(offset=height)
        .rect(length, top_t)
        .loft(combine=True)
    )
```

(Real CadQuery: `.rect`, `.workplane(offset=)`, `.loft`, `.translate`,
`.union`.) Chain both rects onto stacked workplanes so the wires land in the
same pending-wires queue before the loft.

## Pitfalls

- Forgotten root fillet -> panel cracks at the rib root under cyclic
  load. The sharp inside corner is a textbook stress concentrator. (The
  helper applies `root_fillet` by default — keep it > 0.)
- Rib too tall and thin -> the rib itself buckles laterally before it
  does any work. Keep `height <= 8 x thickness`.
- Rib oriented PARALLEL to the bending axis -> does nothing. The rib has
  to cross the bending neutral axis to add I.
- Print orientation: print with the panel flat and ribs growing UP from
  the build plate. Ribs printed sideways are weak across layer lines and
  delaminate at the rib root under load.
- Don't fillet the TOP of the rib — looks nice but adds nothing
  structurally and wastes a fillet operation that can fail when edges
  are too short.
- Hidden trap: a tall rib near the edge of a thin panel shifts the
  panel's stiffness asymmetrically and warps it during cooling. Add
  ribs symmetrically about the panel centre, or expect bowing.
- Ribs spaced too tightly (`< 3 x thickness`) trap heat between them
  during FDM printing, causing the panel underneath to over-extrude and
  bulge. Honour the `5-10x` pitch rule.
