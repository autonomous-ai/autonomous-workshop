---
type: anti-pattern
name: "Unreachable"
created: 2026-08-24
source: agent
status: reviewed
---

# Unreachable

## Definition
A win condition or required game state that no sequence of legal moves can actually produce, making the game unwinnable from setup or from an early reachable state.

## Relations
- mitigated-by:: [[rule-patterns/goal-reachability-validation]]

## Notes
- A merely difficult or strategically lost position is not unreachable if some legal winning continuation still exists.
- Check reachability after every irreversible rule interaction, not only from the initial setup.
- sources: https://www.chiark.greenend.org.uk/~sgtatham/puzzles/devel/writing.html https://gamelab.mit.edu/research/puzzledice/ https://homes.cs.washington.edu/~zoran/answer-set-level-design.pdf
