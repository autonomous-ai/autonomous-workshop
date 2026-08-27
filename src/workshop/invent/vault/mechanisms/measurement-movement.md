---
type: mechanism
name: "Measurement Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Measurement Movement

## Definition
Players move pieces a continuous distance up to a maximum, measured with a ruler on an unmarked play surface. Tension emerges from precision disputes over exact positioning, the overhead of physical measurement during play, and the optimization challenge of choosing the ideal distance within the legal range.

## Relations
- component:: [[components/movement-template-set]]
- component:: [[components/flicking-puck-and-gate]]
- risks:: [[anti-patterns/silent-calc]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]], [[anti-patterns/kingmaking]]
- conflicts-with:: [[mechanisms/movement-template]]

## Notes
Fundamentally incompatible with tessellated boards (grid/hex); requires continuous surface.
Primary friction is measurement disputes as a game-critical resolution mechanic rather than automatic rules arbiter.
sources: https://boardgamegeek.com/boardgamemechanic/2949/measurement-movement https://stratsynergy.wordpress.com/game-mechanics/movement/ https://jonurenawriter.com/2025/03/13/all-board-game-mechanics-movement-spatial/
