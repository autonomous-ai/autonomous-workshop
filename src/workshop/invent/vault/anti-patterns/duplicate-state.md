---
type: anti-pattern
name: "Duplicate State"
created: 2026-08-21
source: agent
status: reviewed
---

# Duplicate State

## Definition
Two components display the same state.

## Relations
- mitigated-by:: [[rule-patterns/single-source-state]], [[rule-patterns/state-display-differentiation]]

## Notes
- Visual redundancy can be useful for accessibility or table visibility, but only when both displays update from one authoritative state or cannot drift apart.
- A display that merely restates a count at scoring time is usually bookkeeping, not a separate game system.
- sources: https://boardgamegeek.com/blog/12853/blogpost/152858/writing-board-game-rules https://www.reddit.com/r/BoardgameDesign/comments/1tqkzog/whats_your_iteration_process_for_removals_and/ https://trepo.tuni.fi/bitstream/handle/10024/231015/KansikasVeera.pdf?isAllowed=y&sequence=2
