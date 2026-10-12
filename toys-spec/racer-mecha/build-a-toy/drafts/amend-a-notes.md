# amend-a (2026-10-12): two invisible contract fixes from round 0 attempt 2

Run `wish-20261012-054637-a6c52bd4` (Claude Code, Opus 5.5, medium) stopped `waiting` with a
Contract Contradiction need after both in-run amendments for R06 were refused.

## Contradictions

1. **R06 vs head-slide.** R06 required 0.5 mm between every pair of moving parts in both poses.
   The head-slide Interface declares three contacts: the lowered helmet resting on the pocket
   floor at Z 156, and the 3 mm dowel stopping at both ends of the post's 3.4 slot. The slot also
   leaves only 0.2 mm on each side of the dowel. The run's in-run amendment 1 exempted only the
   helmet. Its second amendment deleted R06's clearance sentence. The Contract Reviewer refused
   both and named the smallest fix, adopted here word for word. The prose rule under Motion and
   fit carries the same exception.
2. **R02 car height.** R02 and the Car pose prose said 44 tall. In the car pose the spine's airbox
   scoop (Y 15.5 to 22 in the robot pose) flips to Y 29.5. The ground is at Y -19 (the wheel
   bottoms), so the car is 48.5 tall. The run's own draft, `.tmp/amend-r02.json` (never
   proposed), said 47.5 because it counted only the knuckle.
   Changed to 48.5 in R02 and in the prose.

## Visibility

Every reference shows the robot pose. The car pose's height, the hidden pocket floor and the
slot clearances appear in none of them. Both changes are invisible, so no image changes and no
owner approval is needed.

## Re-audit

- **3b:** no image is touched and no landmark moves, so the earlier tables still hold.
- **3c:** no printed geometry changes.
- **3d:** `model.py` had drawn the nose knuckle as a full R5.7 cylinder, so it reported the
  nose 0.7 below the ground. The contract's knuckle is R3.5 round with a 5.7 teardrop below the
  axis, now modelled as TEARX. In the rerun (`checks.txt`), every sweep is >= 0.5. The nose
  clears the torso by 1.0. The nose stands 1.5 above the ground, which meets R04, and the car
  height reads 48.5.

## design-a-toy checks that would have caught these (proposed)

- Stage 3d: a global clearance row must list the contacts that an Interface itself declares
  (end stops, resting faces, running fits under 0.5).
- Stage 3d: every stated envelope of a non-display pose (car length, width and height) is
  measured from the pose model, not carried from the brief.
