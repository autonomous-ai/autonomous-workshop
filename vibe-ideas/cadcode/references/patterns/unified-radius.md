# unified-radius

**Trigger:** load when a part looks blocky / cheap / "like a default CAD box",
when the user asks to make it look nicer, more premium, rounded, softer, more
Apple-like, or when the geometry check reports a `sharp_edges` advisory you want
to clear on visible faces.

## Why this exists (the look)

The single biggest difference between a premium-looking object and a blocky one
is **edges**. A raw box has twelve hard 90° arrises; a considered product gives
every visible convex edge **one consistent radius**. Not a scatter of guessed
fillets — *one* radius language, derived from the part's size and applied
everywhere it belongs. See `references/industrial-design.md` for the full bar.

Get the radius from the part instead of guessing: roughly 6–12% of the short
plan dimension reads resolved (clamped so tiny parts don't vanish and big ones
don't look like a pillow). Concentric rule: a rounded cavity inside a rounded
shell should use `inner_r = outer_r − wall` so the wall stays constant around
the curve.

Function first: keep mating faces, sealing lips, press-fit lands, and the
build-plate edge crisp — a unified radius is for the faces the eye and hand land
on, not literally every edge.

## Use the helper

`cadlib.styling` owns the radius *choice* (so it stays uniform) and the
fillet call. Derive the radius once, then soften the visible convex edges:

```python
from cadlib.styling import design_radius_for, soften_edges

LENGTH, WIDTH, HEIGHT = 130.0, 85.0, 28.0
corner_r = design_radius_for(size=WIDTH)        # ~0.08 * 85 -> clamped to 4.0 mm

body = cq.Workplane("XY").box(LENGTH, WIDTH, HEIGHT)
body = soften_edges(body, radius=corner_r, selector="|Z")   # vertical corners
body = soften_edges(body, radius=1.0, selector=">Z")        # top rim, smaller
```

`design_radius_for(size=..., fraction=0.08, minimum=0.6, maximum=4.0)` returns
the unified radius. `soften_edges(part, radius=..., selector=...)` fillets the
selected edges with that one radius and returns a new `cq.Workplane`. **Scope
the selector** (`"|Z"`, `">Z"`, a tag) rather than rounding every edge — see
Pitfalls.

## Pitfalls

- **Blanket `.fillet` on a complex body fails.** OCCT throws where three fillets
  meet at a vertex. Always pass a `selector` that scopes the operation; soften
  in a few targeted passes (vertical corners, then the top rim) rather than one
  all-edges call. The helper rounds every edge only when `selector=None` — use
  that just on simple primitives.
- **Radius too large for the wall.** A fillet bigger than the wall thickness eats
  through it or leaves a sliver. Keep visible fillets ≤ wall, and let
  `design_radius_for`'s clamp hold the ceiling.
- **Rounding a functional edge.** Don't soften a mating land, a sealing lip, or a
  surface that locates another part — it loses the fit. Select visible *outer*
  convex edges only.
- **Fillet after shell can fail** on the thin shell edges; soften the solid
  before shelling where you can, or scope to robust edges after.
