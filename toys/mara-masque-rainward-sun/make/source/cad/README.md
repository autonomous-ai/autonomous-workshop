# Rainward Sun CAD

Text-derived original design. The Sun is190×190×28 mm; full table layout includes cups and dice beside it. Coordinates are millimeters, XY table, +Z up. All printable parts rest atZ=0. The35 loose pieces require no assembly hardware or captured joints. Drops are lifted by hand between open positions; they are not sliders or connectors.

rainward.step.py is the full standard setup. rainward_lib.py owns dimensions, five reusable part builders and state placements. The35 part_*.step.py files are the individual occurrence print entries. Fifteen of each drop silhouette, two dice, two cups and one Sun are required. Identical occurrences share geometry. State helpers produce before and after evidence from the same live source.

Print on a200×200×200 mm or larger bed, using0.4 mm nozzle. Sun underside down; drop flats down; cup opening up; cube flat down. Dice require100% infill and thin ink numbering1–6, opposite faces sum7. Unprinted CAD does not establish physical fairness. Do not use distorted or unqualified dice. No physical test has been run.

The spec records positions and assumptions. measure/check_fit.py verifies algebraic clearances, counts and the exact legal hit trace; generic gates verify solid geometry and printability.

For exact signature states, set RAINWARD_STATE=before or RAINWARD_STATE=after when generating rainward.step.py with --force --write and an explicit state STEP path. Unset the variable for the standard setup. Only the two documented drop poses change. Presentation states live in ../evidence/states/; they are not additional production parts. A common fixed high three-quarter camera compares them.
