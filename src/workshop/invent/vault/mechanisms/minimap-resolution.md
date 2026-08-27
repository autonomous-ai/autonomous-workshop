---
type: mechanism
name: "Minimap Resolution"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Minimap Resolution

## Definition
Players move pieces to a separate resolution board when a conflict is triggered on the main board, allowing detailed mechanics to handle the interaction before results return to the primary map. This creates a two-layer gameplay where the main board remains strategic and abstract, while the minimap zooms into specific tactical or combat details without cluttering the larger board state.

## Relations
- risks:: [[anti-patterns/duplicate-state]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/rules-overhead]], [[anti-patterns/idle-player]], [[anti-patterns/silent-calc]]
- conflicts-with:: [[mechanisms/real-time]]
- variant-of:: [[mechanisms/area-impulse]]

## Notes
Creates natural pacing breaks for narrative or mechanical resolution layers.
Works well when paired with hidden-information or asymmetric board states to justify the zoom-in.
sources: https://boardgamegeek.com/boardgamemechanic/2863/minimap-resolution https://www.meeplemountain.com/mechanisms/minimap-resolution/ https://boardgameoracle.com/en-CA/boardgame/mechanic/aqy2Tt7HQD/minimap-resolution https://jonurenawriter.com/2025/03/13/all-board-game-mechanics-movement-spatial/
