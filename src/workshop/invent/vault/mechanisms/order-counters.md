---
type: mechanism
name: "Order Counters"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Order Counters

## Definition
Order counters are physical tokens that players place simultaneously on different board regions to designate intended actions or allocations before results are revealed. Players commit to their counter placements without seeing others' choices, creating a layer of hidden planning that resolves in a predetermined order. The tension emerges from balancing aggressive positioning against the risk that multiple players may compete for the same regions or outcomes.

## Relations
- component:: [[components/stackable-order-counter]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/alpha-solve]], [[anti-patterns/first-player-advantage]], [[anti-patterns/kingmaking]]
- variant-of:: [[mechanisms/simultaneous-action-selection]]
- requires:: [[rule-patterns/simultaneous-reveal]]

## Notes
Stacking multiple counters in one region creates logistical friction (pieces dislodge when reading stack height).
Effectiveness depends heavily on whether counter placement is truly simultaneous or if players gain information from opponents' choices.
sources: https://boardgamegeek.com/boardgamemechanic/2844/order-counters https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/ https://www.bgdf.com/forum/archive/archive-game-creation/topics-game-design/tigd-analysis-paralysis-common-problem-1 https://medium.com/theuglymonster/analysis-paralysis-how-smart-game-design-can-keep-everyone-happy-6e97f2e72b10
