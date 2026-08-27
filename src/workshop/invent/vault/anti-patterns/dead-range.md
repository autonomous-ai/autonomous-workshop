---
type: anti-pattern
name: "Dead Range"
created: 2026-08-21
source: agent
status: reviewed
---

# Dead Range

## Definition
A track or counter with values no legal play can reach.

## Relations
- mitigated-by:: [[rule-patterns/reachable-range-sizing]], [[rule-patterns/wraparound-tracking]]

## Notes
- Derive the reachable set, not merely the theoretical maximum; fixed increments can leave holes inside an otherwise valid range.
- Track capacity should reflect legal states across every supported setup and player count.
- sources: https://chitmunk.com/tools/score-track-generator https://forum.vassalengine.org/t/victory-point-track/8019 https://arxiv.org/abs/1908.01417
