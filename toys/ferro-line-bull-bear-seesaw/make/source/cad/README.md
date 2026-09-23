# Bull Bear Seesaw

A desk-scale, tilt-driven expression prototype, approximately 200 mm across,
70 mm deep and 150 mm high through its intended poses. The bull faces forward
in gold-brown; the bear is dark brown with pale blue tear windows. Neutral
gray support carries the two animals.

This is an unprinted digital prototype. Physical fit, friction, stability,
durability and operation are unverified. Motion checks are disabled by the
run's selected policy. Still images show specified poses, not working motion.
No print readiness is claimed.

## Files and rebuilding

`seesaw_lib.py` holds the dimensions, profiles and individual part builders.
The `part_*.step.py` entries place each unique part flat on Z=0 for inspection.
seesaw.step.py is the combined neutral assembly; seesaw_assembly.py places
separate occurrences and defines the intended discrete states.
Generated STEP is the production geometry; no mesh is supplied.
`seesaw_spec.md` records design intent; `measure/` holds actual checks.
Use the materialized CAD `scripts/gen seesaw.step.py --write` to rebuild
an explicit entry. Build123d, cadfits and cadgen are required.

## Parts and orientation

| Role | Quantity | Colour | Bed face |
|---|---:|---|---|
| base | 1 | gray | base underside |
| stand | 1 | gray | mast rear |
| beam | 1 | gray | broad front |
| bull_body | 1 | cocoa_brown | animal front |
| bear_body | 1 | dark_brown | animal front |
| bull_muzzle | 1 | beige | muzzle front |
| shuttle | 1 | beige | broad front |
| bear_mask | 1 | dark_brown | broad front |
| mouth_back | 1 | dark_brown | broad rear |
| tear_back | 1 | misty_blue | broad rear |
| bear_face | 1 | black | broad front |
| main_pin | 1 | gray | headed end |
| mount_pin | 1 | gray | headed end |
| retainer | 8 | gray | broad front |

The split exists for independent movement, removable assembly, support-free
cavities and contrasting colours. PLA or PETG, 0.4 mm nozzle, is the intended
process. Layer height, infill and actual hole compensation require a physical
fit trial. Keep the toy upright: removable rigid cross-keys are gravity seated;
do not infer inversion-proof key retention.

## Assembly intent

Seat the stand tongue in the base and insert the small headed pin and key.
Fit the main axle through beam and stand; add its cross-key. Seat the animals'
integral rear pins through the beam's end bores; their feet rest on the beam
top, preventing rotation, and cross-keys retain them. Rear-load the beige muzzle into its tapered bull seat and the black face
insert into the bear's shallow rear pocket. Fit the carrier behind the faces
around the stand's fixed peg and fit its dark bear mask. Mate the black insert's
upper key into the blue cover's locating recess. Seat both rear
covers on the integral body pins and add four cross-keys. No glue, purchased
fasteners, power hardware or purchased springs are part of this design.

Operate only by gently tilting the beam within its stops. Neutral has a closed
bull mouth and no blue tears; bull-up uncovers the dark smile; bear-up uncovers
both blue tear windows. These are intended states pending physical testing.
