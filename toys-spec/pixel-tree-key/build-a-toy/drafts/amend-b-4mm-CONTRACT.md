# Pixel Tree Key

A Christmas edition of the Autonomous Key that a company gives its team. It is
one flat, solid plate a phone taps: its outline is a key, and its bow is an
8-bit pixel-art Christmas tree in matte green, with six cranberry and six gold
pixel baubles and a gold pixel star on top. The tree's trunk becomes the key's
shaft, and the bit has stepped pixel teeth. A standard NFC inlay is sealed
inside the lower tree during printing. It is a standalone desk object, not a
keychain: no ring hole, no ring.

Inventor: `wyn-seal`. Every trade-off goes to the drawing reading clearly at
arm's length and to a tap that works on the first try.

## Unique geometries

| Geometry | Count | Role |
|---|---|---|
| `key-body` | 1 | The green plate: pixel tree bow, shaft and bit; holds the sealed inlay. Focal Component |
| `star` | 1 | Gold pixel plus on top of the tree |
| `bauble` | 12 | Square colour pixel set flush into the tree's face: six cranberry, six gold |

**Focal Component: the key body.** The pixel tree is the whole drawing. It
costs the star and baubles any relief: they are flush colour bodies, level
with the green face, so the plate stays one flat 4.0 mm slab.

## Frame and coordinates

Assembly coordinates in millimetres: X across the key (+X is the bit side),
Y along it (+Y toward the star), Z up from the back face. Y 0 is the bottom
edge of the tree's widest tier; X 0 is the key's centre line. The back face
lies at Z 0 and the front face at Z 4.0.

**Display Pose:** the key lies flat on its back face, front face up, star
toward +Y. There are no moving parts. Envelope 41.4 x 82.25 x 4.0 mm
(X -20.7 to 20.7, Y -43.25 to 39.0).

Release frames the toy in the Display Pose against `#f5f0e6` from the
assembly reference's camera, straight down on the front face with the star at
the top (`render_review` camera [-90, 90]), the tree's centre at the centre of
the frame.

## Palette

| Body | Filament |
|---|---|
| `key-body` | PLA Matte "dark green" |
| `star` | PLA Lite "sunflower yellow" |
| `bauble` R1 to R6 | PLA Matte "dark red" |
| `bauble` G1 to G6 | PLA Lite "sunflower yellow" |

## Per-geometry spec

### `key-body`

A flat plate 4.0 mm thick whose outline is drawn on a pixel staircase. Every
edge of the outline runs parallel to X or Y, every side face is vertical, and
every corner is square. The plate is solid inside its outline: no hole and no
see-through gap anywhere.

**Tree (bow).** Tiers centred on X 0, from the top down, each with its Y
range and half-width:

| Tier | Y from | Y to | Half-width |
|---|---|---|---|
| neck | 32.0 | 33.0 | 1.25 |
| T1 | 30.0 | 32.0 | 3.1 |
| T2 | 25.75 | 30.0 | 4.9 |
| T3 | 23.75 | 25.75 | 6.75 |
| T4 | 17.5 | 23.75 | 8.5 |
| T5 | 15.5 | 17.5 | 10.4 |
| T6 | 13.0 | 15.5 | 12.2 |
| T7 | 10.75 | 13.0 | 13.9 |
| T8 | 8.5 | 10.75 | 15.6 |
| T9 | 6.0 | 8.5 | 17.3 |
| T10 | 3.5 | 6.0 | 18.95 |
| T11 | 0.0 | 3.5 | 20.7 |

Below the widest tier the tree steps back in toward the trunk: half-width
18.95 from Y 0 to -2.0, 17.3 from -2.0 to -4.5, and 7.5 from -4.5 to -6.5.

**Shaft.** X -4.75 to 4.75, from Y -6.5 down to Y -41.0. Its left edge
(X -4.75) is straight over its whole length.

**Bit.** On the +X side of the shaft, its right edge at each Y range:

| Y from | Y to | Right edge X |
|---|---|---|
| -25.0 | -23.0 | 7.75 |
| -28.25 | -25.0 | 10.5 |
| -29.5 | -28.25 | 7.75 |
| -31.5 | -29.5 | 5.75 |
| -33.75 | -31.5 | 10.5 |
| -36.5 | -33.75 | 12.25 |
| -39.0 | -36.5 | 7.75 |
| -41.0 | -39.0 | 5.75 |

So the bit carries two teeth, the upper one 10.5 out and the lower one
stepping out to 12.25, with a notch to X 5.75 between them. Below the shaft,
a tab X -2.0 to 3.0 runs from Y -41.0 to the key's end at Y -43.25.

**Groove.** One straight engraved groove on the front face, 1.0 wide
(X -0.5 to 0.5) and 0.6 deep (Z 3.4 to 4.0), from Y -6.0 to Y -40.0.

**Bauble recesses.** Twelve 2.0 x 2.0 recesses 1.0 deep (Z 3.0 to 4.0) in
the front face, one under each bauble, at the centres the `bauble-recesses`
Interface lists.

**Inlay pocket.** One sealed pocket for the standard 21.5 x 11.5 x 0.75 mm NFC
inlay: 22.3 x 11.9 x 1.0 mm, X -11.15 to 11.15, Y -2.5 to 9.4, Z 1.0 to 2.0,
its long axis along X, corners relieved R0.5. It is closed on every side: a
1.0 floor under it, 2.0 of plate over it (1.0 under the bauble recesses), and
at least 2.0 of plate round it in plan. Its roof is a flat bridge 11.9 mm
across. Within the pocket's outline grown by 2.0 mm all round nothing cuts
through the plate.

Print stance: back face (Z 0) on the bed.

### `star`

A pixel plus 6.0 x 6.0 x 4.0 mm, through the plate's full thickness: a bar
X -3.0 to 3.0 from Y 35.0 to 37.0, and arms X -1.0 to 1.0 from Y 33.0 to 35.0
and from Y 37.0 to 39.0. Square corners, vertical side faces, flat front and
back faces level with the body's. The bottom arm's bottom face sits on the
neck. Print stance: back face on the bed.

### `bauble`

A square tile 2.0 x 2.0 x 1.0 mm, square corners. Each sits in its recess in
the body with its top level with the body's front face (Z 3.0 to 4.0). Six
are cranberry (R1 to R6) and six gold (G1 to G6). Print stance: in place in
its recess, bottom face down.

## The inlay and the tap

The inlay is the owner's standard 21.5 x 11.5 x 0.75 mm passive NFC inlay. The
print pauses at the top of the layer at Z 2.0, the inlay is dropped flat into
the open pocket, and the print resumes and closes the pocket. Nothing holds the
inlay but the pocket: no glue and no press fit. The phone taps either face
over the lower tree; the inlay is 1.0 under the back face and 2.0 under the
front.

## Print

All 14 bodies print in one multi-colour job (an AMS-type printer), back face
down, at a 0.4 mm nozzle with 0.2 mm layers. Adjacent bodies fuse where they
touch; the star, the baubles and the body meet with zero clearance. Every
layer of the stack is at least 1.0 thick (floor, pocket, roof under a recess,
bauble), so no wall sits at the 0.8 print minimum. The plate
prints with no support: every side face is vertical, and the only ceiling is
the pocket roof, an 11.9 mm bridge.

Every point, chisel, keel and V underside ends in a flat land at least 0.8 mm
across (one print minimum at a 0.4 mm nozzle). A drawn detail under the print
minimums is enlarged to the minimum; when the enlarged detail does not fit its
spot, it is left out, and this contract names it.

No drawn detail is left out. The smallest features are the 1.0 notch step
beyond the shaft, the 1.0 x 0.6 groove, the 2.0 baubles and the recess walls,
each at or above its minimum; the material between any two bauble recesses is
at least 1.6, and between a recess and the outline at least 1.0.

## Handling

The key is held, tapped, pocketed and dropped on a desk. It weighs about
4 g. The first thing to break is the star, at its 2.5 mm neck: it is a
decorative tip that carries only its own weight. Every other section is at
least 4.0 thick and 7.5 wide. The inlay is sealed and cannot fall out.

```design-contract
{
  "schema_version": 4,
  "title": "Pixel Tree Key",
  "inventor": "wyn-seal",
  "envelope_mm": [41.4, 82.25, 4.0],
  "references": [
    {"file": "ref-01-pixel-tree-key.png", "shows": "assembly", "camera": [-90, 90]},
    {"file": "ref-02-key-body.png", "shows": "geometry:key-body", "camera": [-90, 90]},
    {"file": "ref-03-star.png", "shows": "geometry:star", "camera": [-90, 90]},
    {"file": "ref-04-bauble.png", "shows": "geometry:bauble", "camera": [-90, 90]}
  ],
  "geometries": [
    {"id": "key-body", "name": "Pixel tree key plate", "count": 1,
     "extents_mm": [41.4, 76.25, 4.0], "wall_min_mm": 0.8},
    {"id": "star", "name": "Pixel star", "count": 1,
     "extents_mm": [6.0, 6.0, 4.0], "wall_min_mm": 2.0},
    {"id": "bauble", "name": "Pixel bauble", "count": 12,
     "extents_mm": [2.0, 2.0, 1.0], "wall_min_mm": 0.8}
  ],
  "requirements": [
    {"id": "R01", "scope": "geometry:key-body",
     "text": "The bow is a pixel staircase tree, 4.0 thick, every edge parallel to X or Y and every side face vertical, tiers centred on X 0 given as Y range and half-width: neck Y 32.0-33.0 1.25; T1 30.0-32.0 3.1; T2 25.75-30.0 4.9; T3 23.75-25.75 6.75; T4 17.5-23.75 8.5; T5 15.5-17.5 10.4; T6 13.0-15.5 12.2; T7 10.75-13.0 13.9; T8 8.5-10.75 15.6; T9 6.0-8.5 17.3; T10 3.5-6.0 18.95; T11 0.0-3.5 20.7; then stepping back in below Y 0: 18.95 to Y -2.0, 17.3 to Y -4.5, 7.5 to Y -6.5."},
    {"id": "R02", "scope": "geometry:key-body",
     "text": "The shaft runs X -4.75 to 4.75 from Y -6.5 to Y -41.0 with a straight left edge; the bit on its +X side has its right edge at X 7.75 (Y -23.0 to -25.0), 10.5 (to -28.25), 7.75 (to -29.5), 5.75 (to -31.5), 10.5 (to -33.75), 12.25 (to -36.5), 7.75 (to -39.0), 5.75 (to -41.0); a tab X -2.0 to 3.0 ends the key at Y -43.25; one front groove 1.0 wide and 0.6 deep runs along X 0 from Y -6.0 to Y -40.0."},
    {"id": "R03", "scope": "geometry:key-body",
     "text": "A sealed inlay pocket 22.3 x 11.9 x 1.0, X -11.15 to 11.15, Y -2.5 to 9.4, Z 1.0 to 2.0, corners R0.5, is closed on every side with no opening to any face, its roof a flat bridge 11.9 across; nothing cuts through the plate within 2.0 of its outline in plan."},
    {"id": "R04", "scope": "geometry:key-body",
     "text": "The plate is solid matte dark green with no hole and no see-through gap, its back face one flat plane at Z 0 on the print bed and its front face one flat plane at Z 4.0 broken only by the groove and the twelve bauble recesses."},
    {"id": "R05", "scope": "geometry:star",
     "text": "The star is a gold pixel plus through the full 4.0 thickness: a bar 6.0 wide and 2.0 tall with arms 2.0 wide and 2.0 long above and below it, square corners and vertical side faces, flat back face on the print bed."},
    {"id": "R06", "scope": "geometry:bauble",
     "text": "Each bauble is a flat square tile 2.0 x 2.0 and 1.0 thick with square corners and vertical side faces; six are cranberry red and six are gold."},
    {"id": "R07", "scope": "assembly",
     "text": "In the Display Pose the key lies flat on its back face, front up, and reads as a pixel-art Christmas tree key: a stepped green tree bow with a gold plus star on top, twelve square baubles, a shaft with a groove and a two-toothed stepped bit on the +X side."},
    {"id": "R08", "scope": "assembly",
     "text": "The whole key is one solid plate 4.0 thick with no ring hole, no ring and no see-through gap; the star and the body share one flat front face at Z 4.0 and one flat back face at Z 0, and every bauble's top is level with that front face."},
    {"id": "R09", "scope": "assembly",
     "text": "The body is PLA Matte dark green, the star and baubles G1 to G6 are PLA Lite sunflower yellow and baubles R1 to R6 are PLA Matte dark red, printed as one multi-colour job back face down that pauses at Z 2.0 to receive the NFC inlay."},
    {"id": "R10", "scope": "assembly",
     "text": "The key has six red and six gold baubles, at the centres the bauble-recesses Interface lists, with no two baubles touching."}
  ],
  "interfaces": [
    {"id": "star-neck", "kind": "static", "components": ["star", "key-body"],
     "text": "The star's bottom arm (X -1.0 to 1.0, Z 0 to 4.0) stands on the body's neck at Y 33.0: the star's bottom face and the neck's top face (X -1.25 to 1.25) meet flat at Y 33.0 with zero clearance and fuse in the multi-colour print. Neither side carries a peg or socket; the star's front and back faces are level with the body's at Z 4.0 and Z 0."},
    {"id": "bauble-recesses", "kind": "static", "components": ["bauble", "key-body"],
     "text": "Each bauble sits in its own 2.0 x 2.0 recess, 1.0 deep (Z 3.0 to 4.0), cut into the body's front face, with zero clearance, its top level with the front face. Recess and bauble centres (X, Y): R1 (0.5, 19.2), R2 (-5.5, 15.25), R3 (5.5, 15.25), R4 (4.25, 4.0), R5 (14.5, 3.5), R6 (-0.75, -0.25) carry the cranberry baubles; G1 (-1.9, 22.85), G2 (1.25, 11.25), G3 (8.75, 8.0), G4 (-5.0, 7.25), G5 (-13.5, 4.5), G6 (10.25, 0.0) carry the gold ones. Bauble n is instance bauble#n with n 1 to 6 for R1 to R6 and 7 to 12 for G1 to G6."}
  ]
}
```
