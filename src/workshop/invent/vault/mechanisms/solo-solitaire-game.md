---
type: mechanism
name: "Solo / Solitaire Game"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Solo / Solitaire Game

## Definition
A single player competes against the game system itself rather than other people — either by racing a fixed scoring target/threat clock, or by playing against a scripted 'automa' opponent whose moves are resolved through a deterministic flowchart or a small priority-ordered card/token deck. The tension comes from optimizing under resource and turn-order constraints against an adversary that never bluffs, hesitates, or misplays, so the challenge is entirely pre-tuned by the designer rather than emergent from another mind. Because the opponent is scripted, most designs inject variance through random draws, shuffled priority cards, or dice so the same session doesn't play out identically every time.

## Relations
- conflicts-with:: [[mechanisms/voting]]
- conflicts-with:: [[mechanisms/team-based-game]]
- conflicts-with:: [[mechanisms/prisoner-s-dilemma]]
- conflicts-with:: [[mechanisms/player-judge]]
- conflicts-with:: [[mechanisms/i-cut-you-choose]]
- risks:: [[anti-patterns/alpha-solve]]
- risks:: [[anti-patterns/rules-overhead]], [[anti-patterns/decided-early]], [[anti-patterns/degenerate-strategy]]

## Notes
Automa complexity is the core design tradeoff: too simple and the bot feels inert, too elaborate (e.g. COIN-series flowchart bots) and tracking its logic becomes a second job layered on top of playing your own turn.
A fixed victory target turns the game into a puzzle with one best line, which players can eventually solve and then replay on rails rather than genuinely re-decide each time.
sources: https://punchboard.co.uk/blog-solo-modes-in-board-games-part-two-automa/ https://punchboard.co.uk/blog-solo-modes-in-board-games-part-one/ https://fantastic-factories.medium.com/how-i-designed-the-solo-rules-for-fantastic-factories-2d840381153 https://www.brettspiel-news.de/index.php/de/magazin-fuer-brettspieler-start/15412-to-bot-or-not-to-bot-brauchen-brettspiele-ki-gegner
