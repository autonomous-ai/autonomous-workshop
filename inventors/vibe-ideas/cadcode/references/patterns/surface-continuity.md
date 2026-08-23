# surface-continuity

**Trigger:** load when a part has abrupt steps, hard shoulders, or visible seams
you want to resolve — a boss meeting a wall, a stem meeting a base, a top edge
that should catch a clean line of light, or when deciding between a fillet and a
chamfer on a prominent edge.

## Why this exists (the look)

Premium products read as **continuous** — surfaces flow into each other instead
of butting at a hard step. Two cheap moves carry most of it:

1. **Blend transitions.** Where a feature meets the body (boss → wall, stem →
   base), a root fillet replaces the hard shoulder. It looks resolved *and*
   relieves the stress concentration — form and function agree, so this is
   almost always right (see `references/patterns/fillet-stress-relief.md` and
   `references/patterns/rib-stiffener.md` for the structural side).
2. **Chamfer for a crisp line.** Where a round would read soft or mushy, a small
   chamfer catches one clean highlight. On a top edge it also breaks the
   overhang so the edge prints support-free. A chamfer *then* a small fillet on a
   prominent edge gives a soft transition with a defined line.

Commit to **one treatment per visible face** — don't mix raw 90° arrises and
rounds arbitrarily on the same surface, or the object reads accidental. See
`references/industrial-design.md`.

## Use the helper

`cadlib.styling.break_edges` applies one consistent chamfer; pair it with
`soften_edges` (from `references/patterns/unified-radius.md`) for the combo.

```python
from cadlib.styling import break_edges, soften_edges

body = cq.Workplane("XY").box(120, 80, 24)
body = soften_edges(body, radius=4.0, selector="|Z")   # rounded vertical corners
body = break_edges(body, size=1.0, selector=">Z")      # crisp top-edge chamfer
```

`break_edges(part, size=..., selector=...)` chamfers the selected edges by
`size` mm and returns a new `cq.Workplane`. Same selector discipline as
`soften_edges` — scope it, and keep chamfers off functional/mating edges.

For a blended boss-to-wall junction, use the structural helper that already
applies a root fillet (e.g. `cadlib.mechanical.add_rib_stiffener`'s `root_fillet`,
or `cadlib.mounting.add_screw_post`) rather than re-deriving the blend.

## Pitfalls

- **Chamfer/fillet on a mating or sealing edge** destroys the fit — keep the
  treatment on visible, non-functional edges.
- **Top-face fillet that needs support.** A full round on a top overhang prints
  rough; a chamfer (≤45°) bridges clean. Prefer `break_edges` on top edges.
- **Stacking ops that fail.** A chamfer after a fillet (or vice versa) on the
  *same* edge can error if the first op consumed it; chamfer/fillet distinct
  edge selections, or apply to the solid before the feature that splits the edge.
- **Over-blending.** Not every shoulder needs a fillet; a deliberate crisp step
  can be the design. Blend the junctions that carry load or that the eye lands
  on, not reflexively all of them.
