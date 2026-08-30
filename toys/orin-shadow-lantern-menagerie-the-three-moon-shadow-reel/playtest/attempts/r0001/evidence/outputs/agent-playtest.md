# Agent playtest — indexed shadows and first-use read

Binding: Made product artifact
`3c7abf41a4aed6005216e14ad42c5c027e7560ff8cd887f3c991917141d1f7cd`.
Two independent native reviews inspected the exact product render, three
indexed projection PNGs, the 72-state contact sheet, and the static sweep JSON.

## Observed digital evidence

- Rabbit (`state-rabbit-000.png`, SHA-256 `7740282f...`) reads immediately from
  its long ears, haunch, muzzle, and tail.
- Fox (`state-fox-120.png`, SHA-256 `1664e1a3...`) is reasonably distinguishable
  by the snout, ears, horizontal body, and large rising tail.
- Owl (`state-owl-240.png`, SHA-256 `fdbef14c...`) reads chiefly as a symmetric
  oval or pawn-like mass. The promised triangular ear tufts, wing/body
  separation, and perch do not survive as unmistakable projected features.
  This fails the Wish's exact three-unmistakable-creatures requirement.
- The contact sheet (SHA-256 `39426c10...`) truthfully shows all 72 sampled
  poses in 5-degree increments. It exposes tilted/cropped animals, overlap,
  separator spokes, and eclipse wipes instead of implying a literal morph.
- The static sweep (SHA-256 `b1e2e7f6...`) records indexed dark fractions of
  `0.476074` (rabbit), `0.538855` (fox), and `0.601517` (owl). The full-cycle
  range is `0.261028` at 300 degrees through `0.601517` at 240 degrees; the
  largest adjacent 5-degree change is `0.047162` from 265 to 270 degrees.
- The nominal point-source setup is 450 mm source-to-mask and 750 mm
  mask-to-wall with a 116.223 mm projected portal. No exact projection evidence
  challenges all four distance-band corners or bounded yaw/pitch errors.
- The navy/gold render makes the moon-gate form and deployed stand intriguing,
  but the turn direction, phone-facing side, and unique rabbit reset are not
  self-evident in that view.

## Result

**FAIL — implementation improvement in Make.** Preserve the open-carrier
three-profile concept, but revise the owl so its ear tufts and wing/body
separation survive exact portal clipping, add legible reset and beam-direction
cues, then regenerate the indexed views and full sweep. Add point-source tests
at the four stated distance-band corners and bounded alignment offsets.

This agent review is not a human play session. It does not prove recognition by
children, delight, brightness in a normal room, phone-emitter edge softness,
first-use discovery, stability, fit, or any physical response.
