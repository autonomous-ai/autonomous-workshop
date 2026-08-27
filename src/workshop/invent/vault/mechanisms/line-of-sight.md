---
type: mechanism
name: "Line of Sight"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Line of Sight

## Definition
Line of sight is a visibility constraint that limits which figures can interact (typically attack or target) based on whether an unobstructed imaginary line can be drawn between them, accounting for terrain, walls, and other blocking elements. The tension comes from the trade-off between mechanical clarity and the recurring table-judgment calls needed when edge cases arise—is a flag pole blocking, does a weapon barrel count, does a figure's head poking above cover break concealment.

## Relations
- component:: [[components/flicking-puck-and-gate]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]], [[anti-patterns/silent-calc]]

## Notes
True line of sight often creates more adjudication overhead than value; practical implementations use corner-to-corner, color-coded zones, or string measurement depending on desired fidelity.
Edge cases (weapon barrels, flags, exact corner blocking) require repeated table agreements and slow play, offsetting the information-hiding benefits.
sources: https://www.bgdf.com/node/9474 https://www.meeplemountain.com/mechanisms/line-of-sight/ http://deltavector.blogspot.com/2015/02/game-design-27-true-line-of-sight.html https://medium.com/@BastiaanSquared/14-ways-of-reducing-analysis-paralysis-in-your-board-game-535198693828
