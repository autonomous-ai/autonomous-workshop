# Crosscurrent CAD
A 210 mm tabletop board with two independently hand-turned carriers and ten nesting counters.
The assembled file is a viewing assembly. Print the eight part_*.stl files: shore, inner, outer once each, and each numbered boat twice. All print flat, open pockets upward, without supports. Source units are millimetres.
crosscurrent_lib.py owns assumed dimensions and part builders; crosscurrent.step.py composes labeled instances.
Use the materialized CAD gen tool on explicit entries, then export and verify_project. No repaired meshes are used.

The carrier parts lower vertically onto the shore floor. Its integral circular guides locate each carrier with 0.5 mm radial clearance. Lift them out vertically to clean. Gravity supports the assembly on a level table; no captive retention, friction performance or carrying the loaded board is claimed. Counters lower into berths, nest in each other, and travel when the pocket wall pushes them. Remove and replace stacks by hand during the cross-and-drift step. Turn slowly while stabilizing stacks with a finger.

measure/motion.json checks full operating cycles including every passenger, the fixed shore and the other carrier, plus withdrawal paths. The 120/180-sample bulk sweeps resolve a maximum 3.95 mm step, below the 16.4 mm passenger foot diameter. Circular guide clearance is constant at all angles and separately established by the source dimensions; these sweeps do not measure friction. A frozen-pass test checks that each declared passenger is reached by its carrier or supporting passenger.
measure/export_states.py exports the same placed solid builders and polar motion in a common world frame. The animation demonstrates counter carriage; scoring and subsequent hand transfer are taught in docs/RULES.md.
Physical print fit, ease of handling ten-counter stacks, durability and human enjoyment remain untested.

Run measure/check_fit.py for the project fit/print audit: it imports delivered STEP solids and probes centered seating, lateral clearance and arrest, nesting depth, bed datums and vertical installation. The named mating interfaces are inner carrier/shore inner guide, outer carrier/shore outer guide, counter/berth and counter foot/cavity. Circular guides derive from each carrier radius plus one radial clearance. Counter foot/cavity share a 0.4 mm radial nesting allowance; the 1.1 mm rim/berth gap deliberately permits easy hand transfer. The assembly order is shore, carriers, then counters; no inaccessible connector is installed afterward.
