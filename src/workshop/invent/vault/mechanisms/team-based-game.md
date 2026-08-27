---
type: mechanism
name: "Team-Based Game"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Team-Based Game

## Definition
Players are grouped into fixed teams that share a win/loss condition, so individual moves are evaluated by their effect on team standing rather than personal score. Tension comes from coordinating within a team that often has imperfect shared information or unequal skill levels, while still competing against another team's coordinated play. Many implementations add asymmetric roles or hidden information between teammates specifically to force communication instead of silent optimal play. The core design challenge is balancing how much a team can act as one unified brain versus how much each member must contribute independently.

## Relations
- conflicts-with:: [[mechanisms/solo-solitaire-game]]
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/multiplayer-solitaire]], [[anti-patterns/idle-player]], [[anti-patterns/analysis-paralysis]]

## Notes
- conflicts with solo-solitaire-game: Team-based play requires multiple players distributed among teams, while solitaire permits only one player.
Deliberately asymmetric knowledge between teammates is a common counter to alpha-solve/quarterbacking, forcing verbal coordination instead of one player dictating all moves.
Teams with mismatched player skill/experience are especially prone to one member reducing teammates to idle pawns.
sources: https://gideonsgaming.com/board-game-quarterbacking-player-problem-or-game-problem/ https://www.meeplemountain.com/articles/benching-the-quarterback-how-to-deal-with-alpha-players-in-co-op-games/ https://mykindofmeeple.com/quarterbacking-board-games/ https://arxiv.org/pdf/2101.05703
