# QUAYSHIFT challenge content

Open **cards.html** for three setup cards and one rules page. Open
**solutions.html** separately for all 14 currently enumerated arrangements.
Both documents have A4 print styling; setup and answer SVGs are standalone
vector assets. Top views are explicitly symbolic footprint diagrams.

The rules preserve fixed clues, full bridge strips, eight upright modules,
quarter-turns, orthogonal cell-center travel, passage through both high bridges,
straight crossing of each gap, and no revisits, stacking, ferry lifting or
architecture movement during a trip. Colors are taken from the CAD source and
are not a placement rule. Module A–H labels are separate from cell coordinates.

The three cards cover headroom, protecting a lateral detour, and arranging
solid modules around fixed bridges. Difficulty is editorial, not playtested.
Only three cards are delivered; the aspirational 24-card set is not complete.

Counts **2 / 4 / 8** describe footprint completion classes with at least one
validated exact representative pose each. They are **not** counts of every
physically distinguishable facade facing. The [finite CAD evidence](../cad/measure/physical-validation.json)
passes the 14 representative completions and three witness layouts using
continuous sweeps of a diameter 26 mm, height 26 mm containing cylinder, actual
low-gate overlap, and sampled 10 mm top-down finger contacts with a 0.251 mm
inter-sample allowance. This is CAD proxy evidence, not a hands-on comfort test.

**Facing caveat:** Two of 16 Q01 arch-facing aliases fail the conservative
top-down finger proxy. The tested Q02/Q03 aliases pass. Match the exact labels,
rotations and rear-span orientation shown when reproducing a solution. All
upright quarter-turns remain legal; legality alone does not guarantee a
successful trip or comfortable access. The offset band uses the actual span
location, local y = 19.6–31.6 mm within the 32 mm strip, transformed with the
module. It is a facing cue on otherwise symbolic footprint diagrams. See
[facing-access.json](facing-access.json) and [validation-scope.json](validation-scope.json).

The enumeration quotients A/B, E/F and G/H footprint roles and the board group
C2 = {identity, left/right reflection}, preserving C1 and C5 individually.
For equivalent reasoning with reversed travel, the larger unordered-port group
D2 also admits near/far reflection and 180° rotation, each with route reversal.
Requotienting the returned arrangements under this larger group still gives
**2 / 4 / 8**. No quarter-turn board rotation preserves the port pair. Neither
board group proves physical facade or finger-access equivalence. Setup clues
constrain the search before completed arrangements are quotiented. Multiple
routes in one completed town never count as separate construction solutions.

To reproduce with standard-library Python, run `solver.py`, then
`build_cards.py`. `original_grammar.py` is the Wish's recreated original probe.
The solver imports it locally. Card generation reads the authored CAD palette
when available, otherwise the included `palette.json`. No CAD kernel is
required by these scripts. `enumeration-audit.json` records an independent
Cartesian enumeration matching the recursive solver's completion counts.

The HTML and SVG source is generated locally. Browser print pagination and
hands-on usability have not yet been verified.
