---
type: anti-pattern
name: "Missing Info"
created: 2026-08-21
source: agent
status: reviewed
---

# Missing Info

## Definition
A rule needs information no listed component can carry.

## Relations
- mitigated-by:: [[rule-patterns/single-source-state]], [[rule-patterns/component-complete-state]]

## Notes
- A rule is incomplete in practice when its required input disappears from the table state.
- Blind rules tests should include disturbed pieces, neutral objects, ties, and boundary cases.
- sources: https://boardgamegeek.com/blog/12853/blogpost/152858/writing-board-game-rules https://daniel.games/writing-a-rulebook/ https://d-nb.info/116389902X/34
