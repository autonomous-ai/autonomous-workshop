---
type: mechanism
name: "Relative Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Relative Movement

## Definition
Players move pieces relative to other pieces' positions rather than to fixed board locations. Movement is contextual—a card might say "move 5 toward the nearest opponent" instead of "move 5 spaces forward." Tension emerges from continuous position recalculation and players' inability to predict future moves precisely, since where they go depends on where others are.

## Relations
- component:: [[components/movement-template-set]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/count-break]], [[anti-patterns/first-player-advantage]], [[anti-patterns/seat-advantage]]
- variant-of:: [[mechanisms/movement-template]]

## Notes
Eliminates need for absolute board coordinates but adds mental calculation burden; works well in races where order matters more than exact positions.
Physical measurement systems (rulers, card-lengths) often required for omni-directional variants.
sources: https://jonurenawriter.com/2025/03/13/all-board-game-mechanics-movement-spatial/ https://www.bgdf.com/forum/game-creation/design-theory/handling-omni-directional-movement-tabletop-game https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics
