---
type: mechanism
name: "Tile Placement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Tile Placement

## Definition
Players build up a shared or personal board over the course of the game by placing tiles (drawn randomly or held in a limited hand) according to adjacency or matching rules, such as connecting terrain edges or resource types. The tableau itself is the game state, so early placements constrain and enable later ones. Tension arises from spatial scarcity: good spots are limited, tile availability is uncertain, and players must weigh optimizing their own position against occupying or blocking spots opponents want.

## Relations
- component:: [[components/tile-dispensing-magazine]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/kingmaking]], [[anti-patterns/multiplayer-solitaire]], [[anti-patterns/luck-swing-endgame]]

## Notes
Random tile draw order means the pool of remaining tiles late in the game may poorly match open board slots, creating swingy endgame luck.
Personal-tableau variants reduce direct board contention versus shared-board variants, trading competitive tension for higher multiplayer-solitaire risk.
sources: https://www.bert.games/post/the-game-mechanics-tile-placement https://www.thedarkimp.com/blog/2021/07/15/what-is-a-tile-placement-game/ https://www.diva-portal.org/smash/get/diva2:1876522/FULLTEXT01.pdf
