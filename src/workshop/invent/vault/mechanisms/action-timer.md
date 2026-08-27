---
type: mechanism
name: "Action Timer"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Action Timer

## Definition
A mechanism where players have a fixed amount of real time (typically 1-5 minutes per turn or phase, measured by physical timer or hourglass) to complete their actions before the timer expires, forcing quick decisions and creating urgency. Tension arises from the audible/visible countdown and the penalty for exceeding the time limit, which can range from losing the turn to failing a cooperative objective.

## Relations
- component:: [[components/indexed-ratchet-wheel]]
- risks:: [[anti-patterns/fun-strategy-mismatch]]
- risks:: [[anti-patterns/analysis-paralysis]], [[anti-patterns/degenerate-strategy]], [[anti-patterns/idle-player]], [[anti-patterns/rules-overhead]]
- variant-of:: [[mechanisms/elapsed-real-time-ending]]

## Notes
Tension source is the clock itself, not decision branching—works best in cooperative or real-time games rather than highly tactical ones.
Reliably solves slowplay but rewards speed-of-execution over quality of decisions; experienced fast players gain advantage.
sources: https://bombardgames.com/board-game-mechanics-action-timer/ https://www.smartpicks.co.uk/beat-the-clock-the-tension-and-thrill-of-the-action-timer-mechanic/ https://www.boardgameatlas.com/mechanic/j2A0uFmdgc/action-timer https://tabletopgamesblog.com/2023/10/31/about-time-time-as-a-mechanism-in-board-games-topic-discussion/
- [yt:QHHg99hwQGY] medium: With the suspend delay mechanic, players instinctively attacked with a just-resolved creature despite a rule forbidding it; designers changed the rule to match instinct instead of fighting it. (GDC Festival of Gaming 2016)
