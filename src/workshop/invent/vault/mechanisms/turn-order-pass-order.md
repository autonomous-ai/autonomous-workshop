---
type: mechanism
name: "Turn Order: Pass Order"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Turn Order: Pass Order

## Definition
Players choose each turn whether to take an action or pass. The order in which players pass determines the turn order for the next round—first to pass becomes first player, second to pass becomes second, and so on. Tension emerges from a painful dilemma: take another action now (risking losing first-player position and facing depleted options next round) or surrender immediate value to secure favorable sequencing and fresh choices when the round resets.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/runaway-leader]], [[anti-patterns/first-player-advantage]], [[anti-patterns/decided-early]]

## Notes
Mechanism is rarely implemented despite creating powerful tension—design complexity and economy balancing challenges discourage adoption.
Requires careful tuning of first-player bonus; if too strong, entrench leaders; if too weak, passing becomes dominant and removes the dilemma.
sources: https://bombardgames.com/board-game-mechanics-turn-order-until-pass-auction/ https://www.gamesprecipice.com/turn-order/ https://therewillbe.games/articles-analysis/7571-turn-order-topic-discussion https://boardgamedesigncourse.com/game-mechanics-how-to-create-tension-in-your-game/
