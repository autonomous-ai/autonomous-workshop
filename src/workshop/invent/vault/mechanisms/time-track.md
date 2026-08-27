---
type: mechanism
name: "Time Track"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Time Track

## Definition
Players occupy positions on a track representing their consumption of 'time' resources. The player positioned furthest back on the track takes the next turn, regardless of who went previously. Different actions cost different amounts of time, advancing a player's marker by varying distances. The core tension emerges from choosing between high-impact actions that consume substantial time (forcing other players to take multiple turns while you wait) and low-impact actions that preserve position and turn frequency.

## Relations
- component:: [[components/windowed-rotary-dial]]
- risks:: [[anti-patterns/dead-range]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]], [[anti-patterns/idle-player]]
- variant-of:: [[mechanisms/turn-order-progressive]]

## Notes
Mechanically resists runaway-leader by design: leaders sit idle while others catch up.
Canonical implementations: Tokaido (space-based variant), Thebes (action-cost variant).
sources: https://boardgamegeek.com/boardgamemechanic/2663/turn-order-time-track http://www.gamelevellearn.com/game/2018/6/19/51-mechanics-time-track https://tabletoptrove.com/evolution-of-turn-order-mechanics-in-games/ https://tabletopgamesblog.com/2023/10/31/about-time-time-as-a-mechanism-in-board-games-topic-discussion/
