---
type: mechanism
name: "Tech Trees / Tech Tracks"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Tech Trees / Tech Tracks

## Definition
Players advance along branching research paths by spending resources, unlocking increasingly powerful units, abilities, or buildings as they meet prerequisites. The tension emerges from constrained resources forcing prioritization: investing heavily in one tech line forecloses others, and early progression choices compound across the game, making initial decisions disproportionately consequential.

## Relations
- component:: [[components/detented-slider-track]]
- risks:: [[anti-patterns/trap-option]]
- risks:: [[anti-patterns/duplicate-state]]
- risks:: [[anti-patterns/decided-early]]
- risks:: [[anti-patterns/dead-range]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/runaway-leader]], [[anti-patterns/first-player-advantage]], [[anti-patterns/degenerate-strategy]]
- requires:: [[mechanisms/investment]]

## Notes
Tech trees manage complexity by gating options: early game has few choices, later game unlocks new decision space.
The deterministic prerequisite chain creates predictable pacing but can make the optimal path obvious in hindsight.
sources: https://www.gamestudies.org/1201/articles/tuur_ghys https://www.bgdf.com/forum/game-creation/mechanics/best-ways-manage-tech-tree https://www.bgdf.com/forum/archive/archive-game-creation/game-design/tech-trees-board-games https://boardgamegeek.com/boardgamemechanic/2849/tech-trees-tech-tracks
- [yt:P3P70PrE8i4] medium: Charterstone's upgraded buildings are strictly better but were also priced higher than what they replace, making upgrades feel like a tradeoff instead of a clean improvement. (Stonemaier Games 2022)
- [yt:HXA00ZCzSZ4] medium: In Scythe: Upgrading an action permanently relocates a cost cube on your player board, cheapening or boosting that action for the rest of the game, unlike a one-off resource spend. (No Pun Included 2016)
