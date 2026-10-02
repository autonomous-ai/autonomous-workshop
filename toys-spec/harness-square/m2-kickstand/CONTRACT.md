# Harness Square Kickstand

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. One moving part.

A slim tile with a pumpkin flap folded into its back. Flip the flap out and it reclines 30 degrees; fold it in and the tile lies flat or travels. Focal Component: the tile face. It costs a steeper recline (30 degrees) than the other options.

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

- **tile-housing** (1): open-front tub 92.0 x 92.0 x 15.0 mm, 6.0 mm corners. Back recess 72.0 x 62.0 x 3.0 mm, centred left-right, from 4.0 mm to 66.0 mm above the bottom edge, where the flap stows flush. Two hinge lugs at the top of the recess carry a 3.0 mm steel pin on an axis 62.0 mm above the bottom edge. USB-C opening centred on the back face, 2.0 mm below the recess. Reference ref-02 is its rear view.
- **tile-bezel** (1): 92.0 x 92.0 x 3.0 mm, centred 64.0 mm window, so a 14.0 mm band. Reference ref-03 is its front view.
- **tile-flap** (1): pumpkin plate 70.0 mm wide, 56.0 mm from hinge axis to foot edge, 3.0 mm thick, 4.0 mm bottom corner radii; three 7.0 mm hinge knuckles, each 14.0 mm long, with 3.2 mm bores. Extents 70.0 x 59.5 x 7.0 mm. Reference ref-04 is its front view.
- Purchased: one 3.0 x 76.0 mm steel pin.

## Motion and fit

The flap turns on the pin from 0 degrees (stowed flush) to 46.5 degrees open, where its foot meets the desk 15.9 mm behind the hinge and the tile reclines 30 degrees. A 0.6 mm detent bump on the centre knuckle clicks into a notch at 46.5 degrees. Knuckle side gaps 0.5 mm; bore clearance 0.2 mm on diameter. Assembled after printing.

**Display Pose:** flap open, tile reclined 30 degrees resting on its bottom edge and the flap foot. Envelope in the Display Pose 92 x 63 x 89 mm. ref-01 is taken from about az 5, el 37.

Motion plan: `--check-motion true` on the wish and every resume and correction; one sweep of the flap 0 to 46.5 degrees in at most 10 steps against the tile-housing only; a skipped, killed or timed-out sweep fails the motion requirement.

## Handling

A push on the top edge loads the flap in compression; at 30 degrees the device does not tip forward. The flap is the part most likely to break and prints on its own for replacement.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Kickstand",
  "inventor": "rowan-vale",
  "envelope_mm": [
    92,
    63,
    89
  ],
  "references": [
    {
      "file": "ref-01-kickstand-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-tile-housing.png",
      "shows": "geometry:tile-housing"
    },
    {
      "file": "ref-03-tile-bezel.png",
      "shows": "geometry:tile-bezel"
    },
    {
      "file": "ref-04-tile-flap.png",
      "shows": "geometry:tile-flap"
    }
  ],
  "geometries": [
    {
      "id": "tile-housing",
      "name": "Tile rear housing",
      "count": 1,
      "extents_mm": [
        92,
        92,
        15
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "tile-bezel",
      "name": "Tile front bezel",
      "count": 1,
      "extents_mm": [
        92,
        92,
        3
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "tile-flap",
      "name": "Kickstand flap",
      "count": 1,
      "extents_mm": [
        70,
        59.5,
        7
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "In the Display Pose the tile reclines 30 degrees on the open orange flap; from the side they form a narrow inverted V."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "The flap folds flush into the back recess and opens to 46.5 degrees without collision; a skipped, killed or timed-out sweep fails this requirement."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:tile-flap",
      "text": "Three 7.0 mm hinge knuckles, each 14.0 mm long, run along the top edge."
    },
    {
      "id": "R05",
      "scope": "geometry:tile-housing",
      "text": "The 72.0 x 62.0 mm flap recess spans 4.0 to 66.0 mm above the bottom edge."
    },
    {
      "id": "R06",
      "scope": "geometry:tile-bezel",
      "text": "A 64.0 x 64.0 mm window is centred with an even 14.0 mm band."
    }
  ]
}
```
