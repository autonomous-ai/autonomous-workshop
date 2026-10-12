# Racer Mecha - transformation feasibility check (2026-10-12)

Mapping checked: the colour-coded four steps in `review.html`. Arithmetic in
`feasibility.py` (car frame: x from tail to nose; robot z = height). Car 230 long
at these numbers gives a 218 mm robot, so the whole toy scales by 0.92 to hit
200 mm (car ~212 long, ~88 wide).

| # | Check | Result | Fix |
|---|---|---|---|
| 1 | Total robot height | 218 at car 230 | Scale whole toy 0.92 |
| 2 | Nose folds onto chest | 50 nose covers shoulder to upper belly | OK |
| 3 | Arm length | Front sidepod is 45, arm needs ~80 | Forearm slides 35 out of the sidepod shell; fist flips out |
| 4 | Chest width | Monocoque alone ~31, image chest ~55 | Inner half of each front sidepod stays on the torso; arms are the outer shells |
| 5 | Rear wheel height | Centre 50 above floor (image ~52) | OK |
| 6 | Balance | Backpack pulls COM to x -1.8; foot from ankle forward (0..30) leaves it on the edge | Heel flap folds back from the diffuser: foot -15..30 |
| 7 | Backpack height | Spine 110 puts the rear wing 22 above the head | Spine 90: wing top level with head top; rear wing sits just behind the rear wheels in car form |
| 8 | Backpack over cockpit | Spine lying up the back hits the halo | Spine hinge stands the backpack 15 off the back |
| 9 | Front wing on the belly vs arms | Full-width wing (~88) sits in front of the hanging arms | Front wing 70 wide; shoulders limit forward arm swing |
| 10 | Head pocket vs front axle | A through-axle crosses the pocket | Front wheels on stub axles; head pocket 18x22x18 between them |
| 11 | Legs in car vs robot | Legs at Y +-(7..30) both forms once the spine leaves | No hip slide needed |

Verification limit: Workshop's likeness gate scores the robot (Display Pose)
only. Car-form packing is checked through coupled Interface pose tables with a
car pose and a robot pose for every hinge.
