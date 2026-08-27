---
type: mechanism
name: "Grid Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Grid Movement

## Definition
Grid movement divides the board into a lattice of discrete, evenly-shaped cells (squares or hexes) and requires pieces to move by stepping from cell to adjacent cell according to a movement allowance, rather than along a free-form surface or a fixed path network. The tension comes from discretizing space: players must convert their strategic intent into exact legal steps, weighing distance efficiency, positioning relative to other pieces, and how the grid's geometry itself constrains or distorts movement (diagonals, zones of control, obstacles).

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]], [[anti-patterns/contradiction]], [[anti-patterns/turtling]]
- requires:: [[mechanisms/square-grid]], [[mechanisms/hexagon-grid]]

## Notes
Square grids create a rules contradiction where diagonal steps cover ~41% more real distance than orthogonal ones, and corner-adjacency creates ambiguous zone-of-control interactions; hex grids are the common fix since all six neighbors are equidistant.
Dense multi-piece grid tactics games are prone to analysis paralysis; one common mitigation is decoupling movement points from action/attack economy so a bad step doesn't feel like a wasted turn.
sources: https://dichebach.substack.com/p/why-wargames-abandoned-the-square http://wargaming-mechanics.blogspot.com/2017/06/square-grids.html https://www.bgdf.com/forum/archive/archive-game-creation/game-design/analysis-paralysis-movement https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics-grid
