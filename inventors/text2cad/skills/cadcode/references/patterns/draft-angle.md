# draft-angle

**Trigger:** load when designing a stacking / nesting part, a tapered
press-release feature, or when the user complains a tall wall sticks in a
pocket on disassembly. Also the place to look for the "how do I taper a wall
in CadQuery" answer.

> Scope: this is an FDM-printing reference. Mould-making (silicone / resin
> casting), where draft is mandatory, is out of scope for Panda v1 — the
> mechanics below transfer if you ever need it, but the defaults here are
> tuned for printed parts.

## Why this exists (the mechanics)

A 1–3° draft turns a vertical wall into a shallow wedge. For FDM that helps
three ways: (a) a tall wall becomes self-supporting up to ~1 extra mm of
overhang, (b) it hides visible layer steps on glossy materials, (c) stacked
or nested parts separate cleanly instead of wedging. 1° = ~17.5 mm horizontal
per 1000 mm vertical (rule of thumb: tan(1°) ≈ 0.0175).

## When to apply draft

| Use case | Draft angle | Direction |
|---|---|---|
| Stacking / nesting trays | 2° | walls taper inward toward bottom |
| Press-fit pocket release | 0.5–1° | tapered inward (deeper = narrower) |
| Cosmetic curve (hide steps) | 0.5° | either |
| Pure-function FDM | none needed | — |

## CadQuery template

```python
import cadquery as cq

def make_drafted_box(p):
    """A four-sided box with constant draft on the side walls. The
    bottom is larger than the top (positive draft = inward taper as Z+).

    Required params (mm + degrees):
      base_x        — bottom X dimension
      base_y        — bottom Y dimension
      height        — total Z height
      draft_deg     — taper in degrees (positive = inward taper)
      floor         — floor thickness
    """
    import math
    offset = p.height * math.tan(math.radians(p.draft_deg))
    top_x = p.base_x - 2 * offset
    top_y = p.base_y - 2 * offset
    return (
        cq.Workplane("XY")
        .rect(p.base_x, p.base_y).workplane(offset=p.height)
        .rect(top_x, top_y).loft(combine=True)
    )
```

(Real CadQuery: ``.rect``, ``.workplane(offset=...)``, ``.loft``. The
loft of two rectangles creates the drafted side walls automatically.)

## Quick conversions

The horizontal offset is just the formula from the template:

    offset = tan(angle) × height

(tan(1°) ≈ 0.0175, from the mechanics above — so 1° ≈ 0.175 mm of offset
per 10 mm of Z.) Plug in your own angle and height; the table below is only
convenience for the common angles at 10 mm Z:

| Angle | Horizontal offset per 10 mm Z |
|---|---|
| 0.5° | 0.087 mm |
| 1° | 0.175 mm |
| 2° | 0.349 mm |
| 3° | 0.524 mm |
| 5° | 0.875 mm |
| 7° | 1.228 mm |

## Combining with other features

- **Draft + holes**: cut holes AFTER lofting the drafted walls. Holes
  remain cylindrical (their own axis); the wall around them tapers.
- **Draft + ribs**: draft applies to ribs too — typically 1° on rib
  sides for moulding, 0° for FDM.
- **Draft direction**: which way taper goes matters. For a mould, draft
  away from the parting line on BOTH sides. For FDM stacking trays, narrow
  bottom = stacks neatly. For press-fit pocket release, narrow at the
  bottom = pocket "ejects" the inserted part.

## Pitfalls

- Pure FDM with no draft is FINE for most parts — don't add draft "to be
  safe", it just shrinks the top.
- Applying draft to a Workplane chain via ``.taper`` is NOT a standard
  CadQuery API. Build drafted walls using ``loft`` between two rectangles
  (one at the bottom, one at the top), as above.
- Draft angle confusion: "1° draft per side" vs "1° total taper". This
  doc uses "per side" (the standard convention). 1° per side means a 10
  mm wall starts 0.175 mm wider at the bottom than at the top FOR EACH
  SIDE — total widening = 0.35 mm at the bottom on each axis.
- Drafted walls have non-square corners → can interfere with mating
  parts designed flat. If your part mates with a flat-walled part, only
  apply draft to NON-MATING walls.
- Loft of two unequal rectangles makes flat trapezoidal walls; that's
  correct, but the corners are sharp 3D edges. Add fillets after loft
  if cosmetic.
