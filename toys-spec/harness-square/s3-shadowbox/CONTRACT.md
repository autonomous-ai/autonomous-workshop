# Harness Square Shadowbox

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. No moving parts.

A solid block with the screen set deep in a pumpkin-framed recess, like a picture in a shadow box. It reads as an object, not a gadget. Focal Component: the recessed screen and its orange frame. It costs a deeper footprint (50 mm).

## Shared device spec (all options)

- Display: 3.5 inch square 1:1 IPS module, outline 68.0 x 70.0 x 3.0 mm, active area 63.0 x 63.0 mm. The screen window in every bezel is 64.0 x 64.0 mm with 2.0 mm corner radii, centred on the display.
- The screen-carrying shell holds the display in a 68.4 x 70.4 x 3.2 mm pocket and a 64.0 x 64.0 x 9.8 mm electronics cavity behind it; back wall 2.0 mm.
- No buttons anywhere. Input is double-tap on the face and voice; two far-field microphone holes of 1.0 mm diameter, 20.0 mm apart, centred on the top edge of the screen-carrying part.
- Bottom USB-C: one 9.6 x 3.6 mm opening with 1.0 mm corner radii, on the bottom edge or the lower rear face as each option states.
- Speaker holes are 1.5 mm diameter on 4.0 mm pitch unless stated.
- Finish in the references: matte charcoal (Harness "Dark Mode"); pumpkin orange where an option says so.
- Minimum wall 2.0 mm everywhere; nothing load-bearing under 3 mm. Print with a 0.4 mm nozzle, no supports: front bezels print face-down, open-front housings print back-down, blocks print on their bottom face; all overhangs are 45 degree chamfers or teardrop holes.
- Bezels fix to their housing with four M2 x 6 screws from the back, 6.0 mm in from each corner.
- Reference images 01 are AI concept renders; the camera each one was taken from is stated so `--likeness-ref` can declare it (`@AZ,EL`, gate tolerance 30 degrees). Component references are straight-on orthographic views as named.

## Geometry

- **box-body** (1): block 96.0 mm wide and 96.0 mm tall; side profile 50.0 mm deep at the bottom and 33.0 mm at the top, back vertical, front face reclined 10 degrees. Square recess 76.0 x 76.0 x 10.0 mm centred on the front face, then the display pocket and cavity behind it, all narrowing inward so it prints back-down with no overhang. Two rows of 8 speaker holes on the top face. USB-C opening centred on the rear face, 4.0 mm above the desk. Reference ref-02 is its side profile.
- **box-frame** (1): pumpkin-orange insert 75.6 x 75.6 x 6.0 mm, 3.0 mm corners, centred 64.0 mm window, so a 5.8 mm band. It sits in the recess with 0.2 mm clearance, its face 4.0 mm behind the block face. Reference ref-03 is its front view.

## Assembly and pose

Envelope 96 x 50 x 96 mm. No moving parts. ref-01 is taken from about az 44, el 10.

## Handling

A solid block with 1.5 mm edge radii; the frame is held by four M2 screws from inside the cavity. The 10 mm recess protects the screen when the block is set face-down.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Shadowbox",
  "inventor": "rowan-vale",
  "envelope_mm": [
    96,
    50,
    96
  ],
  "references": [
    {
      "file": "ref-01-shadowbox-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-box-body.png",
      "shows": "geometry:box-body"
    },
    {
      "file": "ref-03-box-frame.png",
      "shows": "geometry:box-frame"
    }
  ],
  "geometries": [
    {
      "id": "box-body",
      "name": "Shadowbox block",
      "count": 1,
      "extents_mm": [
        96,
        50,
        96
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "box-frame",
      "name": "Inner frame",
      "count": 1,
      "extents_mm": [
        75.6,
        75.6,
        6
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "The front face reclines 10 degrees; the back is vertical."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "The screen sits 10 mm deep in a square recess, ringed by an orange frame."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:box-body",
      "text": "Two rows of eight 1.5 mm speaker holes sit on the top face."
    },
    {
      "id": "R05",
      "scope": "geometry:box-body",
      "text": "The square recess is 76.0 x 76.0 mm and 10.0 mm deep."
    },
    {
      "id": "R06",
      "scope": "geometry:box-frame",
      "text": "A 64.0 x 64.0 mm window is centred with an even 5.8 mm band."
    }
  ]
}
```
