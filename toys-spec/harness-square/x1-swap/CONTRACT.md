# Harness Square Swap

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. No moving parts.

All the electronics live in one square core module. The shell is a jacket you slide it into: an upright stand for the desk, a low pumpkin plinth for under the monitor, and more later. Swap the jacket, keep the device. Focal Component: the core. It costs a visible parting line and 4 mm of core above the jacket.

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

- **core** (1): self-contained module 80.0 x 80.0 x 16.0 mm, 4.0 mm corners, graphite; 64.0 mm screen with an even 8.0 mm band; USB-C opening centred on its bottom face. Printed as an open-front tub plus a 3.0 mm bezel plate, screwed together (both are inside this one geometry for the prototype). Reference ref-02 is its front view.
- **jacket-stand** (1): charcoal block 92.0 mm wide and 90.0 mm tall; side profile 40.0 mm deep at the bottom and 24.0 mm at the top, back vertical, front reclined 12 degrees. A core slot 80.6 x 16.6 mm, open at the top and parallel to the front, with a 6.0 mm floor; the back is open behind the core with 3.0 mm retaining lips (45 degree chamfered). Front window 70.0 x 70.0 mm. A 12.0 x 6.0 mm cable pass-through in the floor under the core's USB-C. Reference ref-03 is its side profile.
- **jacket-plinth** (1): pumpkin block 120.0 x 56.0 x 24.0 mm, 3.0 mm 45 degree top chamfer; a core slot 80.6 x 16.6 mm, 14.0 mm deep, reclined 18 degrees; nine speaker holes in one row across the front; cable pass-through under the slot to the rear face. Reference ref-04 is its front view.

## Assembly and pose

Display arrangement: the core in jacket-stand, its top edge 4.0 mm proud of the jacket top so it can be pinched out. Envelope 92 x 40 x 94 mm. No articulated parts: the swap is a 0.3 mm-per-side slide fit, held by a 0.4 mm crush rib on each slot side. ref-01 is taken from about az 20, el 15. `lineup-illustration.png` is not a reference; it only shows the family.

## Handling

The core is the only part with electronics; a dropped jacket is a cheap reprint. Both jackets have a flat bottom and their centre of mass inside the footprint.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Swap",
  "inventor": "rowan-vale",
  "envelope_mm": [
    92,
    40,
    94
  ],
  "references": [
    {
      "file": "ref-01-swap-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-core.png",
      "shows": "geometry:core"
    },
    {
      "file": "ref-03-jacket-stand.png",
      "shows": "geometry:jacket-stand"
    },
    {
      "file": "ref-04-jacket-plinth.png",
      "shows": "geometry:jacket-plinth"
    }
  ],
  "geometries": [
    {
      "id": "core",
      "name": "Core module",
      "count": 1,
      "extents_mm": [
        80,
        80,
        16
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "jacket-stand",
      "name": "Stand jacket",
      "count": 1,
      "extents_mm": [
        92,
        40,
        90
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "jacket-plinth",
      "name": "Plinth jacket",
      "count": 1,
      "extents_mm": [
        120,
        56,
        24
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "The core sits in the stand jacket, its top edge 4 mm proud, with a visible parting line all round."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "The jacket's 70 mm window frames the core's screen with an even border."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:jacket-stand",
      "text": "The front reclines 12 degrees and the back is vertical."
    },
    {
      "id": "R05",
      "scope": "geometry:jacket-plinth",
      "text": "Nine 1.5 mm speaker holes in one row across the front face."
    },
    {
      "id": "R06",
      "scope": "geometry:jacket-plinth",
      "text": "The core slot is 80.6 x 16.6 mm, 14.0 mm deep, reclined 18 degrees."
    },
    {
      "id": "R07",
      "scope": "geometry:core",
      "text": "A 64.0 x 64.0 mm screen is centred with an even 8.0 mm band."
    }
  ]
}
```
