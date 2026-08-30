# Mechanical check — PASS (digital geometry)

## Exact binding

- Made file SHA-256: `5b7a7b1c331d65be6b2824d57036052cb8e0661bc640f51de78e39b4237d30cb`
- Product artifact SHA-256: `9ff89565b9c5aa91e7338007c641607da1c3afa0ba9a3cafe749ef9d2cc20403`
- Assembled STEP SHA-256: `6f087a38cf14ac5015f5040e97529b72d7306415b9fbf97a4c30a242e6a38528`
- CAD verification SHA-256: `901d728f88e5ce7a83e2f43f73c710d436d2372ec1928ffd25efb8b1b26355c9`
- Motion manifest SHA-256: `288ffcdae0a60ee48a912bb97cca9fe2906cb23906df316ff0df491a6940c2d4`
- Final pipeline SHA-256: `1f3f803227254a20c974863c75a07115584f3f52b387c69e5676e1e8e25ea574`

All 63 product-manifest files rehashed exactly. Root replay used an isolated copy of the sealed CAD source with a run-local font cache; no sealed product bytes changed. An independent mechanical reviewer separately audited the bindings, source ledgers, and condition semantics.

## Replay results

- Shared nominal fit: 21/21 checks passed, including 0.30 mm spindle radial/blind-end clearance, 0.30 mm axial gaps, one-axis latch clearances/overhang, rounded detent nose/ramp values, and the authored rabbit-home differential.
- Specification: 24/24 checks passed, including four single-solid positive-volume bed-zero parts, 114 x 114 x 3.2 mm reel, 44 mm portal, 112-degree stand deployment, 82.395 mm source endpoint depth, and four-part count. The exact assembled STEP bounding-box depth is 82.844649 mm.
- Motion: 10/10 conditions passed in a fresh root replay:
  - reel clockwise full cycle: 73 samples clear;
  - reel counterclockwise full cycle: 73 samples clear;
  - four 3 mm latch leading-path proxies: clear;
  - retained front-shell pullout: blocked by rear shell at step 1/21, overlap 2.857143 mm³;
  - kickstand deployed-to-folded arc: 57 samples clear;
  - deployed overtravel: blocked at step 1/11, overlap 0.777264 mm³;
  - folded overtravel: blocked at step 6/21, overlap 30.080143 mm³.

The sealed final pipeline independently records exit 0 for source generation, strict fit, local audits, 10-condition motion, STEP validation/interference inspection, exports, mesh/bed checks, and wall checks.

## Limits

Rigid/proxy geometry does not prove elastic latch or detent force/feel, snap strain or survival, physical retention, printer compensation, printed fit, stand tipping/load behavior, pinch safety, strength, durability, or cycle life.
