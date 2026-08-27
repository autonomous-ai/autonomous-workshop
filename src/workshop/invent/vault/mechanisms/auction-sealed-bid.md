---
type: mechanism
name: "Auction: Sealed Bid"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Auction: Sealed Bid

## Definition
Each player simultaneously submits a hidden bid for an item without knowing competitors' offers; bids are revealed and the highest bid wins. In first-price variants, the winner pays their own bid (creating tension between winning and profitability). In second-price variants, the winner pays the second-highest bid (making truthful bidding optimal, though players often overshoot). Tension emerges from blind value estimation against unknown competition and the risk of the winner's curse.

## Relations
- component:: [[components/hidden-choice-selector]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/alpha-solve]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]]
- variant-of:: [[mechanisms/auction-bidding]]
- requires:: [[mechanisms/simultaneous-action-selection]]

## Notes
Second-price (Vickrey) auctions have truthful bidding as dominant strategy, but behavioral evidence shows persistent overbidding despite this.
First-price auctions lack a dominant strategy; optimal bids depend on value estimates and beliefs about opponents' bid-shading depth.
sources: https://bombardgames.com/board-game-mechanics-sealed-bid-auction/ https://bombardgames.com/board-game-mechanics-auctions-bidding/ https://www.numberanalytics.com/blog/ultimate-guide-sealed-bid-auction-game-theory https://www.debexpert.com/blog/game-theory-in-sealed-bid-auction-bidding/
