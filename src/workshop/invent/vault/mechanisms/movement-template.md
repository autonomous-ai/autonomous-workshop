---
type: mechanism
name: "Movement Template"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Movement Template

## Definition
A mechanism where players move pieces using physical template shapes or rulers that define exactly how far and in what direction a piece can travel, rather than allowing free measurement. The tension comes from the constraint itself—pieces are limited to template-defined paths, forcing players to plan around these fixed movement restrictions rather than navigating freely.

## Relations
- component:: [[components/movement-template-set]]
- conflicts-with:: [[mechanisms/measurement-movement]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/count-break]], [[anti-patterns/dead-range]]
- variant-of:: [[mechanisms/movement-points]]

## Notes
Eliminates measurement disputes by replacing ad-hoc measurement with predetermined physical templates.
Heavy reliance on board layout geometry—poor template-to-board fit creates dead zones or unnatural movement.
sources: https://boardgamegeek.com/boardgamemechanic/2963/movement-template https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics https://www.meepleuniversity.com/2023/10/10/space-marine-the-board-game-how-to-play-board-game-with-stella-and-tarrant/
