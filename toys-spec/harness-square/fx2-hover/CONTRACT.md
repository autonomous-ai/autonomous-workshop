# Harness Square Hover Dock

Inventor: Rowan Vale. Square-screen shell for the Harness device in place of the round disc. The device is a thin charcoal tile with a 3.95 inch 720x720 touch panel. On the desk it sits on a soft white wedge at 22 degrees and appears to float. It lifts off for two-handed use and drops back onto a hidden boss. There is no battery. The device runs from a USB-C cable plugged into the tile's top edge. No buttons. No moving parts.

Focal Component: the tile face, meaning the cover glass and its thin rim. The cost is a plain base and a 15.5 mm tile, thicker than a phone. The board stack sets that thickness and the base gives it no visual help.

## Hardware this shell is built around (from the supplied spec, schematic and STEP)

- **Panel** TXW395039B0-HYE: cover glass 84.37 x 84.37 x 1.8 mm with a printed black border (2.5D edge). LCM 74.93 x 78.98 mm sits behind it. Total stack 3.23 mm, plus 0.175 mm 3M 300LSE tape. Active area 71.93 mm. The 30-pin FPC leaves one glass edge and folds behind the panel.
- **Board** PCB_Harness_pro_v1: 80.0 x 40.0 x 1.2 mm. In the STEP file the board is tilted 30 degrees, which is why its bounding box reads 80.7 x 35.2 x 22.3. Positions below are in board coordinates: u along the 80 mm length, v along the 40 mm width, origin at the board centre.
  - Side A (2.1 mm tall parts) carries the LCD FPC connector, two top-port MEMS mics at (-37.5, 13.0) and (37.5, 13.0), the WS2812 LED, the TF socket, and the two tactile switches SW1 and SW3 at (-37.1, -14.0) and (37.2, -14.0).
  - Side B carries the 35.0 x 35.0 x 3.72 mm WT01P4C5-S1 module, centred, and the 2-pin speaker connector.
  - The mid-mount USB-C sits at the -u end, centred v = 4.0, with its face 0.7 mm beyond the board edge.
  - Four M2 holes of 2.2 mm diameter sit at (-33.0, -18.0), (33.0, -18.0), (-24.0, 14.0) and (24.0, 14.0).
  - Stack: side A 2.1 + board 1.2 + module 3.72 = 7.02 mm.
- **Switches.** Both switches stay sealed inside with no opening. SW1 (BOOT) is not needed because the CH343P auto-program circuit flashes over USB. SW3 (IP5306 key) is not needed because the board starts on USB power.
- **Not on the board:** the speaker is a purchased 20 mm round, 4.5 mm thick, 8 ohm 1 W unit wired to the board's connector. The vibration motor and battery are not fitted.

## Shared rules

- Front means the glass side. Coordinates on the tile are seen from the front, with origin at the tile centre, x to the right and y up the slope.
- Assembly frame (Display Pose): X to the right of a person facing the screen, Y away from that person, Z up, origin at the centre of the base's front bottom edge. The tile's x runs along X. Reference cameras use `render_review`'s convention: AZ -90 looks from the front, 0 from +X, 90 from the back; EL 90 looks straight down.
- The glass sits flush with the rim on all four edges. No raised lip anywhere around the screen, because swipes run across the edges.
- No button, switch or dial is visible. The only openings are the USB-C port, two microphone holes and the speaker grille.
- Finish in the references: matte charcoal tile, warm white base. The top 4.0 mm of the base walls is printed in translucent lilac by a filament change. It is not lit, because the base has no power.
- Structural walls are 2.0 mm, except the tile's 1.0 mm recess floor, its 1.0 mm wall behind the USB-C counterbore and its 1.5 mm glass ledge. Nothing load-bearing is under 3 mm.

## Print

Print with a 0.4 mm nozzle and no supports. The bed faces are: tile-housing on its back face, dock-base on its bottom face, pad-arc on its groove-side face.

Every point, chisel, keel and V underside ends in a flat land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle).

A drawn detail under the print minimums is enlarged to the minimum; when the enlarged detail does not fit its spot, it is left out, and this contract names it.

No detail is left out. The smallest details are the 1.0 mm mic holes, the 1.6 mm grille holes and the 1.0 mm deep pad grooves; all of them are above the minimums.

## Geometry

### tile-housing (1)
An open-front tub, 91.0 x 91.0 x 15.5 mm, with 5.0 mm plan corner radii, a 0.6 mm round on the front edge and a 1.0 mm chamfer on the back edge.

- **Glass pocket:** 85.0 x 85.0 x 3.4 mm, centred, so the rim is 3.0 mm all round. It steps down to a ledge 2.5 mm wide and 1.5 mm thick with an 80.0 x 80.0 mm opening, so the LCM passes through and the glass rests on the tape.
- **Cavity behind the ledge:** 85.0 x 85.0 mm. Back wall 2.0 mm.
- **Board.** It is screwed through its four holes with M2 x 4 self-tappers into four bosses of 5.0 mm diameter with 1.6 mm pilots, rising 4.68 mm from the back wall's inner face.
  - The board stands vertical, side A toward the back, USB-C end up. Its centre is at (22.0, 1.8). Board u maps to -y and v maps to x - 22.0.
  - Bosses sit at (4.0, 34.8), (4.0, -31.2), (36.0, 25.8) and (36.0, -22.2).
- **Through-thickness layout from the back face:** back wall 2.0, 0.58 clear, side-A parts from 4.58, board side-A face at 6.68, board to 7.88, module to 11.6, then 0.5 clear to the LCM.
- **USB-C:** a 9.4 x 3.6 mm opening with 1.2 mm corner radii in the top wall, centred at x = +26.0 and 6.7 mm from the back face. The receptacle face meets the wall's inner face. A 12.4 x 6.6 x 2.0 mm counterbore from outside takes the plug overmold and leaves a 1.0 mm wall. Its top is a 45 degree gable so it prints without a bridge.
- **Back face openings:**
  - a speaker grille of 23 holes, 1.6 mm in diameter, whose hole centres fall inside a 20.0 mm circle centred at (-27.0, 0.0) behind the speaker, at least 3.4 mm apart centre to centre;
  - two 1.0 mm mic holes at (35.0, 39.3) and (35.0, -35.7), over the side-A mics.
- **Speaker:** held in a 20.6 mm diameter, 4.6 mm deep ring pocket at (-27.0, 0.0) against the back wall.
- **Dock recess:** 11.6 mm in diameter and 3.0 mm deep, at the back centre. A purchased steel disc, 10.0 mm in diameter and 1.0 mm thick, is glued to its floor, leaving 2.0 mm of recess for the boss.
  - The recess zone reaches 4.0 mm from the back face, clearing the side-A parts by 0.58 mm.
  - Its ceiling is an 11.6 mm bridge, under the 12 mm limit.
- **Print stance:** back down. The glass seat faces up. The ledge underside is a 45 degree chamfer.

### dock-base (1)
A solid wedge, 76.0 mm wide and 72.5 mm deep.

- **Shape:** front face 18.5 mm tall, rear face 47.8 mm tall. The top face is one plane at 22 degrees, 78.2 mm long along the slope. Vertical edges have 6.0 mm fillets and the top edges have 3.0 mm rounds.
- **Boss:** 11.0 mm in diameter and 4.0 mm tall, standing square to the top face at its centre, with a 0.8 mm lead-in chamfer. An N52 magnet, 6.0 mm in diameter and 2.0 mm thick, is glued flush into a 6.4 mm diameter, 2.0 mm deep pocket in the boss top.
- **Pad grooves:** three arc grooves, 6.4 mm wide and 1.0 mm deep, spanning radii 28.8 to 35.2 mm around the boss. Each spans 60 degrees and they are centred at 90, 210 and 330 degrees, with 90 pointing up the slope.
- **Underside:**
  - a ballast pocket 60.4 x 40.4 x 8.2 mm with a 45 degree gable roof, centred 40.0 mm from the front, holding a purchased 60 x 40 x 8 mm steel plate (151 g);
  - four rubber-foot recesses, 10.4 mm in diameter and 1.0 mm deep, 10.0 mm in from each corner;
  - a purchased 1.0 mm felt sheet covering the pocket.
- **Print stance:** bottom down.

### pad-arc (3)
A TPU 95A arc pad, 6.0 mm wide and 3.5 mm thick, spanning 60 degrees between radii 29.0 and 35.0 mm. It has square ends with 1.0 mm corner radii. Extents 35.0 x 9.9 x 3.5 mm. It sits 1.0 mm in its groove and stands 2.5 mm proud, so the tile's back floats 2.5 mm above the top face. Print stance: flat.

## Joints

- **Tile on base (static).** The base's 11.0 mm boss enters the tile's 11.6 mm recess, 0.3 mm clear on each side, and engages it 1.5 mm. The tile's back rests on the three pads, 2.5 mm above the top face, and the boss axis meets the tile centre. The magnet in the boss top pulls the steel disc in the recess floor across 0.8 mm. Nothing else of the tile touches the base.
- **Pad in base (static).** Each 6.0 mm pad sits 1.0 mm deep in its 6.4 mm groove, 0.2 mm clear on each side, and is glued.
- **Tile on pads (static).** Each pad's top face carries the tile's flat back between radii 29.0 and 35.0 mm of the tile centre. The tile's back has no features there.

## Retention and handling

The dock holds a tile of 130 g at 22 degrees:
- The load along the slope is 0.48 N. The boss carries it, engaged 1.5 mm in the recess with 0.3 mm radial clearance.
- The pad ring, 70 mm across, takes the load into the slope. The top pad sits under the upper edge, so a tap near the top-left corner presses onto a pad rather than rocking the tile.
- The magnet only seats the tile. It pulls about 2.5 N across a 0.8 mm gap, less than the base's 270 g weight, so the base stays down when the tile is lifted.

To lift off, tip the bottom edge up and the chamfered boss releases. Most likely to break: the boss, which is solid and 11 mm across. Everything else is over 3 mm.

## Display Pose

The tile is docked. It is centred on the top face, overhanging it by 7.5 mm at each side and by 6.4 mm at the front and back edges. The cable leaves the top edge. Envelope 91.0 x 90.2 x 66.9 mm (width x depth x height). There are no moving parts, so there is no motion check.

## References

The reference images are AI concept renders, edited and measured against this contract. Each was squeezed horizontally by at most 20% to close its aspect.
- ref-01 is an orthographic side elevation of the docked assembly, camera [0, 0]: seen from +X, level, with the front on the left of the image.
- ref-02 is a straight-on rear view of the tile, camera [90, -75]: square to the back of the docked tile, which faces 22 degrees from straight down.
- ref-03 is a side elevation of the base, camera [0, 0], front on the left.
- ref-04 is a top view of one pad, camera [-90, 75]: square to the pad's top face, which lies on the 22 degree slope.

`illustration-hover.jpg` is a three-quarter mood render, not a reference. It shows a steeper tile than the 22 degrees built.

```design-contract
{
  "schema_version": 4,
  "title": "Harness Square Hover Dock",
  "inventor": "rowan-vale",
  "envelope_mm": [91, 90.2, 66.9],
  "references": [
    {"file": "ref-01-hover-assembly.png", "shows": "assembly", "camera": [0, 0]},
    {"file": "ref-02-tile-housing.png", "shows": "geometry:tile-housing", "camera": [90, -75]},
    {"file": "ref-03-dock-base.png", "shows": "geometry:dock-base", "camera": [0, 0]},
    {"file": "ref-04-pad-arc.png", "shows": "geometry:pad-arc", "camera": [-90, 75]}
  ],
  "geometries": [
    {"id": "tile-housing", "name": "Tile housing", "count": 1, "extents_mm": [91, 91, 15.5], "wall_min_mm": 1.0},
    {"id": "dock-base", "name": "Wedge dock base", "count": 1, "extents_mm": [76, 72.5, 47.8], "wall_min_mm": 2.0},
    {"id": "pad-arc", "name": "Arc pad", "count": 3, "extents_mm": [35, 9.9, 3.5], "wall_min_mm": 2.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "The tile rests on the wedge with its face at 22 degrees from the desk, its glass flush with the rim on all four edges and no raised lip."},
    {"id": "R02", "scope": "assembly", "text": "The tile overhangs the base top face by 7.5 mm at each side and 6.4 mm at the front and back edges, standing 2.5 mm off it on the pads, so the tile reads as floating and the boss and pads are hidden."},
    {"id": "R03", "scope": "assembly", "text": "No button, switch or dial is visible anywhere; the only openings are the top-edge USB-C port, two microphone holes and the back speaker grille."},
    {"id": "R04", "scope": "assembly", "text": "The base front face is 18.5 mm tall and its rear face 47.8 mm tall."},
    {"id": "R05", "scope": "geometry:tile-housing", "text": "The front holds an 85.0 x 85.0 x 3.4 mm glass pocket with an even 3.0 mm rim and a ledge opening of 80.0 x 80.0 mm."},
    {"id": "R06", "scope": "geometry:tile-housing", "text": "The back centre has an 11.6 mm diameter recess 3.0 mm deep, and a 23-hole speaker grille of 1.6 mm holes centred 27.0 mm left of centre seen from the front."},
    {"id": "R07", "scope": "geometry:tile-housing", "text": "The top wall has a 9.4 x 3.6 mm USB-C opening centred 26.0 mm right of centre and 6.7 mm from the back face, inside a 12.4 x 6.6 x 2.0 mm counterbore."},
    {"id": "R08", "scope": "geometry:tile-housing", "text": "Two 1.0 mm microphone holes pass through the back at (35.0, 39.3) and (35.0, -35.7) seen from the front, and four 5.0 mm board bosses stand at (4.0, 34.8), (4.0, -31.2), (36.0, 25.8) and (36.0, -22.2)."},
    {"id": "R09", "scope": "geometry:dock-base", "text": "The top face is one 78.2 mm plane at 22 degrees carrying an 11.0 mm boss 4.0 mm tall at its centre."},
    {"id": "R10", "scope": "geometry:dock-base", "text": "Three 60 degree arc grooves 6.4 mm wide and 1.0 mm deep, spanning radii 28.8 to 35.2 mm, are centred at 90, 210 and 330 degrees around the boss with 90 pointing up the slope."},
    {"id": "R11", "scope": "geometry:dock-base", "text": "The underside has a 60.4 x 40.4 x 8.2 mm ballast pocket with a 45 degree gable roof and four 10.4 mm foot recesses."},
    {"id": "R12", "scope": "geometry:pad-arc", "text": "Each pad is a 60 degree arc 6.0 mm wide between radii 29.0 and 35.0 mm with square ends."}
  ],
  "interfaces": [
    {"id": "tile-dock", "kind": "static", "components": ["tile-housing", "dock-base"],
     "text": "The base's 11.0 mm boss, 4.0 mm tall and square to the top face at its centre, enters the tile's 11.6 x 3.0 mm back-centre recess with 0.3 mm clear on each side and engages it 1.5 mm. The boss carries a 6.0 x 2.0 magnet flush in a 6.4 x 2.0 pocket; the recess floor carries a 10.0 x 1.0 steel disc. The tile's back stands 2.5 mm off the top face on the pads, and nothing else touches."},
    {"id": "pad-groove", "kind": "static", "components": ["pad-arc", "dock-base"],
     "text": "Each 6.0 mm wide, 3.5 mm thick pad sits 1.0 mm deep in a 6.4 mm wide, 1.0 mm deep arc groove in the base top face, radii 28.8 to 35.2 mm, centred at 90, 210 or 330 degrees round the boss; glued, 0.2 mm clear on each side."},
    {"id": "pad-tile", "kind": "static", "components": ["pad-arc", "tile-housing"],
     "text": "Each pad's flat top face, 2.5 mm above the base top face, carries the tile's flat back between radii 29.0 and 35.0 mm of the tile centre; the tile's back has no feature there."}
  ]
}
```
