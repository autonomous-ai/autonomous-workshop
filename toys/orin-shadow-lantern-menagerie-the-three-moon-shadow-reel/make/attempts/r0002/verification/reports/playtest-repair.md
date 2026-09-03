# Round-2 accepted Playtest repair

This Make round is bound to `artifacts/playtest/r0001/playtested.json`
(`f14964f1f26df117dc65d48d51e4a384d3eb1df052edf782d0149d67becf283a`).
It changes the rejected round-1 bytes rather than resubmitting them.

## Owl and setup evidence

- The indexed owl retains a connected positive mask and adds broad symmetric
  facial-disc cheeks, exact triangular tufts, and 1.2 mm printable tuft caps.
- `evidence/shadows/shadow-sweep.json` is regenerated from the exact four STL
  meshes at every 5 degrees. It additionally records rabbit/fox/owl at all four
  400/500 mm source by 600/900 mm wall corners and owl at centered and ±2 degree
  yaw/pitch source offsets.
- `distance-corners-contact-sheet.png` and `alignment-sweep-contact-sheet.png`
  expose those cases. The rear projected portal bites remain the bilateral aim
  cue; the front leaf opening points directly at the reel's unique double-V.

## Reset, closure, retention, and stops

- The double-V is the only non-periodic rim feature. Rabbit's 0.50 mm pocket
  fully releases the nominal 0.50 mm flat deflection; fox/owl 0.25 mm pockets
  retain 0.25 mm, yielding the requested 0.25 mm differential.
- Four 0.4 mm top chamfers on printable 1.6 mm caps give each hook a 3.4 x
  5.2 mm lead through its 3.6 x 5.4 mm receiver. The 4.2 x 6.0 mm shoulder then
  retains 0.30 mm per side.
- `check_fit.py` audits those values. `motion.json` separately proves rigid
  shell pullout is blocked, deployed and folded overtravel are blocked, the
  ordinary stand arc is clear, and the reel completes 73 clear rigid poses.
  Elastic snap entry, spring strain, force, and life remain physical unknowns.

## Rear-shell print floor

- The rear optical face is 3.2 mm thick, its curved boundary is represented by
  stable broad facets, and the outer print face carries a broad 0.8 mm chamfer.
- Both the ordinary verifier report and the explicit `--voxel 0.16` report are
  required to pass with zero surface samples below the 0.8 mm wall floor.
- This is deterministic mesh evidence only, not a slicer run or physical print.

## Byte stability

Two independent cache-free source generations produced the same assembled STEP
SHA-256, `bb5108fe6a570a64e72aafd774de9cb6980392722c31ab6c0c234b0f8eadbf20`.
That differs from round 1's rejected-by-Playtest assembled STEP SHA-256,
`f58a818f8b91e75b6708c3bd50b0b7b0e78cfec4c027fc1c767c760ef899e04f`.
