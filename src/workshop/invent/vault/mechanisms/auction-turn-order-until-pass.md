---
type: mechanism
name: "Auction: Turn Order Until Pass"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Auction: Turn Order Until Pass

## Definition
Players take turns bidding upward on an item or resource, with the option to pass on each turn. Once a player passes, they cannot re-enter that auction. The process continues in turn order until only one player remains; that player wins the item. The tension arises from deciding whether to commit more resources to win now or pass early to preserve resources for later auctions.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/first-player-advantage]], [[anti-patterns/kingmaking]]
- variant-of:: [[mechanisms/auction-english]]

## Notes
The 'until pass' rule (no re-entry once you pass) creates an asymmetry where early passers secure positioning but late bidders have more information.
Often used to assign turn order for the next round, creating a cascade of strategic sequencing decisions.
sources: https://bombardgames.com/board-game-mechanics-turn-order-until-pass-auction/ https://boardgamedesignlab.com/mechanism-master-list/ http://gamedesignaspect.blogspot.com/2013/12/auctions-as-game-balancing-tool.html
