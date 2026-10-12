# amend-c — the contract's own joints set the wall floors and two extents

Found by round 0 detection (r00/findings.json); owner approved lowering the
wall floors to what the joints force (2026-10-12).

| Row | Was | Now | Why |
|---|---|---|---|
| torso wall_min_mm | 3.0 | 1.1 | Ø7 nose-hinge cheek around a teardrop Ø2.9 bore (faces 38° from vertical) leaves 3.5 − 1.45/cos 52° = 1.14 above it; hip bore at Z 102 is 3 above the Z 99 bottom, 1.55 below it |
| nose wall_min_mm | 2.0 | 0.9 | R3.5 knuckle around a teardrop Ø3.1 bore: 3.5 − 1.55/cos 52° = 0.98 |
| head wall_min_mm | 3.0 | 1.9 | neck post 8 with a 3.4 slot: 2.3 a side |
| thigh wall_min_mm | 3.0 | 1.4 | knee bore at Z 80.5 is 3 above the Z 77.5 bottom: 1.55 |
| shin wall_min_mm | 3.0 | 1.9 | R4 knee tongue around Ø3.1: 2.45 |
| thigh tongue | R4, Y −6 to 2, extents Z 28.5 | R3.7, Y −5.7 to 1.7, extents Z 28.2 | the torso hip slot's pointed-arch roof is 4.24 from the hip axis; R06's 0.5 clearance allows at most 3.74 (the build chose 3.7) |
| shin extents Y | 27 | 28 | block Y −13 to 9 plus the 1.0 proud knee pad (to Y −14) and heel to Y 14 |

Prose: load-bearing paragraph states each joint-forced floor; thigh and shin
paragraphs and the hip-1 Interface text follow the new tongue.

Re-measured on v01 (r00/detect/thickness19/): torso PASS at 1.1, nose PASS
at 0.9, head PASS at 1.9, thigh PASS at 1.4, shin PASS at 1.9. v01's thigh
measures 28.2 and its shin 28.0, matching the amended extents.

Stage 3d misses (design-a-toy checks to add): a tongue's radius against a
pointed-arch slot roof; a wall_min below what a teardrop bore inside its
cheek leaves; extents that omit a proud pad.
