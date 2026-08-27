---
type: mechanism
name: "Closed Economy Auction"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Closed Economy Auction

## Definition
A closed-economy auction is a meta-mechanism where bids paid to win auctions flow directly to the losing bidders rather than leaving the game system. This traps all currency in perpetual circulation among players, creating constant redistribution of wealth. The tension arises from scarcity: every bid enriches opponents while depleting your own reserves, forcing hard choices between winning desired items and preserving cash for future turns.

## Relations
- component:: [[components/mancala-pocket-board]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/dead-range]], [[anti-patterns/decided-early]]
- conflicts-with:: [[mechanisms/automatic-resource-growth]]
- variant-of:: [[mechanisms/auction-bidding]]
- requires:: [[mechanisms/auction-bidding]], [[mechanisms/income]]

## Notes
Works best when players want multiple different items (fast money re-entry); struggles if one scarce prize is the focus.
Severely unequal wealth distribution mid-game can trap low-cash players in unplayable dead zones where no bid is viable.
sources: https://www.meeplemountain.com/mechanisms/closed-economy-auction/ https://www.boardgameoracle.com/en-AU/boardgame/mechanic/u_w2eos5rz/closed-economy-auction https://allboardgames.com/mechanics/closed-economy-auction/
