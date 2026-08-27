---
type: anti-pattern
name: "Handling Wipe"
created: 2026-08-24
source: agent
status: reviewed
---

# Handling Wipe

## Definition
A required handling motion (sweep, lift, reset) moves or destroys game state mid-game.

## Relations
- mitigated-by:: [[rule-patterns/reset-in-place]], [[rule-patterns/mass-stability-tuning]]

## Notes
- Treat every required lift, flip, sweep, or reset as a collision test: nearby state should remain legible and stationary throughout the motion.
- Prefer indexed wells, rails, overlays, or captive markers when a handled component must share space with persistent state.
- sources: https://boardgames.stackexchange.com/questions/51314/how-can-i-hold-pieces-in-place-between-turns https://boredgamegeeks.blogspot.com/2005/12/shannons-list-of-dos-and-donts-for_08.html https://www.reddit.com/r/BoardgameDesign/comments/1kg9bac
