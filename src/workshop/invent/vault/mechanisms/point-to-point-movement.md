---
type: mechanism
name: "Point to Point Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Point to Point Movement

## Definition
Point-to-point movement represents the board as a fixed network of discrete locations (nodes) joined by defined connections (edges), rather than a continuous grid or set of adjacent regions, and pieces may only travel along those connections rather than freely across space. The tension comes from the topology itself being scarce and shared: routes and junctions can be occupied, congested, or blocked by other players' pieces, so players must plan paths around rivals and race for well-connected or shortcut nodes. Because the graph's shape (branching factor, chokepoints, dead ends, distances) is fixed by the map, most strategic depth is engineered by the designer through network layout rather than emerging from player-built structure.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/turtling]], [[anti-patterns/deadlock]], [[anti-patterns/trap-option]]

## Notes
The network's branching factor and chokepoint density is the primary tuning lever for both pacing and blocking severity.
Often layered with pick-up-and-deliver or network-and-route-building so the fixed topology also carries economic stakes, not just positioning.
sources: https://en.wikiversity.org/wiki/Game_mechanics/Point_to_Point_Movement https://stratsynergy.wordpress.com/game-mechanics/point-to-point-movement/ https://en.wikipedia.org/wiki/Area_movement https://www.g2a.com/news/glossary/what-is-a-choke-point-in-gaming/
