# Rainward Flow CAD

Correction of Rainward Sun from the immutable revision baseline. This is text-directed source modification, not an image-derived reconstruction. Units mm; XY table, +Z up; all production entries rest at Z=0.

Sun190×190×28, body disk radius90,16 rays radius5, deck16. The radius24 bar is now an uninterrupted circle at Z28; all raised crest geometry is removed. There are24 lanes at15-degree pitch, unchanged0.6mm recessed separators, and five radial centers85,72,59,46,33 per lane. Each lane takes three layers of4mm drops for15 total. Cup OD42 ID38 height28 floor2 remains unchanged. Both dice retain16mm edge.

There are35 loose production pieces: Sun,15 single-tail drops,15 split-tail drops,2 dice,2 cups. rainward.step.py builds the combined standard setup; part_*.step.py builds each occurrence in print coordinates. rainward_lib.py contains the retained dimensions and corrected Bezier checker outlines, pip recesses and bar. Internal fork occurrence IDs are preserved; customer terminology is split-tail. No fasteners or captured assembly joints exist. Hand-lifted counters are freely placed on open faces.

Print bed declaration: --bed 200x200x200
Print orientation: Sun and checker flat underside down; cups open upward; dice on a flat cube face. Manufacturing assumption0.4mm nozzle. Every pip is a native radius1mm, depth1.1mm recess. Dark paint fills only those existing recesses; never draw or position pips manually. Both dice have opposite pairs1–6,2–5,3–4. No physical statistical fairness, print success, stack handling or durability claim follows from digital checks.

measure/check_fit.py checks projected actual curved contours and inherited algebraic capacities; measure/check_rules.py checks the preserved setup and legal hit trace. evidence/check_preservation.py at product level checks unchanged clone functions against the immutable archive. Current geometry audit checks each die face and overall dimensions.

For evidence only, RAINWARD_STATE=before or after chooses the documented exact state in the one combined source. Export an explicit STEP path with gen --force --write, then restore setup. Only attacker and victim move. render_states.py reads those exact STEP solids, verifies source correspondence, and tessellates their faces with color. Dark dice recess faces depict the specified paint fill; no raster dots or extra pip geometry are added. Canonical snap/iso.png shows setup; snap/signature.png shows the legal hit with a fixed close camera; dice-detail.png and counter-detail.png expose finishing and contours.
