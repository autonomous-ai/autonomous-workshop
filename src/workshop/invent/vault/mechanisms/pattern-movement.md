---
type: mechanism
name: "Pattern Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Pattern Movement

## Definition
A movement system where each piece type has a fixed set of directional moves it can make from any position, creating a constrained spatial puzzle. Tension arises from needing to plan multiple moves ahead while opponents' pieces move predictably along their patterns, forcing players to navigate around fixed movement corridors and spatial dead-ends.

## Relations
- component:: [[components/movement-template-set]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]], [[anti-patterns/trap-option]]

## Notes
Pattern Movement's depth comes from positional planning and long-range sequencing rather than breadth of choices; constraining the decision space can paradoxically increase cognitive load if spatial evaluation becomes complex.
Works best when combined with tight board geometry or high piece count; sparse boards reduce tactical tension.
sources: https://tabletopbellhop.com/gaming-advice/game-mechanics/ https://jonurenawriter.com/2025/03/13/all-board-game-mechanics-movement-spatial/ https://www.meeplemountain.com/mechanisms/pattern-movement/ https://www.bgdf.com/forum/archive/archive-game-creation/game-design/movement-mechanics
