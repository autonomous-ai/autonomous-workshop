---
type: mechanism
name: "Moving Multiple Units"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Moving Multiple Units

## Definition
A player-controlled action that mandates moving multiple units in a single turn, where not all resulting movements necessarily benefit the actor. Tension arises from the forced coupling of unit movements—a player must time card or action play to minimize harm to unfavorable pieces while maximizing benefit to strong ones, creating a planning puzzle around unit coordination and action sequencing.

## Relations
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/idle-player]]

## Notes
The core tension is asymmetrical incentive: units move together regardless of individual need, so card timing becomes the entire decision.
Can exacerbate quarterbacking in semi-cooperative contexts where alpha players calculate optimal unit arrangements for the whole board.
sources: https://www.bgdf.com/forum/archive/archive-game-creation/game-design/analysis-paralysis-movement https://medium.com/theuglymonster/analysis-paralysis-how-smart-game-design-can-keep-everyone-happy-6e97f2e72b10 https://www.leagueofgamemakers.com/designing-games-to-prevent-analysis-paralysis-part-1/ https://kvachev.com/blog/posts/simultaneous-turns/
