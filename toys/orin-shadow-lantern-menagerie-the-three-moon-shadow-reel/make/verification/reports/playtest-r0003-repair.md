# Round-3 Playtest return repaired in Make round 4

Authoritative input: `artifacts/playtest/r0003/playtested.json`, file SHA-256
`6c53bd9f7693931419434477993124c1524cc4f6f1f2fefa4175bee6be213265`.

## `silhouettes-and-setup-cues-remain-ambiguous`

- `features/profiles.py` removes both flat fox ear caps, lowers and shortens the
  two triangular ears, sharpens the low muzzle, and moves the brush inward so
  it remains visible inside the portal.
- The owl keeps the sealed no-facial-hole constraint. A long external beak now
  projects into open shoulder notches; a pear torso and tapered angular wings
  replace the three round lower lobes that supported a bat/butterfly reading.
- `measure/render_shadows.py` regenerates all 72 motion samples, 12 distance
  corners, and 15 alignment cases from the exact new four-mesh set.
- `measure/render_setup.py` writes `snap/setup-wall-side.png`, an exact-mesh
  assembled view and close-up pairing the fixed shell pointer with both reel
  home-V notches at rabbit/reset.
- The rear shell's disconnected six-tile branch is replaced with a broad
  phone-shaped through-opening joined to a widening three-step beam below and
  aimed toward the portal. `snap/setup-phone-side.png` is rendered directly
  from the exact rear-shell STL.

These are digital geometry and image inspections. They do not prove human
recognition, first-use discovery, finite-emitter sharpness, or room contrast.

## `sealed-rear-shell-fails-fine-wall-replay`

The former 6 mm rectangular diagonal bearing rib met the chamfered rear shell
nearly tangentially. It now uses an 8 mm capsule seated from x=±46 mm into each
bearing block. The cited one-sample region near (-53.6, -37.9, 3.2) is absent
from the regenerated rear shell. `measure/thickness-rear_shell-fine.md` is
regenerated with an explicit 0.16 mm requested voxel and must report zero
samples below the 0.80 mm minimum on the exact delivered rear STL.

Exact round-4 binding after final fresh generation:

- prior rejected rear STL SHA-256:
  `30cc81047ada737b6dba58c53024546d84427c86c48c01b38ea45a6ad33cddcd`
- repaired rear STL SHA-256:
  `847811e2898dc2f971d7fa2c5539efe13064bb8770b4316cdd8879b9452c1b12`
- repaired reel STL SHA-256:
  `2a14b2ab6030b4dd14b5378262b603927598bfecc7c57700c56a61a58103a62e`
- exact fine report SHA-256:
  `a9de2cf779ba3e2aea93c65d5cefdf353a7801a385a2011c9e16f3f49d416692`
- fine result: 0 of 330,865 surface samples below 0.80 mm, thinnest
  resolved within the gate's 0.130 mm half-grid precision; requested voxel
  0.16 mm, effective grid 0.261 mm.

The check is a digital voxel/ray measurement. It does not prove a successful
print, layer adhesion, strength, snap life, or printer compensation.
