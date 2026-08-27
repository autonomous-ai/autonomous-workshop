---
type: anti-pattern
name: "Idle Player"
created: 2026-08-21
source: agent
status: reviewed
---

# Idle Player

## Definition
A seat has no meaningful move left and is still at the table.

## Relations
- mitigated-by:: [[rule-patterns/legal-action-floor]], [[rule-patterns/elimination-compression]]

## Notes
- Distinguish permanent idleness from ordinary downtime: the defining defect is that future state changes cannot restore a meaningful choice.
- A mandatory pass is safe only when it is temporary, strategically relevant, or followed quickly by the end of play.
- sources: https://www.leagueofgamemakers.com/game-elements-elimination/ https://boardgames.stackexchange.com/questions/6716/how-can-i-mitigate-some-of-the-downtime-between-players-turns https://www.pineislandgames.com/blog/player-elimination-mechanics-clank
