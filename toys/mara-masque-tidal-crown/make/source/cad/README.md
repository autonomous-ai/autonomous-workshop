# Tidal Crown parametric CAD
Units mm; XY board center, Z0 bed. --bed 220x220x220
The13 part_*.step.py entries are unique printable components. Each is one upright solid. tidal.step.py is the nonprintable35-occurrence inventory:32 men in standard starting position, plus two spare queens on the tabletop beside the board. Board alone is196x196x12; displayed inventory spans238x196x40. No storage-fit claim.
Sources: tidal_lib.py owns parameters and role shapes; tidal_states.py owns coordinate mappings and exact positions. before.py, after.py and crowded.py are auxiliary state helpers with the same source geometry.
The user guides the queen126mm from h1 to h8 in before.py/after.py; measure/motion.json samples this free move against board and kings. There is no retained joint or coupled operating mechanism. Geometry clearance cannot establish friction or comfortable handling.
Check local dimensions with measure/check_fit.py and corrected three-piece legality with measure/check_demo.py. Integrated verification and independent visual review govern digital completion. Physical printing and human play are untested.
