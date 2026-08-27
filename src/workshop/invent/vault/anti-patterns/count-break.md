---
type: anti-pattern
name: "Count Break"
created: 2026-08-21
source: agent
status: reviewed
---

# Count Break

## Definition
The design works at one player count and fails at another.

## Relations
- mitigated-by:: [[rule-patterns/player-count-normalized-setup]], [[rule-patterns/player-count-matrix-testing]]

## Notes
- Scaling only the number of components is insufficient when player count also changes interaction density, turn frequency, information, or coalition dynamics.
- A narrower honest player-count range is often safer than preserving a weak count through numerous exceptions.
- sources: https://boardgamegeek.com/blog/3039/blogpost/30069/player-count-and-scalability-in-game-design https://www.gamesprecipice.com/terramystica/ https://www.leagueofgamemakers.com/design-playtest-tactic-the-stress-test/
