# amend-b (2026-10-12): the elbows no longer bend forward

## The stop
Run `wish-20261012-054637-a6c52bd4` stopped at 09:40Z with a Contract Contradiction need.

The contract had the elbows bending 90 degrees forward, in R05 and in the elbow-1 and elbow-2
Interfaces. R15 and ref-05 close the arm shell's front wall down to its bottom. The elbow axis
(Y -2, Z 124) sits 6 above the shell bottom and 8 behind the wall's inner face.

The run's check_motion found the forearm overlapping the wall: 28 mm3 at -18 degrees and
468 mm3 at -90.

## Owner decision (2026-10-12)
Drop the forward elbow bend (option 1). The other option, opening the front wall up to Z 132,
was visible: it would have needed a new image and a relaunch.

## Changes
- **R05:** "elbows 90 forward" removed.
- **elbow-1 and elbow-2 text:** the forward bend is removed. The 180 degree fold back for the
  transformation is unchanged.
- **Prose posing line:** says the elbows do not bend forward.
- No pose table changed: the poses held only the +180 fold.

## Why Stage 3d missed it
`model.py` swept the elbow posing at +90. That is the fold's own direction, backward through the
open back. The forward bend is negative. The check is removed with the bend.

## Re-audit
- **3b:** no image changes and no landmark moves.
- **3c:** no printed geometry changes.
- **3d:** rerun of `checks.txt`. It is identical except for the two removed elbow rows, and every
  sweep is >= 0.5.
- **Visible:** no.
