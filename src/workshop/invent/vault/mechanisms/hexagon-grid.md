---
type: mechanism
name: "Hexagon Grid"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Hexagon Grid

## Definition
Hexagon Grid lays the board out as hex-shaped cells, each touching exactly six equidistant neighbors, so movement, placement, or line-of-sight has no diagonal-distance ambiguity the way orthogonal grids do. Tension comes from the six-way branching factor: every space offers more directions to weigh than a four-neighbor grid, and that choice multiplies again once terrain, zones of control, or range rules are layered on top of the lattice. It's typically a spatial substrate for another system (movement, influence, area control) rather than a scoring mechanism in its own right.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]]
- variant-of:: [[mechanisms/grid-movement]]

## Notes
Uniform six-neighbor adjacency removes the square-grid diagonal-distance question but raises the branching factor players must evaluate each turn.
Terrain, line-of-sight, and zone-of-control rules layered onto hexes are a common source of new-player rules overhead in hex wargames.
sources: https://www.idi.ntnu.no/emner/it3105/materials/hex-board-games.pdf https://dev.to/andyreadpnw/hex-based-react-board-game-the-math-1kc0 https://www.gamedev.net/forums/topic/606599-square-or-hex-board/
