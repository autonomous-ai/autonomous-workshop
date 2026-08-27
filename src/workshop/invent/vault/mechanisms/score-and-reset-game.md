---
type: mechanism
name: "Score-and-Reset Game"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Score-and-Reset Game

## Definition
A game structure where players accumulate and score points through rounds or phases, with scores recorded and then reset to zero for the next cycle. The tension emerges from deciding when to commit points (lock in a score and trigger reset) versus continuing to build up a larger score at risk of losing the opportunity, creating a push-your-luck dynamic across multiple scoring periods rather than one final tally.

## Relations
- component:: [[components/detented-slider-track]]
- risks:: [[anti-patterns/handling-wipe]]
- risks:: [[anti-patterns/fiddly-reset]]
- risks:: [[anti-patterns/runaway-leader]], [[anti-patterns/decided-early]], [[anti-patterns/first-player-advantage]], [[anti-patterns/alpha-solve]]
- variant-of:: [[mechanisms/push-your-luck]]

## Notes
Resetting equalizes player positions periodically but can create comeback frustration if early leaders remain ahead despite resets.
The mechanism's success depends on point thresholds and round structure—too many resets flatten tension, too few collapse into a single endgame.
sources: https://www.meeplemountain.com/mechanisms/score-and-reset-game/ https://www.boardgameoracle.com/boardgame/mechanic/wL4BBef0gA/score-and-reset-game https://thethoughtfulgamer.com/2017/03/28/catch-up-mechanisms/ https://fantastic-factories.medium.com/catch-me-if-you-can-the-runaway-leader-and-catch-up-mechanics-53f0356c440d
