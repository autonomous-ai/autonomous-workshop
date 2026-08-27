---
type: mechanism
name: "Hand Management"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Hand Management

## Definition
Players hold a private set of cards representing resources, actions, or combos, and must choose which to commit now versus which to keep for a stronger future play, since playing one card forecloses others and hand size is usually capped. The core tension is opportunity cost under imperfect information: each card can serve multiple purposes depending on future draws and rivals' moves, so timing and sequencing matter as much as raw card power.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/trap-option]], [[anti-patterns/multiplayer-solitaire]], [[anti-patterns/luck-swing-endgame]]
- conflicts-with:: [[constraints/fdm-printed-components-only]]

## Notes
Tension scales with how tightly hand size is capped: loose limits reduce discard pressure and flatten decisions toward a solved optimum.
Criticism clusters on engine-builders where hand play is purely internal optimization with no reactive interaction, tipping into multiplayer-solitaire.
sources: https://mechanicsbg.com/mechanics/hand-management/ https://www.bert.games/post/the-game-mechanics-hand-management https://en.wikiversity.org/wiki/Game_mechanics/Hand_Management https://www.quackalope.com/blog/list-day-5-board-game-mechanics-that-are-tricky-to-balance
- [yt:F_1YcCcBVfY] medium: Rewording a discard as 'mill unseen cards from the deck's bottom' feels less painful than 'discard cards you saw,' even though the unseen version is mathematically worse for the player. (GDC Festival of Gaming 2018)
