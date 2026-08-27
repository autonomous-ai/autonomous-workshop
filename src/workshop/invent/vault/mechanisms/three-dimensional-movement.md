---
type: mechanism
name: "Three Dimensional Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Three Dimensional Movement

## Definition
Pieces occupy and move through three spatial dimensions—horizontally across the board and vertically along a height axis—either via multi-level physical boards or height tokens marking elevation on a 2D surface. Tension arises from simultaneous navigation and prediction across all three axes, forcing players to visualize and calculate positions more abstractly than in flat movement.

## Relations
- component:: [[components/balancing-geometry-set]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]], [[anti-patterns/dead-range]], [[anti-patterns/idle-player]]
- variant-of:: [[mechanisms/area-movement]]

## Notes
Physical layering (Chopper Strike style) presents severe interface friction—moving pieces between levels consumes table real estate and breaks spatial intuition.
Height markers (Attack Vector style) reduce spatial clarity but scale better to complex play areas.
sources: https://boardgamegeek.com/boardgamemechanic/2944/three-dimensional-movement https://jonurenawriter.com/2025/03/13/all-board-game-mechanics-movement-spatial/ https://patents.google.com/patent/US8020871
