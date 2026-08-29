# Printability check — PASS (digital artifact checks)

## Exact binding and inventory

- Made file SHA-256: `5b7a7b1c331d65be6b2824d57036052cb8e0661bc640f51de78e39b4237d30cb`
- Product artifact SHA-256: `9ff89565b9c5aa91e7338007c641607da1c3afa0ba9a3cafe749ef9d2cc20403`
- Manifest audit: all 63 regular files and 13,632,876 bytes rehashed exactly, with no missing, extra, size-mismatched, hash-mismatched, or linked file.
- Independent printability reviewer recommendation: pass within digital scope; no evidence inconsistency found.

## Exact sealed STL replay

Fresh read-only `check_mesh --bed 220x220x220` passed every exact STL as watertight, manifold, consistently wound, positive-volume, single-shell, and bed-fitting:

| part | exact SHA-256 | bed extent (mm) | result |
|---|---|---:|---|
| front shell | `05f5954fe1478cd30668e6bbd592ed14fcbe2b554dd3d1c6030975f66d3f4a29` | 108.0 x 123.0 x 11.0 | pass |
| kickstand | `8a68cbdcdc7571575272218d6df449a5e76af1e2de81ade354a191dce5584cfa` | 108.0 x 76.5 x 9.0 | pass |
| rear shell | `847811e2898dc2f971d7fa2c5539efe13064bb8770b4316cdd8879b9452c1b12` | 114.0 x 123.0 x 12.7 | pass |
| shadow reel | `2a14b2ab6030b4dd14b5378262b603927598bfecc7c57700c56a61a58103a62e` | 114.0 x 114.0 x 3.2 | pass |

## Wall evidence and exact rejection repair

At a 0.4 mm nozzle / 0.80 mm minimum wall, the sealed reports record:

- Front shell: 0/330,383 samples below minimum.
- Kickstand: 0/151,551 below minimum.
- Rear shell standard: 0/322,642 below minimum.
- Shadow reel: 0/394,016 below minimum, 0.170 mm grid / 0.085 mm resolution; report SHA-256 `4ee2c0cfa4c1f77cfdde1912f15d88ea51569ca4ef59c99cd68d36ac3b2c31a1`.
- Rear shell fine replay: **0/330,865 below minimum**, requested voxel 0.16 mm, effective grid 0.261 mm, resolution 0.130 mm. Root replay reproduced the same counts from the exact sealed rear STL. Report SHA-256: `a9de2cf779ba3e2aea93c65d5cefdf353a7801a385a2011c9e16f3f49d416692`.

The rejected rear STL SHA-256 `30cc81047ada737b6dba58c53024546d84427c86c48c01b38ea45a6ad33cddcd` changed to `847811e2898dc2f971d7fa2c5539efe13064bb8770b4316cdd8879b9452c1b12`. The fine report directly names the current round-4 product path; the prior one-sample knife edge at (-53.6, -37.9, 3.2) is absent. Hollowability WARN rows are optimization observations, not wall failures.

## Limits

No slicer/toolpath or support analysis, successful print, warping, layer adhesion, printer compensation, physical fit, snap compliance/force, detent feel, strength, or cycle test was performed.
