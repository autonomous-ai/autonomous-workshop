---
type: mechanism
name: "Cube Tower"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Cube Tower

## Definition
Players drop colored cubes into a tower filled with internal pegs and shelves, and cubes tumble unpredictably out the bottom while some remain trapped inside. Tension emerges from the tower's hidden state—players can never know precisely which or how many cubes will emerge next, making outcome odds unquantifiable, forcing timing decisions on whether to commit resources now or wait and risk opponent action.

## Relations
- component:: [[components/gravity-randomizer-tower]]
- risks:: [[anti-patterns/fiddly-reset]]
- risks:: [[anti-patterns/luck-swing-endgame]], [[anti-patterns/missing-info]], [[anti-patterns/silent-calc]], [[anti-patterns/decided-early]]

## Notes
Tower state acts as a form of distributed memory: cubes trapped inside create turn-to-turn dependency that pure dice cannot replicate.
Intentionally defeats probability calculation—no clear odds distribution prevents conservative play strategies that randomizers often encourage.
sources: https://www.clife.space/post/detail/51/ https://boardgamegeek.com/boardgamemechanic/2990/cube-tower https://en.wikipedia.org/wiki/Wallenstein_(board_game)
