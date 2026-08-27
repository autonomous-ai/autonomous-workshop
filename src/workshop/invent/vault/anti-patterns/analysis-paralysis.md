---
type: anti-pattern
name: "Analysis Paralysis"
created: 2026-08-21
source: manual
status: reviewed
---

# Analysis Paralysis

## Definition
The optimal move is computable and the state space invites computing it, so somebody does — every turn. One player's search time becomes everyone's downtime.

## Relations
- mitigated-by:: [[rule-patterns/action-timer]], [[rule-patterns/simultaneous-reveal]]

## Notes
Caused by design (open information, high branching, no pressure), only expressed by personality. Fix the design.
- [yt:z7_s7KdrtpA] medium: Hidden victory points (Ticket to Ride's destination cards) prevent players from calculating exact standings, forcing faster instinct-based decisions instead of precise optimization. (Adam in Wales - Board Game Design 2016)
- [yt:F_1YcCcBVfY] medium: Struggle of Empires makes new players choose 1 of ~30 special-power tiles before they understand the game; veterans recommend curating 2-3 tiles for first-time players to avoid overwhelming them. (GDC Festival of Gaming 2018)
