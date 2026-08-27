---
type: mechanism
name: "Deck, Bag, and Pool Building"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
aliases: [deck-building, bag-building]
---

# Deck, Bag, and Pool Building

## Definition
Each player starts with an identical, weak personal deck, bag, or pool of cards/tokens and, turn after turn, spends the resources drawn from it to acquire stronger pieces that get shuffled back in for future draws. Because the pool refills randomly rather than being played as a fixed hand, players build a private engine whose average quality they can steadily improve but whose exact draw order they never fully control. The core tension is between committing resources to long-term deck quality (buying power, thinning weak starters, synergy pieces) versus short-term efficiency, with randomness in the reshuffle keeping any given turn's output uncertain even for a deck the owner designed.

## Relations
- component:: [[components/tile-dispensing-magazine]]
- risks:: [[anti-patterns/spiral]], [[anti-patterns/dead-range]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/multiplayer-solitaire]]
- conflicts-with:: [[constraints/fdm-printed-components-only]]

## Notes
Because composition is public knowledge but draw order stays hidden, the mechanism works best when treated as controlled randomness rather than smoothed away with too much draw-fixing or filtering.
Explicit trashing/removal options are the common counterweight to dead-card clutter (e.g. victory-point or starter cards diluting later draws) — omitting them tends to worsen the dead-range and analysis-paralysis risks.
sources: https://www.gamesprecipice.com/pool-builders/ https://www.board-game.co.uk/the-ultimate-guide-to-deck-bag-and-pool-building-board-games/ https://fantastic-factories.medium.com/catch-me-if-you-can-the-runaway-leader-and-catch-up-mechanics-53f0356c440d https://thethoughtfulgamer.com/2017/10/22/10-strategy-tips-dominion/
