---
type: mechanism
name: "Impulse Movement"
created: 2026-08-21
source: agent
status: seeded
bgg_id: null
---

# Impulse Movement

## Definition
Players maintain a shared queue of action cards that all participants execute in sequence. Each turn, a player adds one card to the queue, then executes every action in it from oldest to newest, then discards the oldest card. The core tension emerges from dual optimization: you choose a card that benefits you now, but that same card will be available to your opponents later in the turn order, potentially harming you.

## Relations
- risks:: [[anti-patterns/alpha-solve]], [[anti-patterns/analysis-paralysis]], [[anti-patterns/first-player-advantage]], [[anti-patterns/silent-calc]]
- variant-of:: [[mechanisms/action-queue]]
- requires:: [[rule-patterns/forced-engagement]]

## Notes
Creates emergent 'betrayal by proxy' gameplay where your own contributions weaponize against you.
Wargame variants (e.g., Star Fleet Battles) use impulse points instead, giving each unit discrete activation windows within a turn rather than a shared queue.
sources: https://spacebiff.com/2014/10/13/impulse/ https://islaythedragon.com/featured/review-impulse/ https://www.shutupandsitdown.com/tag/impulse/ https://theplayersaid.com/2018/03/20/old-school-tactical-volume-2-west-front-1944-1945-from-flying-pig-games-action-point-2/
