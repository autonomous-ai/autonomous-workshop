# snap-fit-cantilever

**Trigger:** load when the user asks for a snap-fit lid, clip-on enclosure,
"snap together", removable cover with built-in retention, or any
plastic-on-plastic engagement that should hold without screws.

## Why this exists (the mechanics)

A cantilever snap is a beam fixed at one end with a catch nub at the free end.

**Mechanics.** Tip deflection under load: `y = (F * L^3) / (3 * E * I)`, with
rectangular `I = (b * h^3) / 12`. Stress at the root: `sigma = (3 * E * h * y) /
(2 * L^2)`, so strain `epsilon = (3 * h * y) / (2 * L^2)`. The arm fails when
that root strain exceeds the material's limit.

**Material constants (typical — verify/web-search for your filament).** Modulus
`E` ≈ PLA 3.5 GPa, PETG 2.0 GPa, ABS 2.3 GPa, TPU 0.05 GPa. Strain limit ≈ 1%
for filled PLA, ~2% for PETG/ABS; past it the root crazes after a few
insertions. These are ballpark starting figures, not datasheet values — confirm
for the actual material before trusting a tight design.

**Design rules.** Deflection-to-length ratio `y / L <= 0.1`; root thickness
`h >= 1.5 mm` for FDM; and the catch must protrude no more than the beam can
clear within that ratio (typically 0.5–1.5 mm).

## Use the helper

`cadlib` owns the geometry — don't re-derive it. The helper cuts the two
relief slots that free the arm and adds the catch nub with a lead-in chamfer
in one call:

```python
from cadlib.mechanical import add_snap_fit_cantilever

part = add_snap_fit_cantilever(
    part,
    position=(0, 0, 0),    # local anchor at the arm root
    length=12.0,           # L: root-to-tip arm length
    thickness=2.0,         # h: arm thickness (the bending dimension)
    width=6.0,             # b: arm width
    catch_height=0.8,      # how proud the catch nub stands
    relief_width=1.2,      # slot width either side of the arm
    lead_angle_deg=30.0,   # lead-in chamfer on the insertion side
    axis="+Y",             # arm extends along +X/-X/+Y/-Y
)
```

The helper validates `catch_height < 0.1 * length` and raises `ValueError`
otherwise (see Pitfalls for why). `axis` must be one of `+X/-X/+Y/-Y`.

## Param map

The old doc named everything `snap_*`; the helper uses plain mechanical
terms. Translate as:

| Old doc term | Helper kwarg | Notes |
|---|---|---|
| `snap_length` | `length` | L, root to catch tip |
| `snap_thickness` | `thickness` | h, the bending dimension |
| `snap_width` | `width` | b |
| `snap_catch_height` | `catch_height` | engagement depth |
| `snap_relief_width` | `relief_width` | slot width per side |
| `snap_lead_angle` | `lead_angle_deg` | insertion chamfer angle |
| `snap_catch_depth` | — | helper sizes the nub itself; not a kwarg |
| `snap_relief_depth` | — | helper cuts the full arm depth |
| `snap_root_fillet` | — | not exposed (see Beyond the helper) |
| orientation via face selector | `axis` | direction string, not a `.faces()` pick |

## Beyond the helper

The helper omits a couple of stress-relief refinements the old template had.
Both are **not in cadlib — write a `custom_root_fillet()` / `custom_taper()`,
candidate to promote** if you find yourself needing them often:

- **Root fillet** to spread stress at the fixed end (the #1 failure site).
  After placing the arm, fillet the inside corners where the arm meets the
  parent wall:

  ```python
  # not in cadlib — candidate to promote
  try:
      part = part.faces("<Y[-2]").edges("|X").edges("<Z").fillet(0.5)
  except Exception:
      pass  # filleting tight inside corners can fail; skip if so
  ```

- **Tip taper** (arm thinner at the tip than the root) for a softer click
  and lower peak strain — thin the free end after the union.

## Pitfalls

- `catch_height >= 0.1 * length` is rejected by the helper with a
  `ValueError`. WHY: max safe tip deflection is `y_max ≈ 0.1 * L` (the
  `y / L <= 0.1` rule). A catch taller than that can't be cleared without
  forcing the arm past its safe strain — insertion overstresses the root and
  the arm crazes or shears. With `L = 8 mm`, a `catch_height` of 1.5 mm
  exceeds the 0.8 mm budget → insertion impossible without damage. Lengthen
  the arm or shrink the catch.
- Brittle materials (carbon-filled PLA, dry PETG, old ABS) fatigue in 5–20
  cycles. Double `length` or switch the arm to PETG/PP only. For high cycle
  counts watch the root strain, not just first-insertion success.
- Keep root thickness `h >= 1.5 mm` for FDM; thinner arms delaminate at the
  root.
- Relief slot too narrow (< 0.8 mm) fuses shut on an FDM printer and the
  arm becomes rigid — the snap then either won't insert or shears off.
- Catch on a non-removable face means the lid is permanent. If geometry
  is symmetric, emboss "PRESS" or an arrow on the release side.
- Print orientation: the bending axis (the `thickness` dimension) must lie in
  the XY plane. If `h` is vertical, layer lines run across the bend and the
  arm snaps clean off on first flex.
- For a sliding lid, a single snap lets the lid walk off the other end.
  Pair the snap with a hard stop, a second snap, or a captive rib.
- Forgetting clearance: the mating pocket needs `catch_height + 0.2 mm`
  of depth or the catch bottoms out before the nub engages.
