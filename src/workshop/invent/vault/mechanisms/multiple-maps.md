---
type: mechanism
name: "Multiple Maps"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Multiple Maps

## Definition
A game board comprised of multiple distinct play areas that are connected at defined junction points, allowing players to move between them or have actions on one board affect conditions on another. Tension arises from territory being spread across multiple spaces, forcing players to decide which areas to focus on and manage multiple simultaneous fronts.

## Relations
- risks:: [[anti-patterns/duplicate-state]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/idle-player]], [[anti-patterns/rules-overhead]], [[anti-patterns/silent-calc]]
- variant-of:: [[mechanisms/modular-board]]
- requires:: [[mechanisms/area-movement]]

## Notes
Physical separation of maps (as in Fische Fluppen Frikadellen) requires explicit player movement rules between spaces.
Temporal layering (as in Khronos) creates interesting causal chains where past decisions reshape future boards.
sources: https://www.meeplemountain.com/mechanisms/multiple-maps/ https://boardgamegeek.com/boardgamemechanic/2965/multiple-maps
