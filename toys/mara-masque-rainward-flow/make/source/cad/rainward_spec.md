# Rainward Flow — current CAD specification

[observed] Immutable revision-source.zip and cloned original sources preserve Rainward Sun190×190×28, deck16,24 lanes,35 pieces, historical1911 Backgammon rules and setup. [specified] Current WISH.json changes central crest blocks, blank dice and angular checker silhouettes. No Wish reference photograph was supplied. The baseline iso was inspected for the three corrected defects; dimensions come from source, not image scaling.

See ../DESIGN.md for the complete reviewed correction contract and ../RULES.md for the unchanged rule-equivalence ledger. Coordinate units mm; XY bed and +Z up. Every production solid rests at Z0. Production and review paths are those listed in README.md.

## Preserved dimensions and state
Sun body radius90, ray radius5, ray count16, overall XY190×190. Deck top16. Radius24 bar top28 gives unchanged overall height28 after removing both crests; no raised or engraved orientation motif is added. Six bar rectangles at x−12,0,12 and y−5,+5 remain free, supporting geometric capacity30 as six stacks of5. This is storage capacity, not a reachable-state claim.

Lane p angle−75+15(p−1);24 points in4 banks. Recesses run radius27→88, depth0.6, width2 except4 bank separators width3. Centers85,72,59,46,33, layers16,20,24;15 pieces per point. Neither contours nor capacity may be shrunk to pass checks. Cup OD42 ID38 height28 wall/floor2 unchanged; dice16mm edge unchanged. All production parts fit200×200×200.

Each player has15 checkers,12×8×4, broad planar top/bottom. Native cubic Bezier boundaries replace every old straight-sided polygon. The rounded leading body reaches x6 at y-1 and y-4 at x3. One uninterrupted upper sweep reaches x-5,y4, continuing to rounded x-6 termination. Single has one end. Split has a shallow smooth terminal notch deepest x-4.7 (final1.3mm), between two short rounded lobes with asymmetric sweep toward the body; no shoulders emerge as ears from the body. Exact native Bezier control points are in rainward_lib.py. Sampled supporting widths are single2.1, upper split2.1 and lower split2.0mm, excluding rounded cap extremes. Current thickness gate checks actual geometry at0.4 nozzle. Planar top and bottom remain unchanged for stacking.

Dice contain21 radius1,depth1.1 conical recesses each on4mm face grid. +Z1/−Z6,+X2/−X5,+Y3/−Y4; each value occurs once. Existing recess surfaces are dark charcoal in canonical images and represent post-print dark paint. Paint location is mechanically defined by recesses. There are no insert solids, drawing templates, hidden balancing cavities or claims of physically fair rolls.

Setup A global24:2,13:5,8:3,6:5; B1:2,12:5,17:3,19:5. Before/after retains original legal6,2 hit submove7→1, then usable2. Victim shifts from radius85,Z16 to radius85−sqrt(80²−12²),Z28, giving full80mm displacement. Other28 checkers retain poses. Rules, identity and diagram numbering remain unchanged; board orientation is player-relative using any chosen wide separator consistently.

## Verification limits
Require current layout, solid/mesh topology, no assembly interference, bed fit, print overhang and wall checks, actual-contour lane/bar capacity, six-face pip/opposite audit and frozen rule trace. Fresh independent blind review must observe the exact current canonical images before receiving Wish. Every positive/negative correction criterion is compared separately. Digital checks cannot establish physical handling, print success, stable real stacks, durability, dice fairness or human play response.
