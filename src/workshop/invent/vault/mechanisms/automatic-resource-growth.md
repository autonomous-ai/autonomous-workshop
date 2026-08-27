---
type: mechanism
name: "Automatic Resource Growth"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Automatic Resource Growth

## Definition
Automatic resource growth is a mechanic where resources accumulate for players through predetermined rules or conditions each turn, without requiring active player decisions to generate them. The tension arises from managing the influx of resources and the compounding advantage of players with more resource-generating infrastructure—an early lead becomes exponentially harder to overcome as the leader generates more resources to invest in more generators.

## Relations
- component:: [[components/indexed-ratchet-wheel]]
- risks:: [[anti-patterns/silent-calc]]
- conflicts-with:: [[mechanisms/closed-economy-auction]]
- risks:: [[anti-patterns/runaway-leader]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/luck-swing-endgame]]
- variant-of:: [[mechanisms/income]]

## Notes
Snowballing (positive feedback loops) is the critical design hazard; mitigation strategies include network constraints, diminishing returns, or shared resource pools.
Probability-based generation (dice) introduces swings; fixed income feels more deterministic but can amplify early-game positioning.
sources: https://bombardgames.com/board-game-mechanics-automatic-resource-growth/ https://www.boardgameoracle.com/boardgame/mechanic/xEzmJNi1lU/automatic-resource-growth https://neutronium.games/blog/resource-management-games-2026 https://insideupgames.com/board-game-reviews/the-runaway-leader-problem/
