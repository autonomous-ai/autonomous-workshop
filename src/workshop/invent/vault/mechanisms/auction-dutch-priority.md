---
type: mechanism
name: "Auction: Dutch Priority"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Auction: Dutch Priority

## Definition
Dutch Priority Auction is a sequential auction where players place bidding tokens on items one at a time, with the first bidder typically claiming priority. The winning player pays a price equal to the total number of tokens placed on that lot; other players can pass to reduce the price before commitment. Tension arises from deciding whether to secure a desirable item early or wait for potentially better prices as fewer tokens accumulate on future lots.

## Relations
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]]
- variant-of:: [[mechanisms/auction-dutch]]

## Notes
Market clogging (unsold items blocking new entries) requires careful discard/refresh mechanics to maintain game pace
Priority ordering can create runaway first-mover advantages; designers must tune to keep non-first players competitive
sources: https://www.meeplemountain.com/mechanisms/auction-dutch-priority/ https://www.mechanics-and-meeples.com/2014/04/28/the-design-of-dutch-auctions/ https://bombardgames.com/board-game-mechanics-dutch-auction/
