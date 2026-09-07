# Quiet Arc

One solid circular-segment desk rocker for an adult. Nudge one end of its flat top gently and release; gravity opposes the tilt. There is no assembly. Its only moving body is the entire object rolling on the desk.

CAD brief: millimetres; radius 40, top chord 18 below the curvature centre, depth 28, top corner radius 2. Nominal envelope 72 x 28 x 22. Exact final dimensions and homogeneous mass properties are measured in measure/balance.json. No cavities, separate components or hardware. The two long top corners are rounded; end faces remain planar for printing.

Print exactly one part_rocker.stl on its broad segment-shaped end, as exported: Z=0, 28 mm high. Suggested PLA, 0.4 mm nozzle, 0.2 mm layers, 100% infill, uniform material, no supports. Bed --bed 220x220x250. Uniform solid fill preserves the calculated centre of mass. The constant section has no overhang in this orientation. Do not hollow this balance-dependent body. Filament density 1.24 g/cm3 is an estimate only; actual mass varies.

rocker.step is the same single part positioned on its curved contact surface for viewing; it is not a second print. rocker_lib.py owns dimensions and geometry. part_rocker.step.py owns the printable orientation. rocker.step.py owns the resting placement.

Verification: single solid, exact STEP mass and bounding box, restoring height and torque sign across +/-20 degrees, no penetration of the desk in sampled states, strict bed fit, watertight mesh, thickness at 0.4 mm nozzle and integrated CAD validation. Rolling-state animation uses exact transformed CAD; damping is illustrative, not measured. No physical printing, durability testing or human playtest has occurred.

Use on a level firm desk away from its edge; start with tilts below 15 degrees. Large pushes can flip it onto its flat top or end. Real settling depends on desk level, rolling losses, friction and print quality. Smooth any rough edge and remove debris from the contact arc. This is an adult desk object.

Exact final envelope: 68.622 x 28 x 22 mm. The two render face tones are illustration shading; print as one material and one solid body. The root assembled export is the same body in its desk pose.
