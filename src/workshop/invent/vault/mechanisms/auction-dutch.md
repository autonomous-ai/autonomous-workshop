---
type: mechanism
name: "Auction: Dutch"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Auction: Dutch

## Definition
A price-descent auction where a lot begins at a high value and gradually decreases until a player accepts the current price and claims the item. Tension arises from each player's push-your-luck calculation: accept now and secure the lot at a known cost, or gamble that the price will drop further before another player claims it.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/runaway-leader]]
- variant-of:: [[mechanisms/auction-bidding]]

## Notes
Extremely rare in published games (46 of 125,600 on BGG); requires careful tuning of price descent rate to prevent market stagnation.
Spreads well across multiple rounds rather than a single rapid drop, reducing decision pressure per turn.
sources: https://boardgamegeek.com/boardgamemechanic/2924/auction-dutch https://mechanicsbg.com/mechanics/dutch-auction/ https://www.skeletoncodemachine.com/p/dutch-auctions https://www.bgdf.com/forum/game-creation/design-theory/analysis-paralysis
