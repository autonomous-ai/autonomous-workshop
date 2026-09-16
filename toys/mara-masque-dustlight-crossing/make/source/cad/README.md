# Dustlight Crossing CAD
Units mm. --bed 220x220x220
Flat PLA print stance,0.4 mm nozzle and0.2 mm layers assumed.
Twenty part_*.step.py entries produce four abutting panels and16 independently movable pieces. dustlight_lib.py owns shared dimensions and builders. Component print origins are Z=0; dustlight.step.py places the pieces at board Z=5 in the exact starting setup. No mounting, retention or powered mechanism. Motion verification disabled/unverified. Geometry does not prove physical comfort, durability or successful printing.

Generate an explicit part or dustlight.step.py with the supplied CAD skill's `gen ENTRY --write`. The combined entry is view-only; print the twenty individual parts. The isolated component histories and assembled round are under measure/. The final integrated record is measure/verification-pipeline.md.

measure/check_fit.py checks shared grid, setup and clearance equations. measure/audit_landing.py intersects each of the 63 written STEP cell centers with a 24 by24 by0.1 mm top slab to verify complete flat landing areas. Native CAD validity, mesh, thickness and overhang tools own the separate geometric print checks.

snap/iso.png shows the complete setup. snap/signature.png contains two exact illustrative arrangements, not consecutive turns; their written STEP states and placement records are in ../visual-states/. snap/piece-comparison.png resolves all eight shape pairs and rank markings, with white-seat.png and black-seat.png checking opposed elevated views. The canonical family uses the native CAD review renderer to preserve occurrence colors; the presentation renderer's normal-based palette was rejected. measure/render_states.py generates the state sheet directly from native geometry renders and takes `--renderer PATH_TO_RENDER_REVIEW`.
