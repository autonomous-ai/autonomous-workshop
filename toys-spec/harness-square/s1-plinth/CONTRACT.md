# Harness Square Plinth

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. No moving parts.

A square screen head stands reclined in a low, wide plinth like a slate set in stone. The plinth is the weight and the speaker; the head is the face. Focal Component: the head. It costs the plinth any detail of its own beyond the chamfer and one hole row.

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

- **head-housing** (1): open-front tub 86.0 x 86.0 x 15.0 mm, 6.0 mm corner radii in front view, 1.5 mm edge radii; four screw holes 6.0 mm in from the corners; the two mic holes in the top edge. Reference ref-02 is its straight-on rear view.
- **head-bezel** (1): 86.0 x 86.0 x 3.0 mm plate, 6.0 mm corners, centred 64.0 mm window, so an 11.0 mm band. Reference ref-03 is its front view.
- **plinth** (1): block 128.0 x 60.0 x 22.0 mm, 3.0 mm 45 degree chamfer on the top edges. Slot 87.0 x 19.0 mm in section, 10.0 mm deep, its axis reclined 18 degrees back, centred left-right with its front edge 14.0 mm behind the plinth front; seen from above the slot opening is 87.0 x 20.0 mm. Fifteen speaker holes in one row across the front face, 11.0 mm above the desk. USB-C opening centred on the rear face, 4.0 mm above the desk. Underside ballast pocket 100.0 x 36.0 x 8.0 mm for a purchased steel bar of the same size, covered by a 1.0 mm cork pad. Reference ref-04 is its top plan view.

## Assembly and pose

The head (86 x 86 x 18 mm with bezel) sits in the slot, reclined 18 degrees, bottom edge 12.0 mm above the desk. Its front top edge is 94 mm above the desk. Envelope 128 x 60 x 94 mm. No moving parts. ref-01 is taken from about az 5, el 22 (front-left, nearly straight on).

## Handling

The head is pressed into the slot with 0.5 mm total clearance and two 0.2 mm crush ribs; pulling it straight up removes it. Dropping it: the plinth corners take the hit; the 3.0 mm chamfer avoids chipping. Nothing under 3 mm carries load.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Plinth",
  "inventor": "rowan-vale",
  "envelope_mm": [
    128,
    60,
    94
  ],
  "references": [
    {
      "file": "ref-01-plinth-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-head-housing.png",
      "shows": "geometry:head-housing"
    },
    {
      "file": "ref-03-head-bezel.png",
      "shows": "geometry:head-bezel"
    },
    {
      "file": "ref-04-plinth.png",
      "shows": "geometry:plinth"
    }
  ],
  "geometries": [
    {
      "id": "head-housing",
      "name": "Head rear housing",
      "count": 1,
      "extents_mm": [
        86,
        86,
        15
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "head-bezel",
      "name": "Head front bezel",
      "count": 1,
      "extents_mm": [
        86,
        86,
        3
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "plinth",
      "name": "Plinth",
      "count": 1,
      "extents_mm": [
        128,
        60,
        22
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "The head leans back 18 degrees with its lower 10 mm inside the plinth slot, centred left-right."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "The head is two thirds of the plinth's width and sits toward the plinth's front edge."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:plinth",
      "text": "Fifteen 1.5 mm speaker holes in one row across the front face."
    },
    {
      "id": "R05",
      "scope": "geometry:plinth",
      "text": "A 3 mm 45 degree chamfer runs round the top edges."
    },
    {
      "id": "R06",
      "scope": "geometry:plinth",
      "text": "The slot is 87.0 x 19.0 mm in section, 10.0 mm deep, reclined 18 degrees."
    },
    {
      "id": "R07",
      "scope": "geometry:head-bezel",
      "text": "A 64.0 x 64.0 mm window is centred with an even 11.0 mm band."
    },
    {
      "id": "R08",
      "scope": "geometry:head-housing",
      "text": "Two 1.0 mm microphone holes, 20.0 mm apart, sit centred on the top edge."
    }
  ]
}
```
