---
type: mechanism
name: "Command Cards"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Command Cards

## Definition
Players simultaneously select and program hidden action commands during a planning phase, then all commands are revealed and executed together. This creates strategic tension from incomplete information: you must commit to actions without knowing opponents' plans, and simultaneous execution means your carefully laid strategy often gets disrupted or interacts unpredictably with others' choices.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/first-player-advantage]], [[anti-patterns/dead-range]]
- variant-of:: [[mechanisms/simultaneous-action-selection]]

## Notes
Design success hinges on limiting the decision space—too many possible command combinations causes paralysis; successful games (Shogun, Wallenstein) constrain choices tightly.
Requires clear, unambiguous command resolution order to prevent disputes when simultaneous actions interact.
sources: https://www.oreateai.com/blog/principles-and-methodologies-of-board-game-mechanism-design/fd9eec9d1949b872f28132a8089232fe https://makecraftgame.com/2025/02/28/board-game-mechanics-an-overview/ https://boardgamedesignlab.com/mechanics/ https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/
