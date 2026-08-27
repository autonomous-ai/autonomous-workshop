---
type: mechanism
name: "Critical Hits and Failures"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Critical Hits and Failures

## Definition
Critical hits and failures are extreme outcomes triggered by exceptional die rolls (typically the highest or lowest result) that generate effects far beyond normal success or failure. The tension stems from random, uncontrollable moments that can dramatically swing the game state—a catastrophic fumble or miraculous success—creating both excitement and the risk of trivializing prior decisions through sheer luck.

## Relations
- component:: [[components/gravity-randomizer-tower]]
- risks:: [[anti-patterns/uncontrolled-permanence]]
- risks:: [[anti-patterns/luck-swing-endgame]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/decided-early]], [[anti-patterns/missing-info]]
- variant-of:: [[mechanisms/die-icon-resolution]]
- requires:: [[mechanisms/dice-rolling]]

## Notes
Design success depends entirely on calibration: too common and criticals dominate strategy, too rare and players ignore them.
Different implementations (binary nat-20s vs. graduated degree-of-success systems) show the pattern tolerates wide variation, making it fragile to unintended probability shifts.
sources: https://www.meeplemountain.com/mechanisms/critical-hits-and-failures/ https://tvtropes.org/pmwiki/pmwiki.php/Main/CriticalFailure https://diceroll.uk/blogs/guides/should-you-use-critical-fails-successes https://wizardsrespite.com/2024/10/27/mastering-critical-hit-mechanics-in-ttrpg-design-how-to-calculate-critical-hit/
- [yt:av5Hf7uOu-o] medium: Valve added swingy crits to Team Fortress 2 so newer players felt they could win; years later they dialed down (not removed) the swing once the audience matured and wanted skill more visible. (IGDA Denmark 2013)
- [yt:ZSVREGmO1Xw] medium: Risk Legacy let a triple-six roll permanently destroy map regions at random; the uncontrollable timing taught him permanent effects should be player-triggered, not luck-triggered. (GDC Festival of Gaming 2021)
