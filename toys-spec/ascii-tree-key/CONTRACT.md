# ASCII Tree Key

A Christmas edition of the Autonomous Key that a company gives its team. It is
one flat, solid plate a phone taps: its outline is a key, and its bow is a
small graphite terminal window in the 5:4 proportions of a terminal app icon. A title bar carries three round dots in
cranberry, gold and green, and a black screen shows a Christmas tree typed in
asterisks: four rows of 1, 2, 3 and 4 identical `*`, the top one gold and the
rest green, centred on the screen. A cream layer runs round the bow's edge
between two graphite layers. A slim graphite shaft ends in a three-toothed
stepped bit. A standard NFC inlay is sealed inside the bow during printing. It
is a standalone desk object, not a keychain: no ring hole, no ring.

Inventor: `wyn-seal`. Every trade-off goes to the drawing reading clearly at
arm's length and to a tap that works on the first try.

## Unique geometries

| Geometry | Count | Role |
|---|---|---|
| `base` | 1 | Graphite bottom layer of the bow, the shaft and the bit; holds the sealed inlay |
| `stripe` | 1 | Cream layer the size of the bow; its edge is the cream stripe, and it roofs the inlay pocket |
| `frame` | 1 | Graphite top layer of the bow: the window border and the title bar, with three dot holes |
| `screen` | 1 | Black screen panel in the window, with ten asterisk holes. Focal Component |
| `glyph` | 10 | Typed asterisk set flush in the screen: one gold, nine green |
| `dot` | 3 | Round title-bar dot set flush in the frame: cranberry, gold, green |

**Focal Component: the screen.** The asterisk tree on the black screen is the
whole drawing. It costs the window any sunken step: the screen, the glyphs,
the frame and the dots all end at one flat front face, so the plate stays one
flat 4.0 mm slab and every colour body is at least five layers deep.

## Frame and coordinates

Assembly coordinates in millimetres: X across the key (+X is the bit side),
Y along it (+Y toward the title bar), Z up from the back face. Y 0 is the
bow's bottom edge; X 0 is the key's centre line. The back face lies at Z 0
and the front face at Z 4.0.

**Display Pose:** the key lies flat on its back face, front face up, title bar
toward +Y. There are no moving parts. Envelope 38.0 x 70.6 x 4.0 mm
(X -19.0 to 19.0, Y -40.2 to 30.4, Z 0 to 4.0).

Release frames the toy in the Display Pose against `#f5f0e6` from the
assembly reference's camera, straight down on the front face with the title
bar at the top (`render_review` camera [-90, 90]), the screen's centre near
the centre of the frame.

## Layers

| Z from | Z to | In the bow | In the shaft and bit |
|---|---|---|---|
| 0 | 1.0 | `base` floor | `base` |
| 1.0 | 2.0 | `base`, round the inlay pocket | `base` |
| 2.0 | 3.0 | `stripe` | `base` |
| 3.0 | 4.0 | `frame`, `screen`, `glyph`, `dot` | `base` |

## Palette

| Body | Filament |
|---|---|
| `base`, `frame` | PLA Matte "nardo gray" (graphite) |
| `stripe` | PLA Matte "desert tan" (cream) |
| `screen` | PLA Matte "charcoal" (black) |
| `glyph#1` (top), `dot#2` | PLA Lite "sunflower yellow" (gold) |
| `glyph#2` to `glyph#10`, `dot#3` | PLA Matte "grass green" |
| `dot#1` | PLA Matte "dark red" (cranberry) |

## Per-geometry spec

### `base`

**Bow plate.** A rounded rectangle X -19.0 to 19.0, Y 0 to 30.4, corners
R3.5, from Z 0 to Z 2.0. Its top face at Z 2.0 is flat except for the inlay
pocket.

**Inlay pocket.** One pocket for the standard 21.5 x 11.5 x 0.75 mm NFC
inlay: 22.3 x 11.9 x 1.0 mm, X -11.15 to 11.15, Y 8.35 to 20.25, Z 1.0 to
2.0, its long axis along X, corners R0.5. It is open only at its top, at
Z 2.0, where the stripe closes it. A 1.0 floor lies under it and at least 7.8
of plate round it in plan.

**Shaft.** X -3.0 to 3.0, from the bow's bottom edge at Y 0 down to the key's
end, from Z 0 to Z 4.0. Where it meets the bow's bottom edge, a R1.5 fillet
on each side, full height. Its left edge (X -3.0) is straight down to the
end. The end is a half round R3.0 centred at (0, -37.2), so the key ends at
Y -40.2.

**Bit.** On the +X side of the shaft, Z 0 to 4.0, its right edge at each Y
range:

| Y from | Y to | Right edge X |
|---|---|---|
| -17.0 | -22.5 | 8.9 |
| -22.5 | -23.6 | 5.6 |
| -23.6 | -28.4 | 11.5 |
| -28.4 | -30.6 | 7.2 |
| -30.6 | -35.6 | 10.8 |

So the bit carries three teeth, 8.9, 11.5 and 10.8 out, with notches to
X 5.6 and X 7.2 between them. Each tooth's two outer corners are rounded
R0.8; inner corners are square. Below Y -35.6 the right edge returns to the
shaft (X 3.0).

Every side face is vertical. The base is solid: no hole and no see-through
gap. Print stance: back face (Z 0) on the bed.

### `stripe`

A flat cream slab with the bow's outline, X -19.0 to 19.0, Y 0 to 30.4,
corners R3.5, from Z 2.0 to Z 3.0. Its bottom face lies on the base's bow
plate and is the pocket's roof, a flat bridge 11.9 across. Its edge shows all
round the bow as a 1.0 cream stripe between the graphite layers. Print
stance: bottom face (Z 2.0) down.

### `frame`

A flat graphite layer with the bow's outline (X -19.0 to 19.0, Y 0 to 30.4,
corners R3.5), from Z 3.0 to Z 4.0, with a window cut through it:
X -17.0 to 17.0, Y 3.3 to 25.3, corners R1.2. So the border is 2.0 at each
side and 3.3 at the bottom, and the title bar above the window is 5.1 tall.
Three round holes Ø2.0 go through the title bar, centred at Y 27.9 and
X -14.5, -10.6 and -6.7. The window border is flat and level with the
screen: it has no raised lip and no bevel, and the screen is not sunk below
it. Print stance: bottom face (Z 3.0) down.

### `screen`

A flat black panel filling the frame's window (X -17.0 to 17.0, Y 3.3 to
25.3, corners R1.2), from Z 3.0 to Z 4.0, with ten asterisk-shaped holes cut
through it, one under each glyph, each the glyph's own outline. Print stance:
bottom face (Z 3.0) down.

### `glyph`

A typed asterisk, 1.0 thick (Z 3.0 to 4.0): six straight spokes 0.9 wide,
each from the centre out to 2.0, at 90, 30, -30, -90, -150 and 150 degrees
from +X, so one spoke points straight up and one straight down and the other
four lean 30 degrees off horizontal. Each spoke ends square, in a flat land
0.9 across. The six inside corners between neighbouring spokes are rounded
R0.5, so the screen between two spokes ends in a round tip 1.0 across rather
than a knife point. Extents 3.91 x 4.0 x 1.0. It is a plain font asterisk: no
branches, no barbs, no star points. Print stance: bottom face (Z 3.0) down.

The ten glyphs form the tree, centred on the screen at (0, 14.3). Each row is
offset half a step from the next, like a stack of balls; within a row the
centres are 5.8 apart, and the rows are 4.8 apart:

| Row | Y | Glyph centres X | Colour |
|---|---|---|---|
| 1 | 21.5 | 0 | gold (`glyph#1`) |
| 2 | 16.7 | -2.9, 2.9 | green (`glyph#2`, `#3`) |
| 3 | 11.9 | -5.8, 0, 5.8 | green (`glyph#4` to `#6`) |
| 4 | 7.1 | -8.7, -2.9, 2.9, 8.7 | green (`glyph#7` to `#10`) |

All ten glyphs are the same size and shape; the top one differs only in
colour.

### `dot`

A round disc Ø2.0 x 1.0 (Z 3.0 to 4.0) in its hole in the title bar:
`dot#1` cranberry at X -14.5, `dot#2` gold at X -10.6, `dot#3` green at
X -6.7, each at Y 27.9. Print stance: bottom face (Z 3.0) down.

## The inlay and the tap

The inlay is the owner's standard 21.5 x 11.5 x 0.75 mm passive NFC inlay. The
print pauses at the top of the layer at Z 2.0, the inlay is dropped flat into
the open pocket, and the print resumes with the cream stripe, which closes the
pocket. Nothing holds the inlay but the pocket: no glue and no press fit. The
phone taps either face over the screen; the inlay is 1.0 under the back face
and 2.0 under the front. Within the pocket's outline grown by 2.0 mm all round
nothing cuts through the plate: the glyph holes in the screen are filled by
the glyphs, and the stripe below them is whole.

## Print

All 17 bodies print in one six-colour job (two AMS-type units), back face
down, at a 0.4 mm nozzle with 0.2 mm layers. Adjacent bodies fuse where they
touch, with zero clearance. Every body lies on the bed or on a body printed
before it, so nothing overhangs: every side face is vertical, and the only
ceiling is the pocket roof, an 11.9 mm bridge in the stripe.

Every point, chisel, keel and V underside ends in a flat land at least 0.8 mm
across (one print minimum at a 0.4 mm nozzle). A drawn detail under the print
minimums is enlarged to the minimum; when the enlarged detail does not fit its
spot, it is left out, and this contract names it.

The images' sunken screen step is left out: the screen is flush with the
frame (the frame's row names it), because a 4.0 mm plate holds the floor, the
pocket, the stripe and a 1.0 top layer and nothing more. No other drawn detail
is left out. The smallest features are the glyph spokes, 0.9 wide; the Ø2.0
dots; the 1.1 tall first notch in the bit; and the webs: at least 1.7 between
two glyph holes, 1.8 from a glyph hole to the window's edge, 1.9 between two
dot holes, 1.6 from a dot hole to the window and 1.5 from a dot hole to the
outline. Each is at or above its
minimum. Every body is at least 1.0 thick. The glyphs' R0.5 inside corners
give the screen a round tip between every two spokes, never a knife point.

## Handling

The key is held, tapped, pocketed and dropped on a desk. It weighs about
7 g. The thinnest load-bearing section is the shaft, 6.0 wide and 4.0 thick;
where it meets the bow, its full-height fillets carry it into the bow plate
and the fused layers above. The bit's teeth are 4.0 thick and at least 4.8
tall; the notches are 1.1 and 2.2 tall. The inlay is sealed and cannot fall out.

```design-contract
{
  "schema_version": 4,
  "title": "ASCII Tree Key",
  "inventor": "wyn-seal",
  "envelope_mm": [38.0, 70.6, 4.0],
  "references": [
    {"file": "ref-01-ascii-tree-key.png", "shows": "assembly", "camera": [-90, 90]},
    {"file": "ref-02-base.png", "shows": "geometry:base", "camera": [-90, 90]},
    {"file": "ref-03-stripe.png", "shows": "geometry:stripe", "camera": [-90, 90]},
    {"file": "ref-04-frame.png", "shows": "geometry:frame", "camera": [-90, 90]},
    {"file": "ref-05-screen.png", "shows": "geometry:screen", "camera": [-90, 90]},
    {"file": "ref-06-glyph.png", "shows": "geometry:glyph", "camera": [-90, 90]},
    {"file": "ref-07-dot.png", "shows": "geometry:dot", "camera": [-90, 90]}
  ],
  "geometries": [
    {"id": "base", "name": "Graphite base: bow plate, shaft and bit", "count": 1,
     "extents_mm": [38.0, 70.6, 4.0], "wall_min_mm": 1.0},
    {"id": "stripe", "name": "Cream stripe layer", "count": 1,
     "extents_mm": [38.0, 30.4, 1.0], "wall_min_mm": 1.0},
    {"id": "frame", "name": "Graphite window frame and title bar", "count": 1,
     "extents_mm": [38.0, 30.4, 1.0], "wall_min_mm": 1.0},
    {"id": "screen", "name": "Black screen panel", "count": 1,
     "extents_mm": [34.0, 22.0, 1.0], "wall_min_mm": 1.0},
    {"id": "glyph", "name": "Typed asterisk", "count": 10,
     "extents_mm": [3.91, 4.0, 1.0], "wall_min_mm": 0.9},
    {"id": "dot", "name": "Title-bar dot", "count": 3,
     "extents_mm": [2.0, 2.0, 1.0], "wall_min_mm": 1.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "geometry:base",
     "text": "The bow plate is a rounded rectangle X -19.0 to 19.0, Y 0 to 30.4, corners R3.5, Z 0 to 2.0, its top face flat at Z 2.0 but for the inlay pocket; the shaft and bit stand the full Z 0 to 4.0, every side face vertical, and the base has no hole and no see-through gap, its back face one flat plane at Z 0 on the print bed."},
    {"id": "R02", "scope": "geometry:base",
     "text": "The shaft runs X -3.0 to 3.0 down from the bow's bottom edge at Y 0, with a full-height R1.5 fillet each side where it meets the bow, a straight left edge, and a half-round R3.0 end centred at (0, -37.2) ending the key at Y -40.2; the bit on its +X side has its right edge at X 8.9 (Y -17.0 to -22.5), 5.6 (to -23.6), 11.5 (to -28.4), 7.2 (to -30.6) and 10.8 (to -35.6): three teeth with R0.8 outer corners and square notches."},
    {"id": "R03", "scope": "geometry:base",
     "text": "One inlay pocket 22.3 x 11.9 x 1.0, X -11.15 to 11.15, Y 8.35 to 20.25, Z 1.0 to 2.0, corners R0.5, open only at its top face at Z 2.0, with a 1.0 floor under it; nothing else is cut into the bow plate."},
    {"id": "R04", "scope": "geometry:stripe",
     "text": "The stripe is one flat cream slab Z 2.0 to 3.0 with the bow's outline, X -19.0 to 19.0, Y 0 to 30.4, corners R3.5, with no hole and nothing on either face; its bottom face roofs the inlay pocket as a flat 11.9 bridge."},
    {"id": "R05", "scope": "geometry:frame",
     "text": "The frame is a flat graphite layer Z 3.0 to 4.0 with the bow's outline (X -19.0 to 19.0, Y 0 to 30.4, corners R3.5) and a window cut through it at X -17.0 to 17.0, Y 3.3 to 25.3, corners R1.2, so its border is 2.0 at each side, 3.3 at the bottom and 5.1 at the title bar; three round holes of diameter 2.0 go through the title bar at Y 27.9 and X -14.5, -10.6 and -6.7."},
    {"id": "R06", "scope": "geometry:frame",
     "text": "The frame's front face is one flat plane at Z 4.0 with no raised lip and no bevel round the window: the screen is flush with it, not sunk, and the images' sunken screen step is left out."},
    {"id": "R07", "scope": "geometry:screen",
     "text": "The screen is a flat black panel Z 3.0 to 4.0 filling the window, X -17.0 to 17.0, Y 3.3 to 25.3, corners R1.2, with exactly ten asterisk-shaped holes through it, each the glyph's outline, centred at (0, 21.5); (-2.9, 16.7), (2.9, 16.7); (-5.8, 11.9), (0, 11.9), (5.8, 11.9); (-8.7, 7.1), (-2.9, 7.1), (2.9, 7.1), (8.7, 7.1): a 1-2-3-4 tree centred on the screen at (0, 14.3)."},
    {"id": "R08", "scope": "geometry:glyph",
     "text": "Each glyph is a flat typed asterisk 1.0 thick: six straight spokes 0.9 wide from the centre out to 2.0, at 90, 30, -30, -90, -150 and 150 degrees from +X (one straight up, one straight down, four leaning 30 degrees off horizontal), each ending square in a flat 0.9 land, the six inside corners between spokes rounded R0.5; extents 3.91 x 4.0; no branches, barbs or star points, never a snowflake."},
    {"id": "R09", "scope": "geometry:glyph",
     "text": "All ten glyphs have the same size and shape; glyph#1, the top of the tree, is gold and glyph#2 to glyph#10 are green."},
    {"id": "R10", "scope": "geometry:dot",
     "text": "Each dot is a flat round disc of diameter 2.0 and 1.0 thick (Z 3.0 to 4.0); dot#1 is cranberry, dot#2 gold and dot#3 green."},
    {"id": "R11", "scope": "assembly",
     "text": "In the Display Pose the key lies flat on its back face, front up, and reads as a terminal-window key: a 5:4 graphite window with a title bar and three dots (cranberry, gold, green from the left), a black screen with a typed-asterisk Christmas tree of 1, 2, 3 and 4 asterisks centred on it, the top one gold, a slim shaft and a three-toothed stepped bit on the +X side."},
    {"id": "R12", "scope": "assembly",
     "text": "The whole key is one solid plate 4.0 thick with no ring hole, no ring and no see-through gap: the base's back face is the only face at Z 0, and the shaft and bit, the frame, the screen, the glyphs and the dots share one flat front face at Z 4.0."},
    {"id": "R13", "scope": "assembly",
     "text": "Seen from the side, the bow's edge shows three layers all round: graphite Z 0 to 2.0, a cream stripe Z 2.0 to 3.0 and graphite Z 3.0 to 4.0; the shaft and bit edges are graphite only."},
    {"id": "R14", "scope": "assembly",
     "text": "The base and frame are PLA Matte nardo gray, the stripe PLA Matte desert tan, the screen PLA Matte charcoal, glyph#1 and dot#2 PLA Lite sunflower yellow, glyph#2 to glyph#10 and dot#3 PLA Matte grass green, and dot#1 PLA Matte dark red, printed as one multi-colour job back face down that pauses at Z 2.0 to receive the NFC inlay."}
  ],
  "interfaces": [
    {"id": "pocket-roof", "kind": "static", "components": ["base", "stripe"],
     "text": "The stripe's bottom face lies flat on the base's bow plate top face at Z 2.0 over the whole bow outline (X -19.0 to 19.0, Y 0 to 30.4, corners R3.5) with zero clearance and fuses in the multi-colour print, closing the base's open-topped inlay pocket (X -11.15 to 11.15, Y 8.35 to 20.25). The stripe's edge at Y 0 meets the shaft's end face (X -3.0 to 3.0) and its fillets. Neither side carries a peg or socket."},
    {"id": "top-layer", "kind": "static", "components": ["stripe", "frame", "screen"],
     "text": "The frame and the screen both lie flat on the stripe's top face at Z 3.0 with zero clearance. The screen fills the frame's window exactly (X -17.0 to 17.0, Y 3.3 to 25.3, corners R1.2): the window's side faces and the screen's side faces meet with zero clearance, and both top faces are level at Z 4.0. No pegs, sockets or lips on any side."},
    {"id": "frame-shaft", "kind": "static", "components": ["base", "frame"],
     "text": "The frame's bottom border edge at Y 0 meets the base shaft's end face and fillets with zero clearance from Z 3.0 to 4.0, and the frame's front face is level with the shaft's at Z 4.0. The base carries no feature for it."},
    {"id": "glyph-holes", "kind": "static", "components": ["glyph", "screen", "stripe"],
     "text": "Each glyph fills its own asterisk-shaped hole through the screen with zero clearance, its bottom face on the stripe's top face at Z 3.0 and its top level with the screen's at Z 4.0. Glyph centres (X, Y): glyph#1 (0, 21.5); glyph#2 (-2.9, 16.7), glyph#3 (2.9, 16.7); glyph#4 (-5.8, 11.9), glyph#5 (0, 11.9), glyph#6 (5.8, 11.9); glyph#7 (-8.7, 7.1), glyph#8 (-2.9, 7.1), glyph#9 (2.9, 7.1), glyph#10 (8.7, 7.1). The stripe carries no feature for them."},
    {"id": "dot-holes", "kind": "static", "components": ["dot", "frame", "stripe"],
     "text": "Each dot fills its own diameter 2.0 hole through the frame's title bar with zero clearance, its bottom face on the stripe's top face at Z 3.0 and its top level with the frame's at Z 4.0: dot#1 at (-14.5, 27.9), dot#2 at (-10.6, 27.9), dot#3 at (-6.7, 27.9). The stripe carries no feature for them."}
  ]
}
```
