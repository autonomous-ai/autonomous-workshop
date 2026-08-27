---
type: mechanism
name: "Mancala"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Mancala

## Definition
Mancala is a stone-distribution mechanism where players cyclically move all seeds from one pit, depositing them one-per-space around a board. The central tension arises from the extra-turn rule: if your last stone lands in your own store, you move again, creating opportunities to chain turns and accumulate resources. Opponent interception (capturing across pits) and turn-gating through precise placement produce the strategic friction.

## Relations
- component:: [[components/mancala-pocket-board]]
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/decided-early]], [[anti-patterns/silent-calc]], [[anti-patterns/analysis-paralysis]]

## Notes
Mechanism is dependent on cycle-circuit topology and exact pip-counting; does not scale well beyond 2 players without rule invention.
Some variants (Kalah, Awari) are weakly or strongly solved, reducing strategic depth to memorized openings and pre-determined draws.
sources: https://gameonfamily.com/blogs/tutorials/mancala https://www.ultraboardgames.com/mancala/game-rules.php https://digitalcommons.andrews.edu/cgi/viewcontent.cgi?article=1259&context=honors https://mancala.fandom.com/wiki/Solved_game
