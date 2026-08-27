---
type: mechanism
name: "Turn Order: Random"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Turn Order: Random

## Definition
A player or mechanism determines turn order each round (or game) via randomization—drawing cards, rolling dice, spinning a wheel. This creates unpredictability: players cannot assume they'll act at a particular moment, forcing adaptive decision-making and preventing fixed first-player optimization. The tension comes from the tension between wanting to plan ahead and the inability to do so with certainty.

## Relations
- component:: [[components/pointer-spinner]]
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/idle-player]], [[anti-patterns/luck-swing-endgame]], [[anti-patterns/analysis-paralysis]]

## Notes
Input randomness (player draws activation tokens) preserves agency better than pure output randomness (designer announces order).
Lighter games tolerate random turn order better than strategy-heavy games; catch-up mechanics or resource compensation mitigate fairness concerns.
sources: https://www.meeplemountain.com/mechanisms/turn-order-random/ https://www.gamesprecipice.com/turn-order/ https://coopgestalt.com/2024/01/25/a-discussion-of-variable-turn-order-and-how-to-mitigate-its-randomness/ https://minifiniti.com/blogs/game-talk/turn-order-variations-design-tips-game-creators/
