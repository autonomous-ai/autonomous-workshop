---
type: mechanism
name: "Modular Board"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Modular Board

## Definition
A modular board is assembled at setup time from interchangeable tiles, panels, or hex sections rather than being fixed and printed as one piece, so the map's shape, connections, and resource placement differ from game to game. Tension comes from players having to read and evaluate a freshly-combined geography each session instead of relying on memorized fixed-map knowledge, and from the combinatorics of module arrangement creating positions of uneven quality that strategy must adapt to on the fly.

## Relations
- component:: [[components/interlocking-board-tile]]
- risks:: [[anti-patterns/unreachable]]
- risks:: [[anti-patterns/count-break]]
- risks:: [[anti-patterns/seat-advantage]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/dead-range]]
- variant-of:: [[mechanisms/variable-set-up]]

## Notes
Designers often patch bad module adjacencies after the fact (e.g. Scythe's tile-flip rule so a lake can never end up next to a home base) rather than solving it structurally.
Modular boards trade memorized fixed-map optimization for per-game combinatorial map reading, which raises setup-evaluation overhead even when turn actions stay simple.
sources: https://www.belloflostsouls.net/2021/02/what-even-is-a-modular-game-board.html https://stonemaiergames.com/games/scythe/scythe-modular-board/ https://tabletoptrove.com/crafting-the-board-the-evolution-of-tile-placement-modular-game-design/ https://tabletopgamesblog.com/2025/12/02/losing-balance-the-role-of-balance-in-board-games-topic-discussion/
