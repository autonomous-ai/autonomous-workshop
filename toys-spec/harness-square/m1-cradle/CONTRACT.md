# Harness Square Cradle

Inventor: Rowan Vale. Shell prototype for the Harness device with a 3.5 inch square screen in place of the round one. It sits at the base of a monitor, has no buttons, and takes power through a USB-C port at the bottom. One moving part.

A square pod hung between two cheeks on a pivot; tip it to face you. Classic instrument cradle, very legible. Focal Component: the pod. It costs the base any presence beyond a bar.

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

- **pod-housing** (1): open-front tub 84.0 x 84.0 x 17.0 mm, 6.0 mm corners. One 4.2 mm pivot bore, 8.0 mm deep, in each side face, 26.0 mm above the pod's bottom edge and 10.0 mm behind the pod face (centred in the 20 mm pod). Reference ref-02 is its side profile.
- **pod-bezel** (1): 84.0 x 84.0 x 3.0 mm, centred 64.0 mm window, so a 10.0 mm band. Reference ref-03 is its front view.
- **cradle-base** (1): bar 113.0 x 56.0 x 12.0 mm; two cheeks 10.0 mm wide (X) and 30.0 mm deep, standing 4.0 mm in from each end so their inner faces are 85.0 mm apart, rising to 56.0 mm with a fully rounded top (5.0 mm radius in front view). A 3.9 mm press bore through each cheek at 46.0 mm height. Eleven speaker holes in one row across the bar front. USB-C opening centred on the bar rear face, 3.0 mm above the desk. Reference ref-04 is its front view.
- Purchased: two 4.0 x 16.0 mm steel dowel pins; two 4 x 1 mm silicone O-rings (friction).

## Motion and fit

The pod tilts about the pin axis at 46.0 mm height from 0 degrees (upright) to 35 degrees back. Pins press 8.0 mm into the cheeks and slip 7.5 mm into the 4.2 mm pod bores (0.2 mm diametral clearance); the O-ring on each pin between cheek and pod (0.5 mm gap each side) holds any angle. The pod's lowest point over the full travel stays 6.1 mm above the bar top (computed sweep, -5 to 40 degrees). Assembled, not printed in place.

**Display Pose:** pod tilted 15 degrees back. Envelope in the Display Pose 113 x 56 x 105 mm. ref-01 is taken from about az 47, el 10.

Motion plan: `--check-motion true` on the wish and every resume and correction; one sweep of the tilt 0 to 35 degrees in at most 10 steps against the cradle-base only; a skipped, killed or timed-out sweep fails the motion requirement.

## Handling

Lifting by the pod loads the two pins in shear; the cheeks are 10 mm thick at the bore. Knocked over, the pod swings rather than snapping.

```design-contract
{
  "schema_version": 1,
  "title": "Harness Square Cradle",
  "inventor": "rowan-vale",
  "envelope_mm": [
    113,
    56,
    105
  ],
  "references": [
    {
      "file": "ref-01-cradle-assembly.png",
      "shows": "assembly"
    },
    {
      "file": "ref-02-pod-housing.png",
      "shows": "geometry:pod-housing"
    },
    {
      "file": "ref-03-pod-bezel.png",
      "shows": "geometry:pod-bezel"
    },
    {
      "file": "ref-04-cradle-base.png",
      "shows": "geometry:cradle-base"
    }
  ],
  "geometries": [
    {
      "id": "pod-housing",
      "name": "Pod rear housing",
      "count": 1,
      "extents_mm": [
        84,
        84,
        17
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "pod-bezel",
      "name": "Pod front bezel",
      "count": 1,
      "extents_mm": [
        84,
        84,
        3
      ],
      "wall_min_mm": 2.0
    },
    {
      "id": "cradle-base",
      "name": "Cradle base",
      "count": 1,
      "extents_mm": [
        113,
        56,
        56
      ],
      "wall_min_mm": 2.0
    }
  ],
  "requirements": [
    {
      "id": "R01",
      "scope": "assembly",
      "text": "In the Display Pose the pod tilts 15 degrees back between the two cheeks with a visible gap above the bar."
    },
    {
      "id": "R02",
      "scope": "assembly",
      "text": "The pod tilts 0 to 35 degrees with at least 0.5 mm clearance to the base through the whole travel; a skipped, killed or timed-out sweep fails this requirement."
    },
    {
      "id": "R03",
      "scope": "assembly",
      "text": "No button, switch or dial is visible anywhere."
    },
    {
      "id": "R04",
      "scope": "geometry:cradle-base",
      "text": "The cheeks' inner faces are 85.0 mm apart and their rounded tops reach 56.0 mm."
    },
    {
      "id": "R05",
      "scope": "geometry:cradle-base",
      "text": "Eleven 1.5 mm speaker holes in one row across the bar front."
    },
    {
      "id": "R06",
      "scope": "geometry:pod-housing",
      "text": "A 4.2 mm pivot bore sits in each side 26.0 mm above the bottom edge."
    },
    {
      "id": "R07",
      "scope": "geometry:pod-bezel",
      "text": "A 64.0 x 64.0 mm window is centred with an even 10.0 mm band."
    }
  ]
}
```
