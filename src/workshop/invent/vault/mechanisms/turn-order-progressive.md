---
type: mechanism
name: "Turn Order: Progressive"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Turn Order: Progressive

## Definition
A round-based turn-order system where the player token passes to the next player at the end of each round, shifting who goes first each round. This rotates first-player advantage around the table, theoretically preventing any single player from maintaining a permanent positional edge. Tension arises from calculating how turn-order position compounds with game state across rounds, and whether early round positions set up insurmountable leads.

## Relations
- component:: [[components/indexed-ratchet-wheel]]
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/seat-advantage]]

## Notes
Rotation alone does not eliminate first-player advantage if the game has snowball mechanics or resource acceleration.
Effective when combined with game state that resets or equalizes between rounds, otherwise positional luck compounds.
sources: https://www.meeplemountain.com/mechanisms/turn-order-progressive/ https://minifiniti.com/blogs/game-talk/turn-order-variations-design-tips-game-creators/ https://tabletoptrove.com/evolution-of-turn-order-mechanics-in-games/
