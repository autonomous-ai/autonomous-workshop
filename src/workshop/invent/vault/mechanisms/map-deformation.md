---
type: mechanism
name: "Map Deformation"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Map Deformation

## Definition
The playable map is altered during gameplay through rotation, shifting, or rearrangement of its physical structure, forcing players to continuously recalibrate positions, distances, and movement strategies. The tension comes from the loss of map stability as a reliable reference point—players must adapt in real-time rather than relying on a fixed spatial mental model, creating dynamic repositioning challenges and forcing reassessment of previously optimal positions.

## Relations
- component:: [[components/interlocking-board-tile]]
- risks:: [[anti-patterns/unreachable]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]]
- variant-of:: [[mechanisms/area-movement]]

## Notes
Works best with clear visual distinction between map states to avoid confusion during transitions.
Uncontrolled deformation can make distance-based strategy unviable if players cannot predict the next configuration.
sources: https://medium.com/@pri.hansda/map-deformation-mechanism-in-games-50036f20f7ae https://boardgamegeek.com/boardgamemechanic/2961/map-deformation https://www.boardgamemechanics.com/mechanic/map-reduction/
