---
type: mechanism
name: "Memory"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Memory

## Definition
Players flip face-down cards to find matching pairs. On each turn, a player reveals two cards; matching pairs are scored and removed, while mismatches are re-hidden. The mechanism generates tension through spatial memory and information revelation—early flips create a public knowledge pool that players leverage to find pairs more efficiently than opponents. Winning depends on both memorization ability and the luck of guessing unrevealed card positions.

## Relations
- component:: [[components/tile-dispensing-magazine]]
- risks:: [[anti-patterns/first-player-advantage]], [[anti-patterns/luck-swing-endgame]], [[anti-patterns/alpha-solve]], [[anti-patterns/silent-calc]]

## Notes
Memory approaches zero luck in practice if players have perfect recall; nearly all tension evaporates with optimal play, limiting depth.
Pure memory mechanics offer thin strategic appeal; modern implementations layer additional rules (time pressure, hidden scoring, resource costs) to sustain engagement.
sources: https://www.gameistry.in/post/game-mechanisms-part-2-match-think-win-and-strategize-your-memory https://circlejgames.com/memory-mechanic/ https://www.cardboardempire.blog/blog/memory-two-ways/ https://www.geekyhobbies.com/how-to-play-the-original-memory-game-rules-and-instructions/
