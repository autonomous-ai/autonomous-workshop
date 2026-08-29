# Moonwake Garden mechanical check

## Recommendation

**PASS** for the bounded digital mechanical check of the sealed Made revision. The evidence supports geometry-level rotation, three-position indexing geometry, axial capture, a plausible ordered assembly path, nominal clearances, optical-state isolation, and fresh-build reproducibility. It does **not** establish elastic forces, printer-process fit, retention strength, fatigue, wear, durability, a successful print, optical brightness, or human response.

## Sealed subject

- Playtest subject: `315ed802ae675a75367c0b9be4dc6bfc6ff8859885366227a81a009b0fe003c7`
- Made file: `artifacts/make/r0002/made.json`, SHA-256 `c19c13c6c9d71d2e38e95e4c56b380ba524b9466faf05ec223922c469b49d827`
- Made contract identity: `f02f4e2ee6273ecc7007ddea9fe772886615a9d4b97387213d4aeb1e0a707f8a`
- Product artifact: `d31e05cf5a70714e41d2f26cf2bc7e4ef25a2cbd63545cda651a527c3f76874a`
- Combined STEP: `artifacts/make/r0002/product/assembled.step`, SHA-256 `7d5f4f1f0f88c1bf236a80370b02ca7048e7917efbf5d231706c90d9f5e7682f`
- CAD verification: `artifacts/make/r0002/product/cad-verification.json`, SHA-256 `e75b8c456a40312a25ad224f831b43113239f0ecb044cfd7b5f0cb79e7d943dc`

The sidecar at `artifacts/make/r0002/product/assembled.step.json` (SHA-256 `7e24aa249b4615ef9345d5a3de3c974dec30f5f398deedaa804f874cecb0d7e3`) identifies three separately printable occurrences—rear chassis, sector rotor, and front garden mask—within an 84 x 76 x 6 mm assembly. It records kernel-valid geometry, zero assembly interferences, and a watertight/manifold three-shell assembled mesh.

## Findings

### Rotation and running clearances — pass at geometry level

- `cad/moonwake_garden/measure/motion.json` (SHA-256 `1621fa43a99db9e36d5f852f6ce6834b0fe413eaae80d1965dea6e0e6bac9dd6`) declares a 37-sample, 360-degree rigid rotation sweep with only the elastic detent tooth suppressed. The final pipeline records that this manifest exited zero, and `cad-verification.json` records four passed motion conditions.
- The proxy source `cad/moonwake_garden/motion_proxy.proxy.py` (SHA-256 `2adb622ba68044a3246db075430be6308e29bfee71e41ee40e8112db2274c8a0`) removes only the tooth volume; spindle, guide, front mask, and rotor geometry remain present. This is an appropriately bounded proxy for the rigid clearance question.
- The review-time source audit `measure/check_fit.py` reran with status `pass` and no errors. It reported 0.30 mm radial spindle/bore clearance, 0.40 mm radial rotor/guide clearance, and 0.30 mm axial rotor clearance. The assembly pipeline separately records zero home-pose interference.
- These results support unobstructed nominal rotation once the tooth flexes. They do not quantify detent friction, tooth strain, required torque, or the effect of printed dimensional error.

### Indexing — pass for alignment and isolation geometry

- The source binds rotor notches at local -45, +75, and +195 degrees to rotor poses 0, -120, and -240 degrees, placing each notch at the fixed -45-degree tooth direction.
- The review-time `measure/check_spec.py` rerun passed with no errors. It measured a 2.950188 mm minimum notch-to-sector web against the 2.50 mm requirement, a 0.30 mm tooth-to-notch-root clearance, zero base bridge under the detent free arc, and 1.796754 mm² root attachment area.
- The product-derived detent view `views/inspection/detent-and-notch.png` visually agrees with the modeled annular cantilever, free tooth, rotor rim, and notch relationship; it adds no force claim.
- This supports three discrete indexing locations in geometry. It does not prove that printed PETG will flex safely, click distinctly, resist back-driving, or survive cycling.

### Capture and assembly path — pass for rigid envelopes

- The main motion manifest records a clear axial rotor loading path over the spindle before the front is installed, blocked rotor withdrawal after the front is installed, and blocked direct front withdrawal with expanded snap heads.
- `cad/moonwake_garden/measure/motion_snap_proxy.json` (SHA-256 `32055aa1a6889927d6c02ceb3bb62b21c20689d09bc192bcafc069c80a0e61f4`) checks the reverse seating line with compressed snap heads. `measure/snap-seating-check.md` (SHA-256 `736740a2323f663a2cdbc16d64b22a417da449adf09b207caa9feb0b5c3f3582`) records clear travel through all 16 samples: a 3.2 mm compressed envelope through four derived 3.4 mm holes.
- The exact expanded head geometry separately uses a 3.8 mm nominal envelope and a 3.9 mm head relief. The snap proxy source `snap_proxy.proxy.py` (SHA-256 `fb4b00d2b34613ac08f3033b52865daa87ba1aa55e7c94643fca06881fee42b2`) explicitly substitutes stem-diameter cylinders only for the seating-path test.
- The exploded stack and snap-detail product-derived views agree with the order rear chassis -> rotor -> front mask and show split prongs above the seating collars.
- Together these checks support a rigid-envelope assembly route and post-assembly axial capture. They do not prove that the exact heads can elastically compress without excessive force, whitening, fracture, inadequate retention, or difficult service removal.

### Optical state isolation — pass geometrically

- The review-time spec audit reproduced selected counts of 5, 6, and 7 at the Cassiopeia, Cygnus, and Ursa Minor poses, respectively; every row had zero nonselected intersections and zero sampled oblique-ray failures.
- Its one-degree full-turn sweep found no pose with multiple complete named beds, zero portal leaks from the sector or notches, zero rear-stem/petal intersections, and a 1.944357 mm minimum rear-chamfer ligament.
- This is source-level planar and sampled-ray evidence consistent with the B-rep build and inspected assembly. It establishes geometric aperture isolation at the encoded samples, not brightness, off-axis performance outside the sampled proxy, constellation recognition, or user discovery.

### Reproducibility — pass

- The full isolated pipeline record `cad/moonwake_garden/measure/verification-pipeline.md` (SHA-256 `e691dcd7340c782586c486476bd19b7ccc95e9ce057fc0a7c8d118093c53dc8b`) records exit zero for fresh generation, strict fit, the custom audits, the main motion manifest, nine kernel inspection requests, exports, mesh checks, and thickness checks.
- `cad/moonwake_garden/measure/fresh-output-reproducibility.json` (SHA-256 `df437a1c3f0199c2975eebe4710b6344efe6ae9936f0c954ee804f81c9f72e12`) records two separately copied project directories built in independent Python processes. All four declared STEP outputs and all declared GLB/STL exports were byte-identical; the combined STEP hash matches the sealed root STEP.

## Evidence boundary and follow-up

No implementation or concept repair is required for this digital mechanical check. Release claims must remain bounded to nominal digital geometry. A physical validation program would still need same-material/process snap and detent coupons, measured insertion/retention/operating force, bidirectional cycle testing, inspection for whitening or fracture, and an actual printed assembly-fit/optical-use observation. Those absent tests are limitations, not contradictions in the sealed digital artifact.
