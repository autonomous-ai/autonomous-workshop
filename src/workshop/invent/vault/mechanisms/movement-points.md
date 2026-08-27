---
type: mechanism
name: "Movement Points"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Movement Points

## Definition
Movement points grant each player a fixed budget of points per turn to allocate across moving their pieces on the board, where different terrain or destinations consume different point costs. The tension emerges from the strategic trade-off between distributing points across multiple units to advance piecemeal or concentrating points to move a single piece far—forcing players to prioritize which pieces need advancement on a given turn.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]]
- variant-of:: [[mechanisms/action-points]]

## Notes
Terrain cost variance amplifies tactical depth but increases calculation overhead—designers should vary costs meaningfully rather than make all spaces identical.
Turn tokens or simultaneous action-reveal can mitigate analysis paralysis by reducing think time or removing the need to calculate opponent responses.
sources: https://en.wikiversity.org/wiki/Game_mechanics/Point_to_Point_Movement https://jonurenawriter.com/2025/03/13/all-board-game-mechanics-movement-spatial/ https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics https://www.bgdf.com/forum/archive/archive-game-creation/topics-game-design/tigd-analysis-paralysis-common-problem-1
