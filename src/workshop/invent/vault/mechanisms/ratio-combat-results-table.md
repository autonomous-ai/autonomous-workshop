---
type: mechanism
name: "Ratio / Combat Results Table"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Ratio / Combat Results Table

## Definition
A combat mechanic where opposing units sum their offensive or defensive strength values to create an odds ratio (1:3, 2:1, etc.), which then indexes into a table of possible outcomes. A die roll determines which outcome row applies, resolving the entire combat encounter in a single resolution moment. Tension arises from the collision of deterministic force ratios (which suggest a likely outcome) against random dice, so outmatched forces retain a slim but real chance of victory.

## Relations
- risks:: [[anti-patterns/count-break]], [[anti-patterns/silent-calc]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/alpha-solve]]
- variant-of:: [[mechanisms/stat-check-resolution]]
- requires:: [[mechanisms/dice-rolling]]

## Notes
Formalized in Tactics II (1958) but originates from 1830s Kriegspiel; remains standard in hex-and-counter wargames.
Rounding force ratios to whole numbers to avoid fractions can create discontinuous jumps between odds that don't feel granular.
sources: http://chuckgame.blogspot.com/2012/10/wargame-wednesdays-combat-results-table.html https://www.skeletoncodemachine.com/p/combat-results-table https://en.wikipedia.org/wiki/Combat_results_table https://www.bgdf.com/forum/game-creation/design-theory/crt-combat-results-table
