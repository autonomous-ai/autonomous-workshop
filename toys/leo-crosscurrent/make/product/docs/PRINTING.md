# Crosscurrent — printing, inventory and assembly

This kit is a physical tabletop game with two lift-out rotating carriers. It uses thirteen printed objects, twenty-five paper action cards, a score sheet and a pencil. No electronics, motors, magnets, glue, bearings or purchased fasteners are required. Dimensions are millimeters. Print and fit guidance below is a design starting point; no successful physical print or physical-fit test has been claimed.

## Print inventory

Use the separate printable part exports, one part per file. The assembled STEP/STL is an assembled presentation and checking model; its overlapping build heights do not make a print-in-place plate.

| Printable STL file | Qty | Part | Nominal size |
|---|---:|---|---|
| `../cad/part_shore.stl` | 1 | Fixed shore with six reward groups and circular guides | 210 diameter; 4 floor, guides rise 2 |
| `../cad/part_inner.stl` | 1 | Inner carrier disk | 84 diameter × 5 |
| `../cad/part_outer.stl` | 1 | Outer carrier ring | 160 outside diameter; 90 opening diameter × 5 |
| `../cad/part_boat_1.stl` | 2 | One-tally identity boat | 20 maximum diameter × 5.2 |
| `../cad/part_boat_2.stl` | 2 | Two-tally identity boat | 20 maximum diameter × 5.2 |
| `../cad/part_boat_3.stl` | 2 | Three-tally identity boat | 20 maximum diameter × 5.2 |
| `../cad/part_boat_4.stl` | 2 | Four-tally identity boat | 20 maximum diameter × 5.2 |
| `../cad/part_boat_5.stl` | 2 | Five-tally identity boat | 20 maximum diameter × 5.2 |

There are **8 unique printable geometries and 13 printed objects**. Both copies of each boat identity use the same geometry; labeling distinguishes A and B. Berths are 22.2 diameter and 2 deep. The nested boat stack adds 3.6 height for each additional boat after the first; every legal position may include all ten boats in one berth. This nominal geometry does not prove a tall physical stack is stable.

The CAD sources are in `../cad/`. Use the eight individual STL files listed in the table. Keep all parts at 100% scale: independently scaling the base, rings or boats changes the designed fits.

## Suggested slicer starting point

- A flat usable build area of at least 210 × 210 is required for the shore. On a nominal 220 × 220 bed, check the slicer's actual usable region and avoid a brim that exceeds it.
- Use an ordinary rigid filament such as PLA with a 0.4 nozzle, 0.20 layers, at least three walls and four top/bottom layers as initial settings. Check the sliced preview before printing. These are suggested settings, not a qualified printer/material combination.
- Put the shore's broad flat underside on the bed, guides and pips up. Put both carriers' broad flat undersides on the bed, berth pockets up. Put each boat's small flat foot on the bed, open cup and tally marks up.
- The geometry is intended for printing in these orientations without supports. Inspect the cup transition and low guides in the layer preview. Do not add supports inside running gaps or berth pockets as a substitute for inspecting a failed slice.
- Use the same scale for all parts. A single color works: tally identity and A/B lettering carry the information. Optional colors may distinguish player pairs, rings and shore.

CAD preflight, mesh and motion checks are evidence about the files. They do not account for a printer's first-layer bulge, surface roughness, warping or material variation. Print one boat and a carrier first if you want a physical fit sample before printing duplicates; this is a manufacturing choice, not evidence already obtained.

## Label and assemble

1. Remove only loose strings, brim and rough burrs. Preserve the guide walls, boat feet, nesting rims, reward pips and tally marks. An adult should use any sharp cleanup tool. Remove cracked or chipped prints from the kit.
2. With the shore stationary, choose a reward-two pip group as harbor **1**. Write the harbor numerals **1–6 clockwise**, one numeral beside each alignment mark. Confirm the pip rewards read **2, 4, 3, 2, 4, 3** clockwise from your chosen harbor 1. If they do not, use the other reward-two group as the reference and check again. Keep numerals separate from the pips so harbor identity cannot be mistaken for reward.
3. Take the two boats sharing one tally count. Use permanent marker to write **A** on the top and outside rim of one, **B** on the top and outside rim of the other. Repeat for identities two through five. Keep lettering off bearing and nesting surfaces. Trace the recessed tally marks in a contrasting color if needed. Let the marker dry completely.
4. Place the shore on a level table. Lower the inner disk into its guide and the outer ring around it, both pocket sides up. They rest on the shore floor and remain removable. There is no click, latch or snap-fit step.
5. Turn each carrier independently through a full revolution while holding the shore still. It should move freely without climbing a guide or dragging the other carrier. Do not force a tight or warped part; correct the print or reprint it, then repeat this check.
6. Place one boat in each kind of berth. Check that it rests freely and can be lifted out. Nest a second boat cup-up on it and check that the stack can be separated without force. Inspect a ten-boat stack on the table and during a gentle turn before using that legal game position. Geometry permits nesting; a successful physical handling test remains the owner's check.
7. Align both rings' berth centers with the six shore marks. Read every identity and A/B mark. Hidden boats may always be lifted for inspection, then returned to their original ring and harbor. Stack order is irrelevant.

There are no detents: players align the six sectors by eye. One harbor step is 60 degrees. Support a tall stack lightly during a slow turn without changing its berth. Lift the game for storage only after removing the loose boats. Store all thirteen parts dry and away from heat that could distort them.

## Paper materials

Prepare one matching five-card set per player: **A**, **B**, **+1 CLOCKWISE**, **0 STILL**, **−1 COUNTERCLOCKWISE**. Five players need 25 cards. Use opaque paper or back each card with the same opaque cardstock. All five backs within a player's set must be indistinguishable; double-sided text that shows through defeats secret selection. Cut cards to the same size and label each set with its player's tally identity on the face. When using the supplied printable sheet, follow its trim marks and check the printed scale reference.

Use a score sheet with player names/identities across columns and rounds 1–12 down rows. Write each round's earned points, then total at the end. Mark tide ends after 3, 6, 9 and 12. For the optional 18-round game, add six rows and mark tide ends at 15 and 18. Keep a pencil beside the sheet. A plain handwritten version of these cards and sheet is fully functional if printing is unavailable.

Print `RULES.pdf` on A4 paper for the complete rules. Print page 1 of `CARDS.pdf` on A4 paper and page 2 on A5 paper, single-sided at 100% scale. The A5 score sheet may also be printed centered on A4 paper at 100%. Do not duplex these two pages: the cards require blank, indistinguishable backs. Read `RULES.md` or `RULES.pdf` for setup positions, the complete round procedure, worked examples and the honest limits of simulation evidence. The physical kit must be labeled before that setup can be read unambiguously.
