# Harness Square Fold

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. No moving parts.

One thick band, bent once: the screen slab reclines over its own foot like the back of a deck chair. No base and no joint, just one continuous object. Focal Component: the fold body. It costs a separate stand, so the device's weight sits in the foot.

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

- **fold-body** (1): one continuous band 88.0 mm wide. Slab 88.0 mm long and 15.0 mm thick (open at the front for the display), reclined 20 degrees back, joined by a bend with 12.0 mm outer radius to a flat foot 8.0 mm thick that runs 70.0 mm back under it. The slab's top hangs over the foot. A 4 x 6 grid of speaker holes on the foot top, starting 10.0 mm behind the slab. USB-C opening centred on the rear edge of the foot, 2.2 mm above the desk. Reference ref-02 is its left side profile; profile envelope 70 deep x 89 tall.
- **fold-bezel** (1): 88.0 x 88.0 x 3.0 mm plate, 5.0 mm corners, centred 64.0 mm window, so a 12.0 mm band. Reference ref-03 is its front view.

## Assembly and pose

Envelope 88 x 70 x 89 mm. No moving parts. Prints foot-down: the slab's back leans 20 degrees from vertical, inside the 45 degree limit. ref-01 is taken from about az 29, el 13.

## Handling

The foot behind the slab keeps the centre of mass over the footprint at 20 degrees recline. A 4 mm steel plate (60.0 x 50.0 x 4.0 mm, purchased) sits in a pocket in the foot underside under a 1.0 mm cork pad, to make it heavy enough. The bend is the weakest section; its 8.0 mm minimum thickness carries the slab.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Fold",
  "inventor": "rowan-vale",
  "envelope_mm": [
    88,
    70,
    89
  ],
  "references": [
    {
      "file": "ref-01-fold-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-fold-body.png",
      "shows": "geometry:fold-body"
    },
    {
      "file": "ref-03-fold-bezel.png",
      "shows": "geometry:fold-bezel"
    }
  ],
  "geometries": [
    {
      "id": "fold-body",
      "name": "Folded band body",
      "count": 1,
      "extents_mm": [
        88,
        70,
        89
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "fold-bezel",
      "name": "Front bezel",
      "count": 1,
      "extents_mm": [
        88,
        88,
        3
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "Seen from the side the body forms one leaning L: the slab reclines 20 degrees over a foot that runs behind it."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "Body and foot are the same 88 mm width with no seam between slab and foot."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:fold-body",
      "text": "The bend has a 12.0 mm outer radius and the foot is 8.0 mm thick."
    },
    {
      "id": "R05",
      "scope": "geometry:fold-body",
      "text": "A 4 x 6 grid of 1.5 mm speaker holes sits on the foot top behind the slab."
    },
    {
      "id": "R06",
      "scope": "geometry:fold-bezel",
      "text": "A 64.0 x 64.0 mm window is centred with an even 12.0 mm band."
    }
  ]
}
```
