# Round-3 accepted Playtest repair

This Make attempt is bound to `artifacts/playtest/r0002/playtested.json`
(`2f5754bbc710425c18226427d49be6b77af7896a337d6b596a4ed29fed2b2349`).
It changes the previously Playtest-rejected Make bytes.

## Recognition and fixed setup cues

- The fox now has an angular muzzle, two low triangular ears, four legs, and a
  large angular brush. The owl has a bilateral horned head, central V crown,
  separated lower wings, two feet, and a broad perch. Printable rounded/flat
  tip caps preserve those reads without sub-0.8 mm wedges.
- Exact four-mesh point-source evidence contains 72 reel poses, all 12
  state-by-distance corners, and all 15 rabbit/fox/owl centered and plus/minus
  2 degree yaw/pitch cases. The indexed fox and owl PNGs and the alignment
  contact sheet were visually inspected.
- A large fixed through-arrow on the wall shell points to the reel's unique
  right-rim double-V at rabbit home. Six 5 x 5 x 1.6 mm raised tiles form the
  tactile phone/beam arrow on the rear shell and point toward the portal.

## Detent, closure, and stand

- A 0.95 mm-radius nose and symmetric 0.70 mm-run by 0.18 mm-deep conical
  pocket ramps provide the same cam path in either reel direction. Rabbit
  releases the nominal 0.50 mm flat deflection; fox/owl retain 0.25 mm, for a
  0.25 mm home differential.
- Each shell latch flexes only toward +X. The leading face has 0.4 mm X/Y
  clearance, the positive retention shoulder is 0.6 mm, and the unloaded
  negative-side clearance is 0.2 mm. Four receiver-entry proxies are clear;
  rigid pullout is blocked as intended.
- The stand source endpoint is 112 degrees. Source geometry measures deployed
  depth at 82.395 mm. Its 57-step deployed-to-folded sweep is clear, and both
  endpoint overtravel checks block against the rear shell as intended.
- The rigid reel completes 73-step clockwise and counterclockwise sweeps. That
  proves hard-part clearance, not compliant leaf force or life.

## Manufacturing and byte evidence

- Fresh verification passes layout, STEP validation, zero-clash interference,
  the 220 mm bed, watertight/manifold meshes, and the 0.80 mm wall floor for all
  four parts. The rear shell additionally passes the explicit `--voxel 0.16`
  audit with zero below-minimum samples.
- The widest part is exactly 114.0 mm. The final assembled STEP SHA-256 is
  `c5b591165c8e380faffcd359e5cbc5c11020819e16f548d018a3f4b4d21ec7ef`,
  changed from round 2's `bb5108fe6a570a64e72aafd774de9cb6980392722c31ab6c0c234b0f8eadbf20`.
- All evidence is digital. It does not establish a successful physical print,
  brightness, recognition by people, fit/force, strength, or cycle life.
