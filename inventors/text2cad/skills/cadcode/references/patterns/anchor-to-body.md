# anchor-to-body

**Trigger:** assembly of parts, standoffs / posts / bosses on a curved or
tapered wall, a strut or arm joining a plate, "part is floating", a
`disconnected_bodies` warning, any feature whose position is computed from
parameters rather than selected off an existing face.

## Why this exists

The most common defect in generated parts is geometry that is *valid* but
*detached*: a feature placed by coordinate that never actually touches the body.
Two real failures:

- **Off the footprint.** A standoff at `(x, y)` on an elliptical tray
  (`ellipse(a, b)`) floats because the wall has already narrowed there — the
  ellipse half-width at `x` is `b·√(1 − (x/a)²)`, not `b`. A post at `y = b·0.75`
  is inside near the centre but *outside* the wall near the ends.
- **Terminates inside a thin plate.** A fat, angled strut whose axis ends at the
  mid-plane of a 3 mm tab pokes its rounded end-cap out through the top face,
  because the cap rim reaches further than the axis endpoint.

A boolean `union` only fuses solids that actually overlap. Disjoint solids stay
separate — that is exactly what the `disconnected_bodies` check counts. The fix
is never "union harder"; it is to put the feature where it overlaps the body.

## CadQuery template

```python
import cadquery as cq
import math

# 1) Place features ON the body, not at raw coordinates. Clamp a point to the
#    real footprint before using it (elliptical tray of semi-axes a, b):
def clamp_to_ellipse(x, y, a, b, margin):
    # shrink the allowed ellipse by `margin` so the whole boss stays on the wall
    ae, be = a - margin, b - margin
    r = math.hypot(x / ae, y / be)
    if r <= 1.0:
        return x, y
    return x / r, y / r            # pull the point back onto the boundary

# 2) Embed, don't abut. Give every joining feature an overlap into its mate of
#    at least the wall thickness so the union fuses into ONE solid. A strut that
#    must die into a plate should pass THROUGH the plate, then trim flush:
def strut_into_plate(p1, p2_on_plate, r, plate_top_z, overshoot=2.0):
    d = [b - a for a, b in zip(p1, p2_on_plate)]
    L = math.sqrt(sum(c * c for c in d)) + overshoot      # run past the face
    return cq.Solid.makeCylinder(r, L, cq.Vector(*p1), cq.Vector(*d))
    # union with the plate, then `.cut()` everything above plate_top_z so the
    # strut ends flush instead of poking out as a spike.

# 3) Verify connectivity after building: a single printable part is ONE solid.
part = cq.Workplane("XY").box(20, 20, 10)   # ... build the part ...
assert len(part.solids().vals()) == 1, "part has detached/floating geometry"
```

## Pitfalls

- **Trusting the union.** `a.union(b)` with `a` and `b` apart yields two solids,
  not a joined one. Check `len(part.solids().vals()) == 1`.
- **Constant half-width on a curved wall.** Never reuse the centre-line `b`/`a`
  for features near the ends of an ellipse, fillet, or taper — recompute the
  local width at that `x`.
- **Axis-endpoint thinking for fat angled members.** A cylinder's end-cap rim
  extends `r·sin(θ)` beyond its axis endpoint; an angled strut ending at a thin
  plate's mid-plane will breach the far face. Run it through and trim flush.
- **Per-part vs assembled view.** A floater is invisible in the assembled
  preview when it sits inside another part. Always inspect the per-part render
  (`scripts/review`).
