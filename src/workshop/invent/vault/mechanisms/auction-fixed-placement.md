---
type: mechanism
name: "Auction: Fixed Placement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Auction: Fixed Placement

## Definition
Players place bid markers on a board track below each lot, revealing all bids simultaneously. To outbid, players place their marker higher on the same lot or shift to a different lot entirely. All bidding information is public and visible, creating dynamic repositioning as players jostle for control. The tension arises from watching opponents' intentions in real-time and deciding whether to defend a lot or pivot strategy—every placement is a gamble on whether competitors will follow you or abandon the fight.

## Relations
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/first-player-advantage]]
- variant-of:: [[mechanisms/auction-bidding]]

## Notes
Visibility of all bids is the mechanism's core—it trades sealed-bid secrecy for real-time psychological warfare.
Works well with constrained bid resources (finite action tokens) to prevent runaway spirals on single lots.
sources: https://islaythedragon.com/guides/whats-it-worth-to-ya-a-guide-to-auction-mechanics/ https://www.meeplemountain.com/mechanisms/auction-fixed-placement/ https://bombardgames.com/board-game-mechanics-auctions-bidding/
