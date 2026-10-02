- Design Contract schema 3: every reference carries its Reference Camera,
  `"camera": [AZ, EL]` in the Display Pose frame, estimated by eye in
  design-a-toy and approved with the images. A component round compares each
  reference with the Component in its Display Pose, `assembly_pose(shape,
  None)`, seen from that camera; front, top and iso stay in the print stance.
  Every schema 3 Component defines `assembly_pose`. The Component Reviewer may
  answer camera mismatch, which is not a Shape Round and stops the run with a
  need; `workshop resume <id> --reference-camera FILE=AZ,EL` answers it with a
  host-recorded amendment of that one camera, listed in the receipt and the
  run report, while WISH.json, requirements and images stay sealed. Schema 1
  and 2 contracts and frozen runs are unchanged (ADR 0083, #81).
