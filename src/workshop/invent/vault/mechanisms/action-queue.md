---
type: mechanism
name: "Action Queue"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Action Queue

## Definition
Players pre-plan a sequence of actions arranged ahead of time, which then execute in predetermined order during gameplay—either all at once (batch) or continuously from a queue (rolling). Tension arises from the gap between what players predicted would happen and what actually happens as opponents act and conditions change, forcing difficult trade-offs between detailed planning and adaptive flexibility.

## Relations
- component:: [[components/stackable-order-counter]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]], [[anti-patterns/degenerate-strategy]]
- variant-of:: [[mechanisms/programmed-movement]]

## Notes
Batch queues (all actions resolve together) tend to reduce idle time better than rolling queues.
Hidden information and simultaneous reveal against the queue are common pairings to preserve planning uncertainty.
sources: https://www.smartpicks.co.uk/action-queue-mechanics-mastering-the-ultimate-game-plan/ https://board-game-rules.com/game-mechanics/action-queue/ https://www.bgdf.com/forum/archive/archive-game-creation/topics-game-design/tigd-analysis-paralysis-common-problem-1 https://medium.com/theuglymonster/analysis-paralysis-how-smart-game-design-can-keep-everyone-happy-6e97f2e72b10
