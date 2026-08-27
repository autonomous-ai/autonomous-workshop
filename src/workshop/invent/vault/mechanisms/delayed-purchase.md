---
type: mechanism
name: "Delayed Purchase"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Delayed Purchase

## Definition
A mechanism where purchased or acquired items enter play on a future turn rather than immediately, typically through a deck-discard cycle or build-queue system. Tension emerges from balancing immediate resource constraints against future positioning—players must commit to acquisitions before knowing exactly when they'll be useful or what game state will exist when they arrive.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/silent-calc]], [[anti-patterns/trap-option]]
- variant-of:: [[mechanisms/deck-construction]]
- requires:: [[mechanisms/resource-to-move]], [[mechanisms/time-track]]

## Notes
Creates forward-planning tension by decoupling purchase decisions from payoff timing; common in deck-builders (Dominion).
Can exacerbate analysis paralysis if players must predict future board states to optimize purchase sequencing.
sources: https://boardgamegeek.com/boardgamemechanic/2901/delayed-purchase https://venturacountyboardgamers.com/articles/analysis-paralysis/ https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-2/
