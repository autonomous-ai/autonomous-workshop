---
type: mechanism
name: "Move Through Deck"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Move Through Deck

## Definition
Players progress sequentially through a deck of cards toward a goal—typically reaching the deck's end, defeating a final challenge, or fulfilling a quit condition. Tension arises from incomplete information: knowing certain challenges await but not when they will appear, forcing players to balance forward momentum against resource preservation and risk tolerance.

## Relations
- component:: [[components/tile-dispensing-magazine]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/runaway-leader]], [[anti-patterns/idle-player]], [[anti-patterns/luck-swing-endgame]]
- variant-of:: [[mechanisms/race]]

## Notes
Core tension is rooted in fog of war—certainty that threats exist somewhere in the deck but uncertainty of their exact position.
Works best with limited turn complexity per card; high decision branching at each draw can trigger analysis paralysis.
sources: https://boardgamegeek.com/boardgamemechanic/2962/move-through-deck https://board-game-rules.com/game-mechanics/move-through-deck/ https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics https://thethoughtfulgamer.com/2017/03/28/catch-up-mechanisms/
