---
type: mechanism
name: "Cooperative Game"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
aliases: [co-op, coop]
---

# Cooperative Game

## Definition
Players share one victory or loss condition and win or lose together against a scripted or system-driven adversary (rising infection rates, invading tokens, a timer) rather than against each other. Since everyone can see the same board state, the tension is meant to come from incomplete individual knowledge, limited communication, and asymmetric player powers forcing genuine negotiation over the optimal joint move. That same shared visibility is also the mechanism's core weakness: when nothing is hidden, one confident player can calculate the whole team's 'solution' and simply direct everyone else's turns.

## Relations
- conflicts-with:: [[mechanisms/single-loser-game]]
- risks:: [[anti-patterns/count-break]]
- risks:: [[anti-patterns/spiral]]
- conflicts-with:: [[mechanisms/betting-and-bluffing]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/multiplayer-solitaire]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/idle-player]]

## Notes
- conflicts with single-loser-game: A cooperative game gives all players a shared win or loss, whereas a single-loser game ends with exactly one player losing while the others do not.
Full shared/open information is the root cause of both alpha-solve and analysis-paralysis here; hidden roles, per-player hands, or communication limits are the usual counter-patches.
Escalating scripted difficulty (Pandemic's infection rate, Spirit Island's invaders) substitutes for player-vs-player tension but risks a losing spiral that snowballs out of reach.
sources: https://coopboardgames.com/blog/how-cooperative-board-games-are-designed-to-stop-one-player-from-taking-over/ https://www.meeplemountain.com/articles/benching-the-quarterback-how-to-deal-with-alpha-players-in-co-op-games/ https://gideonsgaming.com/board-game-quarterbacking-player-problem-or-game-problem/ https://bumblingthroughdungeons.com/open-information-games-analysis-paralysis/
