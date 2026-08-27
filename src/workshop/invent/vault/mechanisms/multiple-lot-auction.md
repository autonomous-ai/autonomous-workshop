---
type: mechanism
name: "Multiple-Lot Auction"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Multiple-Lot Auction

## Definition
Players bid on multiple distinct items (lots) offered simultaneously, rather than sequentially through one lot at a time. Each player must allocate limited resources across multiple competing bids while prices shift in real-time as others outbid them. The tension springs from combinatorial decision-making: choosing which lots to prioritize, anticipating rivals' intentions, and managing the risk of winning undesirable combinations while losing the items you wanted most.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/idle-player]], [[anti-patterns/decided-early]]
- variant-of:: [[mechanisms/auction-bidding]]
- requires:: [[mechanisms/simultaneous-action-selection]]

## Notes
Works best when items create valuable synergies; otherwise reduces to simple per-lot value judgments.
Simultaneous bidding masks downtime rather than eliminating it—players still deliberate over multiple interdependent choices.
sources: https://bombardgames.com/board-game-mechaincs-multiple-lot-auction/ https://circlejgames.com/auctioning-mechanic-1/ https://www.bgdf.com/forum/game-creation/design-theory/analysis-paralysis
