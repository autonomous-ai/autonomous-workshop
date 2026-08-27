---
type: mechanism
name: "Turn Order: Role Order"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Turn Order: Role Order

## Definition
Players select roles or actions that directly determine the turn order for a round. This transforms turn sequencing from a fixed parameter into a strategic choice, creating tension between the efficiency of acting early and the positional advantage of acting later. The same role or position carries variable value depending on game state and opponent strategies, making the role selection itself a meaningful decision layer beyond the actions those roles enable.

## Relations
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]]
- variant-of:: [[mechanisms/simultaneous-action-selection]]

## Notes
Role order works best when early-turn roles have drawbacks or advantages vary by game phase; imbalance between roles makes selection obvious.
Effective designs pair role selection with asymmetric role powers so that different roles optimize for different strategies (e.g., aggressive vs. passive play).
sources: https://boardgamegeek.com/boardgamemechanic/2833/turn-order-role-order https://therewillbe.games/articles-analysis/7571-turn-order-topic-discussion https://minifiniti.com/blogs/game-talk/turn-order-variations-design-tips-game-creators/ https://boardsandbees.wordpress.com/2013/02/11/0225/
