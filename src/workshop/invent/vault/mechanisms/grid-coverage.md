---
type: mechanism
name: "Grid Coverage"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Grid Coverage

## Definition
Grid Coverage is a mechanism where players place polyominoes or tiles onto a grid-based board to cover specified areas or complete spatial objectives. The core tension arises from geometric constraints—each piece placement must fit spatially with existing pieces, forcing players to balance immediate progress against future positioning flexibility and competing coverage goals.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/alpha-solve]], [[anti-patterns/decided-early]], [[anti-patterns/silent-calc]]
- variant-of:: [[mechanisms/tile-placement]]
- requires:: [[mechanisms/square-grid]]

## Notes
Efficiency-driven puzzles can create false scarcity of good moves—early placement choices often foreclose entire regions of the board.
Works well as secondary constraint (Cartographers, The Princes of Florence) rather than primary win condition; pure coverage races favor faster calculators.
sources: https://www.meeplemountain.com/mechanisms/grid-coverage/ https://board-game-rules.com/game-mechanics/grid-coverage/ https://www.bgdf.com/forum/archive/archive-game-creation/topics-game-design/tigd-analysis-paralysis-common-problem-1 https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/
