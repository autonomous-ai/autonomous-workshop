# Agent playtest — silhouettes, coverage, transitions, and setup cues

Binding: exact Made product artifact
`7670e30199d25813d015f1b36cf8962e78a01722cff02524ee3240b938793d00`.
An independent native visual reviewer and the root Manager inspected the exact
sealed images and source without modifying Made bytes.

## Coverage that passes

- The alignment sheet contains all 15 required cases: rabbit, fox, and owl at
  centered, ±2° yaw, and ±2° pitch. Dark-fraction ranges are
  `0.473330–0.475607` for rabbit, `0.491799–0.493902` for fox, and
  `0.597539–0.601283` for owl.
- The distance sheet contains all 12 state/source/wall corners. Projected
  portal diameter spans `95.975–141.479 mm`; within-state dark fraction is
  stable across the distance band.
- The motion sheet contains 72 poses at 5° increments. Dark fraction spans
  `0.295329–0.597897`, with maximum adjacent change `0.043463`. It truthfully
  shows indexed animals separated by eclipse wipes and makes no continuous
  recognition claim.

## Failing independent visual judgment

- Rabbit reads immediately from its long ears, muzzle, haunch, and tail.
- Fox is not unmistakable without its caption. Its two long capped stalks read
  as antelope/giraffe horns or antennae more readily than compact fox ears.
  The large tail suggests a fox or squirrel, but does not settle the reading.
- Owl is also ambiguous without its caption. The horned/crowned upper mass and
  paired lower lobes can read as a bat, butterfly, or mask; no eye or decisive
  beak cue settles the silhouette.
- `setup-wall-side.png` shows a large fixed arrow only on an isolated shell.
  Neither the assembled front nor ISO view visibly demonstrates that fixed
  pointer together with the reel's matching double-V, so reset discovery is
  not established.
- `setup-phone-side.png` shows six raised tiles, but the resulting branch/Y
  glyph does not unambiguously communicate a phone, flashlight, or beam.

Exact hashes include rabbit `c5275513…`, fox `695f851c…`, owl `05c0f983…`,
distance sheet `2f458ed4…`, alignment sheet `009e7a0f…`, motion sheet
`1bf7b2d6…`, ISO render `50ee18bc…`, wall-side setup `f0a9bd9f…`, and
phone-side setup `a153913f…`. Silhouette source is `cad/features/profiles.py`
(`0ef1aab9…`); cue source is `cad/parts/shells.py` (`8eae1508…`).

## Result

**FAIL — implementation improvement in Make.** Use compact triangular fox
ears and a clearer low muzzle/brush profile. Give the owl decisive eye/beak
negative space or a much clearer external beak and less bat-like wing/body
lobes. Add an assembled wall-side view that visibly pairs the fixed pointer
with the home V, and replace the abstract tile glyph with an unmistakable
phone/flashlight/beam arrow.

This is digital native-agent judgment, not a human play session. It proves no
human recognition, delight, finite-emitter sharpness, room contrast, first-use
behavior, physical fit, print success, strength, durability, or safety.
