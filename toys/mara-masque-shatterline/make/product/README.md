# Shatterline

Tic-tac-toe inside a split geode. A low-polygon fractured boulder holds nine round pockets; blunt tooth crystals and squat pyrite cube clusters compete to form the first straight line of three.

## In the set

One rock rind with nine pockets, five tooth crystals and four cube-cluster crystals. The seated set measures 140 × 130 × 32 mm. Each removable crystal is 28 mm wide and 26 mm tall.

## How to play

Give one player all five tooth crystals and the other all four cube clusters. Begin with the nine pockets empty. Teeth play first.

Take turns placing one of your unused crystals in any empty pocket. A placed crystal stays there until the game ends. Do not move, stack or capture crystals, and do not skip a turn.

You win immediately when your crystals fill a row, column or corner-to-corner diagonal. Stop as soon as that line is complete. If all nine pockets fill without a winning line, the game is a draw. There are no points or tiebreakers.

Clear the board to start again. Players may exchange crystal types before the next game. Tooth and cube-cluster shapes identify ownership; colour has no rule meaning. Nothing grows or joins mechanically.

## Telling the two sides apart

Tall and pointed against squat and square. A tooth is one six-sided prism rising to a single blunt tip. A cube cluster is a wide mound of five unequal interpenetrating cubes, all flat square faces and sharp corners. The difference reads from a seated player's view and from directly overhead, with no colour: `cad/veinwake/snap/top-neutral.png` is the same board rendered in one neutral grey.

## Files and fabrication

`assembled.step` shows the complete inventory in a legal full-board draw. The ten files in `parts/` are individual production solids, each upright with its flat bottom at zero. `cad/veinwake/` contains editable parametric source and verification evidence. The signature image shows one legal winning placement with the unused supply omitted from its focused view. Its exact before-and-after STEP files are in `presentation/states/`.

Use the individual STEP solids for slicing. The intended process is upright FDM printing in opaque plastic with a 0.4 mm nozzle and no supports or hardware. Every part is fully opaque; nothing is translucent. No face overhangs more than 45° from vertical, and the thickness and overhang gates pass on all ten parts at that nozzle. Pocket clearance is 1 mm on each side. Inspect the first print for dimensional accuracy and finish before use; no physical print, handling or durability test has been performed, and the run's motion checks were switched off by the operator, so seating and withdrawal are unverified rather than passed.

## Revision

This is a corrected revision of an earlier set. Two of the three unique geometries changed: the rind became a faceted boulder with no spline, fillet or round-over anywhere, and the marker that was three rounded lobes became a cube cluster. The tooth was not redesigned, and its five exported STEP files reproduce the earlier set's bytes exactly. Rules, cells, turn order, win condition, part count and every fixed dimension are unchanged. `cad/veinwake/measure/step-lineage.json` lists every per-part hash against the earlier set's manifest.

## Lineage

These are ordinary two-player tic-tac-toe rules, expressed here in original prose. Rule references: [SDU, traditional game on page 3](https://www.imada.sdu.dk/u/petersk/DM537/project1.pdf) and the [public-domain Kata-Log description](https://kata-log.rocks/tic-tac-toe-kata). The geode and mineral forms are an original interpretation. No commercial edition or publisher is affiliated with this set.
