# CadQuery modeling cheat-sheet

Load this when writing or editing a CadQuery `.py` file.

## File shape

```python
"""One-line description of what this part is."""

import cadquery as cq

# --- Parameters (named, mm) ---
PLATE_L = 50
PLATE_W = 30
PLATE_H = 5

# --- Model ---
def gen_step():
    return (
        cq.Workplane("XY")
        .box(PLATE_L, PLATE_W, PLATE_H)
    )
```

`gen_step()` is the contract — the runner calls this function at module scope.
(A trivial single-file script may instead assign a module-level `result`; both
are accepted, but `gen_step()` is preferred.)

## Primitives

```python
cq.Workplane("XY").box(L, W, H)               # rectangular block
cq.Workplane("XY").cylinder(height=H, radius=R)
cq.Workplane("XY").sphere(R)
cq.Workplane("XY").circle(R).extrude(H)        # extruded disk
cq.Workplane("XY").rect(W, L).extrude(H)       # extruded rectangle
```

## Selecting faces / edges

CadQuery uses **string selectors** to grab faces and edges:

- `.faces(">Z")` — single face with the largest Z (top of a box).
- `.faces("<Z")` — bottom face.
- `.faces(">Z[1]")` — second-from-top in Z. Useful when the obvious face has
  been cut away.
- `.edges("|Z")` — all edges parallel to Z (the vertical edges of a box).
- `.edges(">Z")` — top-edge ring.
- `.edges(">Z and |X")` — combinable.
- `.edges("%CIRCLE")` — circular edges only (hole rims, fillet curves).
- `.edges("not %CIRCLE")` — exclude curves; useful when filleting only the
  rectilinear perimeter.

Then `.workplane()` puts you in a 2D drawing plane on that face.

### Selector hygiene

The selector you pick determines whether your code keeps working as the
design evolves. Prefer **stable directional/topological selectors** over
**positional indexing** — the latter breaks the moment any prior operation
adds or reorders faces.

| Prefer | Avoid | Why |
|---|---|---|
| `.faces(">Z")` | `.faces().item(3)` | Index reshuffles after every boolean |
| `.edges("|Z")` | `.edges().vals()[5:9]` | Indexes are an implementation detail |
| `.edges("%CIRCLE")` | filter-by-hand after `.edges().vals()` | Selector is one chain |
| `.faces(">Z[-2]")` | counting from `>Z` after adding bosses | Negative index from the *original* top |

After a `.cut()` that removes the face you wanted, the previous selector
will pick the *new* matching face — which may not be what you meant. If a
selector starts breaking after edits, the fix is almost always tightening
the selector, not chasing the index.

## Holes

```python
.faces(">Z").workplane().hole(3.4)             # straight clearance hole, infinite depth
.faces(">Z").workplane().cboreHole(3.4, 6.5, 3.5)  # counter-bored for an M3 cap-head screw
.faces(">Z").workplane().cskHole(3.4, 6.5, 90) # countersunk for a flathead screw
```

Place hole centers with `.pushPoints([(x1,y1), (x2,y2)])` or
`.rarray(x_spacing, y_spacing, n_x, n_y)` *before* calling `.hole(...)`.

## Fillets and chamfers

```python
.edges(">Z").fillet(1.0)                       # round all top edges
.edges("|Z").chamfer(0.5)                       # chamfer all vertical edges
.faces(">Z").edges("not %CIRCLE").fillet(2.0)   # top perimeter only (skip hole rims)
```

### Fillet-last + filter-always rule

Fillets are the #1 cause of CadQuery failures. Three rules make them safe:

1. **Apply fillets and chamfers LAST.** Build all primitive geometry, all
   booleans, all features first. Then fillet. Filleting early causes later
   booleans to crash on the rounded edges, and selectors that worked before
   the fillet stop matching after.
2. **Never `.edges().fillet(r)` without a filter.** Unfiltered selects
   every edge in the part, including tiny ones from prior booleans —
   the smallest one will throw `OCP.StdFail_NotDone` and abort the operation.
   Always narrow first: `.edges(">Z")`, `.edges("|Z and >X")`, `.edges("not %CIRCLE")`.
3. **Keep `r ≤ wall_thickness / 2` and `r ≤ min_adjacent_feature / 2`.**
   A 3 mm fillet on a 2 mm wall fails. A 5 mm fillet next to a 4 mm hole
   fails. When in doubt, halve the radius.

If a fillet fails: (a) lower the radius first, (b) narrow the selector
second, (c) replace with `.chamfer(r)` third — chamfers are far more
forgiving on awkward geometry.

## Patterns and arrays

```python
# 4x3 grid of M3 holes, 20mm pitch
.faces(">Z").workplane().rarray(20, 20, 4, 3).hole(3.4)

# Specific points
.faces(">Z").workplane().pushPoints([(-10, 0), (10, 0)]).hole(3.4)

# Radial pattern (n holes on a circle of radius R)
.faces(">Z").workplane().polarArray(R, 0, 360, n).hole(3.4)
```

## Polygons (hex etc.)

```python
.polygon(6, diameter, circumscribed=False)     # flat-to-flat = diameter (apothem*2)
.polygon(6, diameter, circumscribed=True)      # vertex-to-vertex = diameter
```

**For hex grids**: pick `circumscribed=False` and use the user's "flat-to-flat"
spec as the diameter. The vertex-to-vertex distance is then
`diameter / cos(30°)` ≈ `1.1547 * diameter`. Spacing for the **rectangular
(non-staggered) grid** (simpler, fine for hobbyist trays):

```python
import math

HEX_FLAT = 20            # what the user said: flat-to-flat
WALL = 2
HEX_VERTEX = HEX_FLAT / math.cos(math.radians(30))     # ≈ 23.094 mm

COL_SPACING = HEX_FLAT + WALL                          # horizontal between centers
ROW_SPACING = HEX_VERTEX + WALL                        # vertical between centers
```

**True honeycomb (staggered) packing.** Only when the user explicitly asks
for it. Three formulas you need, in pointy-top orientation:

```python
import math

HEX_FLAT = 20
WALL = 2
R = HEX_FLAT / math.sqrt(3)                            # circumradius

COL_SPACING = HEX_FLAT + WALL                          # within-row, between centers
ROW_SPACING = 1.5 * R + WALL * math.sin(math.radians(60))   # between rows
ROW_OFFSET  = COL_SPACING / 2                          # half-column shift on odd rows

# Then place hex centers like:
#   for row in range(ROWS):
#       stagger = (row % 2) * ROW_OFFSET
#       for col in range(COLS):
#           cx = col * COL_SPACING + stagger
#           cy = row * ROW_SPACING
```

Without ``ROW_OFFSET`` the rows won't interlock — you'll get a
rectangular-with-extra-vertical-gap grid, not honeycomb.

## Boolean ops

```python
a = cq.Workplane("XY").box(10, 10, 10)
b = cq.Workplane("XY").box(5, 5, 20)
a.union(b)                                     # combine
a.cut(b)                                       # subtract
a.intersect(b)                                 # keep overlap
```

**Always run `result.val().isValid()` after a complex boolean** — broken
booleans produce non-manifold geometry that won't slice.

### Named cutter objects (for any non-trivial subtraction)

Inline `.cut(thing).cut(thing).cut(thing)` chains rot fast: when one fails
you can't tell which, when you want to tweak one you re-derive the others,
and selectors after the chain depend on cumulative state.

For anything beyond one `.hole()`, define each cutter as a named variable
in its own helper, then subtract the list:

```python
# Bad — inline, opaque, hard to debug
body = (
    body
    .cut(usb_box.translate((L/2, 0, USB_Z)))
    .cut(hdmi_box.translate((L/2, OFF, HDMI_Z)))
    .cut(button_cyl.translate((-L/2, 0, BTN_Z)))
)

# Good — named cutters, one per feature
def usb_c_cutter(p):
    return (
        cq.Workplane("YZ")
        .rect(p.usb_w, p.usb_h)
        .extrude(p.wall + 1)            # +1 so it pierces cleanly
        .translate((p.length / 2 - 0.5, 0, p.usb_z))
    )

def hdmi_cutter(p): ...
def button_cutter(p): ...

def add_port_cutouts(body, p):
    for cutter in (usb_c_cutter(p), hdmi_cutter(p), button_cutter(p)):
        body = body.cut(cutter)
    return body
```

Three reasons this pays for itself:

1. **Each cutter is renderable on its own** — drop a `result = usb_c_cutter(p)`
   line, run `scripts/cad`, see the bare cutter shape. Catches sizing bugs
   instantly.
2. **Errors point at the right cutter.** A `cutThruAll` failure that mentions
   "hdmi_cutter" beats one that says "line 87".
3. **Future edits stay local.** Adjusting the USB port doesn't risk breaking
   the HDMI cutout.

**Make cutters slightly oversized along the cut axis** (typically +0.5 to
+1 mm) so they pierce cleanly without coplanar-face artifacts.

## Lofts and sweeps (tapered / curved bodies)

```python
# Tapered cylinder (vase body)
result = (
    cq.Workplane("XY")
    .circle(R_BASE)
    .workplane(offset=H)
    .circle(R_TOP)
    .loft(combine=True)
)
```

For a hollow tapered shell, loft the outer and inner separately and `.cut()`
the inner from the outer:

```python
outer = cq.Workplane("XY").circle(R_BASE).workplane(offset=H).circle(R_TOP).loft()
inner = cq.Workplane("XY").workplane(offset=WALL).circle(R_BASE - WALL).workplane(offset=H - WALL).circle(R_TOP - WALL).loft()
vase = outer.cut(inner)
```

## Rotations and translations

```python
.rotate((0,0,0), (0,0,1), 15)                  # rotate 15° about Z axis through origin
.translate((10, 0, 0))                          # move +10 in X
```

For tilted mounts, rotate the part *before* unioning it with the static base.

## Common pitfalls

1. **Vertical cylinders cutting a tapered surface get deeper toward the
   thin end.** Don't cut flutes on a vase with a plain vertical cylinder —
   it will break through the wall near the top. Instead loft a tapered
   cutter or sweep a circle along a slanted path that hugs the outer wall.

2. **Hex orientation matters.** `polygon(6, d, circumscribed=False)` makes a
   hex with flat sides on top/bottom (vertex on left/right). If the user
   says "20mm flat-to-flat", that's the *vertical* distance — the *horizontal*
   span is `20 / cos(30°) ≈ 23.1mm`. Pack accordingly.

3. **`cutThruAll()` only works on a workplane that's facing the right way.**
   If the hole isn't going all the way through, you probably forgot
   `.faces(">Z").workplane()` before `.hole(...)`, or you used
   `.cutBlind(-depth)` with too small a depth.

4. **Fillets fail silently sometimes.** If `.edges(...).fillet(R)` raises
   `OCP.StdFail_NotDone`, the radius is too big for the local geometry.
   Halve it and re-render.

5. **Direction of mounting holes.** Wall-mount holes go through whichever
   face faces the wall. CadQuery has no built-in "forward" — it depends on
   how you placed the part. Pick the workplane by the normal direction
   you chose during construction: if your backplate is a box with the
   wall-side at +Y, the right selector is `.faces(">Y").workplane()`. If at
   -Y, use `.faces("<Y")`. The wrong choice puts the holes on the wrong
   face; the render will show the holes pointing at the user rather than
   into the wall.

6. **Single-piece vs multi-part: pick the right container.** For a part
   that prints as **one solid** (no separable pieces), `.union()` everything
   into a single `result` — slicers and downstream tools love a single
   manifold. For a design that has **physically separate parts** (lid +
   base, hinge halves, robot chassis + wheels, PCB + enclosure), use
   `cq.Assembly` so each part exports as its own STL and the user can
   print/orient them independently. See `references/assembly.md`. Avoid
   raw `cq.Compound` — it's neither.
