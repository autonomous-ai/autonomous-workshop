# Harness Square Swivel

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. One moving part.

A square head floating just above a low base on a hidden post. Turn it left or right toward whoever is talking to it. Focal Component: the head. It costs a thin, quiet base.

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

- **swivel-housing** (1): open-front tub 86.0 x 86.0 x 15.0 mm, 6.0 mm corners; a socket boss 40.0 x 22.0 mm on the back, its lower edge on the housing's bottom edge, holding a 13.4 mm teardrop socket bore, 20.0 mm deep, vertical when the head reclines 12 degrees. Reference ref-02 is its rear view.
- **swivel-bezel** (1): 86.0 x 86.0 x 3.0 mm, centred 64.0 mm window, so an 11.0 mm band. Reference ref-03 is its front view.
- **swivel-base** (1): block 104.0 x 64.0 x 14.0 mm, 3.0 mm 45 degree top chamfer; a 13.0 mm post rising 17.0 mm from the centre of the top. Nine speaker holes in one row across the front. USB-C opening centred on the rear face, 3.0 mm above the desk. Front-view extents 104.0 x 31.0 mm. Reference ref-04 is its front view.
- Purchased: one M4 x 12 screw and a 12 mm washer retaining the head from the socket's top through a slot; one 13 x 1.5 mm silicone O-ring (friction).

## Motion and fit

The head turns about the vertical post axis from -45 to +45 degrees; a stop pin in the socket rides a 90 degree slot. Radial clearance 0.2 mm; the head's bottom edge stays 3.0 mm above the base top at every angle, because rotation about a vertical axis keeps every height. Assembled after printing.

**Display Pose:** head facing straight forward (0 degrees), reclined 12 degrees. Envelope in the Display Pose 104 x 64 x 101 mm. ref-01 is taken from about az 8, el 22.

Motion plan: `--check-motion true` on the wish and every resume and correction; one sweep of -45 to +45 degrees in at most 10 steps against the swivel-base only; a skipped, killed or timed-out sweep fails the motion requirement.

## Handling

Lifting by the head loads the M4 screw; the post is 13 mm solid. Knocked sideways, the head turns rather than snapping.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Swivel",
  "inventor": "rowan-vale",
  "envelope_mm": [
    104,
    64,
    101
  ],
  "references": [
    {
      "file": "ref-01-swivel-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-swivel-housing.png",
      "shows": "geometry:swivel-housing"
    },
    {
      "file": "ref-03-swivel-bezel.png",
      "shows": "geometry:swivel-bezel"
    },
    {
      "file": "ref-04-swivel-base.png",
      "shows": "geometry:swivel-base"
    }
  ],
  "geometries": [
    {
      "id": "swivel-housing",
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
      "id": "swivel-bezel",
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
      "id": "swivel-base",
      "name": "Swivel base",
      "count": 1,
      "extents_mm": [
        104,
        64,
        31
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "In the Display Pose the head faces forward, reclined 12 degrees, floating 3 mm above the base."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "The head turns -45 to +45 degrees about a vertical axis with at least 0.5 mm clearance to the base; a skipped, killed or timed-out sweep fails this requirement."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:swivel-base",
      "text": "Nine 1.5 mm speaker holes in one row across the front face."
    },
    {
      "id": "R05",
      "scope": "geometry:swivel-base",
      "text": "A 13.0 mm post rises 17.0 mm from the centre of the top."
    },
    {
      "id": "R06",
      "scope": "geometry:swivel-housing",
      "text": "The 40.0 x 22.0 mm socket boss sits inside the square outline at the bottom edge."
    },
    {
      "id": "R07",
      "scope": "geometry:swivel-bezel",
      "text": "A 64.0 x 64.0 mm window is centred with an even 11.0 mm band."
    }
  ]
}
```
