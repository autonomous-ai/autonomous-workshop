# Harness Square Grid Dock

Inventor: Rowan Vale. Square-screen shell for the Harness device, keeping the mechanics of the current dock: a front ledge with magnetic pogo connectors and a sloped back support. It is dressed in the VC4 synthwave VHS look:
- black cassette body with a stepped flap edge, four corner screws and ribbed side bands;
- a rainbow stripe under the glass;
- a black wedge dock with a cyan grid and a chrome front ledge.

The device leans on the dock at 22 degrees and lifts off for two-handed use. There is no battery. A USB-C cable plugs into either the dock, feeding the device through the pogo contacts, or the device's left side. The board's two 5 V inputs are diode-ORed (Q1/Q2), so either works. No buttons. No moving parts.

Focal Component: the device face. The cost is a wide 118 mm body, because the side bands and stripe band add 33 mm of width and 13 mm of height around the glass.

## Hardware this shell is built around (from the supplied spec, schematic and STEP)

- **Panel** TXW395039B0-HYE: cover glass 84.37 x 84.37 x 1.8 mm with a printed black border. LCM 74.93 x 78.98 mm. Total stack 3.23 mm, plus 0.175 mm tape. The 30-pin FPC folds behind the panel.
- **Board** PCB_Harness_pro_v1: 80.0 x 40.0 x 1.2 mm. The STEP file tilts it 30 degrees, which is why the bounding box reads 80.7 x 35.2 x 22.3. Board coordinates: u along 80, v along 40, origin at the board centre.
  - Side A (2.1 mm parts): FPC connector, top-port mics at (-37.5, 13.0) and (37.5, 13.0), WS2812 LED, TF socket, and switches SW1 and SW3 at (+/-37.1, -14.0).
  - Side B: the 35.0 x 35.0 x 3.72 mm WT01P4C5-S1 module, centred, and the speaker connector.
  - Mid-mount USB-C at the -u end, centred v = 4.0, its face 0.7 mm past the edge.
  - Four M2 holes of 2.2 mm diameter at (-33.0, -18.0), (33.0, -18.0), (-24.0, 14.0) and (24.0, 14.0).
  - Through-hole footprints CN1 (USB device) and CN2 (USB host), 4 pins at 2.5 mm pitch, centred at (-24.0, 17.0) and (24.0, 17.0).
- **Switches.** Both stay sealed inside, because CH343P auto-program and power-on from USB make them unnecessary.
- **Purchased:**
  - a 20 x 15 x 4.0 mm rectangular 8 ohm 1 W speaker;
  - two pairs of 5-pin magnetic pogo connectors with a 14.5 x 5.2 mm face, each female 4.5 mm deep and each male 6.0 mm deep with pins 1.0 mm proud. The left pair is wired to CN1 (5 V, D-, D+, GND); the right pair is ground and magnet only;
  - a 16 x 12 mm USB-C breakout in the dock;
  - steel ballast.

## Shared rules

- Coordinates on the device are seen from the front, with origin at the face centre, x to the right and y up. "Left" means the viewer's left when facing the screen (x < 0).
- Assembly frame (Display Pose): X to the right of a person facing the screen, Y away from that person, Z up, origin at the centre of the ledge bar's front bottom edge. Dock positions such as y = 12.0 are along Y. Reference cameras use `render_review`'s convention: AZ -90 looks from the front, 0 from +X, 90 from the back; EL 90 looks straight down.
- The glass sits flush with the face on all four edges, with no raised lip. Nothing on the dock rises above the device's face plane, so swipes from every edge stay clear.
- No button, switch or dial is visible.
- Finish in the references: matte black body and dock, a rainbow orange-to-violet stripe painted into its groove, cyan paint in the dock's grid grooves, and a chrome-silver ledge bar.
- Structural walls are 2.0 mm, except the 1.6 mm glass ledge and the 1.2 mm wall behind the device's USB-C counterbore. Nothing load-bearing is under 3 mm.

## Print

Print with a 0.4 mm nozzle and no supports. The bed faces are: device-front on its inner face, device-back on its back face, dock-wedge on its bottom face, and ledge-bar on its front face. The grid grooves are V-shaped so no groove has a flat roof. Every hole that runs parallel to the bed has a teardrop or pointed top.

Every point, chisel, keel and V underside ends in a flat land at least 0.8 mm across (one print minimum at a 0.4 mm nozzle).

A drawn detail under the print minimums is enlarged to the minimum; when the enlarged detail does not fit its spot, it is left out, and this contract names it.

No detail is left out. The smallest details are the 1.0 mm mic holes, the 1.2 mm ribs and slots with 2.6 mm of material between them, and the 1.2 x 0.6 mm grid grooves; all of them are above the minimums.

## Geometry

### device-front (1)
A face plate, 118.0 x 104.0 x 5.0 mm, with 3.0 mm plan corner radii. Print stance: inner face down. Its thinnest wall is the 1.6 mm glass ledge (5.0 plate less the 3.4 pocket).

- **Glass pocket:** 85.0 x 85.0 x 3.4 mm, spanning x -42.5 to 42.5 and y -39.0 to 46.0. It steps to a 2.5 mm ledge with an 80.0 x 80.0 mm window through the plate.
- **Flap step:** the top 4.0 mm of the face, y 48.0 to 52.0, steps back 1.0 mm across the full width, like a cassette flap.
- **Side bands:**
  - The left band (x -59.0 to -42.5) carries ten horizontal V-grooves, 1.2 mm wide and 0.8 mm deep, 11.0 mm long from x -55.5 to -44.5, on a 3.8 mm pitch from y -14.5 to 19.7.
  - The right band carries ten through-slots of the same size and positions (1.2 x 11.0 mm). They are the speaker grille.
- **Stripe groove:** 90.0 x 4.0 x 1.0 mm, centred at (0, -45.5) in the 13.0 mm band below the glass.
- **Corner screws:** four countersunk M2 holes at (+/-54.5, 44.5) and (+/-54.5, -46.5) for M2 x 10 screws into the back.

### device-back (1)
A tub, 118.0 x 104.0 x 11.0 mm, with 3.0 mm plan corners, 2.5 mm side walls and a 2.0 mm back. Total device thickness 16.0 mm. Print stance: back down.

- **Corner bosses:** four, 6.0 mm in diameter with 1.6 mm pilots, at the face-screw positions, merged into the walls.
- **Board.** The board lies horizontal, side A toward the back, CN edge down. Its centre is at (-15.8, -26.0); board u maps to x + 15.8 and v maps to -(y + 26.0). It spans x -55.8 to 24.2 and y -46.0 to -6.0.
  - Four bosses, 5.0 mm in diameter and 5.18 mm tall with 1.6 mm pilots, at (-48.8, -8.0), (17.2, -8.0), (-39.8, -40.0) and (8.2, -40.0).
  - The board's side-A face sits 7.18 mm from the back face, the module front at 12.1 mm and the LCM back at 12.6 mm.
- **USB-C:** a 9.4 x 3.6 mm opening with 1.2 mm corners in the left wall (x = -59.0), centred y = -30.0 and 7.2 mm from the back face. The receptacle face meets the wall's inner face. A 12.4 x 6.6 x 1.3 mm outside counterbore has a 45 degree gable top and leaves a 1.2 mm wall.
- **Pogo slots:** two slots in the bottom wall, centred x = +/-30.0, 14.9 mm wide and 4.5 mm deep up from the bottom face, for the female connectors, 0.2 mm clear on each side and glued. Their contact faces are flush with the bottom face. Each slot runs from the tub's front edge to 5.6 mm deep, so its centre sits 8.2 mm from the device's back face, so the connector drops in from the front and the face plate closes it with no bridge. The board edge sits 1.5 mm above the slots.
- **Mic holes:** two holes of 1.0 mm diameter through the back at (-53.3, -39.0) and (21.7, -39.0), over the mics.
- **Speaker:** a 20.4 x 15.4 mm pocket at x 41.0 to 56.0, y -6.5 to 13.5, behind the right band's slots, its front at 4.9 mm behind the face.

### dock-wedge (1)
A solid wedge, 128.0 mm wide, spanning y 12.0 to 101.0 behind the ledge bar. Print stance: bottom down.

- **Floor:** a 22 degree plane rising from 10.0 mm at y = 12.0 to 46.0 mm at y = 101.0, 96.0 mm long along the slope. It carries a grid of V-grooves, 1.2 mm wide and 0.6 mm deep, on a 12.0 mm pitch both ways.
- **Cheeks:** two side cheeks, 4.7 mm thick (x +/-59.3 to +/-64.0), rise 8.0 mm square to the floor, lower than the device's 16.0 mm face, so they never block a side swipe. Their outer faces carry the same grid on an 8.0 mm pitch. Wedge height including the cheeks: 18.6 mm at the front and 54.6 mm at the rear.
- **Underside:**
  - a ballast pocket, 80.4 x 40.4 x 8.2 mm with a 45 degree gable roof, centred at y = 75.0, holding a purchased 80 x 40 x 8 mm steel plate (200 g);
  - four foot recesses of 10.4 mm diameter.
- **USB-C:** a 9.4 x 3.6 mm opening centred in the rear face, 6.0 mm above the desk, into a 16.4 x 12.4 x 4.4 mm breakout pocket with a 45 degree gable top.
- **Wires:** a 4.0 mm diamond-section channel runs from the breakout pocket to the front face at x = +/-30.0, 5.0 mm above the desk, meeting the ledge bar's wire holes.
- **Ledge pegs:** two holes of 4.4 mm diameter with teardrop tops, 6.0 mm deep, in the front face at x = +/-40.0, 5.0 mm above the desk, for the ledge bar's pegs.

### ledge-bar (1)
A chrome-silver bar, 128.0 mm wide and 12.0 mm deep, with this side profile: front face 23.0 mm tall, top face 6.8 mm deep, and an inner face square to the floor, running from (y 6.8, z 23.0) down to (12.0, 10.0), then vertical to the desk. Print stance: front face down.

- **Ledge height:** its top sits 14.0 mm above the floor, measured square to the floor, which is 2.0 mm below the docked device's face plane and 13.0 mm short of the glass along the face.
- **Pogo pockets:** two pockets, 14.9 x 5.6 x 6.0 mm, in the inner face at x = +/-30.0, centred 8.2 mm up the face from the floor, for the male connectors, glued. A 4.0 mm wire hole runs from each pocket to the rear face at x = +/-30.0, 5.0 mm above the desk.
- **Pegs:** two pegs, 4.0 mm in diameter and 5.5 mm long, at x = +/-40.0 on the rear face, 5.0 mm above the desk.

## Joints

- **Face plate to back tub (static).** Four M2 x 10 countersunk screws pass through the plate at (+/-54.5, 44.5) and (+/-54.5, -46.5) into the tub's 6.0 mm corner bosses (1.6 mm pilots). The plate's inner face seats on the tub's 2.5 mm wall rim, outlines flush. The plate closes the open fronts of the pogo slots.
- **Device on ledge (static).** The tub's bottom face rests on the ledge bar's inner face. Each female pogo connector meets a male one at x = +/-30.0, 8.2 mm out from the floor.
- **Device on floor (static).** The tub's flat back rests on the floor between the cheeks. The cheek inner faces at x = +/-59.3 leave 0.3 mm on each side of the 118.0 mm device.
- **Ledge bar to wedge (static).** The bar's two 4.0 x 5.5 mm pegs at x = +/-40.0, 5.0 mm above the desk, enter the wedge's 4.4 x 6.0 mm teardrop holes, 0.2 mm clear on each side, and are glued. The bar's rear face at y = 12.0 meets the wedge's front face, and the wire holes line up at x = +/-30.0.

## Retention and handling

The device weighs 170 g:
- It rests on the floor at 22 degrees with its bottom face on the ledge's inner face. The ledge carries the 0.62 N load along the slope. The pogo magnets only align the contacts.
- To lift off, tip the top edge up and away. The magnets release at about 3 N.
- The dock weighs 350 g with its ballast, so it stays down.
- Cable at the dock: the left pogo pair feeds 5 V and USB data to CN1. Cable at the device: the USB-C in the left side wall works docked or in the hands.

Most likely to break: the ledge bar pegs, which are 4.0 mm and glued. Nothing load-bearing is under 3 mm.

## Display Pose

The device is docked, its bottom edge on the ledge, with its top edge running 8.0 mm past the floor's rear end along the slope. Envelope 128.0 x 108.4 x 63.8 mm (width x depth x height). There are no moving parts, so there is no motion check.

## References

The reference images are AI concept renders, edited and measured against this contract. Each was squeezed or stretched horizontally by at most 20% to close its aspect.
- ref-01 is an orthographic side elevation of the docked assembly, camera [0, 0]: seen from +X, level, with the front on the left of the image.
- ref-02 is a straight-on front view of the face plate, camera [-90, 75]: square to the docked face, which tilts 22 degrees back from straight up.
- ref-03 is a straight-on rear view of the back tub, camera [90, -75].
- ref-04 is a side elevation of the dock wedge, camera [0, 0], front on the left.
- ref-05 is a straight-on front view of the ledge bar, camera [-90, 0].

`illustration-grid-dock.jpg` is a three-quarter mood render, not a reference.

```design-contract
{
  "schema_version": 4,
  "title": "Harness Square Grid Dock",
  "inventor": "rowan-vale",
  "envelope_mm": [128, 108.4, 63.8],
  "references": [
    {"file": "ref-01-grid-dock-assembly.png", "shows": "assembly", "camera": [0, 0]},
    {"file": "ref-02-device-front.png", "shows": "geometry:device-front", "camera": [-90, 75]},
    {"file": "ref-03-device-back.png", "shows": "geometry:device-back", "camera": [90, -75]},
    {"file": "ref-04-dock-wedge.png", "shows": "geometry:dock-wedge", "camera": [0, 0]},
    {"file": "ref-05-ledge-bar.png", "shows": "geometry:ledge-bar", "camera": [-90, 0]}
  ],
  "geometries": [
    {"id": "device-front", "name": "Device face plate", "count": 1, "extents_mm": [118, 104, 5], "wall_min_mm": 1.6},
    {"id": "device-back", "name": "Device back tub", "count": 1, "extents_mm": [118, 104, 11], "wall_min_mm": 1.2},
    {"id": "dock-wedge", "name": "Grid dock wedge", "count": 1, "extents_mm": [128, 89, 54.6], "wall_min_mm": 2.0},
    {"id": "ledge-bar", "name": "Chrome ledge bar", "count": 1, "extents_mm": [128, 12, 23], "wall_min_mm": 2.0}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly", "text": "The device leans on the dock floor with its face at 22 degrees from the desk, its bottom edge resting on the chrome ledge."},
    {"id": "R02", "scope": "assembly", "text": "The ledge top sits 2.0 mm below the device face plane and the grid cheeks 8.0 mm below it, so nothing rises past the glass or the face at any edge."},
    {"id": "R03", "scope": "assembly", "text": "No button, switch or dial is visible anywhere."},
    {"id": "R04", "scope": "assembly", "text": "Two magnetic pogo pairs meet at x = -30.0 and +30.0 between the device's bottom face and the ledge's inner face."},
    {"id": "R05", "scope": "assembly", "text": "USB-C ports sit in the device's left side wall (x = -59.0) and the dock's rear face."},
    {"id": "R06", "scope": "geometry:device-front", "text": "An 85.0 x 85.0 x 3.4 mm glass pocket spans y -39.0 to 46.0 with an 80.0 x 80.0 mm window, centred left to right."},
    {"id": "R07", "scope": "geometry:device-front", "text": "Each 16.5 mm side band carries ten 1.2 x 11.0 mm horizontal ribs on a 3.8 mm pitch: V-grooves on the left band, through-slots on the right band."},
    {"id": "R08", "scope": "geometry:device-front", "text": "The top 4.0 mm of the face steps back 1.0 mm, and a 90.0 x 4.0 x 1.0 mm stripe groove is centred at y = -45.5."},
    {"id": "R09", "scope": "geometry:device-front", "text": "Four countersunk M2 screw holes sit at (+/-54.5, 44.5) and (+/-54.5, -46.5)."},
    {"id": "R10", "scope": "geometry:device-back", "text": "The left wall has a 9.4 x 3.6 mm USB-C opening centred at y = -30.0, 7.2 mm from the back, inside a 12.4 x 6.6 x 1.3 mm counterbore."},
    {"id": "R11", "scope": "geometry:device-back", "text": "Two 14.9 mm pogo slots 4.5 mm deep open through the bottom face at x = -30.0 and +30.0."},
    {"id": "R12", "scope": "geometry:device-back", "text": "Two 1.0 mm microphone holes pass through the back at (-53.3, -39.0) and (21.7, -39.0), and four 5.0 mm board bosses stand at (-48.8, -8.0), (17.2, -8.0), (-39.8, -40.0) and (8.2, -40.0)."},
    {"id": "R13", "scope": "geometry:dock-wedge", "text": "The floor is a 96.0 mm plane at 22 degrees rising from 10.0 to 46.0 mm, covered by a 12.0 mm grid of V-grooves."},
    {"id": "R14", "scope": "geometry:dock-wedge", "text": "Two 4.7 mm side cheeks rise 8.0 mm square to the floor and carry an 8.0 mm V-groove grid on their outer faces."},
    {"id": "R15", "scope": "geometry:dock-wedge", "text": "The rear face has a 9.4 x 3.6 mm USB-C opening centred 6.0 mm above the desk, and the underside an 80.4 x 40.4 x 8.2 mm gable-roofed ballast pocket."},
    {"id": "R16", "scope": "geometry:ledge-bar", "text": "The bar's side profile has a 23.0 mm front face, a 6.8 mm top and an inner face square to the 22 degree floor."},
    {"id": "R17", "scope": "geometry:ledge-bar", "text": "Two 14.9 x 5.6 mm pogo pockets 6.0 mm deep sit in the inner face at x = -30.0 and +30.0, centred 8.2 mm up from the floor."}
  ],
  "interfaces": [
    {"id": "face-to-back", "kind": "static", "components": ["device-front", "device-back"],
     "text": "Four M2 x 10 countersunk screws pass through the face plate at (+/-54.5, 44.5) and (+/-54.5, -46.5) into the back tub's 6.0 mm corner bosses with 1.6 mm pilots. The plate's flat inner face seats on the tub's 2.5 mm wall rim with the 118.0 x 104.0 outlines flush, and closes the open fronts of the tub's two pogo slots."},
    {"id": "device-on-ledge", "kind": "static", "components": ["device-back", "ledge-bar"],
     "text": "The back tub's flat bottom face rests on the ledge bar's inner face. The tub's 14.9 x 5.6 pogo slots at x = +/-30.0, centred 8.2 mm from its back face, hold female connectors flush with the bottom face. They meet male connectors glued in the bar's 14.9 x 5.6 x 6.0 pockets at x = +/-30.0, 8.2 mm out from the floor."},
    {"id": "device-on-floor", "kind": "static", "components": ["device-back", "dock-wedge"],
     "text": "The back tub's flat back face rests on the wedge's 22 degree floor between the cheeks. The cheek inner faces at x = +/-59.3 leave 0.3 mm on each side of the 118.0 mm device. The floor carries only its V-groove grid there."},
    {"id": "ledge-to-wedge", "kind": "static", "components": ["ledge-bar", "dock-wedge"],
     "text": "The ledge bar's rear face at y = 12.0 meets the wedge's front face. The bar carries two 4.0 mm pegs, 5.5 mm long, at x = +/-40.0, 5.0 mm above the desk; they enter two 4.4 x 6.0 mm teardrop-topped holes in the wedge, 0.2 mm clear on each side, and are glued. The bar's 4.0 mm wire holes and the wedge's 4.0 mm diamond channels meet at x = +/-30.0, 5.0 mm above the desk."}
  ]
}
```
